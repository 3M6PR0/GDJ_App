# pages/documents/documents_recent_list_page.py # <- Nouveau nom
# Affiche la liste des documents récents et les boutons d'action.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListView # Correction: PyQt5

class DocumentsRecentListPage(QWidget): # <- Nom de classe mis à jour
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Documents Récents")
        self.list_view = QListView() # Pour afficher la liste
        self.open_button = QPushButton("Ouvrir le document sélectionné")
        self.new_button = QPushButton("Nouveau Document")
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.list_view)
        layout.addWidget(self.open_button)
        layout.addWidget(self.new_button)
        
        self.setLayout(layout)
        print("DocumentsRecentListPage UI initialized") # Debug 