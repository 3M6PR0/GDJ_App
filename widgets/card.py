from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSlot as Slot
from PyQt5.QtGui import QIcon
from utils.icon_loader import get_icon_path # Assumer que utils est accessible depuis widgets

# --- Widget Vignette --- 
class EntryVignetteWidget(QWidget):
    def __init__(self, entry_data, entry_type, parent=None):
        super().__init__(parent)
        self.entry_data = entry_data
        self.entry_type = entry_type
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(5)

        # --- Header --- 
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(5, 5, 5, 5)

        # Infos Clés (à adapter par type)
        date_str = "Date Inconnue"
        amount_str = "Montant Inconnu"
        # --- Standardiser l'accès à la date et au montant --- 
        date_val = getattr(self.entry_data, 'date', None) # Suppose une propriété 'date'
        if date_val:
            date_str = date_val.strftime("%Y-%m-%d")
            
        # Pour le montant, besoin d'une propriété standardisée aussi (ex: 'total')
        amount_val = getattr(self.entry_data, 'total', None) 
        if amount_val is not None:
            amount_str = f"{amount_val:.2f} $"
        # -------------------------------------------------------

        header_info = f"{date_str} - {self.entry_type} - {amount_str}"
        info_label = QLabel(header_info)
        info_label.setStyleSheet("font-weight: bold;")

        self.toggle_button = QPushButton()
        self.toggle_button.setIcon(QIcon(get_icon_path("arrow_right.png"))) # Icône initiale (replié)
        self.toggle_button.setFixedSize(20, 20)
        self.toggle_button.setFlat(True)
        self.toggle_button.setObjectName("VignetteToggleButton")
        self.toggle_button.setCheckable(True) # Le bouton garde son état
        self.toggle_button.toggled.connect(self._toggle_details)

        header_layout.addWidget(info_label, 1) # Prend l'espace
        header_layout.addWidget(self.toggle_button)
        header_widget.setObjectName("VignetteHeader")
        # Optionnel: Ajouter un style au header via QSS
        # header_widget.setStyleSheet("background-color: #444;") 

        # --- Détails (initialement cachés) --- 
        self.details_widget = QWidget()
        details_layout = QFormLayout(self.details_widget)
        details_layout.setContentsMargins(10, 5, 5, 5)
        details_layout.setSpacing(5)

        # Peupler les détails en fonction du type
        # TODO: Remplir ce layout avec les champs spécifiques de self.entry_data
        # Exemple simple:
        for attr, value in vars(self.entry_data).items():
            # Exclure les champs déjà dans le header ou non pertinents
            if attr not in ['date', 'total', '_sa_instance_state']: # Adapter les exclusions
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
        self.toggle_button.setIcon(QIcon(get_icon_path(icon_name)))
# --- Fin Widget Vignette --- 