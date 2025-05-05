# pages/about/about_release_notes_page.py # <- Nouveau nom

import logging # AJOUT
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
# Importer le composant Frame personnalisé
from ui.components.frame import Frame

logger = logging.getLogger('GDJ_App') # OBTENIR LE LOGGER

class AboutReleaseNotesPage(QWidget): # <- Nom de classe mis à jour
    # Signal émis lorsque l'utilisateur demande à retourner au README
    request_show_readme = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        page_layout = QVBoxLayout(self)
        # Remettre les marges extérieures de la page à 0
        page_layout.setContentsMargins(0, 0, 0, 0) 
        # Garder l'espacement entre le Frame et le bouton
        page_layout.setSpacing(10)

        # --- Utiliser le composant Frame --- 
        notes_box = Frame()
        content_layout = notes_box.get_content_layout()
        content_layout.setContentsMargins(15, 8, 15, 10) # Garder marges internes
        
        # Créer et configurer le QTextBrowser
        self.text_browser = QTextBrowser()
        self.text_browser.setObjectName("NotesBrowser")
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(True)
        # Ajouter le QTextBrowser au layout INTERNE du Frame
        content_layout.addWidget(self.text_browser, 1)

        # Ajouter le Frame au layout principal de la page
        page_layout.addWidget(notes_box, 1) # Avec stretch vertical

        # --- Bouton "Retour" --- 
        button_layout = QHBoxLayout()
        self.back_button = QPushButton("Retour")
        self.back_button.setObjectName("TopNavButton")
        self.back_button.setFixedWidth(80)
        self.back_button.clicked.connect(self.request_show_readme.emit)
        button_layout.addWidget(self.back_button)
        button_layout.addStretch()
        
        # Ajouter le layout du bouton au layout principal
        page_layout.addLayout(button_layout, 0)
        
        self.setLayout(page_layout)
        logger.info("AboutReleaseNotesPage UI initialized with Frame component, no outer margins")

    def set_content(self, markdown_content):
        """Met à jour le contenu du QTextBrowser."""
        self.text_browser.setMarkdown(markdown_content) 