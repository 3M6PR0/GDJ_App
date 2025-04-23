from PyQt5.QtCore import QObject, pyqtSlot, Qt
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QLineEdit, QComboBox # Ajouter QMessageBox pour feedback
from PyQt5.QtGui import QPixmap # Import correct pour QPixmap
import json # Assurer que json est importé
import functools # Ajouter functools
import os # Ajouter os pour le chemin
from utils.stylesheet_loader import load_stylesheet
from utils import icon_loader # Ajouter import

# Importer le modèle Preference
from models.preference import Preference
from pages.preferences.preferences_page import SimpleToggle, SignaturePreviewWidget # Ajouter SignaturePreviewWidget

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
    def __init__(self, view, main_controller=None):
        """
        Initialise le contrôleur pour la page Préférences.

        Args:
            view (PreferencesPage): L'instance de la vue (page Préférences).
            main_controller: L'instance du contrôleur principal (optionnel pour l'instant).
        """
        super().__init__()
        self.view = view
        self.main_controller = main_controller

        # Charger les données de configuration pour les ComboBox
        self._load_config_data()

        # 1. Charger les préférences sauvegardées
        self.saved_preferences = Preference()
        self.saved_preferences.load() # Charge depuis data/preference.json

        # 2. Créer l'état courant comme copie initiale de l'état sauvegardé
        self.current_preferences = Preference()
        # Utiliser to_dict et update_from_dict pour une copie "profonde" simple
        initial_data = self.saved_preferences.to_dict()
        self.current_preferences.profile.update_from_dict(initial_data["profile"])
        self.current_preferences.jacmar.update_from_dict(initial_data["jacmar"])
        self.current_preferences.application.update_from_dict(initial_data["application"])

        # Stocker le chemin de la signature (basé sur l'état courant/initial)
        self._selected_signature_path = self.current_preferences.profile.signature_path

        # Peupler les ComboBox de la vue AVANT de mettre à jour avec les prefs
        self._populate_view_combos()

        # Connecter les signaux standard (save/import/export/signature)
        self._connect_standard_signals()
        # Connecter les signaux pour la détection de modification et la réinitialisation
        self._connect_modification_signals()

        # Mettre à jour la vue avec l'état COURANT
        self._update_view_from_prefs() 
        # Comparer l'état courant initial avec l'état SAUVEGARDE
        self._check_all_fields_initial()

    def _load_config_data(self, filepath="data/config_data.json"):
        """Charge les listes déroulantes depuis le fichier de configuration."""
        # Initialiser avec des listes vides en cas d'échec
        self.jacmar_emplacements = []
        self.jacmar_departements = []
        self.jacmar_titres = []
        self.jacmar_superviseurs = []
        self.jacmar_plafonds_dict = {} # Stocker le dict {clé: valeur_num}

        try:
            if not os.path.exists(filepath):
                print(f"Avertissement: Fichier de configuration introuvable: {filepath}")
                return
                
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            jacmar_config = config_data.get("jacmar", {})
            self.jacmar_emplacements = jacmar_config.get("emplacements", [])
            self.jacmar_departements = jacmar_config.get("departements", [])
            self.jacmar_titres = jacmar_config.get("titres", [])
            self.jacmar_superviseurs = jacmar_config.get("superviseurs", [])
            
            # Traitement spécial pour plafond_deplacement
            plafond_list = jacmar_config.get("plafond_deplacement", [])
            if plafond_list and isinstance(plafond_list, list) and isinstance(plafond_list[0], dict):
                self.jacmar_plafonds_dict = plafond_list[0]
                self.jacmar_plafonds = list(self.jacmar_plafonds_dict.keys()) # Toujours les clés pour le ComboBox
            else:
                self.jacmar_plafonds = []
                self.jacmar_plafonds_dict = {}
                
            print(f"Données de configuration chargées depuis {filepath}")

        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON dans {filepath}: {e}")
        except Exception as e:
            print(f"Erreur lors du chargement de {filepath}: {e}")
            
    def _populate_view_combos(self):
        """Appelle la méthode de la vue pour remplir les ComboBox Jacmar."""
        try:
            # Vérifier si la méthode existe sur la vue
            if hasattr(self.view, 'populate_jacmar_combos'):
                self.view.populate_jacmar_combos(
                    emplacements=self.jacmar_emplacements,
                    departements=self.jacmar_departements,
                    titres=self.jacmar_titres,
                    superviseurs=self.jacmar_superviseurs,
                    plafonds=self.jacmar_plafonds
                )
                print("ComboBox Jacmar peuplés.")
            else:
                print("Erreur: La vue n'a pas de méthode populate_jacmar_combos.")
        except Exception as e:
            print(f"Erreur lors du peuplement des ComboBox: {e}")

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
                  print("Theme ComboBox connected to _on_theme_changed (via direct reference).")
             else:
                  print("Warning: self.view.cb_theme not found or not a QComboBox.")
        except Exception as e:
             print(f"Error connecting themeComboBox signal: {e}")
        # ------------------------------

    def _connect_modification_signals(self):
        """Connecte les signaux de changement et les clics refresh."""
        for pref_path in self.view.get_all_pref_paths():
            input_widget = self.view.get_input_widget(pref_path)
            refresh_button = self.view.get_refresh_button(pref_path)
            if input_widget and refresh_button:
                # --- SUPPRESSION DU CAS SPÉCIAL POUR cb_theme --- 
                # if input_widget == self.view.cb_theme:
                #     slot_revert = functools.partial(self._revert_field_value, input_widget, pref_path)
                #     refresh_button.clicked.connect(slot_revert)
                #     continue 
                # -------------------------------------------------
                
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
                print(f"Warning: Widget d'entrée ou bouton refresh manquant pour {pref_path}")

    def _check_all_fields_initial(self):
        """Vérifie l'état de tous les champs au démarrage pour afficher/cacher les boutons refresh."""
        print("Vérification initiale des champs...")
        for pref_path in self.view.get_all_pref_paths():
            input_widget = self.view.get_input_widget(pref_path)
            if input_widget:
                self._check_field_modification(input_widget, pref_path)

    def _check_field_modification(self, input_widget, pref_path):
        """Compare la valeur actuelle avec la valeur SAUVEGARDEE et gère l'opacité du bouton."""
        opacity_effect = self.view.get_refresh_effect(pref_path)
        if not opacity_effect:
            # Essayer de récupérer le bouton pour être sûr (au cas où l'effet n'existe pas)
            refresh_button = self.view.get_refresh_button(pref_path)
            if refresh_button: refresh_button.setVisible(False) # Fallback sécurité
            return

        saved_value = _get_nested_attr(self.saved_preferences, pref_path)
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
            print(f"Erreur lecture/comparaison valeur widget {pref_path}: {e}")
            is_different = False # Erreur -> pas différent

        # Mettre à jour l'opacité de l'effet
        opacity_effect.setOpacity(1.0 if is_different else 0.0)
        # Optionnel: Gérer l'état enabled en plus de l'opacité si besoin
        # refresh_button = self.view.get_refresh_button(pref_path)
        # if refresh_button: refresh_button.setEnabled(is_different)

    def _revert_field_value(self, input_widget, pref_path):
        """Réinitialise la valeur du widget à la valeur SAUVEGARDEE."""
        print(f"Réinitialisation du champ: {pref_path}")
        saved_value = _get_nested_attr(self.saved_preferences, pref_path)
        opacity_effect = self.view.get_refresh_effect(pref_path)
        
        try:
            if isinstance(input_widget, QLineEdit):
                input_widget.setText(str(saved_value))
            elif isinstance(input_widget, QComboBox):
                index = input_widget.findText(str(saved_value), Qt.MatchFixedString)
                if index >= 0:
                    input_widget.setCurrentIndex(index)
                else:
                    print(f"Avertissement: Impossible de trouver '{saved_value}' dans {pref_path} QComboBox.")
            elif isinstance(input_widget, SimpleToggle):
                input_widget.setChecked(bool(saved_value))
            elif isinstance(input_widget, SignaturePreviewWidget):
                # Réinitialiser le chemin mémorisé et mettre à jour l'aperçu
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
            print(f"Erreur lors de la réinitialisation de {pref_path}: {e}")

    def _update_view_from_prefs(self):
        """Met à jour les widgets de la vue avec les valeurs de self.current_preferences."""
        # Section Profile
        self.view.le_nom.setText(self.current_preferences.profile.nom)
        self.view.le_prenom.setText(self.current_preferences.profile.prenom)
        self.view.le_tel.setText(self.current_preferences.profile.telephone)
        self.view.le_courriel.setText(self.current_preferences.profile.courriel)
        if self._selected_signature_path:
            pixmap = QPixmap(self._selected_signature_path)
            if not pixmap.isNull():
                self.view.update_signature_preview(pixmap)
            else:
                self.view.update_signature_preview(None, "Chemin invalide")
        else:
             self.view.update_signature_preview(None, "...") # Texte initial

        # Section Jacmar
        self.view.cb_emplacement.setCurrentText(self.current_preferences.jacmar.emplacement)
        self.view.cb_dept.setCurrentText(self.current_preferences.jacmar.departement)
        self.view.cb_titre.setCurrentText(self.current_preferences.jacmar.titre)
        self.view.cb_super.setCurrentText(self.current_preferences.jacmar.superviseur)
        
        # Mettre à jour ComboBox Plafond avec la CLÉ (string) sauvegardée
        plafond_key = self.current_preferences.jacmar.plafond # Peut être int ou str après chargement
        # --- Assurer que c'est une string pour findText --- 
        index = self.view.cb_plafond.findText(str(plafond_key), Qt.MatchFixedString)
        if index >= 0:
            self.view.cb_plafond.setCurrentIndex(index)
        else:
            # Si la clé sauvegardée n'existe plus dans la config, sélectionner le premier item?
            print(f"Avertissement: Clé de plafond sauvegardée \'{plafond_key}\' non trouvée...")
            if self.view.cb_plafond.count() > 0:
                self.view.cb_plafond.setCurrentIndex(0)

        # Section Application
        self.view.cb_theme.setCurrentText(self.current_preferences.application.theme)
        self.view.toggle_auto_update.setChecked(self.current_preferences.application.auto_update)
        self.view.toggle_show_notes.setChecked(self.current_preferences.application.show_note)

        print("Préférences Contrôleur: Vue mise à jour depuis les préférences COURANTES.")

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
                print(f"Erreur: Impossible de charger l'image depuis {file_path}")
                self.view.update_signature_preview(None, "Erreur")
                self._selected_signature_path = "" # Réinitialiser en cas d'erreur
            else:
                print(f"Image sélectionnée par contrôleur: {file_path}")
                self.view.update_signature_preview(pixmap)
                self._selected_signature_path = file_path # Mémoriser le chemin choisi
            
            # --- Vérifier la modification après sélection --- 
            self._check_field_modification(self.view.signature_display_widget, "profile.signature_path")
        # Si annulé, ne rien faire, la vérification n'est pas nécessaire

    @pyqtSlot()
    def export_preferences(self):
        """ Ouvre une boîte de dialogue pour choisir où exporter les préférences actuelles (état courant de l'UI)."""
        print("Préférences Contrôleur: Exportation demandée...")
        options = QFileDialog.Options()
        # Suggérer un nom de fichier par défaut
        suggested_filename = "preference.json"
        file_path, _ = QFileDialog.getSaveFileName(self.view, 
                                                   "Exporter les préférences sous...", 
                                                   suggested_filename, # Fichier suggéré
                                                   "Fichiers JSON (*.json);;Tous les fichiers (*)", 
                                                   options=options)
        
        if not file_path:
            print("Exportation annulée par l'utilisateur.")
            return
            
        # S'assurer que l'extension .json est présente si l'utilisateur ne l'a pas mise
        if not file_path.lower().endswith('.json'):
            file_path += '.json'
            
        print(f"Tentative d'exportation vers: {file_path}")
        try:
            # Sauvegarder l'état COURANT (celui affiché, potentiellement modifié/importé)
            # dans le fichier choisi par l'utilisateur.
            # Note: Cela NE met PAS à jour self.saved_preferences ni ne sauvegarde dans data/preference.json
            self.current_preferences.save(filepath=file_path)
            QMessageBox.information(self.view,
                                    "Exportation réussie",
                                    f"Les préférences actuelles ont été exportées avec succès vers:\n{file_path}")
        except Exception as e:
            print(f"Erreur lors de l'exportation vers {file_path}: {e}")
            QMessageBox.critical(self.view,
                                 "Erreur d'exportation",
                                 f"Une erreur est survenue lors de l'exportation des préférences:\n{e}")

    @pyqtSlot()
    def import_preferences(self):
        """ Ouvre une boîte de dialogue pour importer un fichier JSON de préférences,
            valide sa structure, met à jour l'objet courant et la vue (sans sauvegarder). """
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self.view,
                                                  "Importer un fichier de préférences",
                                                  "", # Pas de chemin par défaut spécifique ici
                                                  "Fichiers JSON (*.json);;Tous les fichiers (*)",
                                                  options=options)
        
        if not file_path:
            print("Importation annulée par l'utilisateur.")
            return
        
        print(f"Tentative d'importation depuis: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                
            # Validation de la structure de base
            if not isinstance(loaded_data, dict) or \
               'profile' not in loaded_data or \
               'jacmar' not in loaded_data or \
               'application' not in loaded_data or \
               not isinstance(loaded_data['profile'], dict) or \
               not isinstance(loaded_data['jacmar'], dict) or \
               not isinstance(loaded_data['application'], dict):
                raise ValueError("Le fichier JSON n'a pas la structure attendue (manque profile/jacmar/application).")
                
            # Mettre à jour l'objet courant en mémoire
            self.current_preferences.profile.update_from_dict(loaded_data['profile'])
            self.current_preferences.jacmar.update_from_dict(loaded_data['jacmar'])
            self.current_preferences.application.update_from_dict(loaded_data['application'])
            
            # Mettre à jour spécialement le chemin de signature mémorisé
            self._selected_signature_path = self.current_preferences.profile.signature_path
            
            # Mettre à jour l'interface utilisateur
            self._update_view_from_prefs()
            
            # --- Relancer la comparaison pour afficher les boutons refresh --- 
            self._check_all_fields_initial()
            
            print(f"Préférences importées (non sauvegardées) depuis {file_path}.")
            QMessageBox.information(self.view, "Importation réussie", "Préférences chargées. Sauvegardez pour conserver.")
            
        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON dans {file_path}: {e}")
            QMessageBox.warning(self.view, "Erreur d'importation", f"Le fichier sélectionné n'est pas un JSON valide:\n{e}")
        except FileNotFoundError:
            print(f"Erreur: Fichier non trouvé {file_path}")
            QMessageBox.warning(self.view, "Erreur d'importation", "Le fichier sélectionné n'a pas pu être trouvé.")
        except ValueError as e:
            print(f"Erreur de structure dans {file_path}: {e}")
            QMessageBox.warning(self.view, "Erreur d'importation", f"La structure du fichier JSON est incorrecte:\n{e}")
        except Exception as e:
            print(f"Erreur inattendue lors de l'importation depuis {file_path}: {e}")
            QMessageBox.critical(self.view, "Erreur d'importation", f"Une erreur inattendue est survenue:\n{e}")

    @pyqtSlot()
    def save_preferences(self):
        """ Met à jour l'objet Preference depuis la vue et appelle sa méthode save. """
        print("Préférences Contrôleur: Sauvegarde demandée...")
        try:
            # Mettre à jour l'objet Profile
            self.current_preferences.profile.nom = self.view.le_nom.text()
            self.current_preferences.profile.prenom = self.view.le_prenom.text()
            self.current_preferences.profile.telephone = self.view.le_tel.text()
            self.current_preferences.profile.courriel = self.view.le_courriel.text()
            self.current_preferences.profile.signature_path = self._selected_signature_path

            # Mettre à jour l'objet Jacmar
            self.current_preferences.jacmar.emplacement = self.view.cb_emplacement.currentText()
            self.current_preferences.jacmar.departement = self.view.cb_dept.currentText()
            self.current_preferences.jacmar.titre = self.view.cb_titre.currentText()
            self.current_preferences.jacmar.superviseur = self.view.cb_super.currentText()
            self.current_preferences.jacmar.plafond = self.view.cb_plafond.currentText()

            # --- Mettre à jour l'objet Application (Y COMPRIS LE THÈME MAINTENANT) --- 
            # Vérifier si le ComboBox existe avant de lire sa valeur
            if hasattr(self.view, 'cb_theme'):
                self.current_preferences.application.theme = self.view.cb_theme.currentText() 
            else:
                 print("Warning: cb_theme not found during save_preferences.")
            self.current_preferences.application.auto_update = self.view.toggle_auto_update.isChecked()
            self.current_preferences.application.show_note = self.view.toggle_show_notes.isChecked()
            # ----------------------------------------------------------------------

            # Appeler la méthode save du modèle (sauvegarde TOUT l'objet current)
            self.current_preferences.save()
            
            # Mettre à jour self.saved_preferences pour refléter le nouvel état sauvegardé
            saved_data = self.current_preferences.to_dict()
            self.saved_preferences.profile.update_from_dict(saved_data["profile"])
            self.saved_preferences.jacmar.update_from_dict(saved_data["jacmar"])
            self.saved_preferences.application.update_from_dict(saved_data["application"])
            
            self._check_all_fields_initial() # Remettre opacité boutons refresh à 0
            QMessageBox.information(self.view, "Sauvegarde", "Préférences sauvegardées.")

        except Exception as e:
            print(f"Erreur lors de la mise à jour ou sauvegarde des préférences: {e}")
            QMessageBox.warning(self.view, "Erreur", f"Impossible de sauvegarder les préférences: {e}")

    # --- SLOT POUR LE CHANGEMENT DE THÈME --- 
    @pyqtSlot(str)
    def _on_theme_changed(self, theme_text):
        """Slot appelé lorsque le ComboBox du thème change.
           Applique UNIQUEMENT le thème VISUELLEMENT.
           La mise à jour de la valeur et la sauvegarde se font via save_preferences.
        """
        print(f"Theme ComboBox changed to: {theme_text} - Applying visual change only.")
        # Déterminer la valeur à appliquer visuellement
        theme_to_apply = 'Sombre' # Défaut
        if theme_text == "Clair":
            theme_to_apply = 'Clair'
        elif theme_text == "Sombre":
            theme_to_apply = 'Sombre'
        # else: # Pas besoin de warning ici, on applique juste le défaut

        # --- SUPPRESSION de la mise à jour de self.current_preferences --- 
        # try:
        #     self.current_preferences.application.theme = new_theme_value
        #     print(f"Current preference theme updated in memory to: {new_theme_value}")
        # except AttributeError:
        #      print("ERROR: Could not set current_preferences.application.theme")
        #      return
        # ----------------------------------------------------------------

        # --- Laisser la vérification du bouton reset (basée sur widget vs saved) ---
        # Cette partie est maintenant gérée par _check_field_modification connecté
        # via _connect_modification_signals, donc on peut la commenter ici aussi
        # pour éviter double appel.
        # if hasattr(self.view, 'cb_theme'):
        #     self._check_field_modification(self.view.cb_theme, "application.theme")
        # --------------------------------------------------------------------------

        # --- Recharger et appliquer le style globalement (immédiatement) --- 
        if self.main_controller and hasattr(self.main_controller, 'apply_theme'):
            print(f"Calling main_controller.apply_theme('{theme_to_apply}')...")
            self.main_controller.apply_theme(theme_to_apply)
        else:
            # Fallback: appliquer QSS et mettre à jour icônes manuellement ici
            print("Warning: MainController not available or missing 'apply_theme' method. Applying style and setting icon theme directly.")
            style_applied_directly = False
            try:
                qss_files = ["resources/styles/global.qss", "resources/styles/frame.qss"]
                combined_stylesheet = load_stylesheet(qss_files, theme_name=theme_to_apply)
                app_instance = QApplication.instance()
                if app_instance:
                    app_instance.setStyleSheet(combined_stylesheet)
                    print("Global stylesheet reapplied directly.")
                    style_applied_directly = True
                else:
                    print("Error: QApplication.instance() returned None.")
            except Exception as e_apply:
                 print(f"Error reapplying stylesheet directly: {e_apply}")
            
            # --- Mettre à jour le thème icône ici aussi dans le fallback ---
            try:
                 icon_loader.set_active_theme(theme_to_apply)
            except Exception as e_icon_fallback:
                 print(f"Error setting icon theme in fallback: {e_icon_fallback}")
            # --------------------------------------------------------------

        # --- Pas de sauvegarde ici --- 

print("PreferencesController (dans controllers/preferences/) defined") # Debug 