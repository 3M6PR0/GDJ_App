# pages/about/about_readme_page.py # <- Nouveau nom
# Définit l'interface utilisateur (QWidget) pour afficher le contenu du README.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QFrame, QPushButton, QHBoxLayout # Ajout QPushButton, QHBoxLayout
from PyQt5.QtCore import pyqtSignal # Ajout pyqtSignal

class AboutReadmePage(QWidget): # <- Nom de classe mis à jour
    # Signal émis lorsque l'utilisateur demande à voir les notes
    request_show_notes = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Layout principal de la page (sans marges pour que la QFrame remplisse)
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        # Créer la QFrame qui contient le QTextBrowser (comme dans welcome_page)
        readme_box = QFrame()
        readme_box.setObjectName("DashboardBox") # Pour appliquer le style CSS
        box_layout = QVBoxLayout(readme_box)
        # Ajouter des marges INTÉRIEURES à la boîte pour le contenu
        box_layout.setContentsMargins(15, 8, 15, 10) 
        box_layout.setSpacing(10) 

        # Créer et configurer le QTextBrowser
        self.text_browser = QTextBrowser()
        self.text_browser.setObjectName("ReadmeBrowser") # Nom spécifique pour CSS si besoin
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(True)
        # Ajouter le QTextBrowser au layout de la boîte (avec stretch)
        box_layout.addWidget(self.text_browser, 1)

        # Ajouter la QFrame (contenant le browser) au layout principal de la page
        page_layout.addWidget(readme_box, 1)

        # --- Ajouter le bouton "Notes de Version" en bas à droite --- 
        button_layout = QHBoxLayout()
        button_layout.addStretch() # Pousse le bouton vers la droite
        self.notes_button = QPushButton("Notes de Version")
        self.notes_button.setObjectName("TopNavButton") # Appliquer le style
        self.notes_button.clicked.connect(self.request_show_notes.emit)
        button_layout.addWidget(self.notes_button)
        
        # Ajouter le layout du bouton au layout principal (sans stretch vertical)
        page_layout.addLayout(button_layout, 0)
        
        # Ajouter de l'espacement entre la QFrame et le layout du bouton
        page_layout.setSpacing(10) 

        self.setLayout(page_layout)
        print("AboutReadmePage UI initialized with QFrame") # Debug
        
    def set_content(self, html_content):
        """Met à jour le contenu HTML du QTextBrowser."""
        # La logique de conversion Markdown -> HTML est dans le contrôleur
        self.text_browser.setHtml(html_content) 