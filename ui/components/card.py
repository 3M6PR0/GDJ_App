from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSlot as Slot
from PyQt5.QtGui import QIcon
from utils.icon_loader import get_icon_path # Assumer que utils est accessible depuis widgets
from utils.theme import get_theme_vars, RADIUS_BOX # Importer depuis utils.theme

# --- Widget Card --- # Renommé
class CardWidget(QWidget):
    def __init__(self, entry_data, entry_type, parent=None):
        super().__init__(parent)
        self.entry_data = entry_data
        self.entry_type = entry_type

        # --- Obtenir les variables de thème --- 
        theme = get_theme_vars() # Obtenir le dictionnaire du thème
        self.card_bg_color = theme.get("COLOR_BACKGROUND_2", "#3a3a3a")
        self.card_border_color = theme.get("COLOR_BACKGROUND_4", "#555555")
        self.header_bg_color = theme.get("COLOR_BACKGROUND_3", "#444444") # Optionnel pour header
        # ------------------------------------

        self._setup_ui()

        # --- Appliquer le style après _setup_ui --- 
        self.setStyleSheet(f"""
            CardWidget {{
                border: 1px solid {self.card_border_color};
                border-radius: {RADIUS_BOX}; /* Utiliser le radius global */
                background-color: {self.card_bg_color};
            }}
            QWidget#VignetteHeader {{
                background-color: {self.header_bg_color};
                /* Pas de bordure ici, la bordure est sur CardWidget */
                border-top-left-radius: {RADIUS_BOX};
                border-top-right-radius: {RADIUS_BOX};
            }}
            /* Ajuster le style du bouton si nécessaire */
            QPushButton#VignetteToggleButton {{
                 border: none;
                 background-color: transparent;
            }}
            QPushButton#VignetteToggleButton:hover {{
                background-color: {theme.get("COLOR_BACKGROUND_4", "#555")}; /* Effet léger */
                border-radius: 4px;
            }}
        """)
        # -----------------------------------------

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(5)

        # --- Header --- 
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(5, 5, 5, 5)

        # Infos Clés
        date_str = "Date Inconnue"
        amount_str = "Montant Inconnu"
        date_val = getattr(self.entry_data, 'date', None)
        if date_val:
            date_str = date_val.strftime("%Y-%m-%d")
        amount_val = getattr(self.entry_data, 'total', None) 
        if amount_val is not None:
            amount_str = f"{amount_val:.2f} $"

        header_info = f"{date_str} - {self.entry_type} - {amount_str}"
        info_label = QLabel(header_info)
        info_label.setStyleSheet("font-weight: bold;")

        # --- Bouton pour déplier/replier (à droite) --- 
        self.expand_button = QPushButton()
        self.expand_button.setIcon(QIcon(get_icon_path("arrow_right.png"))) # Utiliser nom sans préfixe
        self.expand_button.setFixedSize(24, 24) # Taille légèrement plus grande?
        self.expand_button.setFlat(True)
        self.expand_button.setObjectName("CardExpandButton") # Nouveau nom d'objet
        self.expand_button.setCheckable(True) 
        self.expand_button.toggled.connect(self._toggle_details)
        # ---------------------------------------------

        header_layout.addWidget(info_label) # Info à gauche
        header_layout.addStretch(1)         # Espace extensible
        header_layout.addWidget(self.expand_button) # Bouton à droite

        header_widget.setObjectName("VignetteHeader") # Garder? Renommer?

        # --- Détails (initialement cachés) --- 
        self.details_widget = QWidget()
        details_layout = QFormLayout(self.details_widget)
        details_layout.setContentsMargins(10, 5, 5, 5)
        details_layout.setSpacing(5)

        # Peupler les détails en fonction du type (Temporaire)
        for attr, value in vars(self.entry_data).items():
            if attr not in ['date', 'total', '_sa_instance_state']: 
                 details_layout.addRow(f"{attr.replace('_', ' ').capitalize()}:", QLabel(str(value)))

        self.details_widget.setVisible(False) # Caché par défaut

        # Ajouter Header et Détails au layout principal
        main_layout.addWidget(header_widget)
        main_layout.addWidget(self.details_widget)

    @Slot(bool)
    def _toggle_details(self, checked):
        self.details_widget.setVisible(checked)
        # Changer l'icône du bouton
        icon_name = "arrow_drop_down.png" if checked else "arrow_right.png"
        self.expand_button.setIcon(QIcon(get_icon_path(icon_name))) # Utiliser noms sans préfixe
# --- Fin Widget Card --- 