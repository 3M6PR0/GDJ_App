# pages/documents/documents_type_selection_page.py # <- Nouveau nom
# Permet à l'utilisateur de choisir le type de nouveau document à créer.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox # Correction: PyQt5

class DocumentsTypeSelectionPage(QWidget): # <- Nom de classe mis à jour
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Créer un nouveau document")
        self.type_label = QLabel("Choisissez le type de document :")
        self.type_combo = QComboBox() # Pour choisir le type
        # Remplir la combobox avec les types disponibles (depuis le contrôleur idéalement)
        # self.type_combo.addItems(["Type A", "Type B", "Type C"])
        self.create_button = QPushButton("Créer")
        self.cancel_button = QPushButton("Annuler")
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_combo)
        layout.addWidget(self.create_button)
        layout.addWidget(self.cancel_button)
        
        self.setLayout(layout)
        print("DocumentsTypeSelectionPage UI initialized") # Debug 