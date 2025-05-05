# controllers/documents/documents_type_selection_controller.py # <- Nouveau nom
# Gère la logique de sélection du type de document et la création.
# Récupère les données depuis les Singletons Preference et ConfigData.

from PyQt5.QtCore import QObject, pyqtSlot as Slot, pyqtSignal
# --- AJOUT: QMessageBox --- 
from PyQt5.QtWidgets import QMessageBox
# --- AJOUT: json, os --- 
import json
import os
# --- AJOUT: Import logging --- 
import logging
logger = logging.getLogger(__name__)
# ---------------------------------------------------

# --- AJOUT: Importer les Singletons --- 
from models.preference import Preference
from models.config_data import ConfigData
# --------------------------------------

# --- AJOUT: Importer la vue et get_resource_path --- 
from pages.documents.documents_type_selection_page import DocumentsTypeSelectionPage
# Retrait import get_resource_path si plus utilisé ici
# from utils.paths import get_resource_path
# ---------------------------------------------------

class DocumentsTypeSelectionController(QObject): # <- Nom de classe mis à jour
    # --- AJOUT: Signaux émis par ce contrôleur --- 
    create_request = pyqtSignal(str, dict) # Type et données du formulaire
    cancel_requested = pyqtSignal() # Pour revenir en arrière
    # -------------------------------------------

    # --- MODIFICATION: Signature __init__ simplifiée --- 
    def __init__(self, view: DocumentsTypeSelectionPage):
        super().__init__()
        self.view = view
        # logger.info("--- DocumentsTypeSelectionController.__init__ START ---") # AJOUT LOG
        print("*** DocumentsTypeSelectionController.__init__ START ***") # USE PRINT
        
        # --- MODIFICATION: Récupérer les données depuis les Singletons --- 
        try:
            # logger.debug("  Attempting to get ConfigData instance...") # AJOUT LOG
            print("  DTSC: Attempting to get ConfigData instance...") # USE PRINT
            config = ConfigData.get_instance()
            # logger.debug(f"  ConfigData instance obtained: {config}") # AJOUT LOG
            print(f"  DTSC: ConfigData instance obtained: {config}") # USE PRINT
            # logger.debug("  Attempting to get Preference instance...") # AJOUT LOG
            print("  DTSC: Attempting to get Preference instance...") # USE PRINT
            prefs = Preference.get_instance()
            # logger.debug(f"  Preference instance obtained: {prefs}") # AJOUT LOG
            print(f"  DTSC: Preference instance obtained: {prefs}") # USE PRINT
            
            # 1. --- MODIFICATION: Hardcoder les types de documents --- 
            # self.document_types = config.document_types # <- SUPPRIMÉ
            self.document_types = ["Rapport de depense", "CSA"] # <- HARDCODÉ avec CSA
            # logger.debug(f"  TypeSelectionController: Types récupérés de ConfigData: {self.document_types}") # AJOUT LOG + info source
            # print(f"  DTSC: Types récupérés de ConfigData: {self.document_types}") # USE PRINT
            print(f"  DTSC: Types HARDCODÉS: {self.document_types}") # USE PRINT
            # --------------------------------------------------------

            # 2. Options Jacmar depuis ConfigData
            self.jacmar_options = self._extract_jacmar_options(config)
            # logger.debug(f"  TypeSelectionController: Options Jacmar récupérées de ConfigData: keys={list(self.jacmar_options.keys())}") # AJOUT LOG + info source
            print(f"  DTSC: Options Jacmar récupérées de ConfigData: keys={list(self.jacmar_options.keys())}") # USE PRINT

            # 3. Valeurs par défaut depuis Preference
            self.default_profile_values = self._extract_default_values(prefs)
            # logger.debug(f"  TypeSelectionController: Valeurs par défaut récupérées de Preference: {self.default_profile_values}") # AJOUT LOG + info source
            print(f"  DTSC: Valeurs par défaut récupérées de Preference: {self.default_profile_values}") # USE PRINT

        except Exception as e:
             # logger.error(f"  Erreur récupération données Singletons dans TypeSelectionController: {e}", exc_info=True)
             print(f"ERROR DTSC Init Singletons/Hardcoding: {e}") # USE PRINT (Message d'erreur ajusté)
             # Initialiser avec des valeurs vides pour éviter crashs ultérieurs
             self.document_types = [] # Garder fallback vide en cas d'erreur ailleurs
             self.jacmar_options = {}
             self.default_profile_values = {}
        # ------------------------------------------------------------------
        
        # Peupler le combobox initialement
        self._populate_type_selection_combo() # Utilise self.document_types
        
        # Connecter les signaux internes de la vue
        self._connect_view_signals()
        # logger.info("--- DocumentsTypeSelectionController.__init__ END ---") # AJOUT LOG
        print("*** DocumentsTypeSelectionController.__init__ END ***") # USE PRINT
    # -------------------------------------------------------

    # --- AJOUT: Méthodes helper pour extraire les données --- 
    def _extract_jacmar_options(self, config: ConfigData) -> dict:
        """Extrait les listes d'options Jacmar depuis ConfigData."""
        print("--- DTSC: _extract_jacmar_options START ---") # AJOUT PRINT
        jacmar_data = {}
        jacmar_config = config.get_top_level_key("jacmar", default={})
        print(f"  _extract_jacmar_options: Got jacmar_config keys: {list(jacmar_config.keys())}") # AJOUT PRINT
        
        # Emplacements
        emplacements_list = jacmar_config.get('emplacements', [])
        print(f"  _extract_jacmar_options: Retrieved emplacements: {emplacements_list}") # AJOUT PRINT
        jacmar_data["emplacements"] = emplacements_list
        
        # Departements
        departements_list = jacmar_config.get('departements', [])
        print(f"  _extract_jacmar_options: Retrieved departements: {departements_list}") # AJOUT PRINT
        jacmar_data["departements"] = departements_list
        
        # Titres
        titres_list = jacmar_config.get('titres', [])
        print(f"  _extract_jacmar_options: Retrieved titres: {titres_list}") # AJOUT PRINT
        jacmar_data["titres"] = titres_list
        
        # Superviseurs
        superviseurs_list = jacmar_config.get('superviseurs', [])
        print(f"  _extract_jacmar_options: Retrieved superviseurs: {superviseurs_list}") # AJOUT PRINT
        jacmar_data["superviseurs"] = superviseurs_list
        
        # Plafond Deplacement
        # --- CORRECTION: Utiliser la bonne clé 'plafond_deplacement' --- 
        plafonds_raw = jacmar_config.get('plafond_deplacement', []) # <- CORRECTION CLÉ
        print(f"  _extract_jacmar_options: Retrieved plafond_deplacement raw: {plafonds_raw}") # AJOUT PRINT
        # -------------------------------------------------------------
        if isinstance(plafonds_raw, list) and len(plafonds_raw) > 0 and isinstance(plafonds_raw[0], dict):
            jacmar_data["plafond_deplacement"] = list(plafonds_raw[0].keys())
            print(f"  DTSC: Extracted plafond keys: {jacmar_data['plafond_deplacement']}")
        else:
            print(f"WARN DTSC: Structure inattendue pour 'plafond_deplacement' dans config: {plafonds_raw}") # Message ajusté
            jacmar_data["plafond_deplacement"] = [] # Fallback
        
        print("--- DTSC: _extract_jacmar_options END ---") # AJOUT PRINT
        return jacmar_data

    def _extract_default_values(self, prefs: Preference) -> dict:
         """Extrait les valeurs par défaut depuis le Singleton Preference.""" 
         defaults = {}
         if prefs.profile:
             defaults["nom"] = prefs.profile.nom
             defaults["prenom"] = prefs.profile.prenom
         if prefs.jacmar:
             defaults["emplacements"] = prefs.jacmar.emplacement # Valeur par défaut unique
             defaults["departements"] = prefs.jacmar.departement # Valeur par défaut unique
             defaults["titre"] = prefs.jacmar.titre             # Valeur par défaut unique
             defaults["superviseurs"] = prefs.jacmar.superviseur # Valeur par défaut unique
             defaults["plafond_deplacement"] = prefs.jacmar.plafond # Valeur par défaut unique (clé)
         return defaults
    # -------------------------------------------------------

    # --- AJOUT: Méthode _populate_type_selection_combo (depuis DocumentsController) --- 
    def _populate_type_selection_combo(self):
        """Appelle la méthode de la vue TypeSelection pour remplir son ComboBox."""
        # logger.info("--- _populate_type_selection_combo START --- ") # AJOUT LOG
        print("*** DTSC: _populate_type_selection_combo START ***") # USE PRINT
        # logger.debug(f"  Types à ajouter: {self.document_types}") # AJOUT LOG
        print(f"  DTSC: Types à ajouter: {self.document_types}") # USE PRINT
        try:
            if hasattr(self.view, 'set_document_types') and callable(getattr(self.view, 'set_document_types')):
                # logger.debug(f"  Appel de self.view.set_document_types({self.document_types})") # AJOUT LOG
                print(f"  DTSC: Appel de self.view.set_document_types({self.document_types})") # USE PRINT
                self.view.set_document_types(self.document_types)
                # logger.info("  Appel à view.set_document_types effectué.") # Mise à jour Log
                print("  DTSC: Appel à view.set_document_types effectué.") # USE PRINT
            else:
                # logger.error("  Erreur: La vue TypeSelection n'a pas de méthode set_document_types ou elle n'est pas appelable.") # Mise à jour Log
                print("ERROR DTSC: La vue TypeSelection n'a pas de méthode set_document_types ou elle n'est pas appelable.") # USE PRINT
        except Exception as e:
            # logger.error(f"  Erreur lors du peuplement du ComboBox Type de document: {e}", exc_info=True) # Mise à jour Log
            print(f"ERROR DTSC _populate_type_selection_combo: {e}") # USE PRINT
        # logger.info("--- _populate_type_selection_combo END --- ") # AJOUT LOG
        print("*** DTSC: _populate_type_selection_combo END ***") # USE PRINT
    # --------------------------------------------------------------------------

    # --- MODIFICATION: Connecter les signaux de la vue aux slots de CE contrôleur --- 
    def _connect_view_signals(self):
        try:
            self.view.create_requested.connect(self._handle_create_request)
            self.view.cancel_requested.connect(self.cancel_requested.emit)
            self.view.type_combo.currentTextChanged.connect(self._on_document_type_selected)
            # logger.debug("DocumentsTypeSelectionController: Signaux de la vue connectés.")
            print("DocumentsTypeSelectionController: Signaux de la vue connectés.")
        except AttributeError as e:
             # logger.error(f"ERREUR connexion signaux TypeSelectionPage: Un widget/signal attendu est manquant - {e}")
             print(f"ERROR DTSC connexion signaux TypeSelectionPage: Un widget/signal attendu est manquant - {e}")
        except Exception as e:
            # logger.error(f"ERREUR connexion signaux TypeSelectionPage: {e}")
            print(f"ERROR DTSC connexion signaux TypeSelectionPage: {e}")
    # --------------------------------------------------------------------------

    # --- AJOUT: Méthode activate --- 
    def activate(self):
        """Appelé lorsque cette page/contrôleur devient actif."""
        # logger.debug("DocumentsTypeSelectionController activated.")
        print("DocumentsTypeSelectionController activated.")
        try:
            initial_type = self.view.type_combo.currentText()
            if initial_type:
                # logger.debug(f"DEBUG (Activate): Déclenchement initial pour le type: {initial_type}")
                print(f"DEBUG (Activate): Déclenchement initial pour le type: {initial_type}")
                self._on_document_type_selected(initial_type)
            else:
                # logger.debug("DEBUG (Activate): Aucun type initial sélectionné dans le ComboBox.")
                print("DEBUG (Activate): Aucun type initial sélectionné dans le ComboBox.")
                if hasattr(self.view, 'update_content_area'):
                     self.view.update_content_area([], {}, {}) # Vider
        except Exception as e:
            # logger.error(f"ERREUR lors du déclenchement initial des champs (activate): {e}", exc_info=True)
            print(f"ERREUR lors du déclenchement initial des champs (activate): {e}")
    # -----------------------------

    # --- MODIFICATION: Logique hardcodée pour déterminer les champs --- 
    @Slot(str)
    def _on_document_type_selected(self, selected_type):
        """Met à jour la zone de contenu dynamique de la vue en fonction du type."""
        # logger.debug(f"--- _on_document_type_selected: Type='{selected_type}' ---")
        print(f"--- _on_document_type_selected: Type='{selected_type}' ---")
        
        fields_structure_list = [] # Initialiser comme vide
        
        # --- Logique Hardcodée --- 
        # !! IMPORTANT !! Adaptez cette section à VOS types de documents et VOS champs !
        if selected_type == "Rapport de depense":
            # logger.debug(f"Détermination des champs pour: {selected_type}")
            print(f"Détermination des champs pour: {selected_type}")
            fields_structure_list = [
                # Champs attendus par votre vue DocumentsTypeSelectionPage
                "date", "nom", "prenom", 
                "emplacements", "departements", "superviseurs",
                "plafond_deplacement"
                # Ajoutez d'autres champs si nécessaire pour ce type
            ]
        # --- AJOUT DU CAS CSA --- 
        elif selected_type == "CSA":
            print(f"Détermination des champs pour: {selected_type} (aucun champ requis)")
            fields_structure_list = [] # Aucun champ pour CSA
        # --------------------------
        # --- Ajoutez d'autres elif pour d'autres types --- 
        # elif selected_type == "Autre Type Document":
        #    logger.debug(f"Détermination des champs pour: {selected_type}")
        #    fields_structure_list = ["champ_a", "champ_b"]
        else:
            # Cas où le type sélectionné n'est pas géré ici (ou si la string est vide)
            if selected_type:
                # logger.warning(f"Type '{selected_type}' sélectionné mais pas de structure de champs hardcodée définie.")
                print(f"Type '{selected_type}' sélectionné mais pas de structure de champs hardcodée définie.")
            else:
                 # logger.debug("_on_document_type_selected appelé avec un type vide (probablement initial).")
                 print("_on_document_type_selected appelé avec un type vide (probablement initial).")
            fields_structure_list = [] # Assurer que la liste est vide
        # --- Fin Logique Hardcodée ---

        # --- Utiliser les données locales (récupérées des singletons dans __init__) --- 
        default_values = self.default_profile_values 
        jacmar_data = self.jacmar_options 
        # logger.debug(f"Utilisation des données locales: DefaultValues={default_values}, JacmarOptionsKeys={list(jacmar_data.keys())}")
        print(f"Utilisation des données locales: DefaultValues={default_values}, JacmarOptionsKeys={list(jacmar_data.keys())}")
        # -------------------------------------------------------------------------

        # --- AJOUT LOG: Vérifier les données passées à la vue --- 
        # logger.debug(f"DEBUG (Controller): Appelle update_content_area avec:")
        # logger.debug(f"  -> fields_structure_list: {fields_structure_list}")
        # logger.debug(f"  -> default_values: {default_values}") 
        # logger.debug(f"  -> jacmar_data: {jacmar_data}") 
        # -------------------------------------------------------
        if hasattr(self.view, 'update_content_area'):
            try:
                 self.view.update_content_area(fields_structure_list, default_values, jacmar_data)
            except Exception as e_update:
                 # logger.error(f"ERROR: Erreur lors de la mise à jour du formulaire dynamique: {e_update}", exc_info=True)
                 print(f"ERROR: Erreur lors de la mise à jour du formulaire dynamique: {e_update}")
                 import traceback
                 traceback.print_exc()
        else:
             # logger.error("ERREUR: La vue TypeSelectionPage n'a pas de méthode update_content_area.")
             print("ERREUR: La vue TypeSelectionPage n'a pas de méthode update_content_area.")
    # ----------------------------------------------------------------------

    # --- Slot _handle_create_request (Validation inchangée pour l'instant) --- 
    @Slot(str)
    def _handle_create_request(self, selected_type):
        """Gère la demande de création venant de la vue."""
        # logger.info(f"DocumentsTypeSelectionController: Create request received for type '{selected_type}'.")
        print(f"DocumentsTypeSelectionController: Create request received for type '{selected_type}'.")
        form_data = {}
        try:
            if hasattr(self.view, 'get_dynamic_form_data'):
                form_data = self.view.get_dynamic_form_data()
                # logger.debug(f"Données récupérées du formulaire: {form_data}")
                print(f"Données récupérées du formulaire: {form_data}")
            else:
                # logger.warning("AVERTISSEMENT: La vue TypeSelectionPage n'a pas de méthode get_dynamic_form_data().")
                print("AVERTISSEMENT: La vue TypeSelectionPage n'a pas de méthode get_dynamic_form_data().")
                QMessageBox.critical(self.view, "Erreur Interne", "Impossible de récupérer les données du formulaire (méthode manquante).")
                return
        except Exception as e_form:
             # logger.error(f"ERREUR lors de la récupération des données du formulaire: {e_form}", exc_info=True)
             print(f"ERREUR lors de la récupération des données du formulaire: {e_form}")
             QMessageBox.warning(self.view, "Erreur Formulaire", f"Impossible de récupérer les données du formulaire.\n{e_form}")
             return

        # --- Validation (gardée ici, utilise les noms de champs hardcodés) --- 
        if selected_type == "Rapport de depense":
            # !! IMPORTANT !! Mettez à jour cette liste si les champs requis changent
            required_fields = ["nom", "prenom", "date", "emplacements", "departements", "superviseurs", "plafond_deplacement"] 
            missing_fields = []
            for field in required_fields:
                if field not in form_data or not str(form_data.get(field, '')).strip(): 
                    readable_field = field.replace("_", " ").capitalize()
                    if field == "departements": readable_field = "Département"
                    if field == "emplacements": readable_field = "Emplacement"
                    if field == "superviseurs": readable_field = "Superviseur"
                    if field == "plafond_deplacement": readable_field = "Plafond déplacement"
                    missing_fields.append(readable_field)
            if missing_fields:
                logger.error(f"ERREUR: Champs manquants ou vides: {missing_fields}")
                error_message = "Veuillez remplir les champs suivants avant de créer le rapport :\n\n- " + "\n- ".join(missing_fields)
                QMessageBox.warning(self.view, "Champs Requis", error_message)
                return
        # --- Fin Validation --- 
        
        # --- Émettre le signal au lieu de créer la fenêtre --- 
        logger.info(f"DocumentsTypeSelectionController: Émission du signal create_request avec type='{selected_type}'...")
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

print("DocumentsTypeSelectionController defined (uses Singletons)") 