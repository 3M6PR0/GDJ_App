import json
import os
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

from utils.paths import get_resource_path # Pour charger la config
import logging
logger = logging.getLogger(__name__)

class NewDocumentController(QObject):
    # Signal émis lorsque l'utilisateur confirme la création
    # Arguments: str (type de document), dict (données initiales)
    creation_confirmed = pyqtSignal(str, dict)

    def __init__(self, view: 'NewDocumentWindow', main_controller=None):
        super().__init__()
        self.view = view
        self.main_controller = main_controller # Pour référence future si besoin
        
        # Récupérer la page interne depuis la vue
        self.type_selection_page = self.view.type_selection_page

        # Charger la config pour peupler la page
        self._load_config_data()
        self._populate_type_selection_combo()
        
        # Connecter les signaux de la page interne
        self._connect_signals()
        
        # Déclencher la mise à jour initiale des champs (si nécessaire)
        self._trigger_initial_field_update()
        
        logger.info("NewDocumentController initialized.")

    def _load_config_data(self, relative_filepath="data/config_data.json"):
        """Charge les types de documents depuis la config."""
        self.document_types = []
        # Ajouter d'autres structures si besoin pour la logique des champs dynamiques
        self.document_fields_map = {} 
        self.jacmar_data = {} # Exemple pour _on_document_type_selected
        self.jacmar_plafonds_keys = [] # Exemple
        
        config_full_path = get_resource_path(relative_filepath)
        try:
            if not os.path.exists(config_full_path):
                logger.warning(f"Fichier config introuvable: {config_full_path}")
                return
            with open(config_full_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            document_config = config_data.get("document", {})
            self.document_types = list(document_config.keys())
            # --- Optionnel : Charger aussi les autres données si besoin --- 
            self.document_fields_map = document_config
            self.jacmar_data = config_data.get("jacmar", {})
            plafond_list = self.jacmar_data.get("plafond_deplacement", [])
            if plafond_list and isinstance(plafond_list, list) and len(plafond_list) > 0 and isinstance(plafond_list[0], dict):
                self.jacmar_plafonds_keys = list(plafond_list[0].keys())
            else:
                self.jacmar_plafonds_keys = []
            # ----------------------------------------------------------
            logger.info(f"Types de documents chargés pour NewDocument: {self.document_types}")
        except Exception as e:
            logger.error(f"Erreur chargement config ({config_full_path}) dans NewDocumentController: {e}", exc_info=True)

    def _populate_type_selection_combo(self):
        """Remplit le ComboBox de la page de sélection."""
        try:
            self.type_selection_page.set_document_types(self.document_types)
            logger.info("NewDocumentController: ComboBox Type de document peuplé.")
        except Exception as e:
            logger.error(f"NewDocumentController: Erreur peuplement ComboBox: {e}", exc_info=True)

    def _connect_signals(self):
        """Connecte les signaux de la page interne aux slots de ce contrôleur."""
        try:
            self.type_selection_page.create_requested.connect(self._handle_create_request)
            self.type_selection_page.cancel_requested.connect(self._handle_cancel_request)
            self.type_selection_page.type_combo.currentTextChanged.connect(self._on_document_type_selected)
            logger.info("NewDocumentController: Internal page signals connected.")
        except Exception as e:
             logger.error(f"NewDocumentController: Error connecting internal signals: {e}", exc_info=True)
             
    def _trigger_initial_field_update(self):
        """Déclenche la mise à jour initiale des champs dynamiques."""
        try:
            initial_type = self.type_selection_page.type_combo.currentText()
            if initial_type:
                logger.info(f"NewDocumentController: Triggering initial field update for type: {initial_type}")
                self._on_document_type_selected(initial_type)
            else:
                logger.info("NewDocumentController: No initial type selected, clearing fields.")
                self.type_selection_page.update_content_area({}) # Vider les champs
        except Exception as e:
            logger.error(f"NewDocumentController: Error triggering initial fields: {e}", exc_info=True)

    # --- Slots --- 
    @pyqtSlot(str)
    def _handle_create_request(self, selected_type):
        """Gère la demande de création."""
        logger.info(f"NewDocumentController: Create requested for type '{selected_type}'.")
        initial_data = {}
        try:
            if hasattr(self.type_selection_page, 'get_dynamic_fields_data'):
                initial_data = self.type_selection_page.get_dynamic_fields_data()
                logger.info(f"Initial data retrieved: {initial_data}")
            else:
                logger.warning("TypeSelectionPage has no 'get_dynamic_fields_data' method.")
        except Exception as e:
            logger.error(f"Error retrieving initial data: {e}", exc_info=True)
            
        # Émettre le signal vers MainController
        self.creation_confirmed.emit(selected_type, initial_data)
        # Fermer la fenêtre de dialogue
        self.view.close()

    @pyqtSlot()
    def _handle_cancel_request(self):
        """Gère l'annulation."""
        logger.info("NewDocumentController: Cancel requested.")
        self.view.close()
        
    @pyqtSlot(str)
    def _on_document_type_selected(self, selected_type):
        """Met à jour les champs dynamiques lorsque le type change."""
        logger.info(f"NewDocumentController: Document type selected: '{selected_type}'")
        # --- Logique copiée de DocumentsController --- 
        #    (Simplifiée ici, peut nécessiter les préférences ou être adaptée)
        fields_to_display = self.document_fields_map.get(selected_type, []) 
        logger.debug(f"Fields to display for '{selected_type}': {fields_to_display}")
        data_for_view = {}
        
        # Map pour récupérer les valeurs par défaut (ici, juste des exemples)
        # Idéalement, il faudrait accéder aux préférences via main_controller ou autrement
        pref_mock_data = {
            "nom": "Utilisateur",
            "prenom": "Test",
            "emplacements": ["Mascouche", "Quebec"], 
            "departements": ["Service", "Ventes"], 
            "superviseurs": ["Chef A", "Chef B"],
            "plafond_deplacement": ["Cap 0", "Cap 1"]
        }
        pref_mock_defaults = {
            "nom": "Dupont", "prenom": "Jean", "emplacements": "Mascouche",
            "departements": "Service", "superviseurs": "Chef A", "plafond_deplacement": "Cap 1"
        }

        for field_name in fields_to_display:
            if field_name == "date":
                data_for_view[field_name] = {"type": "month_year_combo"}
                continue
                
            field_config = self.jacmar_data.get(field_name) # Utiliser jacmar_data chargé
            is_combo = isinstance(field_config, list) or field_name == "plafond_deplacement"
            widget_type = "combo" if is_combo else "lineedit"
            if field_name in ["nom", "prenom"]: widget_type = "lineedit"
            
            default_value = pref_mock_defaults.get(field_name) # Utiliser mock prefs pour test
            
            if widget_type == "lineedit":
                 current_value = default_value if default_value is not None else ""
                 data_for_view[field_name] = {"type": "lineedit", "value": current_value}
            elif widget_type == "combo":
                options = []
                if field_name == "plafond_deplacement":
                    options = self.jacmar_plafonds_keys
                else:
                    options = self.jacmar_data.get(field_name, []) # Utiliser jacmar_data
                data_for_view[field_name] = {"type": "combo", "options": options, "default": default_value}
            else:
                data_for_view[field_name] = {"type": "label", "value": "Erreur type widget"}
        # -----------------------------------------------
        logger.debug(f"Data for view prepared: {data_for_view}")
        try:
            self.type_selection_page.update_content_area(data_for_view)
            logger.info("NewDocumentController: Dynamic content area updated.")
        except Exception as e:
            logger.error(f"NewDocumentController: Error calling update_content_area: {e}", exc_info=True) 