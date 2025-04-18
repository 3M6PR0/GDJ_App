# GDJ_Installation_UI.py

import sys
import os
import time
import traceback
import zipfile # Pour extraire le payload
import shutil  # Pour copier les fichiers
import winreg  # Pour écrire dans le registre
from math import pi, sin, cos
from collections import deque
import configparser

# Imports PyQt5
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QSizePolicy, QFrame, QMessageBox, QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF, QPointF, QSize
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QFontDatabase, QIcon

# Essayer d'importer winshell pour les raccourcis
try:
    import winshell
    winshell_available = True
except ImportError:
    winshell_available = False
    print("Avertissement: winshell non trouvé (pip install winshell). Les raccourcis ne seront pas créés.")

# --- Logging (Ajout log initial) ---
log_dir = os.environ.get("TEMP", os.getcwd())
log_file_path = os.path.join(log_dir, "gdj_installer_startup_log.txt") # Nom différent pour l'installateur

def log_message(message):
    try:
        import time
        with open(log_file_path, "a", encoding='utf-8') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"ERREUR LOGGING: {e}")

# Log initial pour vérifier le chemin
try:
    log_message(f"--- GDJ Installer UI Démarré --- Log Path: {log_file_path}")
except Exception as log_init_e:
    print(f"ERREUR INIT LOGGING: {log_init_e}")

# --- Classe Barre Circulaire (Copiée de l'helper final) ---
class CircularProgressBar(QWidget):
    def __init__(self, parent=None):
        log_message("[CircularProgressBar] Initialisation...")
        super().__init__(parent)
        self.value = 0
        self.min_value = 0
        self.max_value = 100
        self.suffix = '%'
        self.text = "INSTALLATION"

        # Couleurs (Thème sombre basé sur l'image)
        self.background_color = QColor(30, 32, 34)
        self.progress_background_color = QColor(60, 63, 65)
        self.progress_color = QColor(0, 122, 204)
        self.text_color = QColor(220, 220, 220)
        self.percent_text_color = QColor(240, 240, 240)

        # Polices
        self.percent_font = QFont("Segoe UI", 26, QFont.Bold)
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

        # Marge minimale pour maximiser la taille du cercle
        pen_width = 12
        margin = pen_width / 2
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

# --- Fonction utilitaire format_bytes (Copiée de l'helper final) ---
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

# --- Worker Thread pour l'Installation --- (Refonte copie)
class InstallWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    sizeUpdate = pyqtSignal(str, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, install_dir):
        super().__init__()
        self.install_dir = install_dir
        self.is_running = True
        # Constantes pour le registre/shortcuts
        self.app_name = "GDJ" # Nom à afficher
        self.publisher = "3M6PR0" # Votre nom ou pseudo
        self.app_id = "GDJApp" # ID unique pour le registre
        self.main_exe_name = "GDJ.exe" # Nom de l'exécutable principal
        self.uninstall_exe_name = "unins000.exe" # Nom du désinstalleur généré
        self.app_version = "" # Sera lu depuis version.txt embarqué

    def get_app_version(self, source_dir):
        """Tente de lire la version depuis data/version.txt embarqué."""
        version_file_path = os.path.join(source_dir, 'data', 'version.txt')
        try:
            config = configparser.ConfigParser()
            config.read(version_file_path, encoding="utf-8")
            version = config.get("Version", "value").strip()
            log_message(f"Version lue depuis version.txt embarqué: {version}")
            return version
        except Exception as e:
            log_message(f"Avertissement: Impossible de lire la version depuis {version_file_path}: {e}")
            return "Inconnue"

    def get_source_dir(self):
        """ Retourne le répertoire source des fichiers.
            - Mode --onefile: sys._MEIPASS
            - Mode --onedir: dossier de l'exécutable
            - Mode dev: ./payload_src
        """
        if getattr(sys, 'frozen', False):
            # Mode Compilé (frozen)
            if hasattr(sys, '_MEIPASS'):
                # Mode --onefile : Source est le dossier temporaire _MEIPASS
                log_message(f"Détecté mode compilé (--onefile). Source MEIPASS: {sys._MEIPASS}")
                return sys._MEIPASS
            else:
                # Mode --onedir : Source est le dossier contenant l'exécutable
                # sys.executable est le chemin complet vers GDJ_Installation_UI.exe
                source_dir = os.path.dirname(sys.executable)
                log_message(f"Détecté mode compilé (--onedir). Source: {source_dir}")
                return source_dir
        else:
            # Mode développement (non-frozen)
            source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'payload_src'))
            log_message(f"Détecté mode développement. Source: {source_dir}")
            if not os.path.isdir(source_dir):
                log_message(f"ERREUR: Dossier source dev introuvable: {source_dir}")
                raise FileNotFoundError(f"Dossier source dev introuvable: {source_dir}")
            return source_dir

    def calculate_total_size(self, source_dir, items_to_install):
        """Calcule la taille totale des fichiers/dossiers spécifiés à copier."""
        total_size = 0
        log_message(f"Calcul de la taille pour {len(items_to_install)} éléments depuis: {source_dir}")
        try:
            for item_name in items_to_install:
                item_path = os.path.join(source_dir, item_name)
                if not os.path.exists(item_path):
                     log_message(f"Avertissement calcul taille: {item_path} non trouvé.")
                     continue # Ignorer si l'élément source n'existe pas
                
                if os.path.isfile(item_path):
                    try:
                        total_size += os.path.getsize(item_path)
                    except OSError as e_size_file:
                         log_message(f"Erreur getsize fichier {item_path}: {e_size_file}")
                elif os.path.isdir(item_path):
                    try:
                        for dirpath, dirnames, filenames in os.walk(item_path):
                            for f in filenames:
                                fp = os.path.join(dirpath, f)
                                if os.path.exists(fp) and not os.path.islink(fp):
                                    try:
                                        total_size += os.path.getsize(fp)
                                    except OSError as e_size_dirfile:
                                        log_message(f"Erreur getsize sous-fichier {fp}: {e_size_dirfile}")
                    except Exception as e_walk:
                        log_message(f"Erreur walk dossier {item_path}: {e_walk}")
        except Exception as e_calc:
            log_message(f"Erreur calcul taille totale: {e_calc}\n{traceback.format_exc()}")
            # Ne pas lever d'exception ici pour permettre à l'install de continuer
            # mais retourner 0 pour indiquer un problème
            return 0
        log_message(f"Taille totale calculée: {format_bytes(total_size)}")
        return total_size

    def run(self):
        log_message("[InstallWorker] Démarrage.")
        source_base_dir = ""
        # Liste explicite des éléments à installer depuis le payload
        items_to_install = [
            "GDJ.exe",
            "updater", # Dossier
            "data",    # Dossier
            "RELEASE_NOTES.md",
            "uninstall_gdj.exe" # Notre désinstalleur
        ]
        
        try:
            source_base_dir = self.get_source_dir()
            log_message(f"Répertoire source (MEIPASS ou dev): {source_base_dir}")
            
            # --- LOG DE DIAGNOSTIC : Lister le contenu de source_base_dir ---
            log_message(f"Contenu trouvé dans source_base_dir ({source_base_dir}):")
            try:
                found_items = os.listdir(source_base_dir)
                if not found_items:
                     log_message("  -> (Vide ou inaccessible)")
                else:
                    for item in found_items:
                        log_message(f"  - {item}")
            except Exception as e_list:
                log_message(f"  Erreur lors du listage du contenu: {e_list}")
            log_message("--- Fin du listage du contenu ---")
            # --- FIN LOG DE DIAGNOSTIC ---

            self.app_version = self.get_app_version(source_base_dir)
            log_message(f"Version lue: {self.app_version}")
            
            total_size_bytes = self.calculate_total_size(source_base_dir, items_to_install)
            if total_size_bytes == 0:
                 log_message("Avertissement: Taille totale calculée est 0. La barre de progression pourrait être imprécise.")
            
            self.sizeUpdate.emit("0 B", format_bytes(total_size_bytes))

            # --- 1. Copie des fichiers vers la destination (Sélective) ---
            self.status.emit("Installation des fichiers...")
            log_message(f"Copie sélective depuis {source_base_dir} vers {self.install_dir}")

            # Nettoyer dossier destination avant copie
            if os.path.exists(self.install_dir):
                log_message(f"Suppression de l'ancien dossier: {self.install_dir}")
                try:
                    shutil.rmtree(self.install_dir)
                except Exception as e_rm:
                     log_message(f"Erreur suppression ancien dossier: {e_rm}\n{traceback.format_exc()}")
                     raise Exception(f"Impossible de nettoyer la destination: {e_rm}")
            try:
                 os.makedirs(self.install_dir, exist_ok=True)
            except Exception as e_mkdir:
                log_message(f"Erreur création dossier destination: {e_mkdir}\n{traceback.format_exc()}")
                raise Exception(f"Impossible de créer la destination: {e_mkdir}")

            copied_bytes = 0
            total_items = len(items_to_install)
            current_item_index = 0

            for item_name in items_to_install:
                if not self.is_running: raise Exception("Installation annulée")
                
                source_item_path = os.path.join(source_base_dir, item_name)
                dest_item_path = os.path.join(self.install_dir, item_name)
                current_item_index += 1
                
                self.status.emit(f"Copie: {item_name}")
                log_message(f"Traitement de: {item_name} ({source_item_path})")

                if not os.path.exists(source_item_path):
                     log_message(f"ERREUR: Élément source introuvable: {source_item_path}. Installation échouée.")
                     raise FileNotFoundError(f"Composant requis manquant: {item_name}")

                item_size = 0
                try:
                    if os.path.isdir(source_item_path):
                        log_message(f"  -> Copie du dossier vers {dest_item_path}")
                        shutil.copytree(source_item_path, dest_item_path, copy_function=shutil.copy2, dirs_exist_ok=True)
                        # Calculer la taille du dossier copié pour la progression
                        for dirpath, _, filenames in os.walk(dest_item_path):
                            for f in filenames:
                                try: item_size += os.path.getsize(os.path.join(dirpath, f))
                                except OSError: pass
                        log_message(f"  -> Dossier {item_name} copié.")
                    elif os.path.isfile(source_item_path):
                        log_message(f"  -> Copie du fichier vers {dest_item_path}")
                        shutil.copy2(source_item_path, dest_item_path)
                        item_size = os.path.getsize(dest_item_path)
                        log_message(f"  -> Fichier {item_name} copié.")
                    else:
                         log_message(f"Avertissement: {item_name} n'est ni un fichier ni un dossier source valide.")

                    copied_bytes += item_size
                    progress_percent = int((copied_bytes / total_size_bytes) * 100) if total_size_bytes > 0 else int((current_item_index / total_items) * 100)
                    self.progress.emit(min(progress_percent, 95)) # Limiter à 95% avant étapes finales
                    self.sizeUpdate.emit(format_bytes(copied_bytes), format_bytes(total_size_bytes))

                except Exception as e_copy:
                    log_message(f"ERREUR lors de la copie de {item_name} vers {dest_item_path}: {e_copy}\n{traceback.format_exc()}")
                    # Si la copie du désinstalleur échoue, c'est critique
                    if item_name == "uninstall_gdj.exe":
                         raise Exception(f"Échec copie du désinstalleur: {e_copy}")
                    else:
                         # Pour les autres erreurs, on pourrait choisir de continuer ou d'arrêter
                         # Ici, on arrête pour plus de sécurité
                         raise Exception(f"Erreur copie {item_name}: {e_copy}")

            log_message("Fin de la phase de copie.")
            # Vérification finale de la présence du désinstalleur
            final_uninstaller_path = os.path.join(self.install_dir, "uninstall_gdj.exe")
            if not os.path.exists(final_uninstaller_path):
                log_message("ERREUR CRITIQUE: uninstall_gdj.exe est absent du dossier d'installation final !")
                raise FileNotFoundError("Le composant de désinstallation n'a pas pu être installé.")
            else:
                log_message("Vérification post-copie: uninstall_gdj.exe est présent.")
                
            # --- 2. Écriture dans le registre --- 
            self.status.emit("Configuration (registre)...")
            log_message("Écriture des informations de désinstallation dans le registre.")
            try:
                self._write_registry_keys()
                log_message("Informations de désinstallation écrites.")
                self.progress.emit(97)
            except Exception as e_reg:
                log_message(f"Erreur lors de l'écriture dans le registre: {e_reg}")
                self.status.emit("Erreur configuration registre (voir log)")
                time.sleep(1) 

            # --- 3. Création des raccourcis --- 
            if winshell_available:
                self.status.emit("Création des raccourcis...")
                log_message("Création des raccourcis.")
                try:
                    self._create_shortcuts()
                    log_message("Raccourcis créés.")
                    self.progress.emit(99)
                except Exception as e_shortcut:
                    log_message(f"Erreur lors de la création des raccourcis: {e_shortcut}")
                    self.status.emit("Erreur création raccourcis (voir log)")
                    time.sleep(1)
            else:
                 log_message("Skipping shortcut creation (winshell not available).")
                 self.status.emit("Raccourcis ignorés (module manquant)")
                 time.sleep(1)

            # --- Terminé --- 
            log_message("Installation terminée avec succès.")
            self.progress.emit(100)
            self.status.emit("Installation terminée !")
            self.finished.emit(True, "L'installation de GDJ s'est terminée avec succès.")

        except Exception as e:
            log_message(f"ERREUR D'INSTALLATION: {traceback.format_exc()}")
            self.finished.emit(False, f"L'installation a échoué :\n{e}")

        finally:
             log_message("[InstallWorker] Arrêt.")

    # --- Fonctions pour Registre et Raccourcis ---

    def _get_uninstall_reg_key_path(self):
        # Clé spécifique à l'application sous la branche Uninstall
        # IMPORTANT: S'assurer que l'ID est unique !
        # Note: On utilise toujours le même chemin relatif, mais sous HKCU maintenant.
        # Utiliser des double backslashes pour éviter SyntaxWarning
        return f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{self.app_id}"

    def _write_registry_keys(self):
        """Écrit les informations de désinstallation dans le registre (HKCU).
           Pointe vers notre désinstalleur Python.
        """
        key_path = self._get_uninstall_reg_key_path()
        # Utiliser des double backslashes pour éviter SyntaxWarning
        log_message(f"Chemin registre: HKCU\\{key_path}")
        main_exe_path = os.path.join(self.install_dir, self.main_exe_name)
        # Chemin vers notre désinstalleur Python DANS le dossier d'installation
        uninstaller_path = os.path.join(self.install_dir, "uninstall_gdj.exe")

        # Vérifier si le désinstalleur Python existe (il devrait avoir été copié)
        if not os.path.exists(uninstaller_path):
             log_message(f"Avertissement: Désinstalleur Python {uninstaller_path} non trouvé. La désinstallation échouera.")

        try:
            # Utiliser HKEY_CURRENT_USER
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                # --- Infos standards --- 
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, self.app_name)
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, self.app_version)
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, self.install_dir)
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, self.publisher)
                if os.path.exists(main_exe_path):
                     winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, main_exe_path)
                
                # --- Commande de désinstallation --- 
                if os.path.exists(uninstaller_path):
                    # Pointe vers notre exécutable Python
                    winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_path}"')
                    # La désinstallation silencieuse n'est pas gérée par défaut par notre script
                    # On peut soit la retirer, soit pointer vers la même chose
                    # winreg.DeleteValue(key, "QuietUninstallString") # Option 1: supprimer
                    winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, f'"{uninstaller_path}"') # Option 2: pointer pareil
                
                # --- Autres flags --- 
                winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)

            log_message("Clés de registre écrites avec succès (HKCU), pointant vers uninstall_gdj.exe.")

        except PermissionError as e: # Gardé par sécurité
            log_message(f"Erreur de permission inattendue (HKCU): {e}")
            raise Exception("Erreur permission registre (HKCU).")
        except Exception as e:
            log_message(f"Erreur inattendue registre: {e}\n{traceback.format_exc()}")
            raise

    def _create_shortcuts(self):
        """Crée les raccourcis Bureau et Menu Démarrer."""
        if not winshell_available:
            log_message("Impossible de créer les raccourcis: winshell n'est pas installé.")
            return

        main_exe_path = os.path.join(self.install_dir, self.main_exe_name)
        if not os.path.exists(main_exe_path):
            log_message(f"Impossible de créer les raccourcis: {main_exe_path} non trouvé.")
            return

        desktop_path = winshell.desktop()
        start_menu_path = winshell.programs()
        shortcut_name = f"{self.app_name}.lnk"

        # Raccourci Bureau
        desktop_shortcut_path = os.path.join(desktop_path, shortcut_name)
        log_message(f"Création raccourci Bureau: {desktop_shortcut_path}")
        try:
            with winshell.shortcut(desktop_shortcut_path) as link:
                link.path = main_exe_path
                link.description = f"Lancer {self.app_name}"
                link.arguments = "" # Pas d'arguments spécifiques
                link.working_directory = self.install_dir
                link.icon_location = (main_exe_path, 0)
        except Exception as e:
            log_message(f"Erreur création raccourci bureau: {e}")
            # Continuer pour essayer le menu démarrer

        # Raccourci Menu Démarrer
        start_menu_folder = os.path.join(start_menu_path, self.app_name)
        start_menu_shortcut_path = os.path.join(start_menu_folder, shortcut_name)
        log_message(f"Création raccourci Menu Démarrer: {start_menu_shortcut_path}")
        try:
            if not os.path.exists(start_menu_folder):
                os.makedirs(start_menu_folder)

            with winshell.shortcut(start_menu_shortcut_path) as link:
                link.path = main_exe_path
                link.description = f"Lancer {self.app_name}"
                link.arguments = ""
                link.working_directory = self.install_dir
                link.icon_location = (main_exe_path, 0)
        except Exception as e:
            log_message(f"Erreur création raccourci menu démarrer: {e}")
            # Propager l'erreur si nécessaire ou juste loguer

    def stop(self):
        log_message("Arrêt demandé pour InstallWorker.")
        self.is_running = False

# --- Fenêtre Principale de l'Installateur --- (Adaptée de UpdateAppWindow)
class InstallAppWindow(QWidget):
    INITIAL_WIDTH = 300
    INITIAL_HEIGHT = 480 # Correspond à la dernière taille fixe

    def __init__(self, install_dir):
        super().__init__()
        log_message("[InstallAppWindow] Initialisation...")
        self.install_dir = install_dir
        self.worker = None
        self._is_installing = False
        self._is_finished = False
        self.initUI()
        self.apply_stylesheet()
        log_message("[InstallAppWindow] Initialisation terminée.")

    def initUI(self):
        log_message("[InstallAppWindow] initUI appelée.")
        self.setWindowTitle("Installation GDJ") # Titre changé
        self.setFixedSize(self.INITIAL_WIDTH, self.INITIAL_HEIGHT)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Titre
        title_label = QLabel("Installation GDJ") # Texte changé
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Barre de progression circulaire
        self.progress_bar = CircularProgressBar()
        progressbar_size = 210
        self.progress_bar.setFixedSize(progressbar_size, progressbar_size)
        self.progress_bar.setText("Prêt") # Texte initial changé
        main_layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        # Label de Statut
        self.status_label = QLabel("Prêt à installer.")
        self.status_label.setObjectName("statusLabel") # Assurer la cohérence avec QSS
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)

        # Bouton Installer/Annuler/Fermer
        self.action_button = QPushButton("INSTALLER") # Texte initial changé
        self.action_button.setObjectName("actionButton")
        self.action_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.action_button.setFixedHeight(40)
        self.action_button.clicked.connect(self.handle_action_button)
        main_layout.addWidget(self.action_button)

        # Ligne de séparation
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setObjectName("separatorLine")
        main_layout.addWidget(line)

        # Infos Taille Copiée / Totale
        grid_info = QGridLayout()
        self.copied_label = QLabel("Progression:") # Texte changé
        self.copied_label.setObjectName("infoLabel")
        self.copied_value = QLabel("0 Ko / 0 Ko") # Texte initial changé
        self.copied_value.setObjectName("infoValue")
        self.copied_value.setAlignment(Qt.AlignRight)
        # Pas d'ETA pour la copie pour l'instant
        grid_info.addWidget(self.copied_label, 0, 0)
        grid_info.addWidget(self.copied_value, 0, 1)
        grid_info.setColumnStretch(1, 1)

        main_layout.addLayout(grid_info)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def apply_stylesheet(self):
        log_message("[InstallAppWindow] apply_stylesheet appelée.")
        self.setStyleSheet("""
            QWidget {
                background-color: #1E2022; /* Fond général sombre */
                color: #DCDCDC; /* Texte clair par défaut */
                font-family: "Segoe UI";
                font-size: 9pt;
            }

            #titleLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #FFFFFF; /* Blanc pour le titre */
                padding-bottom: 10px;
            }

            /* Le style de CircularProgressBar est géré dans sa classe */

            #statusLabel {
                font-size: 9pt;
                color: #B0B0B0; /* Gris clair pour le statut */
                padding-top: 5px;
                padding-bottom: 5px;
            }

            #actionButton {
                background-color: #007ACC; /* Bleu primaire */
                color: #FFFFFF; /* Texte blanc */
                border: none;
                padding: 10px;
                font-size: 10pt;
                font-weight: bold;
                border-radius: 4px;
            }

            #actionButton:hover {
                background-color: #005A9E; /* Bleu plus foncé au survol */
            }

            #actionButton:pressed {
                background-color: #004C87; /* Bleu encore plus foncé au clic */
            }

            #actionButton:disabled {
                background-color: #4D4D4D; /* Gris foncé si désactivé */
                color: #808080;
            }

            #separatorLine {
                background-color: #3C3F41; /* Gris foncé pour la ligne */
                height: 1px;
                border: none;
                margin-top: 5px;
                margin-bottom: 5px;
            }

            #infoLabel {
                font-size: 8pt;
                color: #A0A0A0; /* Gris moyen pour les labels d'info */
            }

            #infoValue {
                font-size: 8pt;
                color: #C0C0C0; /* Gris clair pour les valeurs d'info */
                font-weight: bold;
            }

            QToolTip {
                background-color: #3C3F41;
                color: #DCDCDC;
                border: 1px solid #505355;
                padding: 4px;
            }

            QMessageBox {
                 background-color: #25282A;
                 color: #DCDCDC;
                 font-size: 10pt;
            }
            QMessageBox QLabel { /* Texte du message */
                 color: #DCDCDC;
                 font-size: 10pt;
            }
            QMessageBox QPushButton { /* Boutons OK/Annuler etc. */
                 background-color: #007ACC;
                 color: #FFFFFF;
                 border: none;
                 padding: 8px 16px;
                 font-size: 9pt;
                 border-radius: 3px;
                 min-width: 60px; /* Largeur minimale pour les boutons */
            }
            QMessageBox QPushButton:hover {
                 background-color: #005A9E;
            }
            QMessageBox QPushButton:pressed {
                 background-color: #004C87;
            }
        """)

    def handle_action_button(self):
        log_message("[InstallAppWindow] Clic sur bouton action.")
        if self._is_finished:
            self.close()
        elif self._is_installing:
            # Annuler l'installation
            if self.worker and self.worker.isRunning():
                 reply = QMessageBox.question(self, "Annuler l'installation ?",
                                           "L'installation est en cours. Voulez-vous vraiment annuler ?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                 if reply == QMessageBox.Yes:
                    log_message("Demande d'annulation worker...")
                    self.progress_bar.setText("ANNULATION")
                    self.status_label.setText("Annulation en cours...")
                    self.action_button.setEnabled(False) # Désactiver pendant l'arrêt
                    self.worker.stop()
                    # Le worker émettra finished(False, "Annulé...") quand il s'arrêtera
                 # else: On ne fait rien si l'utilisateur dit Non
        else:
            # Démarrer l'installation
            self._is_installing = True
            self._is_finished = False
            self.action_button.setText("ANNULER")
            self.progress_bar.setValue(0)
            self.progress_bar.setText("INSTALLATION")
            self.status_label.setText("Démarrage de l'installation...")
            self.copied_value.setText("...")
            self.start_install_worker()

    def start_install_worker(self):
        log_message("[InstallAppWindow] start_install_worker appelée.")
        self.worker = InstallWorker(self.install_dir)
        # Connecter les signaux du worker aux slots
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.sizeUpdate.connect(self.update_size)
        self.worker.finished.connect(self.install_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, status):
        self.status_label.setText(status)

    def update_size(self, copied_str, total_str):
        self.copied_value.setText(f"{copied_str} / {total_str}") # Format "/"

    def install_finished(self, success, message):
        log_message(f"[InstallAppWindow] install_finished reçu: success={success}, message={message}")
        self._is_installing = False
        self._is_finished = True
        # Réactiver le bouton dans tous les cas (succès, erreur, annulé)
        self.action_button.setEnabled(True)

        if message == "Annulé par l'utilisateur": # Cas spécifique de l'annulation
            self.action_button.setText("INSTALLER") # Revenir au texte initial
            self.progress_bar.setText("ANNULÉ")
            self.progress_bar.setValue(0) # Remettre à zéro
            self.progress_bar.progress_color = QColor(150, 150, 150) # Couleur neutre/grise
            self.progress_bar.update()
            self.status_label.setText("Installation annulée.")
        elif success:
            self.action_button.setText("TERMINÉ")
            self.progress_bar.setText("TERMINÉ")
            self.progress_bar.setValue(100)
            self.progress_bar.progress_color = QColor(0, 122, 204) # Revenir couleur succès
            self.progress_bar.update()
            self.status_label.setText("Installation réussie !")
        else:
            # Gérer les autres erreurs
            self.action_button.setText("ERREUR (Fermer)")
            self.progress_bar.setText("ERREUR")
            self.progress_bar.progress_color = QColor(200, 0, 0) # Erreur en rouge
            self.progress_bar.update()
            # Extraire le message pertinent de l'exception si possible
            error_short = message.split('\n')[-1] if '\n' in message else message
            self.status_label.setText(f"Erreur: {error_short}")
            # Construire le message de la boîte de dialogue séparément pour éviter l'erreur f-string
            error_dialog_title = "Erreur d'Installation"
            error_dialog_text = f"L'installation a échoué:\n{message}" 
            QMessageBox.critical(self, error_dialog_title, error_dialog_text)

    def closeEvent(self, event):
        log_message("[InstallAppWindow] closeEvent appelé.")
        if self._is_installing:
            # Utiliser des triple guillemets pour une robustesse maximale
            title = """Annuler l'installation ?"""
            text = """L'installation est en cours. Voulez-vous vraiment annuler ?"""
            buttons = QMessageBox.Yes | QMessageBox.No
            default_button = QMessageBox.No
            
            # L'appel final avec les variables
            reply = QMessageBox.question(self, title, text, buttons, default_button)
            
            if reply == QMessageBox.Yes:
                if self.worker and self.worker.isRunning(): 
                    log_message("Annulation demandée par l'utilisateur via closeEvent.")
                    self.worker.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

# --- Main Execution --- (Adapté pour l'installateur)
def main():
    log_message("[main_installer] Démarrage.")

    # Déterminer le dossier d'installation par défaut (Profil utilisateur)
    default_install_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser("~")), "GDJ")
    log_message(f"Dossier d'installation par défaut: {default_install_dir}")
    # Note: On ne demande pas le chemin à l'utilisateur pour l'instant

    app = None
    try:
        log_message("[main_installer] Init QApplication.")
        app = QApplication(sys.argv)

        log_message("[main_installer] Init InstallAppWindow.")
        window = InstallAppWindow(default_install_dir)
        window.show()

        log_message("[main_installer] Lancement app.exec_.")
        exit_code = app.exec_()
        log_message(f"[main_installer] Fin avec code {exit_code}.")
        sys.exit(exit_code)

    except Exception as e_main:
        log_message("!!! ERREUR FATALE INSTALLER !!!")
        log_message(traceback.format_exc())
        print(f"ERREUR FATALE INSTALLER: {e_main}")
        try:
            if not app: app = QApplication(sys.argv) # Assurer qu'on a une app pour la boîte de dialogue
            # Construire le message séparément
            error_title = "Erreur Fatale Installation"
            error_text = f"Erreur critique:\n{e_main}"
            QMessageBox.critical(None, error_title, error_text)
        except: 
            # Si même la QMessageBox échoue, on ne peut rien faire
            pass 
        sys.exit(1)


if __name__ == '__main__':
    # --- Logging de démarrage TRES précoce --- START/END (inchangé)
    # ...

    try:
        main()
    except Exception as e_global:
        log_message("!!! ERREUR FATALE GLOBALE INSTALLER (avant main) !!!")
        log_message(traceback.format_exc())
        print(f"ERREUR FATALE GLOBALE INSTALLER: {e_global}")
        try:
            # Assurer qu'on a une app pour la boîte de dialogue
            app_temp = QApplication(sys.argv) 
             # Construire le message séparément
            error_title = "Erreur Fatale Initiale Installation"
            error_text = f"Erreur très précoce:\n{e_global}"
            QMessageBox.critical(None, error_title, error_text)
        except: 
            # Si même la QMessageBox échoue
            pass
        sys.exit(1) 