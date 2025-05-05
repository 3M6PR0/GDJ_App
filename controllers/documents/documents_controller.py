# controllers/documents/documents_controller.py # <- Chemin mis à jour
# Contient la logique principale pour la section Documents.
# Gère l'instanciation et la navigation entre les sous-contrôleurs/pages.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
import logging
# Récupérer le logger configuré
logger = logging.getLogger('GDJ_App') # Utiliser le nom du logger défini

# Importer la vue principale (conteneur)
from pages.documents.documents_page import DocumentsPage

# Importer les contrôleurs des sous-pages
from controllers.documents.documents_recent_list_controller import DocumentsRecentListController
from controllers.documents.documents_type_selection_controller import DocumentsTypeSelectionController


class DocumentsController(QObject):
    """Contrôleur principal pour la section "Documents" de l'application.

    Ce contrôleur agit comme un orchestrateur. Il gère l'instanciation et 
    la communication entre les différents composants de la section Documents 
    (liste récente, sélection de type) et relaie les requêtes importantes 
    (comme la création d'un nouveau document) au contrôleur principal de 
    l'application.

    Attributs:
        view (DocumentsPage): L'instance de la vue conteneur (QStackedWidget).
        main_controller: Référence au contrôleur principal de l'application.
        recent_list_page (DocumentsRecentListPage): Référence à la sous-page d'affichage des documents récents.
        type_selection_page (DocumentsTypeSelectionPage): Référence à la sous-page de sélection de type de document.
        recent_list_controller (DocumentsRecentListController | None): Instance du contrôleur pour la liste récente.
        type_selection_controller (DocumentsTypeSelectionController | None): Instance du contrôleur pour la sélection de type.
    """
    def __init__(self, view: DocumentsPage, main_controller=None):
        """
        Initialise le DocumentsController.

        Args:
            view: L'instance de la vue conteneur (DocumentsPage).
            main_controller: L'instance du contrôleur principal de l'application.
        """
        logger.debug("*** DocumentsController.__init__ START ***")
        super().__init__()
        logger.debug(f"  DocumentsController: Received view = {view}")
        self.view = view
        self.main_controller = main_controller
        # self.preferences_controller = preferences_controller # <- Supprimé
        
        # Récupérer les références aux sous-pages depuis la vue
        logger.debug("  DocumentsController: Attempting to access self.view.recent_list_page...")
        self.recent_list_page = getattr(self.view, 'recent_list_page', None)
        logger.debug(f"  DocumentsController: self.recent_list_page = {self.recent_list_page}")
        logger.debug("  DocumentsController: Attempting to access self.view.type_selection_page...")
        self.type_selection_page = getattr(self.view, 'type_selection_page', None)
        logger.debug(f"  DocumentsController: self.type_selection_page = {self.type_selection_page}")
        
        if not self.recent_list_page or not self.type_selection_page:
            logger.error("DocumentsController: Sous-pages manquantes dans DocumentsPage!")
            # Gérer l'erreur ? Idéalement, ne pas continuer si les vues sont manquantes.
        
        self.recent_list_controller = None
        self.type_selection_controller = None
        
        # Instancier les sous-contrôleurs seulement si les vues existent
        logger.debug("  DocumentsController: Instantiating sub-controllers...")
        if self.recent_list_page:
            try:
                logger.debug("    -> Instantiating DocumentsRecentListController...")
                # RecentListController pourrait avoir besoin de Prefs/Config, à vérifier/adapter si besoin
                self.recent_list_controller = DocumentsRecentListController(
                    view=self.recent_list_page, 
                    parent_controller=self
                )
                logger.debug("    -> DocumentsRecentListController INSTANTIATED.")
            except Exception as e:
                logger.error(f"Erreur instanciation DocumentsRecentListController: {e}", exc_info=True)

        if self.type_selection_page:
            logger.debug(f"DocumentsController: Vérification avant instanciation: self.type_selection_page = {self.type_selection_page}")
            try:
                logger.debug("    -> Instantiating DocumentsTypeSelectionController...")
                # TypeSelectionController récupère ses données lui-même via les Singletons
                self.type_selection_controller = DocumentsTypeSelectionController(
                    view=self.type_selection_page # Ne passe que la vue
                )
                logger.debug("    -> DocumentsTypeSelectionController INSTANTIATED.")
            except Exception as e: # Garder une capture générique
                logger.error(f"Erreur instanciation DocumentsTypeSelectionController: {e}", exc_info=True)

        logger.debug("  DocumentsController: Connecting signals...")
        self._connect_signals()

        logger.debug("  DocumentsController: Showing initial page...")
        self.show_recent_list_page()
        
        logger.info("DocumentsController initialisé (simplifié, utilise Singletons indirectement).")
        logger.debug("*** DocumentsController.__init__ END ***")

    def _connect_signals(self):
        """Connecte les signaux entre les sous-contrôleurs et vers le MainController."""
        if self.recent_list_controller:
            # Connexion des requêtes de la liste récente vers ce contrôleur ou le main_controller
            self.recent_list_controller.request_page_change.connect(self._handle_page_change_request)
            if self.main_controller:
                self.recent_list_controller.request_open_document_dialog.connect(self.main_controller.open_document_from_menu)
                self.recent_list_controller.request_open_specific_document.connect(self.main_controller.open_specific_document)
            else: 
                logger.warning("DocumentsController: main_controller non disponible pour les signaux de RecentListController.")

        if self.type_selection_controller:
            # Connexion des requêtes de la page de sélection vers ce contrôleur
            self.type_selection_controller.create_request.connect(self._handle_document_creation)
            self.type_selection_controller.cancel_requested.connect(self.show_recent_list_page)
        
        logger.info("DocumentsController: Signaux connectés.")

    @pyqtSlot(str)
    def _handle_page_change_request(self, page_name: str):
        """Gère les demandes de changement de page provenant des sous-contrôleurs."""
        logger.debug(f"Demande d'affichage de la page: {page_name}")
        if page_name == "type_selection":
            self.show_type_selection_page()
        # Ajouter d'autres cas si nécessaire
        # elif page_name == "some_other_page":
        #    self.show_some_other_page()
        else:
            logger.warning(f"Demande d'affichage pour une page inconnue: {page_name}. Affichage de la liste récente par défaut.")
            self.show_recent_list_page()

    @pyqtSlot()
    def show_recent_list_page(self):
        """Affiche la page de la liste des documents récents et active son contrôleur."""
        logger.debug("Affichage de DocumentsRecentListPage")
        if self.recent_list_page:
            self.view.show_page(self.recent_list_page)
            if self.recent_list_controller and hasattr(self.recent_list_controller, 'activate'):
                self.recent_list_controller.activate() # Activer le contrôleur associé si besoin
        else: 
            logger.error("Impossible d'afficher RecentListPage: La vue n'est pas initialisée.")
        
    @pyqtSlot()
    def show_type_selection_page(self):
        """Affiche la page de sélection du type de document et active son contrôleur."""
        logger.debug("Affichage de DocumentsTypeSelectionPage")
        if self.type_selection_page:
            self.view.show_page(self.type_selection_page)
            if self.type_selection_controller and hasattr(self.type_selection_controller, 'activate'):
                self.type_selection_controller.activate() # Active le contrôleur pour initialiser les champs
        else: 
            logger.error("Impossible d'afficher TypeSelectionPage: La vue n'est pas initialisée.")
        
    @pyqtSlot(str, dict)
    def _handle_document_creation(self, doc_type: str, data: dict):
        """Reçoit la demande de création du TypeSelectionController et la transmet au MainController."""
        logger.info(f"Demande de création reçue pour le type '{doc_type}'. Transmission au MainController.")
        if self.main_controller and hasattr(self.main_controller, 'show_new_document_window'):
            try:
                logger.debug(f"Appel de main_controller.show_new_document_window(doc_type='{doc_type}', data=...) ")
                self.main_controller.show_new_document_window(doc_type, data)
            except Exception as e: 
                logger.error(f"Erreur lors de l'appel à main_controller.show_new_document_window: {e}", exc_info=True)
        else: 
            logger.error("Impossible de créer le document : main_controller non défini ou méthode 'show_new_document_window' manquante.")

    def show_default_page(self):
        """Affiche la page par défaut pour cette section (la liste des récents)."""
        self.show_recent_list_page()

# logger.info("DocumentsController (classe) définie.") # Retrait ou ajustement log final 