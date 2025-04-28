"""
Widget personnalisé combinant un QLineEdit et un bouton pour ouvrir un QCalendarWidget,
remplaçant QDateEdit pour permettre un style QSS complet.
"""

from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QHBoxLayout, QCalendarWidget, 
    QApplication, QStyle, QSizePolicy
)
from PyQt5.QtCore import QDate, pyqtSignal, Qt, QPoint, QMargins, QSize
from PyQt5.QtGui import QIcon # À utiliser si on choisit une icône fichier/qtawesome

# --- Import du loader d'icônes du projet --- 
from utils import icon_loader

class CustomDateEdit(QWidget):
    """
    Un widget simulant QDateEdit avec un LineEdit stylisable et un bouton calendrier.
    """
    dateChanged = pyqtSignal(QDate)

    def __init__(self, date=None, parent=None):
        super().__init__(parent)
        
        if date is None:
            date = QDate.currentDate()
            
        self._date = date
        self._format = "yyyy-MM-dd" # Format d'affichage par défaut

        self._init_ui()
        self.setDate(self._date) # Met à jour le LineEdit initial

    def _init_ui(self):
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

        # --- Calendrier Popup ---
        self.calendar_widget = QCalendarWidget(self)
        # Utiliser Qt.ToolTip pour un comportement Popup plus robuste
        self.calendar_widget.setWindowFlags(Qt.ToolTip) 
        self.calendar_widget.setFirstDayOfWeek(Qt.Monday)
        self.calendar_widget.setSelectedDate(self._date)
        self.calendar_widget.clicked[QDate].connect(self._on_calendar_date_selected)
        
        self._apply_internal_styles()

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
        """ Affiche le QCalendarWidget sous le bouton. """
        button_pos = self.calendar_button.mapToGlobal(QPoint(0, 0))
        # Positionner sous le bouton
        self.calendar_widget.move(button_pos.x(), button_pos.y() + self.calendar_button.height())
        self.calendar_widget.setSelectedDate(self._date) # S'assurer que la date actuelle est sélectionnée
        self.calendar_widget.show()
        self.calendar_widget.setFocus() # Mettre le focus pour la navigation clavier

    def _on_calendar_date_selected(self, date):
        """ Met à jour la date lorsque sélectionnée dans le calendrier. """
        self.calendar_widget.hide()
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

    # On pourrait ajouter setMinimumDate, setMaximumDate, etc. si nécessaire
    # en les passant au QCalendarWidget. 