# controllers/documents/documents_controller.py # <- Chemin mis à jour
# Contient la logique principale pour la section Documents.
# Gère l'instanciation et la navigation entre les sous-contrôleurs/pages.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QListWidgetItem # Pour vérifier le type d'item

# Import de la vue principale et des vues/contrôleurs des sous-pages
# from pages.documents.documents_page import DocumentsPage
# from pages.documents.recent_list_page import RecentListPage
# from .recent_list_controller import RecentListController
# from pages.documents.type_selection_page import TypeSelectionPage
# from .type_selection_controller import TypeSelectionController

# Importer les VUES (Le conteneur et les pages réelles)
from pages.documents.documents_page import DocumentsPage # Le conteneur
from pages.documents.documents_recent_list_page import DocumentsRecentListPage
from pages.documents.documents_type_selection_page import DocumentsTypeSelectionPage
# Supprimer l'import de DocumentsNewPage (s'il existe)
# from pages.documents.documents_new_page import DocumentsNewPage

# Importer le contrôleur spécifique à la liste
from controllers.documents.documents_recent_list_controller import DocumentsRecentListController

# Importer la classe ProjectListItemWidget (suppose qu'elle est accessible)
# Idéalement, elle serait dans un module partagé ui.components
try:
    # Essayer d'importer depuis l'emplacement actuel (si exécuté depuis la racine?)
    from pages.documents.documents_page import ProjectListItemWidget 
except ImportError:
    # Fallback si la structure change ou pour test localisé
    print("Avertissement: Impossible d'importer ProjectListItemWidget directement.")
    # Définir une classe factice pour éviter les erreurs si l'import échoue
    class ProjectListItemWidget: pass 

class DocumentsController(QObject):
    def __init__(self, view: DocumentsPage, main_controller):
        """
        Initialise le contrôleur pour la page Documents.

        Args:
            view (DocumentsPage): L'instance de la vue (page Documents).
            main_controller: L'instance du contrôleur principal de l'application.
        """
        super().__init__()
        self.view = view
        self.main_controller = main_controller # Pour appeler open_document etc.
        
        # Instancier les sous-pages réelles
        self.recent_list_page = DocumentsRecentListPage()
        self.type_selection_page = DocumentsTypeSelectionPage()
        # Supprimer l'instanciation de documents_new_page
        # self.documents_new_page = DocumentsNewPage(self)
        
        # Instancier le contrôleur pour la liste des récents
        # On lui passe sa vue (recent_list_page) et une référence à ce contrôleur (self)
        self.recent_list_controller = DocumentsRecentListController(self.recent_list_page, self)
        
        # Ajouter les pages au QStackedWidget de la vue (DocumentsPage)
        self.view.documents_stack.addWidget(self.recent_list_page)
        self.view.documents_stack.addWidget(self.type_selection_page)
        # Supprimer l'ajout de documents_new_page au stack
        # self.view.documents_stack.addWidget(self.documents_new_page)
        
        # Connecter les signaux (principalement depuis les contrôleurs/pages enfants)
        self._connect_signals()
        
        # Afficher la page initiale (la liste des récents)
        self.show_recent_list_page() 

    def _connect_signals(self):
        # --- Signaux venant de DocumentsRecentListController --- 
        self.recent_list_controller.request_page_change.connect(self._handle_page_change_request)
        self.recent_list_controller.request_open_document_dialog.connect(self.main_controller.open_document_from_menu)
        self.recent_list_controller.request_open_specific_document.connect(self.main_controller.open_specific_document)
        self.recent_list_controller.request_remove_recent.connect(self._handle_remove_recent)

        # --- Signaux venant de DocumentsTypeSelectionPage --- 
        self.type_selection_page.create_requested.connect(self._handle_create_request)
        self.type_selection_page.cancel_requested.connect(self.show_recent_list_page) # Navigation retour

        # Supprimer les signaux venant de DocumentsNewPage
        # # --- Signaux venant de DocumentsNewPage ---
        # self.documents_new_page.create_requested.connect(self._handle_create_request)
        # self.documents_new_page.cancel_requested.connect(self.show_recent_list_page) # Navigation retour

        print("DocumentsController: Signals from sub-controllers/pages connected.")

    # --- Slots pour gérer la navigation interne et les actions --- 
    @pyqtSlot(str)
    def _handle_page_change_request(self, page_name):
        if page_name == "type_selection":
            self.show_type_selection_page()
        # Supprimer la condition pour documents_new
        # elif page_name == "documents_new":
        #     self.show_new_document_page()
        else:
            print(f"Warning: Unknown page change requested: {page_name}")
            self.show_recent_list_page() # Retour à la liste par défaut

    @pyqtSlot()
    def show_recent_list_page(self):
        print("DocumentsController: Showing Recent List Page")
        self.view.show_page(self.recent_list_page)
        
    @pyqtSlot()
    def show_type_selection_page(self):
        print("DocumentsController: Showing Type Selection Page")
        # TODO: Remplir la combobox depuis le contrôleur principal ou un modèle
        # doc_types = self.main_controller.get_available_document_types()
        # self.type_selection_page.set_document_types(doc_types)
        self.view.show_page(self.type_selection_page)
        
    @pyqtSlot(str)
    def _handle_create_request(self, selected_type):
        print(f"DocumentsController: Create requested for type: {selected_type}")
        # Relayer au contrôleur principal pour la création effective
        # self.main_controller.create_document_of_type(selected_type)
        print(f"TODO: Call main controller to create document of type {selected_type}")
        self.show_recent_list_page() # Revenir à la liste après
        
    @pyqtSlot(str)
    def _handle_remove_recent(self, path):
        print(f"DocumentsController: Remove recent requested: {path}")
        # Logique pour retirer du modèle de données "récent"
        # success = self.main_controller.remove_from_recent_list(path)
        # Rafraîchir la liste si succès
        # if success:
        #     self.recent_list_controller.load_recent_documents() 
        print(f"TODO: Call main controller to remove {path} from recents and refresh list")

    # Retiré: load_recent_projects - Géré par recent_list_controller
    # Retiré: remove_project_from_recents - Géré par _handle_remove_recent

    print("DocumentsController updated for sub-pages")

    print("DocumentsController (dans controllers/documents/) initialized") # Debug 

    # Ajouter une méthode pour afficher la page par défaut
    def show_default_page(self):
        """Affiche la page par défaut pour la section Documents (liste des récents)."""
        self.show_recent_list_page() 

    # Supprimer la méthode show_new_document_page
    # def show_new_document_page(self):
    #     self.view.show_page(self.documents_new_page) 