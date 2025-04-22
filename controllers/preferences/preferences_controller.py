from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QFileDialog # QPixmap est dans QtGui
from PyQt5.QtGui import QPixmap # Import correct pour QPixmap

# Importer le modèle Preference
from models.preference import Preference

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

        # Créer/Charger l'objet de préférences
        self.current_preferences = Preference() # Crée une nouvelle instance avec les valeurs par défaut
        # TODO: Implémenter le chargement depuis le fichier ici si nécessaire
        # self.current_preferences.load() # <--- Logique de chargement future

        # Stocker le chemin de la signature sélectionnée
        self._selected_signature_path = self.current_preferences.profile.signature_path

        # Connecter les signaux
        self._connect_signals()

        # Optionnel: Mettre à jour la vue avec les préférences chargées
        # self._update_view_from_prefs()

    def _connect_signals(self):
        """Connecte les signaux de la vue aux slots du contrôleur."""
        self.view.select_signature_requested.connect(self.select_signature_image)
        self.view.export_prefs_requested.connect(self.export_preferences)
        self.view.import_prefs_requested.connect(self.import_preferences)
        # Le signal save_prefs_requested est maintenant connecté à notre méthode actualisée
        self.view.save_prefs_requested.connect(self.save_preferences)

    def _update_view_from_prefs(self):
        """Met à jour les widgets de la vue avec les valeurs actuelles des préférences."""
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

        print("Préférences Contrôleur: Vue mise à jour depuis les préférences.")

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
        """ Logique pour importer les préférences (placeholder). """
        print("Préférences Contrôleur: Importation demandée...")
        # Logique future: ouvrir QFileDialog.getOpenFileName, lire fichier, désérialiser, appliquer

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
            
            # Optionnel: Afficher une confirmation à l'utilisateur
            # QMessageBox.information(self.view, "Sauvegarde", "Préférences sauvegardées avec succès.")

        except Exception as e:
            print(f"Erreur lors de la mise à jour ou sauvegarde des préférences: {e}")
            # Optionnel: Afficher un message d'erreur à l'utilisateur
            # QMessageBox.warning(self.view, "Erreur", f"Impossible de sauvegarder les préférences: {e}")

    # --- Slots optionnels pour réaction immédiate aux toggles ---
    # @pyqtSlot(bool)
    # def on_auto_update_toggled(self, checked):
    #     print(f"Préférences Contrôleur: MàJ auto réglé sur {checked}")

    # @pyqtSlot(bool)
    # def on_show_notes_toggled(self, checked):
    #     print(f"Préférences Contrôleur: Affichage notes réglé sur {checked}")

print("PreferencesController (dans controllers/preferences/) defined") # Debug 