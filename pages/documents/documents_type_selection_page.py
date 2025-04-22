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
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(10, 10, 10, 10) 
        page_layout.setSpacing(10) 

        # --- Créer le contenu de l'en-tête --- 
        header_layout = QHBoxLayout()
        document_label = QLabel("Nouveau document:")
        document_label.setObjectName("FormLabel")
        document_label.setFixedHeight(26)
        header_layout.addWidget(document_label)
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("HeaderComboBox")
        self.type_combo.setFixedHeight(26)
        header_layout.addWidget(self.type_combo, 1)
        header_container = QWidget()
        header_container.setObjectName("FrameHeaderContainer")
        header_container.setLayout(header_layout)

        # --- Créer le Frame principal avec l'en-tête personnalisé --- 
        main_box = Frame(header_widget=header_container)
        content_layout = main_box.get_content_layout()
        content_layout.setContentsMargins(0,0,0,0)
        content_layout.setSpacing(0)
        content_layout.addStretch(1)

        # Ajouter le Frame au layout de la page AVEC un stretch factor
        page_layout.addWidget(main_box, 1) # Le stretch factor 1 le fait s'étendre

        # --- Ajouter les boutons Annuler/Créer SOUS le Frame --- 
        bottom_button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setObjectName("TopNavButton") 
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        bottom_button_layout.addWidget(self.cancel_button)
        bottom_button_layout.addStretch() 
        self.create_button = QPushButton("Créer")
        self.create_button.setObjectName("TopNavButton") 
        self.create_button.clicked.connect(self._on_create_clicked)
        bottom_button_layout.addWidget(self.create_button) 
        
        # Ajouter le layout des boutons au layout principal de la page
        page_layout.addLayout(bottom_button_layout)

        print("DocumentsTypeSelectionPage UI: Frame expands, Buttons Below")

    def _on_create_clicked(self):
        selected_type = self.type_combo.currentText()
        if selected_type:
            self.create_requested.emit(selected_type)

    # Méthode pour remplir la combobox depuis le contrôleur
    def set_document_types(self, types_list):
        self.type_combo.clear()
        self.type_combo.addItems(types_list) 