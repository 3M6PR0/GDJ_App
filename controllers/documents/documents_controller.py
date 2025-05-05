# controllers/documents/documents_controller.py # <- Chemin mis à jour
# Contient la logique principale pour la section Documents.
# Gère l'instanciation et la navigation entre les sous-contrôleurs/pages.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
# Retrait import json, os, QMessageBox si plus utilisés
import logging
logger = logging.getLogger(__name__)

# Importer la vue principale (conteneur)
from pages.documents.documents_page import DocumentsPage

# Importer les contrôleurs des sous-pages
from controllers.documents.documents_recent_list_controller import DocumentsRecentListController
from controllers.documents.documents_type_selection_controller import DocumentsTypeSelectionController

# --- SUPPRESSION Imports inutiles --- 
# from controllers.preferences.preferences_controller import PreferencesController
# from models.config_data import ConfigData 
# -----------------------------------

class DocumentsController(QObject):
    # --- MODIFICATION: Signature __init__ simplifiée --- 
    def __init__(self, view: DocumentsPage, main_controller=None):
        """
        Initialise le contrôleur pour la page Documents.
        Ne gère plus l'extraction de données, seulement l'orchestration.

        Args:
            view (DocumentsPage): L'instance de la vue (page Documents).
            main_controller: L'instance du contrôleur principal de l'application.
        """
        print("*** DocumentsController.__init__ START ***") # AJOUT PRINT
        super().__init__()
        print(f"  DocumentsController: Received view = {view}") # AJOUT PRINT
        self.view = view
        self.main_controller = main_controller
        # self.preferences_controller = preferences_controller # <- Supprimé
        
        # Récupérer les références aux sous-pages depuis la vue
        print("  DocumentsController: Attempting to access self.view.recent_list_page...") # AJOUT PRINT
        self.recent_list_page = self.view.recent_list_page 
        print(f"  DocumentsController: self.recent_list_page = {self.recent_list_page}") # AJOUT PRINT
        print("  DocumentsController: Attempting to access self.view.type_selection_page...") # AJOUT PRINT
        self.type_selection_page = self.view.type_selection_page
        print(f"  DocumentsController: self.type_selection_page = {self.type_selection_page}") # AJOUT PRINT
        
        if not self.recent_list_page or not self.type_selection_page:
            logger.error("DocumentsController: Sous-pages manquantes dans DocumentsPage!")
            print("ERROR: DocumentsController: Sous-pages manquantes dans DocumentsPage!") # AJOUT PRINT
            # Gérer l'erreur ?

        # --- SUPPRESSION: Chargement ConfigData et extraction Préférences --- 
        # config = ConfigData.get_instance()
        # document_types = config.document_types 
        # logger.info(f"DocumentsController: Types récupérés depuis ConfigData: {document_types}")
        # ... (suppression extraction default_profile_values, jacmar_options) ...
        # ---------------------------------------------------------------------
        
        # --- Instancier les sous-contrôleurs (SIMPLIFIÉ) --- 
        print("  DocumentsController: Instantiating sub-controllers...") # AJOUT PRINT
        try:
            print("    -> Instantiating DocumentsRecentListController...") # AJOUT PRINT
            # RecentListController pourrait avoir besoin de Prefs/Config, à vérifier/adapter si besoin
            self.recent_list_controller = DocumentsRecentListController(
                view=self.recent_list_page, 
                parent_controller=self
            )
            print("    -> DocumentsRecentListController INSTANTIATED.") # AJOUT PRINT
        except Exception as e:
            logger.error(f"Erreur instanciation DocumentsRecentListController: {e}", exc_info=True)
            print(f"ERROR instantiating DocumentsRecentListController: {e}") # AJOUT PRINT
            self.recent_list_controller = None

        # --- AJOUT LOG DE VERIFICATION (Déjà présent, gardé) ---
        logger.debug(f"DocumentsController: Vérification avant instanciation: self.type_selection_page = {self.type_selection_page}")
        # ----------------------------------
        try:
            print("    -> Instantiating DocumentsTypeSelectionController...") # AJOUT PRINT
            # TypeSelectionController récupère ses données lui-même via les Singletons
            self.type_selection_controller = DocumentsTypeSelectionController(
                view=self.type_selection_page # Ne passe que la vue
            )
            print("    -> DocumentsTypeSelectionController INSTANTIATED.") # AJOUT PRINT
        except Exception as e: # Garder une capture générique
            logger.error(f"Erreur instanciation DocumentsTypeSelectionController: {e}", exc_info=True)
            print(f"ERROR instantiating DocumentsTypeSelectionController: {e}") # AJOUT PRINT
            self.type_selection_controller = None
        # -------------------------------------------------------

        # Connecter les signaux (seulement si les contrôleurs existent)
        print("  DocumentsController: Connecting signals...") # AJOUT PRINT
        self._connect_signals()

        # Afficher la page initiale (liste des récents)
        print("  DocumentsController: Showing initial page...") # AJOUT PRINT
        self.show_recent_list_page()
        
        logger.info("DocumentsController initialisé (simplifié, utilise Singletons indirectement).")
        print("*** DocumentsController.__init__ END ***") # AJOUT PRINT

    def _connect_signals(self):
        """Connecte tous les signaux nécessaires entre les sous-contrôleurs et vers le MainController."""
        if self.recent_list_controller:
            self.recent_list_controller.request_page_change.connect(self._handle_page_change_request)
            if self.main_controller:
                self.recent_list_controller.request_open_document_dialog.connect(self.main_controller.open_document_from_menu)
                self.recent_list_controller.request_open_specific_document.connect(self.main_controller.open_specific_document)
            else: logger.warning("DocumentsController: main_controller non disponible pour RecentList.")

        if self.type_selection_controller:
            self.type_selection_controller.create_request.connect(self._handle_document_creation)
            self.type_selection_controller.cancel_requested.connect(self.show_recent_list_page)
        logger.info("DocumentsController: Signaux connectés.")

    @pyqtSlot(str)
    def _handle_page_change_request(self, page_name):
        if page_name == "type_selection": self.show_type_selection_page()
        else: logger.warning(f"Demande page inconnue: {page_name}"); self.show_recent_list_page()

    @pyqtSlot()
    def show_recent_list_page(self):
        """Affiche la page de la liste des documents récents."""
        logger.debug("DocumentsController: Affichage Recent List Page")
        if self.recent_list_page:
            self.view.show_page(self.recent_list_page)
            if self.recent_list_controller and hasattr(self.recent_list_controller, 'activate'):
                self.recent_list_controller.activate()
        else: logger.error("Impossible d'afficher RecentListPage: non initialisée.")
        
    @pyqtSlot()
    def show_type_selection_page(self):
        """Affiche la page de sélection de type et active son contrôleur."""
        logger.debug("DocumentsController: Affichage Type Selection Page")
        if self.type_selection_page:
            self.view.show_page(self.type_selection_page)
            if self.type_selection_controller and hasattr(self.type_selection_controller, 'activate'):
                self.type_selection_controller.activate()
        else: logger.error("Impossible d'afficher TypeSelectionPage: non initialisée.")
        
    @pyqtSlot(str, dict)
    def _handle_document_creation(self, doc_type: str, data: dict):
        """Reçoit la demande de création du TypeSelectionController et la transmet au MainController."""
        logger.info(f"DocumentsController: Demande création reçue: Type='{doc_type}'")
        if self.main_controller:
            try:
                logger.debug("Appel de main_controller.show_new_document_window...")
                self.main_controller.show_new_document_window(doc_type, data)
            except AttributeError: logger.error("main_controller n'a pas show_new_document_window")
            except Exception as e: logger.error(f"Erreur appel show_new_document_window: {e}", exc_info=True)
        else: logger.error("main_controller non défini, impossible de créer le document.")

    def show_default_page(self):
        """Affiche la page par défaut (la liste des récents)."""
        self.show_recent_list_page()

# logger.info("DocumentsController (classe) définie.") # Retrait ou ajustement log final 