# pages/documents/documents_page.py # <- Chemin mis à jour
# Définit l'interface utilisateur (QWidget) principale pour la section Documents.
# Sert de point d'entrée et peut contenir la navigation vers les sous-pages.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget # Correction: PyQt5

# Import des sous-pages (si gérées ici)
# from .recent_list_page import RecentListPage
# from .type_selection_page import TypeSelectionPage

class DocumentsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Exemple avec un QStackedWidget pour gérer les sous-pages
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Initialisation et ajout des sous-pages au stack
        # self.recent_list_page = RecentListPage()
        # self.type_selection_page = TypeSelectionPage()
        # self.stack.addWidget(self.recent_list_page)
        # self.stack.addWidget(self.type_selection_page)
        
        # Label temporaire pour montrer que c'est le conteneur principal
        temp_label = QLabel("Conteneur principal de la page Documents (UI)")
        self.main_layout.addWidget(temp_label)
        
        self.setLayout(self.main_layout)
        print("DocumentsPage UI (dans pages/documents/) initialized") # Debug 