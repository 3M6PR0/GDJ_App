# controllers/settings/settings_controller.py
from PyQt5.QtCore import QObject, pyqtSlot as Slot, QThread
from PyQt5.QtWidgets import QApplication
import sys
import subprocess
import os
from config import CONFIG

# Importer la vue et potentiellement le main_controller et update_checker
from pages.settings.settings_page import SettingsPage
# from controllers.main_controller import MainController # Décommenter si besoin
from updater.update_checker import check_for_updates, prompt_update 
# Importer le worker de téléchargement
from updater.downloader import DownloadWorker 

class SettingsController(QObject):
    def __init__(self, view: SettingsPage, main_controller):
        super().__init__(view)
        self.view = view
        self.main_controller = main_controller
        # --- Stocker les infos de la dernière MàJ vérifiée --- 
        self.last_update_info = {"available": False, "version": None, "url": None}
        # --- Références pour le thread de téléchargement --- 
        self.download_thread = None
        self.download_worker = None

        self._connect_signals()
        self._update_initial_view()
        
        print("SettingsController initialized")

    def _connect_signals(self):
        """Connecte les signaux aux slots. Gère la reconnexion si nécessaire."""
        # Déconnecter d'abord pour éviter connexions multiples si appelé plusieurs fois
        try:
            self.view.btn_check_updates.clicked.disconnect()
        except TypeError: # Signal n'avait pas de connexion
            pass
        # Connecter au slot de vérification par défaut
        self.view.btn_check_updates.clicked.connect(self._check_for_updates_manually)
        # Connecter le bouton Annuler
        try:
            self.view.btn_cancel_update.clicked.disconnect()
        except TypeError: 
            pass
        self.view.btn_cancel_update.clicked.connect(self._cancel_download)
        print("SettingsController: Signals connected/reconnected")

    def _update_initial_view(self):
        """Met à jour les widgets de la vue avec les données initiales."""
        try:
            # Afficher la version actuelle
            current_version = self.main_controller.current_version_str
            self.view.lbl_current_version.setText(f"Version actuelle : {current_version}")
            
            self._set_idle_state() # Assurer l'état initial
        except Exception as e:
            print(f"Error updating initial settings view: {e}")
            self.view.lbl_current_version.setText("Version actuelle : Erreur")
            self.view.lbl_update_status.setText("Statut : Erreur")

    def _set_idle_state(self):
        """Configure l'UI pour l'état 'Prêt à vérifier'."""
        self.view.lbl_update_status.setText("Statut : Prêt") 
        self.view.btn_check_updates.setText("Vérifier les mises à jour")
        self.view.btn_check_updates.setEnabled(True)
        # S'assurer que les éléments de progression sont cachés
        self.view.progress_bar.setVisible(False)
        self.view.lbl_speed.setVisible(False)
        self.view.downloaded_details_widget.setVisible(False)
        self.view.remaining_details_widget.setVisible(False)
        self.view.btn_cancel_update.setVisible(False)
        self.view.progress_bar.setValue(0) # Réinitialiser la barre
        
        # (Re)connecter au slot de vérification
        self._connect_signals() 

    def _set_update_available_state(self, version, url):
        """Configure l'UI pour l'état 'Mise à jour disponible'."""
        self.view.lbl_update_status.setText(f"Statut : Mise à jour trouvée : {version}")
        self.view.btn_check_updates.setText("Mettre à jour")
        self.view.btn_check_updates.setEnabled(True)
        
        # Déconnecter l'ancien slot et connecter le nouveau
        try:
            self.view.btn_check_updates.clicked.disconnect()
        except TypeError: 
            pass
        self.view.btn_check_updates.clicked.connect(self._perform_update) 
        print("SettingsController: Button reconnected to _perform_update")

    def _set_downloading_state(self):
        """Configure l'UI pour l'état 'Téléchargement en cours'."""
        print("Setting UI to downloading state...")
        self.view.lbl_current_version.setVisible(False)
        self.view.lbl_update_status.setText("Statut : Téléchargement...") # ou vide
        self.view.btn_check_updates.setVisible(False) # Cacher "Vérifier/Mettre à jour"
        
        self.view.progress_bar.setVisible(True)
        self.view.progress_bar.setValue(0)
        self.view.lbl_speed.setVisible(True)
        self.view.lbl_speed.setText("Vitesse : 0.00 MB/s")
        self.view.downloaded_details_widget.setVisible(True)
        self.view.lbl_downloaded_value.setText("0 / 0 MB")
        self.view.remaining_details_widget.setVisible(True)
        self.view.lbl_remaining_value.setText("Calcul...")
        self.view.btn_cancel_update.setVisible(True)
        self.view.btn_cancel_update.setEnabled(True)

    @Slot()
    def _check_for_updates_manually(self):
        """Vérifie les MaJ et met à jour l'UI en fonction du résultat."""
        print("Manual update check requested...")
        self.view.lbl_update_status.setText("Statut : Vérification en cours...")
        QApplication.processEvents()
        self.view.btn_check_updates.setEnabled(False) 
        
        status_msg = "Erreur inconnue"
        update_info = {"available": False, "version": None, "url": None}
        try:
            # Appeler la fonction et récupérer les deux valeurs de retour
            status_msg, update_info = check_for_updates(manual_check=True)
            print(f"Update check finished. Result msg: '{status_msg}', Info: {update_info}")
            
            # Stocker les infos pour le bouton "Mettre à jour"
            self.last_update_info = update_info 
            
            # Mettre à jour le label de statut
            self.view.lbl_update_status.setText(f"Statut : {status_msg}")

            # Changer l'état du bouton si une mise à jour est disponible ET a une URL
            if update_info["available"] and update_info["url"]:
                self._set_update_available_state(update_info["version"], update_info["url"])
            else:
                # Remettre à l'état idle (texte bouton, connexion slot)
                self._set_idle_state()
                self.view.lbl_update_status.setText(f"Statut : {status_msg}") # Réappliquer le msg après idle state
                self.view.btn_check_updates.setEnabled(True) # Assurer réactivation

        except Exception as e:
            print(f"Error calling check_for_updates function: {e}")
            self.view.lbl_update_status.setText(f"Statut : Erreur critique ({e})")
            self._set_idle_state() # Remettre à l'état idle en cas d'erreur
        # finally:
            # La réactivation est maintenant gérée dans les états
            # self.view.btn_check_updates.setEnabled(True) 

    # --- NOUVEAU SLOT --- 
    @Slot()
    def _perform_update(self):
        """Lance le téléchargement de la mise à jour."""
        print("Update button clicked. Initiating download...")
        if self.last_update_info["available"] and self.last_update_info["url"]:
            installer_url = self.last_update_info["url"]
            
            # Passer à l'état téléchargement
            self._set_downloading_state()
            
            # Définir le dossier de destination (ex: dossier temporaire de l'OS)
            # Attention: Il faut pouvoir retrouver ce chemin après téléchargement
            # Peut-être un sous-dossier dans AppData/Local/GDJ/temp ?
            temp_dir = os.path.join(os.getenv('LOCALAPPDATA', '.'), CONFIG.get('APP_NAME', 'GDJ'), 'temp_updates')
            os.makedirs(temp_dir, exist_ok=True)
            print(f"Download destination folder: {temp_dir}")

            # Créer et démarrer le thread de téléchargement
            self.download_thread = QThread(self) # parent=self pour cleanup
            self.download_worker = DownloadWorker(installer_url, temp_dir)
            self.download_worker.moveToThread(self.download_thread)

            # Connecter les signaux du worker aux slots du contrôleur
            self.download_worker.progress.connect(self._update_download_progress)
            self.download_worker.finished.connect(self._download_finished)
            self.download_worker.error.connect(self._download_error)

            # Connecter le démarrage du thread à l'exécution du worker
            self.download_thread.started.connect(self.download_worker.run)
            # Connecter la fin du worker à l'arrêt du thread
            self.download_worker.finished.connect(self.download_thread.quit)
            # Optionnel: Nettoyer les ressources quand le thread finit
            self.download_thread.finished.connect(self.download_thread.deleteLater)
            self.download_worker.finished.connect(self.download_worker.deleteLater)

            print("Starting download thread...")
            self.download_thread.start()

        else:
             print("ERROR: _perform_update called but no valid update info available.")
             self._set_idle_state()

    # --- Slots pour les signaux du downloader ---
    @Slot(int, int, float)
    def _update_download_progress(self, current_bytes, total_bytes, speed_mbps):
        self.view.progress_bar.setRange(0, total_bytes if total_bytes > 0 else 100) # Éviter division par zéro
        self.view.progress_bar.setValue(current_bytes)
        self.view.lbl_speed.setText(f"Vitesse : {speed_mbps:.2f} MB/s")
        
        # Afficher en MB ou GB
        if total_bytes > 1024*1024*1024: # Go
            current_gb = current_bytes / (1024**3)
            total_gb = total_bytes / (1024**3)
            self.view.lbl_downloaded_value.setText(f"{current_gb:.1f} / {total_gb:.1f} GB")
        elif total_bytes > 0:
            current_mb = current_bytes / (1024**2)
            total_mb = total_bytes / (1024**2)
            self.view.lbl_downloaded_value.setText(f"{current_mb:.1f} / {total_mb:.1f} MB")
        else:
            current_mb = current_bytes / (1024**2)
            self.view.lbl_downloaded_value.setText(f"{current_mb:.1f} MB / ?")
        
        # Calcul simple du temps restant (peut être amélioré)
        if speed_mbps > 0.01 and total_bytes > 0:
            remaining_bytes = total_bytes - current_bytes
            remaining_seconds = remaining_bytes / ((speed_mbps * 1024 * 1024) / 8)
            if remaining_seconds < 60:
                 self.view.lbl_remaining_value.setText(f"{remaining_seconds:.0f} sec restantes")
            else:
                 remaining_minutes = remaining_seconds / 60
                 self.view.lbl_remaining_value.setText(f"{remaining_minutes:.1f} min restantes")
        elif total_bytes == 0:
            self.view.lbl_remaining_value.setText("Taille inconnue")
        else:
            self.view.lbl_remaining_value.setText("Calcul...")

    @Slot(bool, str)
    def _download_finished(self, success, path_or_error):
        print(f"Download finished signal received. Success: {success}, Path/Error: {path_or_error}")
        self.download_thread = None # Réinitialiser
        self.download_worker = None
        if success:
            self.view.lbl_update_status.setText("Statut : Téléchargement terminé. Lancement...")
            QApplication.processEvents()
            self._launch_installer_and_exit(path_or_error)
        else:
            # Afficher l'erreur (path_or_error contient le message d'erreur ici)
            if path_or_error != "Annulé": # Ne pas réafficher si déjà annulé
                 self.view.lbl_update_status.setText(f"Statut : Échec téléchargement ({path_or_error})")
            self._set_idle_state() # Revenir à l'état initial

    @Slot(str)
    def _download_error(self, message):
         # Ce slot est un peu redondant avec finished(False, error_msg)
         # mais on le garde pour l'instant.
        print(f"Download error signal received: {message}")
        if self.download_thread: # S'assurer qu'on n'est pas déjà revenu à idle
            self.view.lbl_update_status.setText(f"Statut : Erreur ({message})")
            self._set_idle_state()
            self.download_thread = None 
            self.download_worker = None

    @Slot()
    def _cancel_download(self):
        """Slot appelé par le bouton ARRÊTER."""
        print("Cancel button clicked.")
        if self.download_worker:
             print("  Signalling download worker to cancel...")
             self.download_worker.cancel() # Appelle le slot cancel du worker
             # --- Réinitialiser l'UI en fonction de l'état PRÉCÉDENT --- 
             print("  Resetting UI based on previous update status...")
             if self.last_update_info["available"] and self.last_update_info["url"]:
                 print("  Restoring to 'update available' state.")
                 self._set_update_available_state(self.last_update_info["version"], self.last_update_info["url"])
                 # --- S'assurer que les éléments de progression sont cachés --- 
                 self.view.progress_bar.setVisible(False)
                 self.view.lbl_speed.setVisible(False)
                 self.view.downloaded_details_widget.setVisible(False)
                 self.view.remaining_details_widget.setVisible(False)
                 self.view.btn_cancel_update.setVisible(False)
                 # --- Réafficher le bouton 'Mettre à jour' --- 
                 self.view.btn_check_updates.setVisible(True)
                 self.view.lbl_current_version.setVisible(True) # Réafficher la version
             else:
                 print("  Restoring to initial 'idle' state.")
                 self._set_idle_state()
             # On laisse le worker terminer son annulation en arrière-plan
        else:
             print("  No active download worker found to cancel.")
             # Restaurer l'état basé sur last_update_info aussi ici pour la cohérence
             if self.last_update_info["available"] and self.last_update_info["url"]:
                 self._set_update_available_state(self.last_update_info["version"], self.last_update_info["url"])
             else:
                 self._set_idle_state()

    def _launch_installer_and_exit(self, installer_path):
        """Lance l'installateur et quitte l'application."""
        try:
            print(f"Launching installer: {installer_path}")
            # Utiliser Popen pour ne pas attendre la fin de l'installateur
            subprocess.Popen([installer_path])
            print("Installer launched. Exiting application.")
            QApplication.instance().quit()
            # sys.exit(0) # Peut aussi fonctionner
        except FileNotFoundError:
             print(f"ERROR: Installer not found at {installer_path}")
             self.view.lbl_update_status.setText(f"Erreur : Installateur non trouvé ({os.path.basename(installer_path)})")
             self._set_idle_state()
        except Exception as e:
             print(f"Error launching installer: {e}")
             self.view.lbl_update_status.setText(f"Erreur lancement installeur: {e}")
             self._set_idle_state()

    # --- NOUVELLE MÉTHODE PUBLIQUE --- 
    def initiate_update_from_prompt(self, update_info):
        """Lance le téléchargement directement à partir des infos fournies."""
        print(f"Initiating update download directly with info: {update_info}")
        if update_info and update_info.get("available") and update_info.get("url"):
            # Stocker ces infos comme si on venait de les vérifier
            self.last_update_info = update_info
            installer_url = update_info["url"]
            
            # Passer à l'état téléchargement
            self._set_downloading_state()
            
            # Définir le dossier de destination (identique à _perform_update)
            temp_dir = os.path.join(os.getenv('LOCALAPPDATA', '.'), CONFIG.get('APP_NAME', 'GDJ'), 'temp_updates')
            os.makedirs(temp_dir, exist_ok=True)
            print(f"Download destination folder: {temp_dir}")

            # Créer et démarrer le thread de téléchargement (identique à _perform_update)
            # S'assurer qu'un téléchargement n'est pas déjà en cours (sécurité)
            if self.download_thread is not None:
                 print("Warning: Download thread already exists. Cancelling previous one?")
                 # Optionnel: Tenter d'annuler l'ancien avant de lancer le nouveau?
                 # Pour l'instant, on écrase les références, l'ancien thread pourrait continuer un peu
                 # S'il est géré correctement par Qt (parent=self), il sera détruit.
            
            self.download_thread = QThread(self) # parent=self pour cleanup
            self.download_worker = DownloadWorker(installer_url, temp_dir)
            self.download_worker.moveToThread(self.download_thread)

            # Connecter les signaux du worker
            self.download_worker.progress.connect(self._update_download_progress)
            self.download_worker.finished.connect(self._download_finished)
            self.download_worker.error.connect(self._download_error)

            # Connecter le démarrage/fin du thread
            self.download_thread.started.connect(self.download_worker.run)
            self.download_worker.finished.connect(self.download_thread.quit)
            self.download_thread.finished.connect(self.download_thread.deleteLater)
            self.download_worker.finished.connect(self.download_worker.deleteLater)

            print("Starting download thread from prompt...")
            self.download_thread.start()

        else:
             print("ERROR: initiate_update_from_prompt called with invalid update info.")
             # Revenir à l'état par défaut au cas où
             self._set_idle_state()

# Ajouter d'autres méthodes si nécessaire (ex: pour gérer des retours de check_for_updates) 