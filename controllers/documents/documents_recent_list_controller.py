# controllers/documents/documents_recent_list_controller.py # <- Nouveau nom
# Gère la logique de la liste des documents récents (chargement, actions).

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
import os # Importer os pour expanduser

# Importer la VUE associée
from pages.documents.documents_recent_list_page import DocumentsRecentListPage

class DocumentsRecentListController(QObject): 
    # Signaux émis vers le contrôleur parent (DocumentsController)
    request_page_change = pyqtSignal(str) # Pour demander changement de page (ex: vers type_selection)
    request_open_document_dialog = pyqtSignal()
    request_open_specific_document = pyqtSignal(str)
    request_remove_recent = pyqtSignal(str)
    # request_browse_document = pyqtSignal(str) # Si besoin

    def __init__(self, view: DocumentsRecentListPage, parent_controller=None):
        super().__init__()
        self.view = view
        self.parent_controller = parent_controller # Référence au DocumentsController
        
        self._connect_signals()
        self.load_recent_documents() # Charger la liste au démarrage

    def _connect_signals(self):
        # Connecter les signaux de la VUE aux SLOTS de CE contrôleur
        self.view.new_document_requested.connect(self._handle_new_request)
        self.view.open_document_requested.connect(self._handle_open_request)
        self.view.open_specific_document_requested.connect(self._handle_open_specific_request)
        self.view.remove_document_requested.connect(self._handle_remove_request)
        # self.view.search_text_changed.connect(self.filter_list) # Exemple pour recherche
        print("DocumentsRecentListController signals connected.")

    def load_recent_documents(self):
        # Logique pour charger la liste des documents récents 
        # Pour l'instant, utilise la méthode placeholder de la vue
        print("RecentListController: Loading recent documents...")
        # projects = self._get_recent_projects_from_model() # Idéalement depuis un modèle
        # self.view.populate_list(projects) # Met à jour la vue
        self.view.populate_list(None) # Utilise les données placeholder de populate_list

    # --- Slots pour gérer les signaux de la vue --- 
    @pyqtSlot()
    def _handle_new_request(self):
        # Demander au contrôleur parent d'afficher la page de sélection de type
        print("RecentListController: New document requested.")
        self.request_page_change.emit("type_selection") 

    @pyqtSlot()
    def _handle_open_request(self):
        # Demander au contrôleur parent d'ouvrir le dialogue "Ouvrir"
        print("RecentListController: Open document dialog requested.")
        self.request_open_document_dialog.emit()
        
    @pyqtSlot(str)
    def _handle_open_specific_request(self, path):
        # Demander au contrôleur parent d'ouvrir ce fichier spécifique
        print(f"RecentListController: Open specific document requested: {path}")
        self.request_open_specific_document.emit(path)
        
    @pyqtSlot(str)
    def _handle_remove_request(self, path):
        # Logique pour retirer un projet des récents
        print(f"RecentListController: Remove recent requested: {path}")
        # 1. Appeler la logique pour le retirer du stockage (modèle, fichier config)
        # success = self.model.remove_recent(path)
        # 2. Émettre un signal vers le parent OU recharger la liste directement
        self.request_remove_recent.emit(path) # Le DocumentsController gèrera
        # Ou, si ce contrôleur gère tout:
        # if success:
        #     self.load_recent_documents() # Recharger la liste pour màj l'UI

    # --- Autres méthodes (ex: filtrage) --- 
    # def filter_list(self, text):
    #    ... 

print("DocumentsRecentListController defined") 