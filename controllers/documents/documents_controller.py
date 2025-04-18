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
    def __init__(self, view, main_controller):
        """
        Initialise le contrôleur pour la page Documents.

        Args:
            view (DocumentsPage): L'instance de la vue (page Documents).
            main_controller: L'instance du contrôleur principal de l'application.
        """
        super().__init__()
        self.view = view
        self.main_controller = main_controller # Pour appeler open_document etc.
        self._connect_signals()

    def _connect_signals(self):
        # Connecter les signaux principaux de la page Documents au MainController
        
        # Le bouton "Ouvrir" de la page documents devrait probablement ouvrir 
        # le dialogue standard, comme l'action du menu.
        self.view.open_document_requested.connect(self.main_controller.open_document_from_menu)
        
        # L'ouverture d'un item spécifique (simple clic sur item) est correcte
        self.view.open_specific_document_requested.connect(self.main_controller.open_specific_document)
        
        # La demande de création depuis la page de sélection de type devrait 
        # appeler la même logique que l'action du menu.
        self.view.create_new_document_requested.connect(self.main_controller.create_new_document_from_menu)

        # Retiré: La navigation interne est gérée par la vue
        # self.view.btn_back_to_list.clicked.connect(self.show_document_list_page) 

        # Les connexions pour les actions du menu contextuel des items (browse, remove)
        # devront être ajoutées si on veut que le contrôleur les gère.
        # Exemple: 
        # self.connect_list_item_signals() # Appeler une méthode qui boucle sur les items?

        print("DocumentsController signals connected.")

    # --- Méthodes de navigation (potentiellement redondantes) --- 
    # La vue gère maintenant son propre QStackedWidget
    # def show_document_list_page(self):
    #     print("Controller: Showing document list page")
    #     self.view.documents_stack.setCurrentIndex(0) # Ou utiliser setCurrentWidget

    # def show_new_document_page(self):
    #     print("Controller: Showing new document page")
    #     self.view.documents_stack.setCurrentIndex(1) # Ou utiliser setCurrentWidget
    
    # --- Autres méthodes du contrôleur --- 
    def load_recent_projects(self):
        # Logique pour charger les projets récents
        pass
    
    def add_project_to_recents(self, path):
        # Logique pour ajouter un projet aux récents
        pass
        
    def remove_project_from_recents(self, path):
        # Logique pour retirer un projet des récents
        print(f"Controller: TODO - Remove {path} from recent projects list")
        # Il faudra probablement mettre à jour la vue ici

    print("DocumentsController (dans controllers/documents/) initialized") # Debug 