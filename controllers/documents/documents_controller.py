# controllers/documents/documents_controller.py # <- Chemin mis à jour
# Contient la logique principale pour la section Documents.
# Gère l'instanciation et la navigation entre les sous-contrôleurs/pages.

from PyQt5.QtCore import QObject, pyqtSlot as Slot

# Import de la vue principale et des vues/contrôleurs des sous-pages
# from pages.documents.documents_page import DocumentsPage
# from pages.documents.recent_list_page import RecentListPage
# from .recent_list_controller import RecentListController
# from pages.documents.type_selection_page import TypeSelectionPage
# from .type_selection_controller import TypeSelectionController

class DocumentsController(QObject):
    def __init__(self, view: 'QWidget'): # Type hint avec DocumentsPage idéalement
        super().__init__()
        self.view = view
        
        # Initialiser les vues et contrôleurs des sous-pages
        # self.recent_list_page = RecentListPage()
        # self.recent_list_controller = RecentListController(self.recent_list_page)
        # self.type_selection_page = TypeSelectionPage()
        # self.type_selection_controller = TypeSelectionController(self.type_selection_page)
        
        # Ajouter les vues au QStackedWidget de la vue principale (DocumentsPage)
        # self.view.stack.addWidget(self.recent_list_page)
        # self.view.stack.addWidget(self.type_selection_page)
        
        self._connect_signals()
        self.show_recent_list() # Afficher la liste par défaut

    def _connect_signals(self):
        # Connecter les signaux émis par les sous-contrôleurs pour gérer la navigation
        # Par exemple, si RecentListController émet un signal new_document_requested:
        # self.recent_list_controller.new_document_requested.connect(self.show_type_selection)
        # Ou si TypeSelectionController émet cancel_requested:
        # self.type_selection_controller.cancel_requested.connect(self.show_recent_list)
        pass

    # --- Slots pour la navigation interne --- 
    @Slot()
    def show_recent_list(self):
        # index = self.view.stack.indexOf(self.recent_list_page)
        # if index != -1:
        #    self.view.stack.setCurrentIndex(index)
        print("Affichage de la liste des documents récents demandé")
        pass

    @Slot()
    def show_type_selection(self):
        # index = self.view.stack.indexOf(self.type_selection_page)
        # if index != -1:
        #    self.view.stack.setCurrentIndex(index)
        print("Affichage de la sélection du type de document demandé")
        pass

    print("DocumentsController (dans controllers/documents/) initialized") # Debug 