# pages/about/about_readme_page.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
# Importer le composant Frame personnalisé
from ui.components.frame import Frame

class AboutReadmePage(QWidget):
    # Signal émis lorsque l'utilisateur demande à voir les notes
    request_show_notes = pyqtSignal()
    
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
        # Créer le Frame (sans titre)
        readme_box = Frame()
        # Obtenir son layout interne pour ajouter le contenu
        content_layout = readme_box.get_content_layout()
        # Ajouter des marges INTÉRIEURES au contenu DANS le Frame
        content_layout.setContentsMargins(15, 8, 15, 10) 
        # Pas besoin de setSpacing ici si on ajoute qu'un seul widget

        # Créer et configurer le QTextBrowser
        self.text_browser = QTextBrowser()
        self.text_browser.setObjectName("ReadmeBrowser")
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(True)
        # Ajouter le QTextBrowser au layout INTERNE du Frame
        content_layout.addWidget(self.text_browser, 1)

        # Ajouter le Frame au layout principal de la page
        page_layout.addWidget(readme_box, 1) # Avec stretch vertical

        # --- Bouton "Notes de Version" --- 
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.notes_button = QPushButton("Notes de Version")
        self.notes_button.setObjectName("TopNavButton")
        self.notes_button.clicked.connect(self.request_show_notes.emit)
        button_layout.addWidget(self.notes_button)
        
        # Ajouter le layout du bouton au layout principal
        page_layout.addLayout(button_layout, 0)
        
        self.setLayout(page_layout)
        print("AboutReadmePage UI initialized with Frame component, no outer margins") # Debug
        
    def set_content(self, html_content):
        """Met à jour le contenu HTML du QTextBrowser."""
        # La logique de conversion Markdown -> HTML est dans le contrôleur
        self.text_browser.setHtml(html_content) 