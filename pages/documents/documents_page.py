# pages/documents/documents_page.py
# Contient UNIQUEMENT le QStackedWidget pour naviguer entre les sous-pages Documents.

import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
# Retiré import pyqtSignal car plus utilisé ici

# --- AJOUT: Importer les sous-pages réelles --- 
from .documents_recent_list_page import DocumentsRecentListPage
from .documents_type_selection_page import DocumentsTypeSelectionPage
# ----------------------------------------------

# --- AJOUT: Import logging --- 
import logging
logger = logging.getLogger(__name__)
# -----------------------------

# --- Classe DocumentsPage (Conteneur uniquement) --- 
class DocumentsPage(QWidget):
    def __init__(self, parent=None):
        print("*** DocumentsPage.__init__ EXECUTED ***")
        super().__init__(parent)
        self.setObjectName("DocumentsPageWidget")
        logger.info("--- DocumentsPage.__init__ START --- ")
        # --- Initialiser les attributs à None pour vérification --- 
        self.recent_list_page = None 
        self.type_selection_page = None
        # -------------------------------------------------------
        self.init_ui()
        logger.info("--- DocumentsPage.__init__ END --- ")

    def init_ui(self):
        logger.info("--- DocumentsPage.init_ui START --- ")
        page_documents_layout = QVBoxLayout(self)
        page_documents_layout.setContentsMargins(0, 0, 0, 0)
        page_documents_layout.setSpacing(0)

        self.documents_stack = QStackedWidget()
        
        # --- AJOUT: Instancier et stocker les sous-pages --- 
        try:
            self.recent_list_page = DocumentsRecentListPage()
            logger.debug("DocumentsPage: recent_list_page instanciée avec succès.")
        except Exception as e:
            logger.error(f"DocumentsPage: Erreur instanciation DocumentsRecentListPage: {e}", exc_info=True)
            # recent_list_page reste None
            
        try:
            self.type_selection_page = DocumentsTypeSelectionPage()
            logger.debug("DocumentsPage: type_selection_page instanciée avec succès.")
        except Exception as e:
             logger.error(f"DocumentsPage: Erreur instanciation DocumentsTypeSelectionPage: {e}", exc_info=True)
             # type_selection_page reste None

        # --- AJOUT LOG: Vérifier l'état après instanciation --- 
        logger.debug(f"DocumentsPage.init_ui: Vérification attributs - recent_list_page is None: {self.recent_list_page is None}, type_selection_page is None: {self.type_selection_page is None}")
        # -----------------------------------------------------
        
        # Ajouter les pages au stack (seulement si elles existent)
        if self.recent_list_page:
            self.documents_stack.addWidget(self.recent_list_page)
        if self.type_selection_page:
            self.documents_stack.addWidget(self.type_selection_page)
        # --------------------------------------------------
        
        page_documents_layout.addWidget(self.documents_stack)
        logger.info("--- DocumentsPage.init_ui END --- ")

    def show_page(self, page_widget):
        """Affiche le widget de page spécifié dans le stack."""
        # --- AJOUT: Vérifier si page_widget est None --- 
        if page_widget is None:
             logger.warning("DocumentsPage.show_page: Tentative d'afficher une page None")
             return
        # ------------------------------------------------
        if page_widget in [self.documents_stack.widget(i) for i in range(self.documents_stack.count())]:
            # --- MODIF LOG --- 
            logger.debug(f"DocumentsPage: Affichage page {page_widget}")
            # ---------------
            self.documents_stack.setCurrentWidget(page_widget)
        else:
            # --- MODIF LOG --- 
            logger.error(f"ERREUR: Tentative d'afficher une page non ajoutée au stack: {page_widget}")
            # ---------------

print("DocumentsPage (Container) defined") 