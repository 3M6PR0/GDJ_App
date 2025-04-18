# pages/documents/documents_type_selection_page.py # <- Nouveau nom
# Permet à l'utilisateur de choisir le type de nouveau document à créer.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.components.frame import Frame

class DocumentsTypeSelectionPage(QWidget):
    # Ajouter les signaux manquants
    create_requested = pyqtSignal(str) # Émet le type de document choisi
    cancel_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentsTypeSelectionPageWidget") # Ajouter ID si besoin
        self._setup_ui()

    def _setup_ui(self):
        # Layout principal de la page
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(10, 10, 10, 10) # Marges externes de la page
        page_layout.setSpacing(10) # Espace entre Frame et boutons

        # --- Créer le contenu de l'en-tête (Label + ComboBox) ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0) 
        header_layout.setSpacing(8) 
        
        document_label = QLabel("Document:") 
        document_label.setObjectName("FormLabel")
        header_layout.addWidget(document_label)

        self.type_combo = QComboBox()
        self.type_combo.setObjectName("HeaderComboBox") # ID si besoin de style
        self.type_combo.setFixedHeight(26) 
        # TODO: Remplir depuis contrôleur
        header_layout.addWidget(self.type_combo, 1) 

        # Mettre dans un conteneur
        header_container = QWidget()
        header_container.setObjectName("FrameHeaderContainer") 
        header_container.setLayout(header_layout)

        # --- Créer le Frame contenant UNIQUEMENT l'en-tête --- 
        main_box = Frame(header_widget=header_container)
        # Le corps du Frame (content_layout) reste vide
        # content_layout = main_box.get_content_layout()
        # content_layout.addStretch(0) # S'assurer qu'il ne prend pas de place?

        # Ajouter le Frame (avec en-tête) au layout principal
        page_layout.addWidget(main_box)

        # --- Ajouter les boutons Annuler/Créer SOUS le Frame --- 
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.create_button = QPushButton("Créer")
        self.create_button.setObjectName("AccentButton") 
        self.create_button.clicked.connect(self._on_create_clicked)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setObjectName("StandardButton")
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.create_button) 
        
        # Ajouter le layout des boutons au layout principal de la page
        page_layout.addLayout(button_layout)

        # Ajouter un stretch final pour pousser le Frame et les boutons vers le haut
        page_layout.addStretch(1)

        print("DocumentsTypeSelectionPage UI: Header=Label+Combo, Buttons Below Frame")

    def _on_create_clicked(self):
        selected_type = self.type_combo.currentText()
        if selected_type:
            self.create_requested.emit(selected_type)

    # Méthode pour remplir la combobox depuis le contrôleur
    def set_document_types(self, types_list):
        self.type_combo.clear()
        self.type_combo.addItems(types_list) 