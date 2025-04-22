# pages/documents/documents_page.py
# Contient UNIQUEMENT le QStackedWidget pour naviguer entre les sous-pages Documents.

import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
# Retiré import pyqtSignal car plus utilisé ici

# --- Classe DocumentsPage (Conteneur uniquement) --- 
class DocumentsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentsPageWidget")
        self.init_ui()

    def init_ui(self):
        page_documents_layout = QVBoxLayout(self)
        page_documents_layout.setContentsMargins(0, 0, 0, 0)
        page_documents_layout.setSpacing(0)

        self.documents_stack = QStackedWidget()
        
        page_documents_layout.addWidget(self.documents_stack)

    def show_page(self, page_widget):
        """Affiche le widget de page spécifié dans le stack."""
        if page_widget in [self.documents_stack.widget(i) for i in range(self.documents_stack.count())]:
            print(f"DocumentsPage: Showing page {page_widget}")
            self.documents_stack.setCurrentWidget(page_widget)
        else:
            print(f"ERREUR: Tentative d'afficher une page non ajoutée au stack: {page_widget}")

print("DocumentsPage (Container) defined") 