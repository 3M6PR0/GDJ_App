# updater/downloader.py
import requests
import time
import os
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import logging

# Initialisation du logger
logger = logging.getLogger('GDJ_App')

class DownloadWorker(QObject):
    progress = pyqtSignal(int, int, float) # current_bytes, total_bytes, speed_mbps
    finished = pyqtSignal(bool, str) # success, downloaded_path_or_error
    error = pyqtSignal(str)
    
    _is_cancelled = False

    def __init__(self, url, dest_folder):
        super().__init__()
        self.url = url
        self.dest_folder = dest_folder
        self._is_cancelled = False

    @pyqtSlot()
    def run(self):
        """Exécute le téléchargement."""
        self._is_cancelled = False
        downloaded_path = ""
        try:
            logger.info(f"Starting download from: {self.url}")
            response = requests.get(self.url, stream=True, timeout=20)
            response.raise_for_status() # Lève une exception pour les codes 4xx/5xx

            total_size = int(response.headers.get('content-length', 0))
            filename = self.url.split('/')[-1] # Essayer d'obtenir un nom de fichier
            if not filename:
                 filename = "downloaded_installer.exe" # Nom par défaut
            downloaded_path = os.path.join(self.dest_folder, filename)
            
            # S'assurer que le dossier de destination existe
            os.makedirs(self.dest_folder, exist_ok=True)

            logger.info(f"Saving to: {downloaded_path}")
            logger.info(f"Total size: {total_size} bytes")
            
            downloaded_size = 0
            start_time = time.time()
            last_update_time = start_time
            chunk_size = 8192 # 8KB
            
            with open(downloaded_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self._is_cancelled:
                        logger.info("Download cancelled by user.")
                        # Supprimer le fichier partiellement téléchargé
                        if os.path.exists(downloaded_path):
                           try:
                               os.remove(downloaded_path)
                               logger.info(f"Removed partially downloaded file: {downloaded_path}")
                           except OSError as e:
                               logger.error(f"Error removing partial file {downloaded_path}: {e}")
                        self.error.emit("Téléchargement annulé.")
                        self.finished.emit(False, "Annulé")
                        return # Sortir de la boucle et de la fonction
                        
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Calculer la vitesse et émettre la progression
                        current_time = time.time()
                        # Mettre à jour la vitesse et la progression toutes les 0.5 secondes
                        if current_time - last_update_time >= 0.5:
                             elapsed_time_total = current_time - start_time
                             speed_bps = downloaded_size / elapsed_time_total if elapsed_time_total > 0 else 0
                             speed_mbps = (speed_bps * 8) / (1024 * 1024) # Megabits per second
                             self.progress.emit(downloaded_size, total_size, speed_mbps)
                             last_update_time = current_time
            
            # Émettre une dernière fois la progression complète
            final_speed = (downloaded_size / (time.time() - start_time) * 8) / (1024*1024) if (time.time() - start_time) > 0 else 0
            self.progress.emit(downloaded_size, total_size, final_speed)
            
            if not self._is_cancelled:
                logger.info("Download finished successfully.")
                self.finished.emit(True, downloaded_path)

        except requests.exceptions.RequestException as e:
            logger.error(f"Download error: {e}")
            self.error.emit(f"Erreur réseau : {e}")
            self.finished.emit(False, str(e))
        except Exception as e:
            logger.error(f"Unexpected download error: {e}")
            self.error.emit(f"Erreur inattendue : {e}")
            self.finished.emit(False, str(e))

    @pyqtSlot()
    def cancel(self):
         """Slot pour demander l'annulation du téléchargement."""
         logger.info("Cancel requested for download worker.")
         self._is_cancelled = True

# Note: Ce worker est conçu pour être déplacé dans un QThread.
# L'appelant devra créer un QThread, créer une instance de DownloadWorker,
# déplacer le worker vers le thread avec worker.moveToThread(thread),
# connecter les signaux du worker aux slots de l'UI,
# connecter thread.started au slot worker.run,
# connecter worker.finished à thread.quit,
# et enfin appeler thread.start(). 