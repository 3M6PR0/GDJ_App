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

    # --- MODIFICATION: __init__ pour accepter les données directement --- 
    def __init__(self, view: DocumentsTypeSelectionPage, 
                 document_types: list, document_fields_map: dict, 
                 default_profile_values: dict, jacmar_options: dict):
        super().__init__()
        self.view = view
        # --- RETRAIT: self.preferences_controller = preferences_controller ---
        
        # --- Stocker les données reçues --- 
        self.document_types = document_types
        self.document_fields_map = document_fields_map
        self.default_profile_values = default_profile_values
        self.jacmar_options = jacmar_options
        # --------------------------------
        
        # Charger la configuration (types, champs) - Déjà fait par le parent
        # self._load_config_data()
        
        # Peupler le combobox initialement
        self._populate_type_selection_combo() # Utilise self.document_types
        
        # Connecter les signaux internes de la vue
        self._connect_view_signals()
    # -------------------------------------------------------

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
            # --- MODIFICATION: create_requested de la vue est connecté à _handle_create_request ICI --- 
            # self.view.create_requested.connect(self._handle_create_request) # Déjà connecté via la vue?
            # Vérifier la logique de connexion dans _on_create_clicked de la vue
            # Si la vue émet le signal create_requested(type), il faut le connecter ici.
            # -> _on_create_clicked émet create_requested(type). On le connecte ici.
            self.view.create_requested.connect(self._handle_create_request) 
            # ---------------------------------------------------------------------------------------
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
                     self.view.update_content_area([], {}, {}) # Vider
        except Exception as e:
            print(f"ERREUR lors du déclenchement initial des champs (activate): {e}")
    # -----------------------------

    # --- Slots --- 
    # --- MODIFICATION: Slot _on_document_type_selected pour utiliser les données stockées --- 
    @Slot(str)
    def _on_document_type_selected(self, selected_type):
        """Met à jour la zone de contenu dynamique de la vue en fonction du type."""
        print(f"--- _on_document_type_selected: Type='{selected_type}' ---") 
        if selected_type in self.document_fields_map:
            fields_structure_list = self.document_fields_map[selected_type] # C'est une liste de noms
            
            # --- Utiliser les données passées à __init__ --- 
            default_values = {} 
            # Combiner les défauts de profil et jacmar (si besoin)
            # Attention: Ici on prend juste les valeurs directes passées.
            # Si on voulait combiner 'profile.nom' etc, il faudrait ajuster
            # la structure de default_profile_values passée
            # Pour l'instant, on suppose que default_profile_values contient { 'nom': ..., 'prenom': ... }
            # et jacmar_options contient { 'emplacement': ..., 'departement': ... etc }
            # -> On a besoin de TOUTES les valeurs par défaut possibles dans un seul dict
            #    Donc, default_profile_values devrait contenir AUSSI les défauts jacmar.
            default_values = self.default_profile_values # Utiliser directement le dict reçu
            jacmar_data = self.jacmar_options # Utiliser directement le dict reçu
            print(f"DEBUG: Utilisation des données reçues: DefaultValues={default_values}, JacmarOptionsKeys={list(jacmar_data.keys())}")
            # ---------------------------------------------

            # --- AJOUT LOG: Vérifier les données passées à la vue --- 
            print(f"DEBUG (Controller): Appelle update_content_area avec:")
            print(f"  -> fields_structure_list: {fields_structure_list}")
            print(f"  -> default_values: {default_values}") 
            print(f"  -> jacmar_data: {jacmar_data}") 
            # -------------------------------------------------------
            if hasattr(self.view, 'update_content_area'):
                try:
                     # Passer la liste et les dictionnaires préparés
                     self.view.update_content_area(fields_structure_list, default_values, jacmar_data)
                except Exception as e_update:
                     print(f"ERROR: Erreur lors de la mise à jour du formulaire dynamique: {e_update}")
                     import traceback
                     traceback.print_exc()
            else:
                 print("ERREUR: La vue TypeSelectionPage n'a pas de méthode update_content_area.")
        else:
            print(f"Warning: Type '{selected_type}' non trouvé dans la config.")
            if hasattr(self.view, 'update_content_area'):
                self.view.update_content_area([], {}, {}) # Vider
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
        # --- MODIFIER : Utiliser selected_type --- 
        if selected_type == "Rapport de depense":
            required_fields = ["nom", "prenom", "date", "emplacements", "departements", "superviseurs", "plafond_deplacement"]
            missing_fields = []
            for field in required_fields:
                if field not in form_data or not str(form_data.get(field, '')).strip(): # Utiliser get()
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