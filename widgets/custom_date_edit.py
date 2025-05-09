"""
Widget personnalisé combinant un QLineEdit et un bouton pour ouvrir un QCalendarWidget,
remplaçant QDateEdit pour permettre un style QSS complet.
"""

from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QHBoxLayout, QCalendarWidget, 
    QApplication, QStyle, QSizePolicy, QToolButton, QComboBox, QSpinBox, QLabel, QSpacerItem,
    QTableView, QFrame, QVBoxLayout # AJOUT: QTableView, QFrame, QVBoxLayout
)
from PyQt5.QtCore import QDate, pyqtSignal, Qt, QPoint, QMargins, QSize, QRectF, QEvent # AJOUTER QEvent
from PyQt5.QtGui import QIcon, QPalette, QColor, QTextCharFormat, QBrush, QPainter, QPen # AJOUT: QTextCharFormat, QBrush, QPainter, QPen, QRectF

# --- Import du loader d'icônes du projet --- 
from utils import icon_loader

# --- AJOUT: Import logging ---
import logging
# Utiliser un logger spécifique au module pour plus de clarté
logger = logging.getLogger('GDJ_App') # MODIFIÉ pour utiliser le logger GDJ_App
# -----------------------------

# Import du nouveau calendrier
from .calendar import Calendar 

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

        # Installer le filtre d'événements pour gérer les clics en dehors
        QApplication.instance().installEventFilter(self)

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
        self.line_edit.editingFinished.connect(self._handle_input_validation) # NOUVELLE CONNEXION

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
        self.calendar_frame = QWidget(self)
        self.calendar_frame.setObjectName("CalendarFrame")
        self.calendar_frame.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.Popup) # Ajout de Qt.Popup peut aider
        frame_layout = QVBoxLayout(self.calendar_frame)
        frame_layout.setContentsMargins(1,1,1,1)
        
        self.calendar_widget = Calendar(initial_date=self._date, parent=self.calendar_frame) 
        self.calendar_widget.setObjectName("CustomDateEditCalendar")
        
        if hasattr(self.calendar_widget, 'setFirstDayOfWeek'):
            self.calendar_widget.setFirstDayOfWeek(Qt.Sunday) 
        
        # Connecter le signal dateSelected de notre nouveau Calendar
        if hasattr(self.calendar_widget, 'dateSelected'):
            self.calendar_widget.dateSelected.connect(self._on_calendar_date_selected)
        
        # Les autres appels aux méthodes de QCalendarWidget restent commentés
        # if hasattr(self.calendar_widget, 'setVerticalHeaderFormat'): self.calendar_widget.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)       
        
        frame_layout.addWidget(self.calendar_widget)

        # --- La barre de navigation personnalisée devra être recréée DANS notre Calendar widget ---
        # Pour l'instant, on commente tout ce qui concerne l'ancienne barre de navigation
        # navigation_bar = self.calendar_widget.findChild(QWidget, "qt_calendar_navigationbar")
        # if navigation_bar:
        #     nav_layout = navigation_bar.layout()
        #     if not nav_layout:
        #         nav_layout = QHBoxLayout(navigation_bar)
        #         navigation_bar.setLayout(nav_layout)
        #         nav_layout.setContentsMargins(2,2,2,2)
        #         nav_layout.setSpacing(5)
        #     else:
        #         nav_layout.setSpacing(5)

        #     nav_buttons = navigation_bar.findChildren(QToolButton)
        #     for btn in nav_buttons:
        #         btn.setVisible(False)
            
        #     month_combo_orig = navigation_bar.findChild(QComboBox)
        #     if month_combo_orig:
        #         month_combo_orig.setVisible(False)
                
        #     year_spin_orig = navigation_bar.findChild(QSpinBox)
        #     if year_spin_orig:
        #         year_spin_orig.setVisible(False)

        #     while nav_layout.count():
        #         child = nav_layout.takeAt(0)
        #         if child.widget():
        #             child.widget().setVisible(False)
            
        #     text_color_primary = QApplication.instance().property("COLOR_TEXT_PRIMARY") or "#FFFFFF"
        #     label_font_weight = "bold"
        #     self.month_label.setStyleSheet(f"color: {text_color_primary}; font-weight: {label_font_weight};")
        #     self.year_label.setStyleSheet(f"color: {text_color_primary}; font-weight: {label_font_weight};")

        #     nav_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        #     nav_layout.addWidget(self.month_label)
        #     nav_layout.addWidget(self.year_label)
        #     nav_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        #     self._update_month_year_labels() 
        #     self.calendar_widget.currentPageChanged.connect(self._update_month_year_labels) # Ce signal n'existe pas encore

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
            logger.warning(f"CustomDateEdit - Icône '{icon_name}' non trouvée.")
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
        # S'assurer que le calendrier affiche la date actuelle du CustomDateEdit
        if hasattr(self.calendar_widget, 'setDate'):
            self.calendar_widget.setDate(self._date)
        self.calendar_frame.move(button_pos.x(), button_pos.y() + self.calendar_button.height())
        self.calendar_frame.show()
        self.calendar_frame.raise_() # S'assurer qu'il est au-dessus des autres
        # if hasattr(self.calendar_widget, 'setFocus'): self.calendar_widget.setFocus() # Commenté pour l'instant

    def _on_calendar_date_selected(self, date):
        """ Met à jour la date lorsque sélectionnée dans le calendrier. """
        if self.calendar_frame:
            self.calendar_frame.hide()
        self.setDate(date)
        # Le signal self.calendar_widget.clicked[QDate] est commenté, donc cette méthode
        # ne sera plus appelée directement par le calendrier pour l'instant.
        # Il faudra un nouveau signal depuis notre Calendar personnalisé.

    def _handle_input_validation(self): # Anciennement _on_text_changed
        text = self.line_edit.text() # Lire le texte actuel du QLineEdit
        ref_year = self._date.year()
        ref_month = self._date.month()
        original_day = self._date.day()

        day_to_set = -1
        temp_date = QDate.fromString(text, self._format)

        if temp_date.isValid():
            # Si le texte est une date valide, on vérifie si l'année et le mois
            # correspondent à notre date de référence. Si oui, on prend le jour.
            if temp_date.year() == ref_year and temp_date.month() == ref_month:
                day_to_set = temp_date.day()
            else:
                # Année/mois ont été modifiés dans le QLineEdit pour former une date valide
                # mais différente de notre référence. On réinitialise à self._date.
                self.setDate(self._date) # Ceci reformatera le QLineEdit
                return
        else:
            # Le parsing complet a échoué. Tentons d'extraire juste le jour.
            parts = text.split('-')
            if len(parts) == 3:
                try:
                    # On s'attend à ce que l'année et le mois dans le texte soient ceux de référence.
                    # Si ce n'est pas le cas, l'entrée est considérée comme trop invalide pour une correction ciblée du jour.
                    if int(parts[0]) == ref_year and int(parts[1]) == ref_month:
                        if parts[2]: # S'assurer qu'il y a une chaîne pour le jour
                            day_to_set = int(parts[2])
                        else: # Jour effacé (chaîne vide)
                            day_to_set = original_day # Rétablir l'ancien jour
                    else:
                        self.setDate(self._date)
                        return
                except ValueError: # Jour ou autre partie n'est pas un entier valide
                    self.setDate(self._date) # Réinitialiser
                    return
            else:
                # Le format n'est plus yyyy-MM-dd
                self.setDate(self._date) # Réinitialiser
                return

        if day_to_set != -1:
            if day_to_set < 1:
                final_day = 1
            else:
                days_in_ref_month = QDate(ref_year, ref_month, 1).daysInMonth()
                if day_to_set > days_in_ref_month:
                    final_day = days_in_ref_month
                else:
                    final_day = day_to_set
            
            new_date = QDate(ref_year, ref_month, final_day)
            self.setDate(new_date)
        else:
            # Si aucun jour n'a pu être déterminé, réinitialiser (devrait être couvert par les cas ci-dessus)
            self.setDate(self._date)

    # --- Méthodes publiques simulant QDateEdit ---
    
    def date(self):
        """ Retourne la QDate actuelle. """
        return self._date

    def setDate(self, date: QDate):
        """ Définit la QDate et met à jour l'affichage. """
        if isinstance(date, QDate) and date.isValid():
            date_has_changed = (date != self._date)
            
            self._date = date 

            current_text_in_line_edit = self.line_edit.text()
            expected_text = self._date.toString(self._format)
            if current_text_in_line_edit != expected_text:
                self.line_edit.blockSignals(True)
                self.line_edit.setText(expected_text)
                # Placer le curseur à la fin de la partie jour pour faciliter l'édition suivante
                day_str_len = len(str(self._date.day()))
                # Format "yyyy-MM-dd" -> jour à la fin
                cursor_pos = len(expected_text) 
                if self._format == "yyyy-MM-dd": # Si c'est notre format standard
                    pass # len(expected_text) est déjà bon
                # Si on avait un format comme "dd/MM/yyyy", il faudrait calculer autrement
                self.line_edit.setCursorPosition(cursor_pos)
                self.line_edit.blockSignals(False)
            
            if hasattr(self.calendar_widget, 'setDate'):
                self.calendar_widget.setDate(self._date)
            
            if date_has_changed:
                self.dateChanged.emit(self._date)

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
                logger.warning("CustomDateEdit: Calendar widget n'a pas de méthode setMinimumDate.")
        
    def setMaximumDate(self, date):
        """Définit la date maximale sélectionnable dans le calendrier popup."""
        if isinstance(date, QDate) and date.isValid():
            if hasattr(self, 'calendar_widget'):
                self.calendar_widget.setMaximumDate(date)
            else:
                 logger.warning("CustomDateEdit: Calendar widget n'a pas de méthode setMaximumDate.")
    # -----------------------------------------------------

    # --- AJOUT: Méthode pour mettre à jour les labels Mois/Année ---
    def _update_month_year_labels(self, year=None, month=None):
        # Cette méthode dépendait de self.calendar_widget.yearShown() et monthShown()
        # qui n'existent pas encore sur notre Calendar.
        # Pour l'instant, nous allons la désactiver ou la faire retourner des valeurs par défaut.
        # if hasattr(self.calendar_widget, 'yearShown') and hasattr(self.calendar_widget, 'monthShown'):
        #     year = self.calendar_widget.yearShown()
        #     month = self.calendar_widget.monthShown()
        # else:
        #     current_dt = QDate.currentDate()
        #     year = current_dt.year()
        #     month = current_dt.month()
        pass # Temporairement, ne fait rien

        # MONTHS_FR = [
        #     "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
        #     "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        # ]
        # month_name = MONTHS_FR[month - 1] if 1 <= month <= 12 else "Mois?"
        # self.month_label.setText(month_name)
        # self.year_label.setText(str(year))
    
    def _apply_calendar_widget_styles(self):
        app = QApplication.instance()

        COLOR_BACKGROUND_LIGHT = app.property("COLOR_BACKGROUND_LIGHT") or "#3F3F3F"
        COLOR_TEXT_PRIMARY = app.property("COLOR_TEXT_PRIMARY") or "#FFFFFF"
        COLOR_BORDER = app.property("COLOR_BORDER") or "#505050"
        COLOR_PRIMARY_MEDIUM = app.property("COLOR_PRIMARY_MEDIUM") or "#353535" 
        # ... (autres couleurs) ...
        RADIUS_DEFAULT = app.property("RADIUS_DEFAULT") or "3px"
        if not isinstance(RADIUS_DEFAULT, str):
            RADIUS_DEFAULT = f"{RADIUS_DEFAULT}px"

        # 1. Styles QSS pour les éléments INTERNES du calendrier
        # Cette section entière cible les sous-éléments de QCalendarWidget, elle n'est plus pertinente
        # pour notre Calendar personnalisé. Nous la commenterons. Le style du Calendar lui-même (s'il est simple)
        # peut être fait via son `paintEvent` ou un style QSS simple sur `CustomCalendarView` (son objectName).

        # calendar_internals_qss = f""" ... """ # TOUT CE BLOC EST COMMENTÉ
        # self.calendar_widget.setStyleSheet(calendar_internals_qss) # COMMENTÉ

        # Notre nouveau widget Calendar a son propre paintEvent pour le fond.
        # Si on veut un fond via QSS sur le widget lui-même (qui a objectName "CustomCalendarView"):
        # self.calendar_widget.setStyleSheet(f"QWidget#CustomCalendarView {{ background-color: {COLOR_PRIMARY_MEDIUM}; border: none; }}")
        # Mais pour l'instant, la couleur est dans le paintEvent de Calendar.

        # 2. Appliquer le style des en-têtes via QTextCharFormat
        # Ceci est spécifique à QCalendarWidget et n'est plus applicable.
        # logger.debug("Application de setHeaderTextFormat pour les en-têtes.")
        # header_format = QTextCharFormat()
        # try:
        #     header_format.setBackground(QBrush(QColor(COLOR_PRIMARY_MEDIUM)))
        # ... (reste de setHeaderTextFormat) ...
        #     self.calendar_widget.setHeaderTextFormat(header_format)
        # except Exception as e:
        #     logger.error(f"Erreur lors de l'application de setHeaderTextFormat: {e}", exc_info=True)
            
        # 3. Appliquer un style direct au CONTENEUR (QWidget#CalendarFrame)
        # CECI RESTE VALIDE ET IMPORTANT pour les coins arrondis globaux du popup.
        logger.debug("Application directe de QSS au conteneur QWidget#CalendarFrame")
        container_direct_qss = (
            f"QWidget#CalendarFrame {{"
            f"    background-color: {COLOR_BACKGROUND_LIGHT}; "
            f"    border: 1px solid {COLOR_BORDER}; "
            f"    border-radius: 10px; "
            f"    background-clip: border-box; "
            f"}}"
        )
        self.calendar_frame.setStyleSheet(container_direct_qss)
        logger.debug(f"Style complet appliqué directement au frame: {container_direct_qss}")

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonPress:
            if self.calendar_frame and self.calendar_frame.isVisible():
                # Vérifier si le clic est en dehors du calendar_frame et non sur le bouton pour l'ouvrir
                # Le QWidget qui a reçu le clic est event.widget() si c'est un MouseEvent sur un QWidget,
                # mais pour les filtres installés sur l'application, `watched` peut être plus pertinent.
                # `QApplication.widgetAt(event.globalPos())` est le plus fiable pour obtenir le widget sous le curseur.
                
                clicked_widget = QApplication.widgetAt(event.globalPos())
                
                # Ne pas fermer si on clique sur le bouton qui ouvre le calendrier
                if clicked_widget == self.calendar_button:
                    return super().eventFilter(watched, event)

                # Vérifier si le clic est à l'intérieur du calendar_frame ou de ses enfants
                is_inside_calendar_popup = False
                temp_widget = clicked_widget
                while temp_widget:
                    if temp_widget == self.calendar_frame:
                        is_inside_calendar_popup = True
                        break
                    temp_widget = temp_widget.parentWidget()
                
                if not is_inside_calendar_popup:
                    self.calendar_frame.hide()
                    # Ne pas changer la date, juste cacher.
                    return True # Événement géré, ne pas le propager davantage pour ce cas.

        return super().eventFilter(watched, event)

    # Il serait bon de désinstaller le filtre dans __del__ ou un équivalent,
    # mais pour simplifier, on suppose que CustomDateEdit vit aussi longtemps que l'application
    # ou est correctement géré par son parent.
    # def __del__(self):
    #     app = QApplication.instance()
    #     if app: # S'assurer que l'application existe toujours
    #         app.removeEventFilter(self)
    #     super().__del__() # Si nécessaire

    # On pourrait ajouter setMinimumDate, setMaximumDate, etc. si nécessaire
    # en les passant au QCalendarWidget. 