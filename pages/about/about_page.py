# pages/about/about_page.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget, QHBoxLayout # Correction: PyQt5


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

        self.setLayout(self.main_layout)
        print("AboutPage UI (dans pages/about/) initialized") # Debug 