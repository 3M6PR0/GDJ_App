# updater/update_helper.py

import sys
import os
import traceback # Pour logguer les exceptions complètes
import time
from math import pi, sin, cos

# --- Logging de démarrage TRES précoce --- START
log_dir = os.environ.get("TEMP", os.getcwd())
log_file_path = os.path.join(log_dir, "update_helper_startup_log.txt")
def log_message(message):
    try:
        with open(log_file_path, "a", encoding='utf-8') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        # Si même le logging échoue, on ne peut pas faire grand chose
        print(f"ERREUR LOGGING: {e}")

log_message("--- update_helper.exe DÉMARRÉ ---")
log_message(f"Arguments reçus: {sys.argv}")
log_message(f"PID: {os.getpid()}")
log_message(f"CWD: {os.getcwd()}")
log_message(f"sys.executable: {sys.executable}")
log_message("Tentative d'import des modules principaux...")
# --- Logging de démarrage TRES précoce --- END

try:
    import requests
    import subprocess
    import time
    from math import pi, sin, cos
    from collections import deque
    log_message("Imports standards OK.")

    # Importations PyQt5
    log_message("Tentative d'import PyQt5...")
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
        QSizePolicy, QFrame, QMessageBox, QGridLayout
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF, QPointF, QSize
    from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QFontDatabase
    log_message("Imports PyQt5 OK.")

    # --- Custom Circular Progress Bar Widget ---

    class CircularProgressBar(QWidget):
        def __init__(self, parent=None):
            log_message("[CircularProgressBar] Initialisation...")
            super().__init__(parent)
            self.value = 0
            self.min_value = 0
            self.max_value = 100
            self.suffix = '%'
            self.text = "TÉLÉCHARGEMENT"

            # Couleurs (Thème sombre basé sur l'image)
            self.background_color = QColor(30, 32, 34)
            self.progress_background_color = QColor(60, 63, 65)
            self.progress_color = QColor(0, 122, 204)
            self.text_color = QColor(220, 220, 220)
            self.percent_text_color = QColor(240, 240, 240)

            # Polices (Ajustement taille pourcentage)
            self.percent_font = QFont("Segoe UI", 26, QFont.Bold) # Réduit de 30 à 26
            self.text_font = QFont("Segoe UI", 8, QFont.Normal)

            self.setMinimumSize(150, 150)
            log_message("[CircularProgressBar] Initialisation terminée.")

        def setValue(self, value):
            self.value = max(self.min_value, min(value, self.max_value))
            self.update()

        def setText(self, text):
            self.text = text
            self.update()

        def paintEvent(self, event):
            width = self.width()
            height = self.height()
            side = min(width, height)

            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Rétablir une marge standard
            pen_width = 12
            margin = 10 # Remis à 10 (valeur raisonnable)
            rect = QRectF(margin, margin, side - 2 * margin, side - 2 * margin)

            # 1. Cercle de fond
            pen = QPen()
            pen.setColor(self.progress_background_color)
            pen.setWidth(pen_width)
            pen.setCapStyle(Qt.FlatCap)
            painter.setPen(pen)
            painter.drawArc(rect, 0, 360 * 16)

            # 2. Arc de progression
            pen.setColor(self.progress_color)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            span_angle = (self.value / (self.max_value - self.min_value)) * 360
            start_angle = 90 * 16
            painter.drawArc(rect, start_angle, -int(span_angle * 16))

            # 3. Texte (pourcentage)
            painter.setFont(self.percent_font)
            painter.setPen(self.percent_text_color)
            percent_text = f"{int(self.value)}{self.suffix}"
            percent_rect = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.75)
            painter.drawText(percent_rect, Qt.AlignCenter, percent_text)

            # 4. Sous-texte (status)
            painter.setFont(self.text_font)
            painter.setPen(self.text_color)
            text_rect = QRectF(rect.x(), rect.y() + rect.height() * 0.68, rect.width(), rect.height() * 0.2)
            painter.drawText(text_rect, Qt.AlignCenter, self.text)

            painter.end()


    # --- Worker Thread (Adapté pour les nouvelles infos) ---

    class Worker(QThread):
        progress = pyqtSignal(int)       # Pourcentage global (0-100)
        speedUpdate = pyqtSignal(float)  # Vitesse en octets/s
        sizeUpdate = pyqtSignal(int, int) # downloaded_bytes, total_bytes
        etaUpdate = pyqtSignal(str)      # Temps restant formaté (str)
        finished = pyqtSignal(bool, str) # Bool: succès/échec, Str: message/chemin

        def __init__(self, installer_url, output_path):
            log_message("[Worker] Initialisation...")
            super().__init__()
            self.installer_url = installer_url
            self.output_path = output_path
            self.is_running = True
            self.filename = os.path.basename(self.output_path)
            self.speed_buffer = deque(maxlen=10)
            self.last_time = 0
            self.last_downloaded = 0
            log_message("[Worker] Initialisation terminée.")

        def run(self):
            log_message("[Worker] Démarrage du thread.")
            print(f"Téléchargement depuis: {self.installer_url}")
            try:
                response = requests.get(self.installer_url, stream=True, timeout=60)
                response.raise_for_status()
                total_length_str = response.headers.get('content-length')

                if total_length_str is None:
                    self.handle_error("Impossible d'obtenir la taille du fichier.")
                    return

                total_length = int(total_length_str)
                self.sizeUpdate.emit(0, total_length) # Envoyer taille initiale

                with open(self.output_path, 'wb') as f:
                    dl = 0
                    chunk_size = 8192 * 4 # Chunk un peu plus gros
                    self.last_time = time.monotonic()
                    self.last_downloaded = 0
                    self.speed_buffer.clear()

                    for data in response.iter_content(chunk_size=chunk_size):
                        if not self.is_running:
                            self.speedUpdate.emit(0)
                            self.etaUpdate.emit("Annulé")
                            self.finished.emit(False, "Annulé par l'utilisateur")
                            log_message("[Worker] Annulation détectée.")
                            return

                        chunk_len = len(data)
                        dl += chunk_len
                        f.write(data)
                        done_percent = int(100 * dl / total_length)
                        self.progress.emit(done_percent)
                        self.sizeUpdate.emit(dl, total_length) # Mettre à jour taille téléchargée

                        # Calcul vitesse et ETA
                        current_time = time.monotonic()
                        time_diff = current_time - self.last_time
                        if time_diff >= 0.4: # Update un peu plus fréquent
                            bytes_diff = dl - self.last_downloaded
                            current_speed = bytes_diff / time_diff if time_diff > 0 else 0
                            self.speed_buffer.append(current_speed)
                            avg_speed = sum(self.speed_buffer) / len(self.speed_buffer) if self.speed_buffer else 0
                            self.speedUpdate.emit(avg_speed)

                            bytes_remaining = total_length - dl
                            eta_seconds = bytes_remaining / avg_speed if avg_speed > 0 else -1
                            self.etaUpdate.emit(self.format_eta(eta_seconds))

                            self.last_time = current_time
                            self.last_downloaded = dl

                # Fin du téléchargement
                self.speedUpdate.emit(0)
                self.etaUpdate.emit("Terminé")
                log_message("[Worker] Téléchargement terminé.")
                time.sleep(0.5)

                # Lancement
                if self.launch_installer():
                    log_message("[Worker] Installeur lancé avec succès.")
                    self.finished.emit(True, self.output_path)
                else:
                    log_message("[Worker] Échec lancement installeur.")
                    self.finished.emit(False, "Échec du lancement de l'installeur.")

            except requests.exceptions.Timeout: self.handle_error("Erreur réseau: Timeout")
            except requests.exceptions.RequestException as e: self.handle_error(f"Erreur réseau: {e}")
            except IOError as e: self.handle_error(f"Erreur disque: {e}")
            except Exception as e: self.handle_error(f"Erreur inattendue: {e}")
            log_message("[Worker] Fin du thread.")

        def handle_error(self, message):
            log_message(f"[Worker] Erreur: {message}")
            print(f"\nErreur: {message}")
            self.speedUpdate.emit(0)
            self.etaUpdate.emit("Erreur")
            self.finished.emit(False, message)

        def format_eta(self, seconds):
            if seconds < 0: return "Calcul..."
            if seconds < 60: return f"{int(seconds)} secondes restantes"
            if seconds < 3600: return f"{int(seconds // 60)} minutes restantes"
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes:02d}min restantes"

        def launch_installer(self):
            log_message("[Worker] Tentative de lancement installeur...")
            print(f"Lancement de l'installeur : {self.output_path}")
            try:
                subprocess.Popen([self.output_path])
                print("Installeur lancé.")
                return True
            except Exception as e:
                print(f"Erreur lancement installeur: {e}")
                log_message(f"[Worker] Erreur Popen: {e}")
                return False

        def stop(self):
            log_message("[Worker] Signal d'arrêt reçu.")
            self.is_running = False

    # --- Helper function to format size ---
    def format_bytes(size_bytes):
        """Convertit les octets en Ko, Mo ou Go avec une décimale."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024*1024:
            return f"{size_bytes/1024:.1f} Ko"
        elif size_bytes < 1024*1024*1024:
            return f"{size_bytes/(1024*1024):.1f} Mo"
        else:
            return f"{size_bytes/(1024*1024*1024):.1f} Go"

    # --- Main Application Window ---

    class UpdateAppWindow(QWidget):
        def __init__(self, installer_url):
            log_message("[UpdateAppWindow] Initialisation...")
            super().__init__()
            self.installer_url = installer_url
            self.worker = None
            self._is_finished = False
            self.initUI()
            self.apply_stylesheet()
            self.start_update()
            log_message("[UpdateAppWindow] Initialisation terminée.")

        def initUI(self):
            log_message("[UpdateAppWindow] initUI appelée.")
            self.setWindowTitle("Téléchargement GDJ")
            # Définir une taille fixe pour la fenêtre
            self.setFixedSize(300, 480) # Largeur 300, Hauteur ajustée pour barre 210px

            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(20, 20, 20, 20)
            main_layout.setSpacing(15)

            # Titre
            title_label = QLabel("Téléchargement")
            title_label.setObjectName("titleLabel")
            title_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(title_label)

            # Barre de progression circulaire - Taille Augmentée
            self.progress_bar = CircularProgressBar()
            progressbar_size = 210
            self.progress_bar.setFixedSize(progressbar_size, progressbar_size)
            main_layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

            # Vitesse
            self.speed_label = QLabel("0 MB/s")
            self.speed_label.setObjectName("speedLabel")
            self.speed_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.speed_label)

            # Bouton Arrêter
            self.stop_button = QPushButton("ARRÊTER")
            self.stop_button.setObjectName("stopButton")
            self.stop_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.stop_button.setFixedHeight(40)
            self.stop_button.clicked.connect(self.stop_update)
            main_layout.addWidget(self.stop_button)

            # Ligne de séparation
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setObjectName("separatorLine")
            main_layout.addWidget(line)

            # Infos Téléchargé / Restant (Layout horizontal)
            info_layout = QHBoxLayout()
            info_layout.setContentsMargins(0, 5, 0, 5) # Pas de marges H, petites V

            self.downloaded_label = QLabel("Téléchargé")
            self.downloaded_label.setObjectName("infoLabel")
            self.downloaded_value = QLabel("0,0 sur 0,0 Mo") # Initialisation Mo par défaut
            self.downloaded_value.setObjectName("infoValue")
            self.downloaded_value.setAlignment(Qt.AlignRight)

            self.eta_label = QLabel("Durée restante")
            self.eta_label.setObjectName("infoLabel")
            self.eta_value = QLabel("Calcul...")
            self.eta_value.setObjectName("infoValue")
            self.eta_value.setAlignment(Qt.AlignRight)

            # Utiliser un layout en grille pour un meilleur alignement
            grid_info = QGridLayout()
            grid_info.addWidget(self.downloaded_label, 0, 0)
            grid_info.addWidget(self.downloaded_value, 0, 1)
            grid_info.addWidget(self.eta_label, 1, 0)
            grid_info.addWidget(self.eta_value, 1, 1)
            grid_info.setColumnStretch(1, 1) # Laisser la colonne 1 s'étendre

            main_layout.addLayout(grid_info)
            main_layout.addStretch(1)

            self.setLayout(main_layout)
            # Retrait de adjustSize()
            # self.adjustSize()

        def apply_stylesheet(self):
            log_message("[UpdateAppWindow] apply_stylesheet appelée.")
            # Charger la police Segoe UI si possible
            # QFontDatabase.addApplicationFont("path/to/segoeui.ttf") # Si non installée

            self.setStyleSheet("""
                QWidget {
                    background-color: #1E2022; /* Fond sombre */
                    color: #DCDCDC; /* Texte gris clair par défaut */
                    font-family: "Segoe UI", sans-serif;
                }
                #titleLabel {
                    font-size: 18px;
                    font-weight: normal;
                    color: #FFFFFF; /* Blanc */
                    padding-bottom: 10px;
                }
                #speedLabel {
                    font-size: 20px;
                    font-weight: normal;
                    color: #FFFFFF; /* Blanc */
                    padding-top: 5px;
                    padding-bottom: 10px;
                }
                #stopButton {
                    background-color: #3C3F41; /* Gris foncé bouton */
                    color: #DCDCDC;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 10px;
                }
                #stopButton:hover {
                    background-color: #4C4F51; /* Un peu plus clair au survol */
                }
                #stopButton:pressed {
                    background-color: #2C2F31; /* Plus foncé si pressé */
                }
                #separatorLine {
                    background-color: #3C3F41;
                    border: none;
                    height: 1px;
                }
                #infoLabel {
                    font-size: 11px;
                    color: #AAAAAA; /* Gris plus foncé pour les labels */
                }
                #infoValue {
                    font-size: 11px;
                    color: #DCDCDC; /* Gris clair pour les valeurs */
                    font-weight: normal;
                }
            """)

        def start_update(self):
            log_message("[UpdateAppWindow] start_update appelée.")
            temp_dir = os.environ.get("TEMP", os.getcwd())
            try: # Essayer d'extraire le nom de fichier de l'URL
                potential_filename = self.installer_url.split('/')[-1]
                filename = potential_filename if ".exe" in potential_filename.lower() else "GDJ_downloaded_setup.exe"
            except: filename = "GDJ_downloaded_setup.exe"
            output_installer = os.path.join(temp_dir, filename)

            self.worker = Worker(self.installer_url, output_installer)
            self.worker.progress.connect(self.update_progress)
            self.worker.speedUpdate.connect(self.update_speed)
            self.worker.sizeUpdate.connect(self.update_size)
            self.worker.etaUpdate.connect(self.update_eta)
            self.worker.finished.connect(self.update_finished)
            self.worker.start()

        def update_progress(self, value):
            self.progress_bar.setValue(value)

        def update_speed(self, speed_bps):
            self.speed_label.setText(f"{format_bytes(speed_bps)}/s")

        def update_size(self, downloaded_b, total_b):
            downloaded_str = format_bytes(downloaded_b)
            total_str = format_bytes(total_b)
            self.downloaded_value.setText(f"{downloaded_str} sur {total_str}")

        def update_eta(self, eta_str):
            self.eta_value.setText(eta_str)

        def update_finished(self, success, message):
            log_message(f"[UpdateAppWindow] update_finished reçu: success={success}, message={message}")
            self._is_finished = True
            self.stop_button.setText("FERMER")
            self.stop_button.setEnabled(True)
            if success:
                self.progress_bar.setText("TERMINÉ")
                print(f"Installeur {message} lancé.")
                # Rétablir la fermeture automatique après 2 secondes de succès
                log_message("Programmation de la fermeture automatique dans 2000 ms.")
                QTimer.singleShot(2000, self.close) # Utiliser self.close() est généralement suffisant
            else:
                self.progress_bar.setText("ERREUR")
                self.progress_bar.progress_color = QColor(200, 0, 0)
                self.progress_bar.update()
                self.speed_label.setText("Erreur")
                self.eta_value.setText("-")
                self.downloaded_value.setText("-")
                print(f"Échec de la mise à jour: {message}")

        def stop_update(self):
            log_message("[UpdateAppWindow] stop_update appelé.")
            if self._is_finished:
                self.close()
            elif self.worker and self.worker.isRunning():
                self.progress_bar.setText("ANNULATION...")
                self.stop_button.setEnabled(False)
                self.worker.stop()

        def closeEvent(self, event):
            log_message("[UpdateAppWindow] closeEvent appelé.")
            if self.worker and self.worker.isRunning() and not self._is_finished:
                self.worker.stop()
                self.worker.wait(500)
            event.accept()

    # --- Main Execution ---

    def main():
        log_message("[main] Fonction main démarrée.")
        # Gestion des arguments
        if len(sys.argv) < 2:
            log_message("Erreur: Arguments manquants.")
            print("Erreur: URL de l'installeur manquante.")
            print("Usage: update_helper.exe <installer_url>")
            # Afficher une QMessageBox simple sans dépendre de UpdateAppWindow
            app_temp = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Erreur Arguments", "URL de l'installeur manquante.\nUsage: update_helper.exe <installer_url>")
            sys.exit(1)

        installer_url = sys.argv[1]
        log_message(f"URL reçue: {installer_url}")
        print("-- Update Helper Démarré (Mode GUI Circulaire avec Logging) --")
        print(f"URL de l'installeur reçue : {installer_url}")

        # Bloc try-except global pour attraper les erreurs d'initialisation
        app = None # Initialiser à None
        try:
            log_message("[main] Initialisation de QApplication...")
            app = QApplication(sys.argv)
            log_message("[main] QApplication initialisée.")

            # Icône ?
            # log_message("[main] Tentative de chargement icône...")
            # try:
            #     app_icon = QIcon("chemin/vers/votre/icone.ico")
            #     if not app_icon.isNull(): app.setWindowIcon(app_icon)
            #     log_message("[main] Icône chargée (ou non trouvée).")
            # except Exception as e_icon:
            #     log_message(f"[main] Erreur chargement icône: {e_icon}")

            log_message("[main] Initialisation de UpdateAppWindow...")
            window = UpdateAppWindow(installer_url)
            log_message("[main] UpdateAppWindow initialisée.")
            log_message("[main] Affichage de la fenêtre...")
            window.show()
            log_message("[main] Lancement de app.exec_()...")
            exit_code = app.exec_()
            log_message(f"[main] app.exec_() terminé avec code: {exit_code}")
            sys.exit(exit_code)

        except Exception as e_main:
            # Log l'erreur fatale
            log_message("!!! ERREUR FATALE DANS MAIN !!!")
            log_message(traceback.format_exc()) # Log la stack trace complète
            print("ERREUR FATALE DANS MAIN:", e_main)
            print(traceback.format_exc())
            # Afficher une boîte de message d'erreur simple si possible
            try:
                 if not app: # Si QApplication n'a pas pu être créée
                     app = QApplication(sys.argv)
                 QMessageBox.critical(None, "Erreur Fatale Update Helper",
                                     f"Une erreur critique est survenue au démarrage de l'assistant:\n\n{e_main}\n\nConsultez le fichier log pour détails:\n{log_file_path}")
            except Exception as e_msgbox:
                 log_message(f"Impossible d'afficher la QMessageBox d'erreur: {e_msgbox}")
                 print(f"Impossible d'afficher la QMessageBox d'erreur: {e_msgbox}")
            sys.exit(1)

    if __name__ == '__main__':
        main()

except Exception as e_global:
    # Catch exception PENDANT les imports ou avant même le main
    log_message("!!! ERREUR FATALE GLOBALE (avant main) !!!")
    log_message(traceback.format_exc())
    print("ERREUR FATALE GLOBALE:", e_global)
    print(traceback.format_exc())
    # Essayer d'afficher une boîte d'erreur minimale
    try:
        app_temp = QApplication(sys.argv)
        QMessageBox.critical(None, "Erreur Fatale Initiale", f"Erreur très précoce:\n{e_global}")
    except:
        pass # Si même ça échoue...
    sys.exit(1)
