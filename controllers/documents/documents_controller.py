# controllers/documents/documents_controller.py # <- Chemin mis à jour
# Contient la logique principale pour la section Documents.
# Gère l'instanciation et la navigation entre les sous-contrôleurs/pages.

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QListWidgetItem, QMessageBox # Ajouter QMessageBox
import json
import os

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

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

# --- Importer la fenêtre DocumentWindow --- 
# --- MODIFICATION: Ne plus importer DocumentWindow ici, géré par MainController --- 
# from windows.document_window import DocumentWindow
# ------------------------------------------------------------------------------

# --- AJOUT: Importer le contrôleur de sélection de type --- 
from controllers.documents.documents_type_selection_controller import DocumentsTypeSelectionController
# ---------------------------------------------------------

class DocumentsController(QObject):
    def __init__(self, view: DocumentsPage, main_controller, preferences_controller):
        """
        Initialise le contrôleur pour la page Documents.

        Args:
            view (DocumentsPage): L'instance de la vue (page Documents).
            main_controller: L'instance du contrôleur principal de l'application.
            preferences_controller: L'instance du contrôleur des préférences.
        """
        super().__init__()
        self.view = view
        self.main_controller = main_controller # Pour appeler open_document etc.
        self.preferences_controller = preferences_controller
        
        # --- SUPPRIMER chargement config, fait par les sous-contrôleurs --- 
        # self._load_config_data()
        # -----------------------------------------------------------------
        
        # Instancier les sous-pages réelles
        self.recent_list_page = DocumentsRecentListPage()
        self.type_selection_page = DocumentsTypeSelectionPage()
        
        # --- Instancier les sous-contrôleurs --- 
        self.recent_list_controller = DocumentsRecentListController(self.recent_list_page, self)
        self.type_selection_controller = DocumentsTypeSelectionController(
            view=self.type_selection_page, 
            preferences_controller=self.preferences_controller
            # main_controller n'est pas requis par TypeSelectionController pour l'instant
        )
        # ----------------------------------------
        
        # Ajouter les pages au QStackedWidget de la vue (DocumentsPage)
        self.view.documents_stack.addWidget(self.recent_list_page)
        self.view.documents_stack.addWidget(self.type_selection_page)
        
        # --- SUPPRIMER appel direct à _populate_type_selection_combo --- 
        # self._populate_type_selection_combo()
        # -------------------------------------------------------------
        
        # Connecter les signaux
        self._connect_signals()
        
        # Afficher la page initiale (la liste des récents)
        self.show_recent_list_page() 

    # --- SUPPRIMER _load_config_data --- 
    # def _load_config_data(...): 
    #     ...
    # -----------------------------------
            
    # --- SUPPRIMER _populate_type_selection_combo --- 
    # def _populate_type_selection_combo(self):
    #     ...
    # ---------------------------------------------

    def _connect_signals(self):
        """Connecte tous les signaux nécessaires."""
        # Signaux venant de RecentListController (inchangé)
        self.recent_list_controller.request_page_change.connect(self._handle_page_change_request)
        self.recent_list_controller.request_open_document_dialog.connect(self.main_controller.open_document_from_menu)
        self.recent_list_controller.request_open_specific_document.connect(self.main_controller.open_specific_document)
        # --- MODIFICATION: Connecter à _handle_remove_recent de DocumentsRecentListController --- 
        # self.recent_list_controller.request_remove_recent.connect(self._handle_remove_recent)
        # Note: Ce signal est géré en interne par RecentListController ou émis vers le modèle.
        # Si DocumentsController DOIT être notifié, le signal doit être reconnecté ici.
        # Pour l'instant, on suppose que RecentListController gère sa logique de suppression.
        # ------------------------------------------------------------------------------------

        # --- MODIFICATION: Connecter les signaux de TypeSelectionController --- 
        # Le signal `create_request` est émis par le contrôleur
        self.type_selection_controller.create_request.connect(self._handle_document_creation)
        # Le signal `cancel_requested` aussi
        self.type_selection_controller.cancel_requested.connect(self.show_recent_list_page)
        # -------------------------------------------------------------------
        
        # --- SUPPRIMER les connexions directes à TypeSelectionPage --- 
        # self.type_selection_page.create_requested.connect(self._handle_create_request)
        # self.type_selection_page.cancel_requested.connect(self.show_recent_list_page)
        # try:
        #     self.type_selection_page.type_combo.currentTextChanged.connect(self._on_document_type_selected)
        #     print("DEBUG: Connecté type_combo.currentTextChanged à _on_document_type_selected")
        # except Exception as e:
        #     print(f"ERREUR connexion type_combo: {e}")
        # -----------------------------------------------------------
        
        print("DocumentsController: Signaux connectés entre contrôleurs.") # Message mis à jour

    # --- Slots pour gérer la navigation interne et les actions --- 
    @pyqtSlot(str)
    def _handle_page_change_request(self, page_name):
        if page_name == "type_selection":
            self.show_type_selection_page()
        else:
            print(f"Warning: Unknown page change requested: {page_name}")
            self.show_recent_list_page() # Retour à la liste par défaut

    @pyqtSlot()
    def show_recent_list_page(self):
        print("DocumentsController: Showing Recent List Page")
        self.view.show_page(self.recent_list_page)
        # --- AJOUT: Activer le contrôleur de la liste (si nécessaire) --- 
        if hasattr(self.recent_list_controller, 'activate'):
            self.recent_list_controller.activate()
        # ------------------------------------------------------------
        
    @pyqtSlot()
    def show_type_selection_page(self):
        """Affiche la page de sélection de type ET active son contrôleur."""
        print("DocumentsController: Showing Type Selection Page")
        self.view.show_page(self.type_selection_page)
        # --- MODIFICATION: Activer le contrôleur au lieu de déclencher directement --- 
        self.type_selection_controller.activate()
        # --------------------------------------------------------------------------
        
    # --- RENOMMÉ: _handle_create_request -> _handle_document_creation --- 
    # --- Ce slot reçoit maintenant les données directement du signal --- 
    @pyqtSlot(str, dict)
    def _handle_document_creation(self, doc_type: str, data: dict):
        print(f"DocumentsController: Demande de création reçue du sous-contrôleur: Type='{doc_type}'")
        if self.main_controller:
            try:
                print("  -> Appel de main_controller.show_new_document_window...")
                self.main_controller.show_new_document_window(doc_type, data)
            except AttributeError:
                 print("ERREUR: main_controller n'a pas de méthode show_new_document_window")
            except TypeError as e_type:
                 print(f"ERREUR lors de l'appel à show_new_document_window: {e_type}")
                 import traceback
                 traceback.print_exc()
            except Exception as e:
                 print(f"ERREUR inattendue lors de l'appel à show_new_document_window: {e}")
        else:
            print("ERREUR: main_controller non défini dans DocumentsController.")
    # --------------------------------------------------------------------------

    # --- SUPPRIMER _handle_create_request (ancienne version) --- 
    # @pyqtSlot(str)
    # def _handle_create_request(self, selected_type):
    #     ...
    # -----------------------------------------------------------

    # --- SUPPRIMER _handle_remove_recent --- 
    # @pyqtSlot(str)
    # def _handle_remove_recent(self, path):
    #     ...
    # --------------------------------------
        
    # --- SUPPRIMER _on_document_type_selected --- 
    # @pyqtSlot(str)
    # def _on_document_type_selected(self, selected_type):
    #    ...
    # ---------------------------------------------

    # --- Garder show_default_page si utile --- 
    def show_default_page(self):
        """Affiche la page par défaut (la liste des récents)."""
        self.show_recent_list_page()

print("DocumentsController updated for sub-pages") # Debug 