from PyQt5.QtCore import QObject, pyqtSlot, Qt
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QLineEdit, QComboBox # Ajouter QMessageBox pour feedback
from PyQt5.QtGui import QPixmap # Import correct pour QPixmap
import json # Assurer que json est importé
import functools # Ajouter functools
import os # Ajouter os pour le chemin
import copy # AJOUT pour deepcopy
import logging # AJOUT
from utils.signals import signals
from utils.stylesheet_loader import load_stylesheet
from utils import icon_loader # Ajouter import

# Importer le modèle Preference
from models.preference import Preference # Singleton
from models.config_data import ConfigData # Singleton
from pages.preferences.preferences_page import SimpleToggle, SignaturePreviewWidget # Ajouter SignaturePreviewWidget

# --- AJOUT Logger --- 
logger = logging.getLogger(__name__)
# ------------------

def _get_nested_attr(obj, attr_path, default=None):
    """Accède à un attribut imbriqué en utilisant une chaîne de caractères (ex: 'profile.nom').""" 
    attributes = attr_path.split('.')
    for attr in attributes:
        try:
            obj = getattr(obj, attr)
        except AttributeError:
            return default
    return obj

class PreferencesController(QObject):
    """Contrôleur pour la page des Préférences.

    Ce contrôleur gère la logique de la page des préférences utilisateur. Il interagit
    avec les Singletons `Preference` (pour lire/écrire les valeurs des préférences) et
    `ConfigData` (pour lire les options de configuration, ex: listes Jacmar).

    Responsabilités principales :
    - Charger les options de configuration (listes Jacmar) depuis `ConfigData`.
    - Peupler les ComboBox de la vue avec ces options.
    - Charger les valeurs actuelles des préférences depuis le Singleton `Preference`.
    - Afficher ces valeurs dans les widgets correspondants de la vue.
    - Gérer les interactions utilisateur : sélection d'image de signature, 
      import/export de préférences, sauvegarde des modifications.
    - Gérer la logique d'activation/désactivation et de réinitialisation 
      des champs modifiés.
    - Appliquer les changements de thème visuellement et notifier les autres 
      composants via un signal.

    Attributes:
        view: L'instance de la vue `PreferencesPage` associée.
        main_controller: Référence (optionnelle) au contrôleur principal 
            de l'application, utilisé pour l'application globale du thème.
        prefs_singleton (Preference): L'instance unique du Singleton Preference.
        initial_prefs_copy (Preference): Une copie profonde de l'état initial des 
            préférences, utilisée pour détecter les modifications et réinitialiser les champs.
        jacmar_emplacements (list): Liste des emplacements Jacmar chargée depuis ConfigData.
        jacmar_departements (list): Liste des départements Jacmar chargée depuis ConfigData.
        jacmar_titres (list): Liste des titres Jacmar chargée depuis ConfigData.
        jacmar_superviseurs (list): Liste des superviseurs Jacmar chargée depuis ConfigData.
        jacmar_plafonds (list): Liste des noms de plafonds chargée depuis ConfigData.
        _selected_signature_path (str | None): Chemin vers le fichier image de 
            signature actuellement sélectionné ou chargé.
    """
    def __init__(self, view, main_controller=None):
        """
        Initialise le contrôleur pour la page Préférences.
        Lit les données depuis les Singletons Preference et ConfigData.

        Args:
            view (PreferencesPage): L'instance de la vue (page Préférences).
            main_controller: L'instance du contrôleur principal.
        """
        super().__init__()
        self.view = view
        self.main_controller = main_controller

        # --- MODIFICATION: Obtenir le Singleton Preference --- 
        self.prefs_singleton = Preference.get_instance()
        # Faire une copie initiale pour la logique de reset/comparaison
        self.initial_prefs_copy = copy.deepcopy(self.prefs_singleton) 
        # ----------------------------------------------------

        # --- MODIFICATION: Charger les options Jacmar via ConfigData --- 
        self.jacmar_emplacements = []
        self.jacmar_departements = []
        self.jacmar_titres = []
        self.jacmar_superviseurs = []
        self.jacmar_plafonds = [] # Liste des clés (str)
        self._load_jacmar_options() # Charge depuis ConfigData
        # ------------------------------------------------------------

        # --- Stocker le chemin de signature de l'état initial --- 
        # (Utilisé pour la prévisualisation et comparaison)
        self._selected_signature_path = self.initial_prefs_copy.profile.signature_path
        # -----------------------------------------------------

        # Peupler les ComboBox de la vue AVANT de mettre à jour avec les prefs
        self._populate_view_combos() # Utilise les listes jacmar chargées

        # Connecter les signaux
        self._connect_standard_signals()
        self._connect_modification_signals() # Pour les boutons reset

        # Mettre à jour la vue avec l'état du Singleton Preference
        self._update_view_from_prefs(self.prefs_singleton) # Passer le singleton à mettre à jour
        
        # Comparer l'état de la vue avec la COPIE INITIALE pour les boutons reset
        self._check_all_fields_initial()

    # --- MODIFICATION: Charger options Jacmar depuis ConfigData --- 
    def _load_jacmar_options(self):
         """Charge les listes d'options Jacmar depuis ConfigData.""" 
         try:
             config = ConfigData.get_instance()
             jacmar_config = config.get_top_level_key("jacmar", default={})
             
             self.jacmar_emplacements = jacmar_config.get('emplacements', [])
             self.jacmar_departements = jacmar_config.get('departements', [])
             self.jacmar_titres = jacmar_config.get('titres', [])
             self.jacmar_superviseurs = jacmar_config.get('superviseurs', [])
             plafonds_raw = jacmar_config.get('plafond_deplacement', []) 
             if isinstance(plafonds_raw, list) and len(plafonds_raw) > 0 and isinstance(plafonds_raw[0], dict):
                 self.jacmar_plafonds = list(plafonds_raw[0].keys()) 
             else:
                 logger.warning(f"Structure inattendue pour 'plafond_deplacement' dans config: {plafonds_raw}")
                 self.jacmar_plafonds = []
             
             logger.info("Options Jacmar chargées depuis ConfigData pour PreferencesController.")
             
         except Exception as e:
             logger.error(f"Erreur lors du chargement des options Jacmar pour PreferencesController: {e}", exc_info=True)
    # -------------------------------------------------------------
             
    def _populate_view_combos(self):
        """Appelle la méthode de la vue pour remplir les ComboBox Jacmar."""
        try:
            if hasattr(self.view, 'populate_jacmar_combos'):
                self.view.populate_jacmar_combos(
                    emplacements=self.jacmar_emplacements,
                    departements=self.jacmar_departements,
                    titres=self.jacmar_titres,
                    superviseurs=self.jacmar_superviseurs,
                    plafonds=self.jacmar_plafonds
                )
                logger.debug("ComboBox Jacmar peuplés.") # Mis à jour log level
            else:
                logger.error("Erreur: La vue n'a pas de méthode populate_jacmar_combos.")
        except Exception as e:
            logger.error(f"Erreur lors du peuplement des ComboBox: {e}", exc_info=True)

    def _connect_standard_signals(self):
        """Connecte les signaux généraux de la vue."""
        self.view.select_signature_requested.connect(self.select_signature_image)
        self.view.export_prefs_requested.connect(self.export_preferences)
        self.view.import_prefs_requested.connect(self.import_preferences)
        self.view.save_prefs_requested.connect(self.save_preferences)
        
        # --- CONNEXION POUR LE THÈME --- 
        try:
             # --- Utiliser la référence directe --- 
             if hasattr(self.view, 'cb_theme') and isinstance(self.view.cb_theme, QComboBox):
                  self.view.cb_theme.currentTextChanged.connect(self._on_theme_changed)
                  logger.debug("Theme ComboBox connected to _on_theme_changed (via Pref Controller).") # Mis à jour
             else:
                  logger.warning("Warning: self.view.cb_theme not found or not a QComboBox.") # Mis à jour
        except Exception as e:
             logger.error(f"Error connecting themeComboBox signal: {e}") # Mis à jour
        # ------------------------------

    def _connect_modification_signals(self):
        """Connecte les signaux de changement et les clics refresh."""
        for pref_path in self.view.get_all_pref_paths():
            input_widget = self.view.get_input_widget(pref_path)
            refresh_button = self.view.get_refresh_button(pref_path)
            if input_widget and refresh_button:
                # --- Connexion du signal de modification (TOUS les champs, y compris cb_theme) ---
                signal = None
                # Le slot_check appellera _check_field_modification pour TOUS les widgets
                slot_check = functools.partial(self._check_field_modification, input_widget, pref_path)
                
                if isinstance(input_widget, QLineEdit):
                    signal = input_widget.textChanged
                elif isinstance(input_widget, QComboBox):
                    # Ceci s'appliquera maintenant aussi à cb_theme
                    signal = input_widget.currentTextChanged
                elif isinstance(input_widget, SimpleToggle):
                    signal = input_widget.toggled
                elif isinstance(input_widget, SignaturePreviewWidget):
                    # Signature gérée différemment (pas de signal direct)
                    pass 
                
                if signal:
                    # Connecter le changement de valeur à la vérification de modification
                    signal.connect(slot_check)
                
                # --- Connexion du clic du bouton refresh (TOUS les champs) ---
                slot_revert = functools.partial(self._revert_field_value, input_widget, pref_path)
                refresh_button.clicked.connect(slot_revert)
            else:
                logger.warning(f"Warning: Widget d'entrée ou bouton refresh manquant pour {pref_path}") # Mis à jour

    def _check_all_fields_initial(self):
        """Vérifie l'état de tous les champs au démarrage pour afficher/cacher les boutons refresh."""
        logger.debug("Vérification initiale des champs...") # Mis à jour
        for pref_path in self.view.get_all_pref_paths():
            input_widget = self.view.get_input_widget(pref_path)
            if input_widget:
                self._check_field_modification(input_widget, pref_path)

    def _check_field_modification(self, input_widget, pref_path):
        """Compare la valeur actuelle avec la valeur de la COPIE INITIALE et gère l'opacité du bouton."""
        opacity_effect = self.view.get_refresh_effect(pref_path)
        if not opacity_effect:
            # Essayer de récupérer le bouton pour être sûr (au cas où l'effet n'existe pas)
            refresh_button = self.view.get_refresh_button(pref_path)
            if refresh_button: refresh_button.setVisible(False) # Fallback sécurité
            return

        # Comparer à la copie faite dans __init__
        saved_value = _get_nested_attr(self.initial_prefs_copy, pref_path) 
        current_value = None
        is_different = False

        try:
            if isinstance(input_widget, QLineEdit):
                current_value = input_widget.text()
            elif isinstance(input_widget, QComboBox):
                current_value = input_widget.currentText()
                if pref_path == 'jacmar.plafond':
                    saved_value = str(saved_value)
            elif isinstance(input_widget, SimpleToggle):
                current_value = input_widget.isChecked()
            elif isinstance(input_widget, SignaturePreviewWidget):
                # Comparer les chemins mémorisés
                current_value = self._selected_signature_path 
                # S'assurer que les None ou "" sont traités pareil
                saved_value = saved_value if saved_value else ""
                current_value = current_value if current_value else ""
            else:
                current_value = None # Type non géré

            if current_value is not None:
                 is_different = (current_value != saved_value)

        except Exception as e:
            logger.error(f"Erreur lecture/comparaison valeur widget {pref_path}: {e}") # Mis à jour
            is_different = False # Erreur -> pas différent

        # Mettre à jour l'opacité de l'effet
        opacity_effect.setOpacity(1.0 if is_different else 0.0)
        # Optionnel: Gérer l'état enabled en plus de l'opacité si besoin
        # refresh_button = self.view.get_refresh_button(pref_path)
        # if refresh_button: refresh_button.setEnabled(is_different)

    def _revert_field_value(self, input_widget, pref_path):
        """Réinitialise la valeur du widget à la valeur de la COPIE INITIALE."""
        logger.debug(f"Réinitialisation du champ: {pref_path}") # Mis à jour
        # Lire depuis la copie faite dans __init__
        saved_value = _get_nested_attr(self.initial_prefs_copy, pref_path) 
        opacity_effect = self.view.get_refresh_effect(pref_path)
        
        try:
            if isinstance(input_widget, QLineEdit):
                input_widget.setText(str(saved_value or '')) # S'assurer str
            elif isinstance(input_widget, QComboBox): 
                index = input_widget.findText(str(saved_value or ''), Qt.MatchFixedString)
                if index >= 0: input_widget.setCurrentIndex(index)
                else: logger.warning(f"Avertissement: Impossible de trouver '{saved_value}' dans {pref_path} QComboBox.")
            elif isinstance(input_widget, SimpleToggle): input_widget.setChecked(bool(saved_value))
            elif isinstance(input_widget, SignaturePreviewWidget):
                self._selected_signature_path = saved_value if saved_value else ""
                pixmap = QPixmap(self._selected_signature_path) if self._selected_signature_path else QPixmap()
                input_widget.setPixmap(pixmap if not pixmap.isNull() else None)
            
            # Rendre le bouton transparent après réinitialisation
            if opacity_effect:
                opacity_effect.setOpacity(0.0)
            # Optionnel: Désactiver aussi
            # refresh_button = self.view.get_refresh_button(pref_path)
            # if refresh_button: refresh_button.setEnabled(False)

        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation de {pref_path}: {e}") # Mis à jour

    def _update_view_from_prefs(self, prefs: Preference): # Prend l'instance en argument
        """Met à jour les widgets de la vue avec les valeurs du Singleton Preference."""
        logger.debug("PreferencesController: Mise à jour vue depuis Singleton Preference...") # Mis à jour
        # Section Profile
        self.view.le_nom.setText(prefs.profile.nom)
        self.view.le_prenom.setText(prefs.profile.prenom)
        self.view.le_tel.setText(prefs.profile.telephone)
        self.view.le_courriel.setText(prefs.profile.courriel)
        # Utiliser _selected_signature_path qui est synchronisé avec l'état initial/importé
        if self._selected_signature_path:
            pixmap = QPixmap(self._selected_signature_path)
            self.view.update_signature_preview(pixmap if not pixmap.isNull() else None, 
                                              "Chemin invalide" if pixmap.isNull() else None)
        else:
             self.view.update_signature_preview(None, "...")

        # Section Jacmar
        self.view.cb_emplacement.setCurrentText(prefs.jacmar.emplacement)
        self.view.cb_dept.setCurrentText(prefs.jacmar.departement)
        self.view.cb_titre.setCurrentText(prefs.jacmar.titre)
        self.view.cb_super.setCurrentText(prefs.jacmar.superviseur)
        plafond_key = prefs.jacmar.plafond
        index = self.view.cb_plafond.findText(str(plafond_key), Qt.MatchFixedString)
        if index >= 0: self.view.cb_plafond.setCurrentIndex(index)
        else: 
             logger.warning(f"Avertissement: Clé de plafond '{plafond_key}' non trouvée dans combo...")
             if self.view.cb_plafond.count() > 0: self.view.cb_plafond.setCurrentIndex(0)

        # Section Application (Thème, etc.)
        if hasattr(self.view, 'cb_theme'):
            theme_value = prefs.application.theme
            self.view.cb_theme.setCurrentText(theme_value)
            logger.debug(f"  - Theme ComboBox set to: '{theme_value}' (from Singleton)") # Mis à jour
        else: logger.warning("  - Warning: Theme ComboBox (self.view.cb_theme) not found.") # Mis à jour
        self.view.toggle_auto_update.setChecked(prefs.application.auto_update)
        self.view.toggle_show_notes.setChecked(prefs.application.show_note)

        logger.debug("Préférences Contrôleur: Vue mise à jour depuis Singleton.") # Mis à jour
    # --------------------------------------------------------------

    @pyqtSlot()
    def select_signature_image(self):
        """ Ouvre une boîte de dialogue pour sélectionner une image et met à jour la vue. """
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self.view, # Parent est la vue
                                                  "Sélectionner une image de signature",
                                                  self._selected_signature_path or "", # Ouvre au dernier chemin
                                                  "Images (*.png *.jpg *.jpeg *.bmp)",
                                                  options=options)
        
        if file_path:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                logger.error(f"Erreur: Impossible de charger l'image depuis {file_path}") # Mis à jour
                self.view.update_signature_preview(None, "Erreur")
                self._selected_signature_path = "" # Réinitialiser en cas d'erreur
            else:
                logger.debug(f"Image sélectionnée par contrôleur: {file_path}") # Mis à jour
                self.view.update_signature_preview(pixmap)
                self._selected_signature_path = file_path # Mémoriser le chemin choisi
            
            # --- Vérifier la modification après sélection --- 
            self._check_field_modification(self.view.signature_display_widget, "profile.signature_path")
        # Si annulé, ne rien faire, la vérification n'est pas nécessaire

    @pyqtSlot()
    def export_preferences(self):
        """ Exporte les préférences ACTUELLES du Singleton Preference."""
        logger.info("Préférences Contrôleur: Exportation demandée...") # Mis à jour
        options = QFileDialog.Options()
        suggested_filename = "preference.json"
        file_path, _ = QFileDialog.getSaveFileName(self.view, 
                                                   "Exporter les préférences sous...", 
                                                   suggested_filename,
                                                   "Fichiers JSON (*.json);;Tous les fichiers (*)", 
                                                   options=options)
        if not file_path: logger.debug("Exportation annulée."); return # Mis à jour
        if not file_path.lower().endswith('.json'): file_path += '.json'
        logger.debug(f"Tentative d'exportation vers: {file_path}") # Mis à jour
        try:
            # Utiliser la méthode save du Singleton pour écrire son état actuel
            self.prefs_singleton.save(relative_filepath=file_path) # Passer le chemin choisi
            QMessageBox.information(self.view, "Exportation réussie",
                                    f"Les préférences actuelles ont été exportées vers:\n{file_path}")
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation vers {file_path}: {e}", exc_info=True) # Mis à jour
            QMessageBox.critical(self.view, "Erreur d'exportation",
                                 f"Une erreur est survenue:\n{e}")
    # ----------------------------------------------------------

    @pyqtSlot()
    def import_preferences(self):
        """ Importe un fichier, met à jour le Singleton Preference et la vue (sans sauvegarder)."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self.view,
                                                  "Importer un fichier de préférences", "",
                                                  "Fichiers JSON (*.json);;Tous les fichiers (*)", options=options)
        if not file_path: logger.debug("Importation annulée."); return # Mis à jour
        logger.debug(f"Tentative d'importation depuis: {file_path}") # Mis à jour
        try:
            with open(file_path, 'r', encoding='utf-8') as f: loaded_data = json.load(f)
            # Validation (inchangée)
            if not isinstance(loaded_data, dict) or \
               'profile' not in loaded_data or 'jacmar' not in loaded_data or 'application' not in loaded_data or \
               not isinstance(loaded_data['profile'], dict) or not isinstance(loaded_data['jacmar'], dict) or not isinstance(loaded_data['application'], dict):
                raise ValueError("Structure JSON invalide.")
                
            # Mettre à jour l'instance Singleton en mémoire
            self.prefs_singleton.update_from_dict(loaded_data)
            
            # Mettre à jour la copie locale pour la logique de reset
            self.initial_prefs_copy = copy.deepcopy(self.prefs_singleton)
            # Mettre à jour le chemin de signature local
            self._selected_signature_path = self.initial_prefs_copy.profile.signature_path
            
            # Mettre à jour l'interface utilisateur
            self._update_view_from_prefs(self.prefs_singleton)
            # Relancer la comparaison pour les boutons refresh
            self._check_all_fields_initial()
            
            logger.info(f"Préférences importées (non sauvegardées) depuis {file_path}.") # Mis à jour
            QMessageBox.information(self.view, "Importation réussie", "Préférences chargées. Sauvegardez pour conserver.")
            
        except (json.JSONDecodeError, FileNotFoundError, ValueError, Exception) as e:
            error_title = "Erreur d'importation"
            error_msg = f"Une erreur est survenue:\n{e}"
            if isinstance(e, json.JSONDecodeError): error_msg = f"Fichier JSON invalide:\n{e}"
            elif isinstance(e, FileNotFoundError): error_msg = "Fichier non trouvé."
            elif isinstance(e, ValueError): error_msg = f"Structure JSON incorrecte:\n{e}"
            logger.error(f"Erreur importation depuis {file_path}: {e}", exc_info=True) # Mis à jour
            QMessageBox.warning(self.view, error_title, error_msg)
    # -------------------------------------------------------------

    @pyqtSlot()
    def save_preferences(self):
        """ Met à jour le Singleton Preference depuis la vue et appelle sa méthode save. """
        logger.info("Préférences Contrôleur: Sauvegarde demandée...") # Mis à jour
        try:
            # --- Mettre à jour le Singleton Preference depuis la vue --- 
            prefs = self.prefs_singleton # Raccourci
            # Profile
            prefs.profile.nom = self.view.le_nom.text()
            prefs.profile.prenom = self.view.le_prenom.text()
            prefs.profile.telephone = self.view.le_tel.text()
            prefs.profile.courriel = self.view.le_courriel.text()
            prefs.profile.signature_path = self._selected_signature_path
            # Jacmar
            prefs.jacmar.emplacement = self.view.cb_emplacement.currentText()
            prefs.jacmar.departement = self.view.cb_dept.currentText()
            prefs.jacmar.titre = self.view.cb_titre.currentText()
            prefs.jacmar.superviseur = self.view.cb_super.currentText()
            prefs.jacmar.plafond = self.view.cb_plafond.currentText()
            # Application
            if hasattr(self.view, 'cb_theme'): prefs.application.theme = self.view.cb_theme.currentText()
            else: logger.warning("Warning: cb_theme not found during save_preferences.")
            prefs.application.auto_update = self.view.toggle_auto_update.isChecked()
            prefs.application.show_note = self.view.toggle_show_notes.isChecked()
            # ---------------------------------------------------------

            # Appeler la méthode save du Singleton (qui utilise le chemin par défaut)
            self.prefs_singleton.save()
            
            # Mettre à jour la copie locale pour refléter le nouvel état sauvegardé
            self.initial_prefs_copy = copy.deepcopy(self.prefs_singleton)
            
            self._check_all_fields_initial() # Remettre opacité boutons refresh à 0
            QMessageBox.information(self.view, "Sauvegarde", "Préférences sauvegardées.")

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour ou sauvegarde des préférences: {e}", exc_info=True) # Mis à jour
            QMessageBox.warning(self.view, "Erreur", f"Impossible de sauvegarder les préférences: {e}")
    # ------------------------------------------------------------------------------

    # --- SLOT POUR LE CHANGEMENT DE THÈME (inchangé, applique visuellement et signale) --- 
    @pyqtSlot(str)
    def _on_theme_changed(self, theme_text):
        logger.debug(f"Theme ComboBox changed to: {theme_text} - Applying visual change only.") # Mis à jour
        theme_to_apply = 'Sombre'
        if theme_text == "Clair": theme_to_apply = 'Clair'
        elif theme_text == "Sombre": theme_to_apply = 'Sombre'
        try: icon_loader.set_active_theme(theme_to_apply)
        except Exception as e_icon: logger.error(f"Error setting icon loader theme: {e_icon}") # Mis à jour
        if self.main_controller and hasattr(self.main_controller, 'apply_theme'):
            logger.debug(f"Calling main_controller.apply_theme('{theme_to_apply}')...") # Mis à jour
            self.main_controller.apply_theme(theme_to_apply)
        else:
            logger.warning("Warning: MainController unavailable/missing apply_theme. Applying style directly.") # Mis à jour
            try:
                qss_files = ["resources/styles/global.qss", "resources/styles/frame.qss"]
                combined_stylesheet = load_stylesheet(qss_files, theme_name=theme_to_apply)
                app_instance = QApplication.instance()
                if app_instance: app_instance.setStyleSheet(combined_stylesheet); logger.debug("Global stylesheet reapplied directly.") # Mis à jour
                else: logger.error("Error: QApplication.instance() returned None.")
            except Exception as e_apply: logger.error(f"Error reapplying stylesheet directly: {e_apply}")
        try: signals.theme_changed_signal.emit(theme_to_apply)
        except Exception as e_signal: logger.error(f"Error emitting theme_changed_signal: {e_signal}")

print("PreferencesController (utilisant Preference Singleton) defined") # Message final 