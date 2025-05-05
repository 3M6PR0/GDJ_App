# pages/documents/documents_page.py
"""Définit la page conteneur pour la section Documents.

Ce module contient la classe DocumentsPage, qui agit comme un conteneur principal
pour les différentes sous-pages de la section "Documents" (liste récente, 
sélection de type). Il utilise un QStackedWidget pour gérer l'affichage 
de ces sous-pages.
"""

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
    """Widget conteneur utilisant un QStackedWidget pour afficher les sous-pages Documents.

    Cette classe est responsable de l'instanciation des différentes vues 
    (DocumentsRecentListPage, DocumentsTypeSelectionPage) et de leur ajout 
    à un QStackedWidget. Elle fournit une méthode pour afficher une page spécifique.

    Attributes:
        recent_list_page (DocumentsRecentListPage | None): Instance de la page 
            affichant la liste des documents récents. Initialisée à None.
        type_selection_page (DocumentsTypeSelectionPage | None): Instance de la page 
            permettant la sélection du type de document. Initialisée à None.
        documents_stack (QStackedWidget): Le widget qui gère l'affichage 
            des sous-pages.
    """
    def __init__(self, parent=None):
        """Initialise la DocumentsPage.
        
        Args:
            parent: Le widget parent, ou None.
        """
        # print("*** DocumentsPage.__init__ EXECUTED ***") # DEBUG
        super().__init__(parent)
        self.setObjectName("DocumentsPageWidget")
        logger.info("Initialisation de DocumentsPage...")
        self.recent_list_page = None
        self.type_selection_page = None
        self.documents_stack = None
        self.init_ui()
        logger.info("DocumentsPage initialisée.")

    def init_ui(self):
        """Construit l'interface utilisateur de la page conteneur.
        
        Crée le layout principal, instancie le QStackedWidget, instancie les 
        sous-pages (Recent List et Type Selection) et les ajoute au stack.
        """
        logger.debug("Construction de l'UI pour DocumentsPage...")
        page_documents_layout = QVBoxLayout(self)
        page_documents_layout.setContentsMargins(0, 0, 0, 0)
        page_documents_layout.setSpacing(0)

        self.documents_stack = QStackedWidget()
        
        # Instancier et stocker les sous-pages
        try:
            self.recent_list_page = DocumentsRecentListPage()
            logger.debug("Instance de DocumentsRecentListPage créée.")
        except Exception as e:
            logger.error(f"Erreur lors de l'instanciation de DocumentsRecentListPage: {e}", exc_info=True)
            
        try:
            self.type_selection_page = DocumentsTypeSelectionPage()
            logger.debug("Instance de DocumentsTypeSelectionPage créée.")
        except Exception as e:
             logger.error(f"Erreur lors de l'instanciation de DocumentsTypeSelectionPage: {e}", exc_info=True)

        logger.debug(f"Vérification après instanciation : recent_list_page is None: {self.recent_list_page is None}, type_selection_page is None: {self.type_selection_page is None}")
        
        # Ajouter les pages au stack seulement si elles ont été créées avec succès
        if self.recent_list_page:
            self.documents_stack.addWidget(self.recent_list_page)
        else: 
            logger.warning("recent_list_page n'a pas été ajoutée au stack (instanciation échouée?).")
            
        if self.type_selection_page:
            self.documents_stack.addWidget(self.type_selection_page)
        else: 
            logger.warning("type_selection_page n'a pas été ajoutée au stack (instanciation échouée?).")
            
        page_documents_layout.addWidget(self.documents_stack)
        logger.debug("UI pour DocumentsPage construite.")

    def show_page(self, page_widget: QWidget):
        """Affiche le widget de sous-page spécifié dans le QStackedWidget.

        Args:
            page_widget: Le widget de la sous-page à afficher.
        """
        if self.documents_stack is None:
            logger.error("Tentative d'afficher une page alors que documents_stack n'est pas initialisé.")
            return
            
        if page_widget is None:
             logger.warning("DocumentsPage.show_page a reçu un widget None.")
             return
        
        # Vérifier si le widget est bien dans le stack avant de le montrer
        is_in_stack = False
        for i in range(self.documents_stack.count()):
            if self.documents_stack.widget(i) == page_widget:
                is_in_stack = True
                break
                
        if is_in_stack:
            logger.debug(f"Affichage de la page : {page_widget.objectName() if hasattr(page_widget, 'objectName') else page_widget}")
            self.documents_stack.setCurrentWidget(page_widget)
        else:
            logger.error(f"Tentative d'afficher une page qui n'est pas dans le documents_stack: {page_widget}")

# Commentaire de fin de fichier supprimé car redondant avec le nom du fichier. 