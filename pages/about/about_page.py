# pages/about/about_page.py # <- Chemin mis à jour
# Définit l'interface utilisateur (QWidget) principale pour la section "A Propos".
# Sert de point d'entrée et gère l'affichage des sous-pages.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget, QHBoxLayout # Correction: PyQt5

# Import des sous-pages
# from .readme_page import ReadmePage
# from .release_notes_page import ReleaseNotesPage

class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10) # Ajouter des marges générales
        self.main_layout.setSpacing(10) # Ajouter de l'espacement
        
        # Conteneur pour les sous-pages (README, Notes)
        self.stack = QStackedWidget()
        print(f"DEBUG: AboutPage._setup_ui: id(self)={id(self)}, stack created: id(self.stack)={id(self.stack)}") # DEBUG
        # Donner un stretch factor au stack pour qu'il prenne l'espace disponible
        self.main_layout.addWidget(self.stack, 1)
        
        # Boutons de navigation - SUPPRIMÉS d'ici, déplacés vers les sous-pages
        # self.btn_layout = QHBoxLayout()
        # self.btn_show_readme = QPushButton("A Propos")
        # self.btn_show_readme.setObjectName("TopNavButton") # Ajouter objectName
        # self.btn_show_notes = QPushButton("Notes de Version")
        # self.btn_show_notes.setObjectName("TopNavButton") # Ajouter objectName
        # self.btn_layout.addWidget(self.btn_show_readme)
        # self.btn_layout.addWidget(self.btn_show_notes)
        # self.btn_layout.addStretch()
        # # Ajouter le layout des boutons APRÈS le stack, sans stretch pour qu'il reste en bas
        # self.main_layout.addLayout(self.btn_layout, 0)

        self.setLayout(self.main_layout)
        print("AboutPage UI (dans pages/about/) initialized") # Debug 