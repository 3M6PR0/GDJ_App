from PyQt5.QtCore import QObject, pyqtSlot, Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QLineEdit, QComboBox # Ajouter QMessageBox pour feedback
from PyQt5.QtGui import QPixmap # Import correct pour QPixmap
import json # Assurer que json est importé
import functools # Ajouter functools

# Importer le modèle Preference
from models.preference import Preference
from pages.preferences.preferences_page import SimpleToggle # Assurer l'import de SimpleToggle

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

        # Connecter les signaux standard (save/import/export/signature)
        self._connect_standard_signals()
        # Connecter les signaux pour la détection de modification et la réinitialisation
        self._connect_modification_signals()

        # Mettre à jour la vue avec l'état COURANT
        self._update_view_from_prefs() 
        # Comparer l'état courant initial avec l'état SAUVEGARDE
        self._check_all_fields_initial()

    def _connect_standard_signals(self):
        """Connecte les signaux généraux de la vue."""
        self.view.select_signature_requested.connect(self.select_signature_image)
        self.view.export_prefs_requested.connect(self.export_preferences)
        self.view.import_prefs_requested.connect(self.import_preferences)
        self.view.save_prefs_requested.connect(self.save_preferences)
        
    def _connect_modification_signals(self):
        """Connecte les signaux de changement des widgets d'entrée et les clics des boutons refresh."""
        for pref_path in self.view.get_all_pref_paths():
            input_widget = self.view.get_input_widget(pref_path)
            refresh_button = self.view.get_refresh_button(pref_path)

            if input_widget and refresh_button:
                # Connecter le signal de modification du widget d'entrée
                signal = None
                if isinstance(input_widget, QLineEdit):
                    signal = input_widget.textChanged
                elif isinstance(input_widget, QComboBox):
                    # Utiliser currentTextChanged pour gérer aussi la saisie
                    signal = input_widget.currentTextChanged 
                elif isinstance(input_widget, SimpleToggle):
                    signal = input_widget.toggled
                
                if signal:
                    # Utiliser functools.partial pour passer le widget au slot
                    slot_check = functools.partial(self._check_field_modification, input_widget, pref_path)
                    signal.connect(slot_check)
                
                # Connecter le clic du bouton refresh
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
        """Compare la valeur actuelle du widget avec la valeur SAUVEGARDEE.
           Affiche/cache le bouton refresh.
        """
        refresh_button = self.view.get_refresh_button(pref_path)
        if not refresh_button:
            return
        
        saved_value = _get_nested_attr(self.saved_preferences, pref_path)
        current_value = None
        
        # Obtenir la valeur actuelle et la convertir au type attendu pour comparaison
        try:
            if isinstance(input_widget, QLineEdit):
                current_value = input_widget.text()
            elif isinstance(input_widget, QComboBox):
                current_value = input_widget.currentText()
                # Comparaison spécifique pour plafond (int vs str)
                if pref_path == 'jacmar.plafond':
                    saved_value = str(saved_value) # Comparer comme chaînes
            elif isinstance(input_widget, SimpleToggle):
                current_value = input_widget.isChecked()
            else:
                # Type de widget non géré
                refresh_button.setVisible(False)
                return 
        except Exception as e:
            print(f"Erreur lecture valeur widget {pref_path}: {e}")
            refresh_button.setVisible(False) # Cacher en cas d'erreur
            return

        # Comparer les valeurs
        is_different = (current_value != saved_value)
        # print(f"Check {pref_path}: Current='{current_value}' ({type(current_value)}), Saved='{saved_value}' ({type(saved_value)}), Different={is_different}")
        refresh_button.setVisible(is_different)

    def _revert_field_value(self, input_widget, pref_path):
        """Réinitialise la valeur du widget à la valeur SAUVEGARDEE."""
        print(f"Réinitialisation du champ: {pref_path}")
        saved_value = _get_nested_attr(self.saved_preferences, pref_path)
        
        try:
            if isinstance(input_widget, QLineEdit):
                input_widget.setText(str(saved_value))
            elif isinstance(input_widget, QComboBox):
                # Trouver l'index correspondant au texte sauvegardé
                index = input_widget.findText(str(saved_value), Qt.MatchFixedString)
                if index >= 0:
                    input_widget.setCurrentIndex(index)
                else:
                    # Si la valeur sauvegardée n'est plus dans la liste, on ne fait rien ou on met une valeur par défaut
                    print(f"Avertissement: Impossible de trouver '{saved_value}' dans {pref_path} QComboBox.")
                    # input_widget.setCurrentIndex(0) # Optionnel: revenir au premier élément
            elif isinstance(input_widget, SimpleToggle):
                input_widget.setChecked(bool(saved_value))
            
            # Après réinitialisation, la valeur correspond, donc on cache le bouton
            # (peut être redondant si le signal de modification est bien émis, mais plus sûr)
            refresh_button = self.view.get_refresh_button(pref_path)
            if refresh_button:
                refresh_button.setVisible(False)
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
        # Attention: Plafond est un int dans le modèle, mais texte dans QComboBox. Conversion nécessaire.
        # Pour l'instant, on suppose une correspondance texte simple. À adapter si besoin.
        self.view.cb_plafond.setCurrentText(str(self.current_preferences.jacmar.plafond)) 

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
        # Si aucun fichier n'est choisi, _selected_signature_path garde sa valeur précédente

    @pyqtSlot()
    def export_preferences(self):
        """ Logique pour exporter les préférences (placeholder). """
        print("Préférences Contrôleur: Exportation demandée...")
        # Logique future: ouvrir QFileDialog.getSaveFileName, sérialiser les prefs, écrire fichier

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
            # Conversion pour plafond - Simpliste, suppose que le texte est un int valide
            try:
                plafond_text = self.view.cb_plafond.currentText()
                # Gérer les cas non numériques si nécessaire (ex: "Aucun" -> 0)
                if plafond_text.isdigit():
                    self.current_preferences.jacmar.plafond = int(plafond_text)
                else:
                    # Logique par défaut ou gestion d'erreur si le texte n'est pas un chiffre
                    self.current_preferences.jacmar.plafond = 0 # Exemple simple
                    print(f"Avertissement: Plafond non numérique '{plafond_text}', mis à 0.")
            except ValueError:
                self.current_preferences.jacmar.plafond = 0 # Fallback
                print(f"Erreur de conversion du plafond '{plafond_text}', mis à 0.")

            # Mettre à jour l'objet Application
            self.current_preferences.application.theme = self.view.cb_theme.currentText()
            self.current_preferences.application.auto_update = self.view.toggle_auto_update.isChecked()
            self.current_preferences.application.show_note = self.view.toggle_show_notes.isChecked()

            # Appeler la méthode save du modèle
            self.current_preferences.save() # Utilise le chemin par défaut "data/preference.json"
            
            # --- Mettre à jour self.saved_preferences pour refléter le nouvel état sauvegardé --- 
            saved_data = self.current_preferences.to_dict()
            self.saved_preferences.profile.update_from_dict(saved_data["profile"])
            self.saved_preferences.jacmar.update_from_dict(saved_data["jacmar"])
            self.saved_preferences.application.update_from_dict(saved_data["application"])
            
            # Cacher tous les boutons refresh car état courant == état sauvegardé
            self._check_all_fields_initial() 
            QMessageBox.information(self.view, "Sauvegarde", "Préférences sauvegardées avec succès.")

        except Exception as e:
            print(f"Erreur lors de la mise à jour ou sauvegarde des préférences: {e}")
            QMessageBox.warning(self.view, "Erreur", f"Impossible de sauvegarder les préférences: {e}")

    # --- Slots optionnels pour réaction immédiate aux toggles ---
    # @pyqtSlot(bool)
    # def on_auto_update_toggled(self, checked):
    #     print(f"Préférences Contrôleur: MàJ auto réglé sur {checked}")

    # @pyqtSlot(bool)
    # def on_show_notes_toggled(self, checked):
    #     print(f"Préférences Contrôleur: Affichage notes réglé sur {checked}")

print("PreferencesController (dans controllers/preferences/) defined") # Debug 