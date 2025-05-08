"""
Widget personnalisé combinant un QLineEdit et un bouton pour ouvrir un QCalendarWidget,
remplaçant QDateEdit pour permettre un style QSS complet.
"""

from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QHBoxLayout, QCalendarWidget, 
    QApplication, QStyle, QSizePolicy, QToolButton, QComboBox, QSpinBox, QLabel, QSpacerItem,
    QTableView, QFrame, QVBoxLayout # AJOUT: QTableView, QFrame, QVBoxLayout
)
from PyQt5.QtCore import QDate, pyqtSignal, Qt, QPoint, QMargins, QSize, QRectF
from PyQt5.QtGui import QIcon, QPalette, QColor, QTextCharFormat, QBrush, QPainter, QPen # AJOUT: QTextCharFormat, QBrush, QPainter, QPen, QRectF

# --- Import du loader d'icônes du projet --- 
from utils import icon_loader

# --- AJOUT: Import logging ---
import logging
# Utiliser un logger spécifique au module pour plus de clarté
logger = logging.getLogger('GDJ_App') # MODIFIÉ pour utiliser le logger GDJ_App
# -----------------------------

class CustomDateEdit(QWidget):
    """
    Un widget simulant QDateEdit avec un LineEdit stylisable et un bouton calendrier.
    """
    dateChanged = pyqtSignal(QDate)

    def __init__(self, date=None, parent=None):
        super().__init__(parent)
        logger.debug("CustomDateEdit __init__ appelé") # Log de test
        
        if date is None:
            date = QDate.currentDate()
            
        self._date = date
        self._format = "yyyy-MM-dd" # Format d'affichage par défaut

        # --- AJOUT: Labels pour mois et année ---
        self.month_label = QLabel(self)
        self.year_label = QLabel(self)
        # ---------------------------------------
        self.calendar_frame = None

        self._init_ui()
        self.setDate(self._date) # Met à jour le LineEdit initial

    def _init_ui(self):
        # logger.critical("!!!!!!!!!! CUSTOM_DATE_EDIT _init_ui COMMENCE ICI !!!!!!!!!!") # Log de test très visible
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Pas de marges externes
        self.main_layout.setSpacing(0) # Pas d'espacement entre lineedit et bouton

        # --- QLineEdit ---
        self.line_edit = QLineEdit(self)
        # S'assurer qu'il prend la politique de taille horizontale par défaut (Expanding)
        self.line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) 
        # Le style (bordure, fond, padding) viendra du QSS global pour QLineEdit
        # On pourrait le rendre non-éditable si l'on préfère forcer la sélection via calendrier
        # self.line_edit.setReadOnly(True) 
        self.line_edit.textChanged.connect(self._on_text_changed) # Pour validation si édition manuelle

        # --- Bouton Calendrier ---
        self.calendar_button = QPushButton(self)
        self.calendar_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Style du bouton (taille, icône) à définir
        self._set_button_icon() # Appel méthode pour configurer l'icône
        self.calendar_button.setFocusPolicy(Qt.NoFocus) # Éviter qu'il prenne le focus
        self.calendar_button.setObjectName("CalendarButton") # Pour stylage QSS potentiel

        # --- S'assurer que le bouton a une taille minimale même si l'icône ne charge pas ---
        # On utilise sizeHint du LineEdit comme référence pour la hauteur
        button_height = self.line_edit.sizeHint().height()
        self.calendar_button.setMinimumSize(button_height, button_height)

        self.calendar_button.clicked.connect(self._show_calendar)

        # --- Ajout au Layout ---
        self.main_layout.addWidget(self.line_edit)
        self.main_layout.addWidget(self.calendar_button)

        # --- Conteneur QWidget pour le Popup Calendrier ---
        self.calendar_frame = QWidget(self) # <<< CHANGÉ QFrame EN QWidget
        self.calendar_frame.setObjectName("CalendarFrame") # Garder le nom pour QSS
        self.calendar_frame.setWindowFlags(Qt.Window | Qt.FramelessWindowHint) # <<< CHANGÉ LES FLAGS
        # self.calendar_frame.setAttribute(Qt.WA_TranslucentBackground, True) # <<< RETIRÉ POUR TEST

        frame_layout = QVBoxLayout(self.calendar_frame)
        frame_layout.setContentsMargins(1,1,1,1) # <<< REMETTRE MARGE ICI

        # --- Calendrier (enfant du QWidget conteneur) ---
        self.calendar_widget = QCalendarWidget(self.calendar_frame)
        self.calendar_widget.setObjectName("CustomDateEditCalendar")
        self.calendar_widget.setAttribute(Qt.WA_StyledBackground, True)
        self.calendar_widget.setFirstDayOfWeek(Qt.Sunday)
        self.calendar_widget.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar_widget.setSelectedDate(self._date)
        self.calendar_widget.clicked[QDate].connect(self._on_calendar_date_selected)
        
        frame_layout.addWidget(self.calendar_widget)

        # --- MODIFICATION: Remplacer ComboBox/SpinBox par des QLabel personnalisés (dans le calendrier) ---
        navigation_bar = self.calendar_widget.findChild(QWidget, "qt_calendar_navigationbar")
        if navigation_bar:
            nav_layout = navigation_bar.layout() # Obtenir le layout de la barre de navigation
            if not nav_layout:
                nav_layout = QHBoxLayout(navigation_bar)
                navigation_bar.setLayout(nav_layout)
                nav_layout.setContentsMargins(2,2,2,2)
                nav_layout.setSpacing(5) # Augmenter l'espacement par défaut si on le crée
            else:
                # Si le layout existe déjà, on ajuste son espacement
                nav_layout.setSpacing(5) # AJOUT: Définir l'espacement

            # Masquer les boutons Précédent/Suivant
            nav_buttons = navigation_bar.findChildren(QToolButton)
            for btn in nav_buttons:
                btn.setVisible(False)
            
            # Masquer le ComboBox du mois et le SpinBox de l'année originaux
            month_combo_orig = navigation_bar.findChild(QComboBox)
            if month_combo_orig:
                month_combo_orig.setVisible(False)
                # Supprimer du layout si possible pour éviter qu'il prenne de la place cachée
                # nav_layout.removeWidget(month_combo_orig) 
                
            year_spin_orig = navigation_bar.findChild(QSpinBox)
            if year_spin_orig:
                year_spin_orig.setVisible(False)
                # nav_layout.removeWidget(year_spin_orig)

            # Configurer et ajouter nos labels personnalisés
            # Il faudra peut-être ajuster l'ordre ou ajouter des spacers
            # pour un bon alignement. Pour l'instant, on les ajoute simplement.
            
            # Supprimer tous les widgets existants du layout pour le reconstruire proprement
            # (plus sûr que de tenter d'insérer au bon endroit)
            while nav_layout.count():
                child = nav_layout.takeAt(0)
                if child.widget():
                    child.widget().setVisible(False) # Masquer au lieu de supprimer pour éviter crash si Qt y réfère encore
                    # child.widget().deleteLater() # Alternativement, si on est sûr
            
            # Style pour les labels (peut être dans _apply_calendar_widget_styles aussi)
            text_color_primary = QApplication.instance().property("COLOR_TEXT_PRIMARY") or "#FFFFFF"
            label_font_weight = "bold" # ou normal
            self.month_label.setStyleSheet(f"color: {text_color_primary}; font-weight: {label_font_weight};")
            self.year_label.setStyleSheet(f"color: {text_color_primary}; font-weight: {label_font_weight};")

            # Ajouter les éléments dans l'ordre souhaité: Spacer, Mois, Année, Spacer
            nav_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
            nav_layout.addWidget(self.month_label)
            nav_layout.addWidget(self.year_label)
            nav_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

            self._update_month_year_labels() # Initialiser le texte
            self.calendar_widget.currentPageChanged.connect(self._update_month_year_labels)

        # --- MODIFIÉ: Appliquer setStyleSheet directement au QHeaderView horizontal --- (SECTION À COMMENTER)
        # calendar_view = self.calendar_widget.findChild(QTableView, "qt_calendar_calendarview")
        # if calendar_view:
        #     horizontal_header = calendar_view.horizontalHeader()
        #     if horizontal_header:
        #         logger.debug("Trouvé horizontalHeader du QTableView. Tentative d'application de setStyleSheet direct.")
        #         
        #         # Récupérer les couleurs nécessaires (assurez-vous que ces propriétés sont disponibles)
        #         app = QApplication.instance()
        #         color_bg_dark_str = app.property("COLOR_BACKGROUND_DARK") or "#2C2C2C"
        #         color_text_secondary_str = app.property("COLOR_TEXT_SECONDARY") or "#B0B0B0"
        #         color_border_str = app.property("COLOR_BORDER") or "#505050"

        #         header_qss = f"""
        #             QHeaderView::section:horizontal {{
        #                 background-color: {color_bg_dark_str};
        #                 color: {color_text_secondary_str};
        #                 border: none; /* Empêche les bordures individuelles de section */
        #                 border-bottom: 1px solid {color_border_str}; /* Bordure sous les jours */
        #                 font-weight: bold;
        #                 padding: 4px 2px; /* padding vertical, padding horizontal réduit */
        #             }}
        #         """
        #         # horizontal_header.setVisible(True) # Supprimé car créait un nouveau header
        #         horizontal_header.setStyleSheet(header_qss)
        #         # horizontal_header.update() # Peut être nécessaire si le style ne s'applique pas immédiatement
        #     else:
        #          logger.warning("horizontalHeader non trouvé pour qt_calendar_calendarview lors de l'application directe de QSS.")
        # else:
        #     logger.warning("QTableView qt_calendar_calendarview non trouvé lors de l'application directe de QSS au header.")
        # --- FIN DE LA SECTION COMMENTÉE ---

        # --- DÉBUT DU CODE DE DIAGNOSTIC (COMMENTÉ) ---
        # logger.debug("--- Début de l'inspection des enfants du QCalendarWidget ---")
        # La fonction inspect_children n'est plus utilisée, findChildren(QWidget) est déjà récursif.
        
        # all_child_widgets = self.calendar_widget.findChildren(QWidget) # Trouve tous les QWidget enfants, récursivement

        # logger.debug("Liste de tous les QWidget enfants (récursif via findChildren):")
        # for i, child in enumerate(all_child_widgets):
        #     try:
        #         class_name = child.metaObject().className()
        #         object_name = child.objectName()
        #         parent_widget = child.parentWidget()
        #         parent_class_name = parent_widget.metaObject().className() if parent_widget else 'None'
        #         parent_object_name = parent_widget.objectName() if parent_widget and parent_widget.objectName() else '-'
        #         logger.debug(f"  Widget {i}: {class_name}, NomObjet: '{object_name if object_name else '-'}', Visible: {child.isVisible()}, Parent: {parent_class_name} ('{parent_object_name}')")
        #     except Exception as e:
        #         logger.debug(f"  Erreur lors de l'inspection du widget {i}: {e}")

        # logger.debug("--- Fin de l'inspection des enfants du QCalendarWidget ---")
        # --- FIN DU CODE DE DIAGNOSTIC ---

        # Commenter les logs CRITICAL superflus
        # logger.critical("!!!!!!!!!! CUSTOM_DATE_EDIT _init_ui COMMENCE ICI !!!!!!!!!!")
        # logger.critical("!!!!!!!!!! CUSTOM_DATE_EDIT _init_ui JUSTE AVANT apply_internal_styles !!!!!!!!!!") 
        self._apply_internal_styles()
        self._apply_calendar_widget_styles() # AJOUT: Appliquer les styles au QCalendarWidget

    def _set_button_icon(self):
        # --- Utilisation de la fonction de gestion d'icônes du projet --- 
        icon_name = "round_calendar_month.png" # Nom de l'icône fournie
        icon_path = icon_loader.get_icon_path(icon_name)
        if icon_path:
            icon = QIcon(icon_path)
            self.calendar_button.setIcon(icon)
            # Définir une taille d'icône raisonnable (peut être ajustée)
            button_height = self.line_edit.sizeHint().height() 
            # Viser une icône légèrement plus petite que la hauteur totale pour marge
            icon_size = max(16, button_height - 6) 
            self.calendar_button.setIconSize(QSize(icon_size, icon_size))
            self.calendar_button.setText("") # Retirer texte si icône chargée
        else:
            # Fallback si l'icône n'est pas trouvée
            print(f"WARNING: CustomDateEdit - Icône '{icon_name}' non trouvée.")
            self.calendar_button.setText("...") # Texte de secours
            self.calendar_button.setIcon(QIcon()) # Icône vide
        
    def _apply_internal_styles(self):
        # Ajuste la taille du bouton pour correspondre à la hauteur calculée du QLineEdit
        # et s'assure qu'il n'y a pas de bordure ou de fond par défaut sur le bouton
        # pour mieux s'intégrer visuellement avec le QLineEdit.
        button_height = self.line_edit.sizeHint().height()
        # Rendre le bouton carré
        button_width = button_height 
        self.calendar_button.setFixedSize(button_width, button_height)

        # Style QSS interne pour le bouton, peut être surchargé par global.qss
        # Essayer de le rendre visuellement intégré au QLineEdit
        
        # --- Récupérer les couleurs du thème avec fallback ---
        app_instance = QApplication.instance()
        default_hover_color = "#555555" # Gris foncé pour survol
        default_pressed_color = "#666666" # Gris un peu plus clair pour appui
        
        color_item_hover = app_instance.property('COLOR_ITEM_HOVER') if app_instance else default_hover_color
        color_accent_pressed = app_instance.property('COLOR_ACCENT_PRESSED') if app_instance else default_pressed_color
        
        # Assurer que ce sont des strings, même si la propriété retourne None
        if color_item_hover is None:
            color_item_hover = default_hover_color
        if color_accent_pressed is None:
            color_accent_pressed = default_pressed_color
        # ------------------------------------------------------

        self.calendar_button.setStyleSheet(f"""
            QPushButton#CalendarButton {{
                border: none; /* Pas de bordure propre */
                background-color: transparent; /* Fond transparent par défaut */
                padding: 0px; /* Pas de padding interne */
                /* Laisser la couleur du texte/icône hériter ou être définie globalement */
            }}
            QPushButton#CalendarButton:hover {{
                 background-color: {color_item_hover}; /* Utiliser variable lue ou défaut */
            }}
            QPushButton#CalendarButton:pressed {{
                 background-color: {color_accent_pressed}; /* Utiliser variable lue ou défaut */
            }}
        """)
           
        # Style pour le QLineEdit interne pour retirer le coin arrondi droit
        # afin qu'il s'assemble bien avec le bouton
        current_radius = self.line_edit.property("borderRadius") # Lire depuis QSS ou défaut
        # --- Ajouter un fallback pour current_radius ---
        if current_radius is None: 
            current_radius = "0px" # Mettre défaut si non trouvé
        # --------------------------------------------
        
        self.line_edit.setStyleSheet(f"""
            QLineEdit {{
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                /* Conserver les autres styles (bordure, fond, padding...) via QSS global */
            }}
        """)

    def _show_calendar(self):
        """ Affiche le QFrame contenant le QCalendarWidget sous le bouton. """
        button_pos = self.calendar_button.mapToGlobal(QPoint(0, 0))
        # Positionner le frame sous le bouton
        self.calendar_frame.move(button_pos.x(), button_pos.y() + self.calendar_button.height())
        self.calendar_widget.setSelectedDate(self._date) # S'assurer que la date actuelle est sélectionnée
        self.calendar_frame.show()
        self.calendar_widget.setFocus() # Mettre le focus sur le calendrier pour la navigation clavier

    def _on_calendar_date_selected(self, date):
        """ Met à jour la date lorsque sélectionnée dans le calendrier. """
        if self.calendar_frame:
            self.calendar_frame.hide()
        self.setDate(date)

    def _on_text_changed(self, text):
        """ (Optionnel) Valide la date si modifiée manuellement dans QLineEdit. """
        # Tenter de parser la date selon le format
        parsed_date = QDate.fromString(text, self._format)
        if parsed_date.isValid():
            # Vérifier si la date interne est différente pour éviter boucle de signaux
            if parsed_date != self._date:
                self._date = parsed_date
                # Mettre à jour la sélection du calendrier pour la prochaine ouverture
                self.calendar_widget.setSelectedDate(self._date) 
                self.dateChanged.emit(self._date)
        else:
            # Gérer l'erreur de format (ex: remettre l'ancienne date, indiquer erreur)
            # Pour l'instant, on remet l'ancienne date valide
            self.line_edit.blockSignals(True)
            self.line_edit.setText(self._date.toString(self._format))
            self.line_edit.blockSignals(False)
            # Peut-être ajouter un tooltip ou changer la couleur de bordure temporairement

    # --- Méthodes publiques simulant QDateEdit ---
    
    def date(self):
        """ Retourne la QDate actuelle. """
        return self._date

    def setDate(self, date):
        """ Définit la QDate et met à jour l'affichage. """
        if isinstance(date, QDate) and date.isValid():
            if date != self._date:
                self._date = date
                self.line_edit.blockSignals(True) # Éviter déclenchement de _on_text_changed
                self.line_edit.setText(self._date.toString(self._format))
                self.line_edit.blockSignals(False)
                self.calendar_widget.setSelectedDate(self._date) # Pour la prochaine ouverture
                self.dateChanged.emit(self._date) # Émettre le signal

    def setDateFormat(self, format_str):
        """ Définit le format d'affichage de la date. """
        self._format = format_str
        # Mettre à jour l'affichage immédiatement
        self.line_edit.setText(self._date.toString(self._format))

    def dateFormat(self):
        """ Retourne le format d'affichage actuel. """
        return self._format
        
    def setCalendarPopup(self, enable):
        # Cette méthode existe sur QDateEdit, on la fournit pour compatibilité
        # mais notre widget a toujours un popup.
        pass # Ne fait rien fonctionnellement ici

    def calendarPopup(self):
        # Pour compatibilité
        return True

    # --- AJOUT: Méthodes pour définir la plage de dates --- 
    def setMinimumDate(self, date):
        """Définit la date minimale sélectionnable dans le calendrier popup."""
        if isinstance(date, QDate) and date.isValid():
            if hasattr(self, 'calendar_widget'):
                self.calendar_widget.setMinimumDate(date)
            else:
                # Log ou avertissement si le calendrier n'existe pas encore?
                print("Avertissement: Impossible de définir la date minimale, calendar_widget non trouvé.")
        
    def setMaximumDate(self, date):
        """Définit la date maximale sélectionnable dans le calendrier popup."""
        if isinstance(date, QDate) and date.isValid():
            if hasattr(self, 'calendar_widget'):
                self.calendar_widget.setMaximumDate(date)
            else:
                 print("Avertissement: Impossible de définir la date maximale, calendar_widget non trouvé.")
    # -----------------------------------------------------

    # --- AJOUT: Méthode pour mettre à jour les labels Mois/Année ---
    def _update_month_year_labels(self, year=None, month=None):
        # Liste des mois en français (peut être déplacée ou rendue configurable)
        MONTHS_FR = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]

        if year is None or month is None:
            year = self.calendar_widget.yearShown()
            month = self.calendar_widget.monthShown() # monthShown() est 1-indexé
        
        month_name = MONTHS_FR[month - 1] if 1 <= month <= 12 else "Mois?"
        
        self.month_label.setText(month_name)
        self.year_label.setText(str(year))
    # ------------------------------------------------------------

    # --- AJOUT: Méthode pour styler QCalendarWidget directement en Python ---
    def _apply_calendar_widget_styles(self):
        app = QApplication.instance()

        # Récupérer les couleurs du thème avec des valeurs de secours
        COLOR_BACKGROUND_LIGHT = app.property("COLOR_BACKGROUND_LIGHT") or "#3F3F3F"
        COLOR_TEXT_PRIMARY = app.property("COLOR_TEXT_PRIMARY") or "#FFFFFF"
        COLOR_BORDER = app.property("COLOR_BORDER") or "#505050"
        COLOR_BACKGROUND_DARK = app.property("COLOR_BACKGROUND_DARK") or "#2C2C2C"
        COLOR_PRIMARY_MEDIUM = app.property("COLOR_PRIMARY_MEDIUM") or "#353535" # Pour le fond des headers
        COLOR_ITEM_HOVER = app.property("COLOR_ITEM_HOVER") or "#4A4A4A"
        COLOR_ACCENT_PRESSED = app.property("COLOR_ACCENT_PRESSED") or "#005A9E"
        COLOR_TEXT_SECONDARY = app.property("COLOR_TEXT_SECONDARY") or "#B0B0B0" # Pour le texte des headers
        COLOR_ACCENT = app.property("COLOR_ACCENT") or "#0078D4"
        COLOR_TEXT_ON_ACCENT = app.property("COLOR_TEXT_ON_ACCENT") or "#FFFFFF"
        COLOR_TEXT_DISABLED = app.property("COLOR_TEXT_DISABLED") or "#808080"
        COLOR_ACCENT_LIGHT = app.property("COLOR_ACCENT_LIGHT") or "#50A6F0"
        RADIUS_DEFAULT = app.property("RADIUS_DEFAULT") or "3px"
        
        if not isinstance(RADIUS_DEFAULT, str):
            RADIUS_DEFAULT = f"{RADIUS_DEFAULT}px"

        # logger.debug(f"[Calendar Styles Update] COLOR_PRIMARY_MEDIUM: {COLOR_PRIMARY_MEDIUM}, COLOR_TEXT_SECONDARY: {COLOR_TEXT_SECONDARY}, COLOR_BORDER: {COLOR_BORDER}")

        # Appliquer le style des en-têtes via QTextCharFormat (garder ceci)
        logger.debug("Tentative de style des en-têtes via setHeaderTextFormat.")
        header_format = QTextCharFormat()
        try:
            header_format.setBackground(QBrush(QColor(COLOR_PRIMARY_MEDIUM)))
            header_format.setForeground(QBrush(QColor(COLOR_TEXT_SECONDARY)))
            font = header_format.font()
            font.setBold(True)
            header_format.setFont(font)
            self.calendar_widget.setHeaderTextFormat(header_format)
            logger.debug(f"setHeaderTextFormat appliqué avec fond {COLOR_PRIMARY_MEDIUM} et texte {COLOR_TEXT_SECONDARY}")
        except Exception as e:
            logger.error(f"Erreur lors de l'application de setHeaderTextFormat: {e}", exc_info=True)
            
        # MAINTENANT: Appliquer un style COMPLET et direct au CONTENEUR (calendar_frame)
        logger.debug("Application directe de QSS COMPLET au conteneur QWidget#CalendarFrame")
        container_direct_qss = f"""\
            QWidget#CalendarFrame {{ /* Cibler spécifiquement par ID */
                background-color: {COLOR_BACKGROUND_LIGHT}; 
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px; /* <<< VALEUR AUGMENTÉE */
                background-clip: border-box; /* Important */
            }}
        """ 
        self.calendar_frame.setStyleSheet(container_direct_qss)
        logger.debug(f"Style complet appliqué directement au frame: {container_direct_qss}")

    # ------------------------------------------------------------------

    # On pourrait ajouter setMinimumDate, setMaximumDate, etc. si nécessaire
    # en les passant au QCalendarWidget. 