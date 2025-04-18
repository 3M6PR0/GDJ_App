# pages/about/about_release_notes_page.py # <- Nouveau nom
# Définit l'interface utilisateur (QWidget) pour afficher les notes de version.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QPushButton, QFrame, QHBoxLayout
from PyQt5.QtCore import pyqtSignal

class AboutReleaseNotesPage(QWidget): # <- Nom de classe mis à jour
    # Signal émis lorsque l'utilisateur demande à retourner au README
    request_show_readme = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Layout principal de la page (sans marges pour que la QFrame remplisse)
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        # Créer la QFrame qui contient le QTextBrowser
        notes_box = QFrame()
        notes_box.setObjectName("DashboardBox") # Pour appliquer le style CSS
        box_layout = QVBoxLayout(notes_box)
        # Ajouter des marges INTÉRIEURES à la boîte pour le contenu
        box_layout.setContentsMargins(15, 8, 15, 10) 
        box_layout.setSpacing(10) 

        # Créer et configurer le QTextBrowser
        self.text_browser = QTextBrowser()
        self.text_browser.setObjectName("NotesBrowser") # Nom spécifique pour CSS
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(True)
        # Ajouter le QTextBrowser au layout de la boîte (avec stretch)
        box_layout.addWidget(self.text_browser, 1)

        # Ajouter la QFrame (contenant le browser) au layout principal de la page
        page_layout.addWidget(notes_box, 1) # Stretch factor 1 pour la box

        # --- Ajouter le bouton "Retour" en bas à gauche --- 
        button_layout = QHBoxLayout()
        self.back_button = QPushButton("Retour")
        self.back_button.setObjectName("TopNavButton") # Appliquer le style
        self.back_button.setFixedWidth(80) # Garder largeur fixe comme avant si besoin
        self.back_button.clicked.connect(self.request_show_readme.emit)
        button_layout.addWidget(self.back_button)
        button_layout.addStretch() # Pousse le bouton vers la gauche
        
        # Ajouter le layout du bouton au layout principal (sans stretch vertical)
        page_layout.addLayout(button_layout, 0)
        
        # Ajouter de l'espacement entre la QFrame et le layout du bouton
        page_layout.setSpacing(10)
        
        self.setLayout(page_layout)
        print("AboutReleaseNotesPage UI initialized with QFrame") # Debug

    def set_content(self, markdown_content):
        """Met à jour le contenu du QTextBrowser."""
        # La logique de conversion Markdown -> HTML est dans le contrôleur
        # Mais ici, le contrôleur passe du markdown brut, donc setMarkdown
        self.text_browser.setMarkdown(markdown_content) 