from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QFileDialog # QPixmap est dans QtGui
from PyQt5.QtGui import QPixmap # Import correct pour QPixmap

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

        # Connecter les signaux des widgets de la vue aux slots de ce contrôleur
        self.view.select_signature_requested.connect(self.select_signature_image)
        self.view.export_prefs_requested.connect(self.export_preferences)
        self.view.import_prefs_requested.connect(self.import_preferences)
        self.view.save_prefs_requested.connect(self.save_preferences)
        # Connecter les toggles si besoin de logique immédiate (sinon lire l'état lors de la sauvegarde)
        # self.view.toggle_auto_update.toggled.connect(self.on_auto_update_toggled)
        # self.view.toggle_show_notes.toggled.connect(self.on_show_notes_toggled)

    @pyqtSlot()
    def select_signature_image(self):
        """ Ouvre une boîte de dialogue pour sélectionner une image et met à jour la vue. """
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self.view, # Parent est la vue
                                                  "Sélectionner une image de signature",
                                                  "",
                                                  "Images (*.png *.jpg *.jpeg *.bmp)",
                                                  options=options)
        
        if file_path:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                print(f"Erreur: Impossible de charger l'image depuis {file_path}")
                self.view.update_signature_preview(None, "Erreur")
                return
            
            print(f"Image sélectionnée par contrôleur: {file_path}")
            # Demander à la vue de mettre à jour l'aperçu
            self.view.update_signature_preview(pixmap)
            # Ici, on pourrait aussi sauvegarder le chemin dans un modèle/config

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
        """ Logique pour sauvegarder les préférences (placeholder). """
        print("Préférences Contrôleur: Sauvegarde demandée...")
        # Logique future: lire les valeurs des widgets de la vue, les sauvegarder (config, BDD...)
        # Exemple: theme = self.view.cb_theme.currentText()
        #          auto_update = self.view.toggle_auto_update.isChecked()
        #          ... etc

    # --- Slots optionnels pour réaction immédiate aux toggles ---
    # @pyqtSlot(bool)
    # def on_auto_update_toggled(self, checked):
    #     print(f"Préférences Contrôleur: MàJ auto réglé sur {checked}")

    # @pyqtSlot(bool)
    # def on_show_notes_toggled(self, checked):
    #     print(f"Préférences Contrôleur: Affichage notes réglé sur {checked}")

print("PreferencesController (dans controllers/preferences/) defined") # Debug 