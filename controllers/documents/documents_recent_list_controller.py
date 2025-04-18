# controllers/documents/documents_recent_list_controller.py # <- Nouveau nom
# Gère la logique de la liste des documents récents (chargement, actions).

from PyQt5.QtCore import QObject, pyqtSlot as Slot

# from pages.documents.documents_recent_list_page import DocumentsRecentListPage

class DocumentsRecentListController(QObject): # <- Nom de classe mis à jour
    def __init__(self, view: 'QWidget'): # ou DocumentsRecentListPage
        super().__init__()
        self.view = view
        self._load_recent_documents() # Charger la liste au démarrage
        self._connect_signals()

    def _load_recent_documents(self):
        # Logique pour charger la liste des documents récents 
        # et les afficher dans self.view.list_view
        print("Chargement des documents récents...")
        pass

    def _connect_signals(self):
        # Connecter les boutons aux slots
        if hasattr(self.view, 'open_button'):
            self.view.open_button.clicked.connect(self.open_selected_document)
        if hasattr(self.view, 'new_button'):
            self.view.new_button.clicked.connect(self.request_new_document)
        # Connecter la sélection dans la liste (si nécessaire)
        # self.view.list_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        pass

    # --- Slots ---
    @Slot()
    def open_selected_document(self):
        # Logique pour ouvrir le document sélectionné dans self.view.list_view
        print("Ouverture du document demandé...")
        pass

    @Slot()
    def request_new_document(self):
        # Logique pour initier la création d'un nouveau document
        # Peut-être émettre un signal pour que le contrôleur parent (DocumentsController) change de page vers type_selection
        print("Demande de nouveau document...")
        # Exemple: self.parent().show_type_selection() ou émettre un signal
        pass
        
    # @Slot()
    # def on_selection_changed(self, selected, deselected):
    #     # Activer/désactiver le bouton "Ouvrir" par exemple
    #     pass

    print("DocumentsRecentListController initialized") # Debug 