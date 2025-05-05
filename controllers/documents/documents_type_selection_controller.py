# controllers/documents/documents_type_selection_controller.py # <- Nouveau nom
# Gère la logique de sélection du type de document et la création.

from PyQt5.QtCore import QObject, pyqtSlot as Slot, pyqtSignal
# --- AJOUT: QMessageBox --- 
from PyQt5.QtWidgets import QMessageBox
# --- AJOUT: json, os --- 
import json
import os

# --- AJOUT: Importer la vue et get_resource_path --- 
from pages.documents.documents_type_selection_page import DocumentsTypeSelectionPage
from utils.paths import get_resource_path
# ---------------------------------------------------

class DocumentsTypeSelectionController(QObject): # <- Nom de classe mis à jour
    # --- AJOUT: Signaux émis par ce contrôleur --- 
    create_request = pyqtSignal(str, dict) # Type et données du formulaire
    cancel_requested = pyqtSignal() # Pour revenir en arrière
    # -------------------------------------------

    # --- MODIFICATION: __init__ pour accepter les dépendances --- 
    def __init__(self, view: DocumentsTypeSelectionPage, preferences_controller):
        super().__init__()
        self.view = view
        self.preferences_controller = preferences_controller
        
        # Charger la configuration (types, champs)
        self._load_config_data()
        
        # Peupler le combobox initialement
        self._populate_type_selection_combo()
        
        # Connecter les signaux internes de la vue
        self._connect_view_signals()
    # -------------------------------------------------------

    # --- AJOUT: Méthode _load_config_data (depuis DocumentsController) --- 
    def _load_config_data(self, relative_filepath="data/config_data.json"):
        """Charge la config depuis le chemin relatif via get_resource_path."""
        self.document_types = []
        self.document_fields_map = {}
        # Pas besoin des données Jacmar ou plafond ici, géré dans _on_document_type_selected
        config_full_path = get_resource_path(relative_filepath)
        print(f"DEBUG (TypeSelectionController): Chemin config_data.json calculé: {config_full_path}")
        try:
            if not os.path.exists(config_full_path):
                print(f"Avertissement: Fichier config introuvable: {config_full_path}")
                return
            with open(config_full_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            document_config = config_data.get("document", {})
            self.document_types = list(document_config.keys())
            self.document_fields_map = document_config
            print(f"Types de documents chargés: {self.document_types}")
        except Exception as e:
            print(f"Erreur chargement config ({config_full_path}): {e}")
    # --------------------------------------------------------------

    # --- AJOUT: Méthode _populate_type_selection_combo (depuis DocumentsController) --- 
    def _populate_type_selection_combo(self):
        """Appelle la méthode de la vue TypeSelection pour remplir son ComboBox."""
        try:
            if hasattr(self.view, 'set_document_types'):
                self.view.set_document_types(self.document_types)
                print("ComboBox Type de document peuplé.")
            else:
                print("Erreur: La vue TypeSelection n'a pas de méthode set_document_types.")
        except Exception as e:
            print(f"Erreur lors du peuplement du ComboBox Type de document: {e}")
    # --------------------------------------------------------------------------

    # --- MODIFICATION: Connecter les signaux de la vue aux slots de CE contrôleur --- 
    def _connect_view_signals(self):
        try:
            self.view.create_requested.connect(self._handle_create_request)
            self.view.cancel_requested.connect(self.cancel_requested.emit) # Émet le signal
            self.view.type_combo.currentTextChanged.connect(self._on_document_type_selected)
            print("DEBUG (TypeSelectionController): Signaux de la vue connectés.")
        except AttributeError as e:
             print(f"ERREUR connexion signaux TypeSelectionPage: Un widget/signal attendu est manquant - {e}")
        except Exception as e:
            print(f"ERREUR connexion signaux TypeSelectionPage: {e}")
    # --------------------------------------------------------------------------

    # --- AJOUT: Méthode activate --- 
    def activate(self):
        """Appelé lorsque cette page/contrôleur devient actif."""
        print("DEBUG: DocumentsTypeSelectionController activated.")
        # Déclencher la mise à jour initiale des champs dynamiques pour le type sélectionné
        try:
            initial_type = self.view.type_combo.currentText()
            if initial_type:
                print(f"DEBUG (Activate): Déclenchement initial pour le type: {initial_type}")
                self._on_document_type_selected(initial_type)
            else:
                print("DEBUG (Activate): Aucun type initial sélectionné dans le ComboBox.")
                if hasattr(self.view, 'update_content_area'):
                     self.view.update_content_area({}, {}, {}) # Vider
        except Exception as e:
            print(f"ERREUR lors du déclenchement initial des champs (activate): {e}")
    # -----------------------------

    # --- Slots --- 
    # --- AJOUT: Slot _on_document_type_selected (depuis DocumentsController) --- 
    @Slot(str)
    def _on_document_type_selected(self, selected_type):
        """Met à jour la zone de contenu dynamique de la vue en fonction du type."""
        print(f"--- _on_document_type_selected: Type='{selected_type}' ---") 
        if selected_type in self.document_fields_map:
            fields_structure_dict = self.document_fields_map[selected_type]
            default_values = {}
            jacmar_values_for_type = {} 
            try:
                if self.preferences_controller:
                    jacmar_values_for_type = {
                        "emplacements": getattr(self.preferences_controller, 'jacmar_emplacements', []),
                        "departements": getattr(self.preferences_controller, 'jacmar_departements', []),
                        "titres": getattr(self.preferences_controller, 'jacmar_titres', []),
                        "superviseurs": getattr(self.preferences_controller, 'jacmar_superviseurs', []),
                        "plafond_deplacement": getattr(self.preferences_controller, 'jacmar_plafonds', [])
                    }
                    print(f"DEBUG: Données Jacmar extraites des attributs de PrefsController: {list(jacmar_values_for_type.keys())}")

                    def get_pref_value_obj(base_pref_obj, path, default=None):
                        keys = path.split('.')
                        val = base_pref_obj
                        try:
                            for key in keys:
                                if key in ['profile', 'jacmar', 'application']:
                                    val = getattr(val, key)
                                else:
                                    val = getattr(val, key)
                            return val if val is not None else default
                        except AttributeError:
                            print(f"  -> get_pref_value_obj: Path '{path}' -> ATTRIBUTE ERROR, returning default: {default}")
                            return default
                        except Exception as e:
                            print(f"ERROR get_pref_value_obj ({path}): {e}")
                            print(f"  -> get_pref_value_obj: Path '{path}' -> EXCEPTION, returning default: {default}")
                            return default

                    current_prefs_obj = self.preferences_controller.current_preferences
                    print(f"DEBUG: Current Preferences Object state before extraction:")
                    try:
                        print(f"  -> Profile: {current_prefs_obj.profile.to_dict()}")
                        print(f"  -> Jacmar: {current_prefs_obj.jacmar.to_dict()}")
                    except Exception as e_log_prefs:
                        print(f"  -> ERROR logging prefs state: {e_log_prefs}")
                    
                    if "nom" in fields_structure_dict:
                         default_values["nom"] = get_pref_value_obj(current_prefs_obj, 'profile.nom', '')
                    if "prenom" in fields_structure_dict:
                         default_values["prenom"] = get_pref_value_obj(current_prefs_obj, 'profile.prenom', '')
                    if "date" in fields_structure_dict: pass 
                    if "emplacements" in fields_structure_dict:
                         default_values["emplacements"] = get_pref_value_obj(current_prefs_obj, 'jacmar.emplacement', '')
                    if "departements" in fields_structure_dict:
                         default_values["departements"] = get_pref_value_obj(current_prefs_obj, 'jacmar.departement', '')
                    if "superviseurs" in fields_structure_dict:
                         default_values["superviseurs"] = get_pref_value_obj(current_prefs_obj, 'jacmar.superviseur', '')
                    if "plafond_deplacement" in fields_structure_dict:
                         default_values["plafond_deplacement"] = get_pref_value_obj(current_prefs_obj, 'jacmar.plafond', '')

                    print(f"DEBUG: Valeurs par défaut extraites de current_preferences: {default_values}")
                else:
                    print("WARNING: preferences_controller non disponible.")
            except AttributeError as e_attr:
                 print(f"ERREUR lecture attribut PreferencesController: {e_attr}")
            except Exception as e_prefs:
                print(f"ERREUR lecture préférences/jacmar: {e_prefs}")

            # --- AJOUT LOG: Vérifier les données passées à la vue --- 
            print(f"DEBUG (Controller): Appelle update_content_area avec:")
            print(f"  -> fields_structure_dict: {fields_structure_dict}")
            # print(f"  -> default_values: {default_values}") # Moins pertinent si les champs n'apparaissent pas
            # print(f"  -> jacmar_values_for_type: {jacmar_values_for_type}") # Idem
            # -------------------------------------------------------
            if hasattr(self.view, 'update_content_area'):
                try:
                     self.view.update_content_area(fields_structure_dict, default_values, jacmar_values_for_type)
                except Exception as e_update:
                     print(f"ERROR: Erreur lors de la mise à jour du formulaire dynamique: {e_update}")
                     import traceback
                     traceback.print_exc()
            else:
                 print("ERREUR: La vue TypeSelectionPage n'a pas de méthode update_content_area.")
        else:
            print(f"Warning: Type '{selected_type}' non trouvé dans la config.")
            if hasattr(self.view, 'update_content_area'):
                self.view.update_content_area({}, {}, {}) # Vider
    # ----------------------------------------------------------------------

    # --- MODIFICATION: Slot _handle_create_request (depuis DocumentsController) --- 
    @Slot(str) # Le signal create_requested de la vue émet le type (str)
    def _handle_create_request(self, selected_type):
        """Gère la demande de création venant de la vue."""
        print(f"DocumentsTypeSelectionController: Create request received for type '{selected_type}'.")
        form_data = {}
        try:
            if hasattr(self.view, 'get_dynamic_form_data'):
                form_data = self.view.get_dynamic_form_data()
                print(f"Données récupérées du formulaire: {form_data}")
            else:
                print("AVERTISSEMENT: La vue TypeSelectionPage n'a pas de méthode get_dynamic_form_data().")
                QMessageBox.critical(self.view, "Erreur Interne", "Impossible de récupérer les données du formulaire (méthode manquante).")
                return
        except Exception as e_form:
             print(f"ERREUR lors de la récupération des données du formulaire: {e_form}")
             QMessageBox.warning(self.view, "Erreur Formulaire", f"Impossible de récupérer les données du formulaire.\n{e_form}")
             return

        # --- Validation (gardée ici) --- 
        if selected_type == "Rapport de depense":
            required_fields = ["nom", "prenom", "date", "emplacements", "departements", "superviseurs", "plafond_deplacement"]
            missing_fields = []
            for field in required_fields:
                if field not in form_data or not str(form_data[field]).strip():
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
                return
        # --- Fin Validation --- 
        
        # --- Émettre le signal au lieu de créer la fenêtre --- 
        print(f"DocumentsTypeSelectionController: Émission du signal create_request avec type='{selected_type}'...")
        self.create_request.emit(selected_type, form_data)
        # -----------------------------------------------------
    # ------------------------------------------------------------------------

    # --- SUPPRIMER ANCIENNES MÉTHODES PLACEHOLDER --- 
    # @Slot()
    # def create_document(self):
    #     pass

    # @Slot()
    # def cancel_creation(self):
    #      pass 
    # --------------------------------------------

print("DocumentsTypeSelectionController defined") 