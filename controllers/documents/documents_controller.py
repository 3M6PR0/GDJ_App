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

        # Connecter les signaux des widgets de la vue aux slots de ce contrôleur
        self.view.btn_new.clicked.connect(self.show_new_document_page)
        self.view.btn_back_to_list.clicked.connect(self.show_document_list_page)
        
        # Connecter les signaux émis par la vue pour les actions globales
        self.view.open_document_requested.connect(self.request_open_document)
        self.view.open_specific_document_requested.connect(self.request_open_specific_document)

    @pyqtSlot()
    def show_new_document_page(self):
        """Affiche la page de création de nouveau document dans le stack interne."""
        print("DocumentsController: Switching to New Document Page") # Debug
        self.view.documents_stack.setCurrentWidget(self.view.documents_new_page)

    @pyqtSlot()
    def show_document_list_page(self):
        """Affiche la page de liste des documents récents dans le stack interne."""
        print("DocumentsController: Switching to Document List Page") # Debug
        self.view.documents_stack.setCurrentWidget(self.view.documents_list_page)

    @pyqtSlot()
    def request_open_document(self):
        """Relaye la demande d'ouverture de document au contrôleur principal."""
        print("DocumentsController: Relaying 'Open Document' request to main controller") # Debug
        if hasattr(self.main_controller, 'open_document'):
            self.main_controller.open_document()
        else:
            print("Erreur: main_controller n'a pas de méthode 'open_document'")

    @pyqtSlot(str)
    def request_open_specific_document(self, file_path):
        """Relaye la demande d'ouverture d'un document spécifique au contrôleur principal."""
        print(f"DocumentsController: Relaying 'Open Specific Document' ({file_path}) request to main controller") # Debug
        if hasattr(self.main_controller, 'open_specific_document'):
            self.main_controller.open_specific_document(file_path)
        else:
            print("Erreur: main_controller n'a pas de méthode 'open_specific_document'")

    print("DocumentsController (dans controllers/documents/) initialized") # Debug 