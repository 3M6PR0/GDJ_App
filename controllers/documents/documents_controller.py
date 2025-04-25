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
from windows.document_window import DocumentWindow
# -----------------------------------------

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
        
        # Charger les données de config (types et structure/données jacmar)
        self._load_config_data()
        
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
        
        # Peupler le ComboBox de la page de sélection AVANT de connecter les signaux
        self._populate_type_selection_combo()
        
        # Connecter les signaux (principalement depuis les contrôleurs/pages enfants)
        self._connect_signals()
        
        # Afficher la page initiale (la liste des récents)
        self.show_recent_list_page() 

    def _load_config_data(self, relative_filepath="data/config_data.json"):
        """Charge la config depuis le chemin relatif via get_resource_path."""
        self.document_types = []
        self.document_fields_map = {}
        self.jacmar_data = {}
        self.jacmar_plafonds_keys = []

        # Construire le chemin absolu
        config_full_path = get_resource_path(relative_filepath)
        print(f"DEBUG: Chemin config_data.json calculé: {config_full_path}") # Ajout debug

        try:
            # Utiliser le chemin absolu
            if not os.path.exists(config_full_path):
                print(f"Avertissement: Fichier config introuvable: {config_full_path}")
                return
            
            with open(config_full_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Charger les types et la structure des champs par type
            document_config = config_data.get("document", {})
            self.document_types = list(document_config.keys())
            self.document_fields_map = document_config
            print(f"Types de documents chargés: {self.document_types}")
            
            # Charger les données Jacmar
            jacmar_config = config_data.get("jacmar", {})
            self.jacmar_data = jacmar_config
            plafond_list = self.jacmar_data.get("plafond_deplacement", [])
            if plafond_list and isinstance(plafond_list, list) and isinstance(plafond_list[0], dict):
                self.jacmar_plafonds_keys = list(plafond_list[0].keys())
            else:
                self.jacmar_plafonds_keys = []
                
            print(f"Données Jacmar chargées.")

        except Exception as e:
            print(f"Erreur chargement config ({config_full_path}): {e}")
            
    def _populate_type_selection_combo(self):
        """Appelle la méthode de la vue TypeSelection pour remplir son ComboBox."""
        try:
            if hasattr(self.type_selection_page, 'set_document_types'):
                self.type_selection_page.set_document_types(self.document_types)
                print("ComboBox Type de document peuplé.")
            else:
                print("Erreur: La vue TypeSelection n'a pas de méthode set_document_types.")
        except Exception as e:
            print(f"Erreur lors du peuplement du ComboBox Type de document: {e}")

    def _connect_signals(self):
        """Connecte tous les signaux nécessaires."""
        # Signaux venant de RecentListController
        self.recent_list_controller.request_page_change.connect(self._handle_page_change_request)
        self.recent_list_controller.request_open_document_dialog.connect(self.main_controller.open_document_from_menu)
        self.recent_list_controller.request_open_specific_document.connect(self.main_controller.open_specific_document)
        self.recent_list_controller.request_remove_recent.connect(self._handle_remove_recent)

        # Signaux venant de TypeSelectionPage
        self.type_selection_page.create_requested.connect(self._handle_create_request)
        self.type_selection_page.cancel_requested.connect(self.show_recent_list_page)
        # === Vérifier la connexion ===
        try:
            self.type_selection_page.type_combo.currentTextChanged.connect(self._on_document_type_selected)
            print("DEBUG: Connecté type_combo.currentTextChanged à _on_document_type_selected")
        except Exception as e:
            print(f"ERREUR connexion type_combo: {e}")
        
        print("DocumentsController: Signaux connectés.")

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
        """Affiche la page de sélection de type ET déclenche la mise à jour initiale des champs."""
        print("DocumentsController: Showing Type Selection Page")
        # Assurer que le combo est peuplé (redondant si fait dans init, mais sûr)
        # self._populate_type_selection_combo() 
        
        # Afficher la page
        self.view.show_page(self.type_selection_page)
        
        # --- Déclencher la mise à jour initiale des champs dynamiques --- 
        try:
            initial_type = self.type_selection_page.type_combo.currentText()
            if initial_type:
                print(f"DEBUG: Déclenchement initial pour le type: {initial_type}")
                self._on_document_type_selected(initial_type)
            else:
                print("DEBUG: Aucun type initial sélectionné dans le ComboBox.")
                # Optionnel: Appeler update_content_area avec des données vides
                if hasattr(self.type_selection_page, 'update_content_area'):
                     self.type_selection_page.update_content_area({}) 
                     
        except Exception as e:
            print(f"ERREUR lors du déclenchement initial des champs: {e}")
        
    @pyqtSlot(str)
    def _handle_create_request(self, selected_type):
        print(f"DocumentsController: Create request received for type '{selected_type}'.")
        
        form_data = {}
        # --- 1. Récupérer les données --- 
        try:
            if hasattr(self.type_selection_page, 'get_dynamic_form_data'):
                form_data = self.type_selection_page.get_dynamic_form_data()
                print(f"Données récupérées du formulaire: {form_data}")
            else:
                print("AVERTISSEMENT: La vue TypeSelectionPage n'a pas de méthode get_dynamic_data().")
                # Afficher une erreur car les données sont nécessaires
                QMessageBox.critical(self.view, "Erreur Interne", "Impossible de récupérer les données du formulaire (méthode manquante).")
                return
        except Exception as e_form:
             print(f"ERREUR lors de la récupération des données du formulaire: {e_form}")
             QMessageBox.warning(self.view, "Erreur Formulaire", f"Impossible de récupérer les données du formulaire.\n{e_form}")
             return # Arrêter si on ne peut pas lire les données

        # --- 2. Valider les données requises pour Rapport de depense --- 
        if selected_type == "Rapport de depense":
            required_fields = ["nom", "prenom", "date", "emplacements", "departements", "superviseurs", "plafond_deplacement"]
            missing_fields = []
            for field in required_fields:
                # Vérifier la présence ET si la valeur n'est pas vide (après str conversion)
                if field not in form_data or not str(form_data[field]).strip(): 
                    # Rendre le nom du champ plus lisible pour le message
                    readable_field = field.replace("_", " ").capitalize()
                    if field == "departements": readable_field = "Département"
                    if field == "emplacements": readable_field = "Emplacement"
                    if field == "superviseurs": readable_field = "Superviseur"
                    if field == "plafond_deplacement": readable_field = "Plafond déplacement"
                    missing_fields.append(readable_field)
            
            if missing_fields:
                print(f"ERREUR: Champs manquants ou vides: {missing_fields}")
                error_message = "Veuillez remplir les champs suivants avant de créer le rapport :\n\n- " + "\n- ".join(missing_fields)
                QMessageBox.warning(self.view, "Champs Requis", error_message)
                return # Arrêter le processus si des champs manquent
        # --- Fin Validation --- 

        # --- 3. Instancier et afficher DocumentWindow (seulement si validation OK) --- 
        try:
            print(f"Instanciation de DocumentWindow avec type='{selected_type}' et données validées.")
            self.doc_window_instance = DocumentWindow(initial_doc_type=selected_type, initial_doc_data=form_data)
            self.doc_window_instance.showMaximized() 
            print("DocumentWindow affichée.")
            
            if self.main_controller and self.main_controller.welcome_window and self.main_controller.welcome_window.isVisible():
                print("Fermeture de WelcomeWindow depuis DocumentsController...")
                self.main_controller.welcome_window.close()

        except Exception as e:
            print(f"ERREUR lors de l'instanciation/affichage de DocumentWindow: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self.view, "Erreur Critique", f"Impossible d'ouvrir la fenêtre de document.\n{e}")
        # ---------------------------------------------

    @pyqtSlot(str)
    def _handle_remove_recent(self, path):
        print(f"DocumentsController: Remove recent requested: {path}")
        # Logique pour retirer du modèle de données "récent"
        # success = self.main_controller.remove_from_recent_list(path)
        # Rafraîchir la liste si succès
        # if success:
        #     self.recent_list_controller.load_recent_documents() 
        print(f"TODO: Call main controller to remove {path} from recents and refresh list")

    @pyqtSlot(str)
    def _on_document_type_selected(self, selected_type):
        """Appelé quand le type de document change. Pré-remplit avec les préférences."""
        print(f"--- _on_document_type_selected: Type='{selected_type}' ---") 
        # Récupérer la liste des champs depuis la map
        fields_to_display = self.document_fields_map.get(selected_type, []) 
        # *** DEBUG: Afficher les champs récupérés ***
        print(f"DEBUG: Champs récupérés depuis config pour '{selected_type}': {fields_to_display}") 
        # *******************************************
            
        data_for_view = {}
        print("DEBUG: Préparation data_for_view avec valeurs par défaut des préférences...")
        
        # --- Helper function to safely get nested attributes --- 
        def get_pref_value(base_obj, path, default=None):
            try:
                attrs = path.split('.')
                obj = base_obj
                for attr in attrs:
                    obj = getattr(obj, attr)
                return obj
            except AttributeError:
                print(f"    -> Attribut non trouvé dans les prefs: {path}")
                return default
            except Exception as e:
                print(f"    -> Erreur accès pref {path}: {e}")
                return default

        # --- Map des noms de champs config vers les chemins des attributs de Prefs --- 
        pref_path_map = {
            "nom": "profile.nom",
            "prenom": "profile.prenom",
            "emplacements": "jacmar.emplacement",
            "departements": "jacmar.departement",
            "titres": "jacmar.titre",
            "superviseurs": "jacmar.superviseur",
            "plafond_deplacement": "jacmar.plafond",
            # Ajoutez d'autres mappings si nécessaire
        }

        for field_name in fields_to_display:
            print(f"  - Traitement champ: {field_name}")
            
            # --- Traitement spécial pour le champ "date" --- 
            if field_name == "date":
                data_for_view[field_name] = {"type": "month_year_combo"}
                print("    -> Type: month_year_combo")
                continue # Passer au champ suivant
            
            # --- Traitement des autres champs --- 
            field_type_from_config = self.jacmar_data.get(field_name)
            is_combo = isinstance(field_type_from_config, list) or field_name == "plafond_deplacement"
            widget_type = "combo" if is_combo else "lineedit"
            
            if field_name in ["nom", "prenom"]:
                widget_type = "lineedit"

            default_value = None
            pref_path = pref_path_map.get(field_name)

            if pref_path:
                default_value = get_pref_value(self.preferences_controller.current_preferences, pref_path)
                print(f"    -> Pref trouvée ({pref_path}): '{default_value}'")
            else:
                print(f"    -> Pas de mapping de pref défini pour: {field_name}")

            # --- Construire l'entrée pour data_for_view --- 
            if widget_type == "lineedit":
                 current_value = default_value if default_value is not None else ""
                 if field_name in ["nom", "prenom"] and default_value is None:
                     current_value = ""
                 data_for_view[field_name] = {"type": "lineedit", "value": current_value}
                 print(f"    -> Type: lineedit, Valeur: '{current_value}'")
            
            elif widget_type == "combo":
                options = []
                if field_name == "plafond_deplacement":
                    options = self.jacmar_plafonds_keys
                else:
                    options = self.jacmar_data.get(field_name, [])
                
                data_for_view[field_name] = {"type": "combo", "options": options, "default": default_value}
                print(f"    -> Type: combo, Options: {options}, Défaut: '{default_value}'")
            
            else:
                print(f"    -> WARN: Type de widget non déterminé pour {field_name}")
                data_for_view[field_name] = {"type": "label", "value": "Erreur type widget"} 

        print(f"DEBUG: data_for_view préparé: {data_for_view}")
        print(f"DEBUG: Appel de update_content_area sur la vue...")
        try:
            if hasattr(self.type_selection_page, 'update_content_area'):
                self.type_selection_page.update_content_area(data_for_view)
                print("DEBUG: update_content_area appelé avec succès.")
            else:
                print("ERREUR: La vue TypeSelection n'a pas de méthode update_content_area.")
        except Exception as e:
             print(f"ERREUR lors de l'appel à update_content_area: {e}")
        print("--- Fin _on_document_type_selected ---")

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