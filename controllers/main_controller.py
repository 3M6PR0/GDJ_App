from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSlot, QCoreApplication
# --- AJOUT DE L'IMPORT QIcon ---
from PyQt5.QtGui import QIcon
from pages.document_page import DocumentPage
# from pages.profile_page import ProfilePage # Commenté
# from models.profile import Profile # Commenté
import os
import sys
import configparser
from packaging import version
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox, QDialog,
                             QVBoxLayout, QTextBrowser, QPushButton, QSizePolicy)
from config import CONFIG
from updater.update_checker import check_for_updates
from utils.stylesheet_loader import load_stylesheet
import logging
logger = logging.getLogger('GDJ_App')

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

# --- Import des nouvelles pages/fenêtres ---
# from pages.welcome_page import WelcomePage # ANCIEN
from windows.welcome_window import WelcomeWindow # NOUVEAU
from ui.main_window import MainWindow
# --- AJOUT IMPORTS POUR ABOUT ---
from pages.about.about_page import AboutPage
from controllers.about.about_controller import AboutController
# --- AJOUT IMPORT DocumentWindow ---
from windows.document_window import DocumentWindow
# --- AJOUT IMPORT SettingsWindow ---
from windows.settings_window import SettingsWindow

# --- Classe pour la boîte de dialogue des notes de version ---
class ReleaseNotesDialog(QDialog):
    def __init__(self, version_str, notes_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Nouveautés de la version {version_str}")
        self.setModal(True)
        self.setMinimumSize(500, 400) # Taille minimale

        layout = QVBoxLayout(self)

        text_browser = QTextBrowser(self)
        text_browser.setMarkdown(notes_content) # Afficher le contenu Markdown
        text_browser.setOpenExternalLinks(True)
        layout.addWidget(text_browser)

        button_box = QPushButton("Fermer", self)
        button_box.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        button_box.clicked.connect(self.accept)
        layout.addWidget(button_box, alignment=Qt.AlignRight)

        self.setLayout(layout)

# --- MODIFICATION: Faire hériter de QObject --- 
class MainController(QObject):
# -------------------------------------------
    def __init__(self):
        # --- AJOUT: Appeler __init__ du parent --- 
        super().__init__()
        # ---------------------------------------
        logger.info("--- Entering MainController __init__ ---")
        self.main_window = None
        self.welcome_window = None
        self.documents = {}
        self.about_page = None
        self.about_controller_instance = None
        # --- SUPPRESSION: Instanciation PreferencesController --- 
        # try:
        #     from controllers.preferences.preferences_controller import PreferencesController
        #     self.preferences_controller = PreferencesController(main_controller=self) 
        #     logger.info("MainController: PreferencesController instance created.")
        # except ImportError as e_imp:
        #     logger.critical(f"CRITICAL ERROR: Cannot import PreferencesController: {e_imp}")
        #     self.preferences_controller = None
        # except Exception as e_prefs_init:
        #     logger.critical(f"CRITICAL ERROR: Cannot initialize PreferencesController: {e_prefs_init}")
        #     self.preferences_controller = None
        # ------------------------------------------------------
        self.navigate_to_notes_after_welcome = False 
        self._startup_update_check_done = False
        self.new_doc_window = None # Garder une référence si DocumentWindow est unique
        self.settings_window = None # <<< AJOUT: Référence à SettingsWindow

        # --- Corrected Logic AGAIN (Focus on Version Comparison) --- 
        self.version_file = get_resource_path("data/version.txt")
        self.release_notes_file = get_resource_path("RELEASE_NOTES.md")
        self.current_version_str = self._read_version_file(self.version_file)
        
        last_run_version_file = get_resource_path("data/last_run_version.txt")
        last_run_version_str = self._read_version_file(last_run_version_file) 
        logger.debug(f"DEBUG __init__: Current Version='{self.current_version_str}', Last Run Version Read='{last_run_version_str}'")

        do_navigate_on_startup = False
        try:
            current_v = version.parse(self.current_version_str)
            last_run_v = version.parse(last_run_version_str) 
            # Navigate if current version is strictly greater than the last run version
            if current_v > last_run_v:
                do_navigate_on_startup = True
                logger.debug(f"DEBUG __init__: Update detected (current {current_v} > last run {last_run_v}). Setting navigation flag.")
            else:
                 logger.debug(f"DEBUG __init__: No update detected (current {current_v} <= last run {last_run_v}).")
        except version.InvalidVersion:
            # Treat parse error (like first run "0.0.0") as needing navigation
            logger.debug(f"DEBUG __init__: InvalidVersion detected. Setting navigation flag for first run/update.")
            try:
                 version.parse(self.current_version_str) # Check current is valid
                 do_navigate_on_startup = True
            except version.InvalidVersion:
                 logger.error("ERROR __init__: Current version is also invalid. Navigation flag set to False.")
                 do_navigate_on_startup = False

        # Set the flag for later use in show_welcome_page
        self.navigate_to_notes_after_welcome = do_navigate_on_startup

        # If navigation is needed, update the last_run_version file NOW
        if do_navigate_on_startup:
            logger.debug("DEBUG __init__: Writing current version to last_run_version.txt because navigation flag is set.")
            self._write_last_run_version(last_run_version_file, self.current_version_str)
            
        # --- Exiting MainController __init__ --- 
        logger.info("--- Exiting MainController __init__ --- ")

    def show_welcome_page(self):
        """Crée et affiche la WelcomeWindow, et lance la vérif MàJ."""
        if self.welcome_window is None:
            app_name = CONFIG.get('APP_NAME', 'MonApp')
            self.welcome_window = WelcomeWindow(self, app_name, self.current_version_str)
            # --- DÉFINIR L'ICÔNE DE LA FENÊTRE DE BIENVENUE ---
            try:
                icon_path = get_resource_path("resources/images/logo-gdj.ico")
                if os.path.exists(icon_path):
                    self.welcome_window.setWindowIcon(QIcon(icon_path))
                else:
                    logger.warning(f"Avertissement: Icône de fenêtre non trouvée à {icon_path}")
            except Exception as e:
                logger.error(f"Erreur lors de la définition de l'icône pour WelcomeWindow: {e}", exc_info=True)
        
        self.welcome_window.show()
        logger.debug("DEBUG show_welcome_page: WelcomeWindow shown.")

        # --- MODIFICATION : Appeler la vérification SEULEMENT si pas déjà faite --- 
        if not self._startup_update_check_done:
             logger.debug("DEBUG show_welcome_page: Performing startup update check (first time)...")
             self._perform_startup_update_check()
             self._startup_update_check_done = True # Marquer comme fait
        else:
             logger.debug("DEBUG show_welcome_page: Startup update check already performed.")
        # --------------------------------------------------------------------

        # --- Gestion de la navigation vers les notes (reste pareil) ---
        if self.navigate_to_notes_after_welcome:
            logger.debug("DEBUG show_welcome_page: Flag is True, attempting navigation to 'A Propos' section...")
            try:
                # Assume welcome_window has this method
                self.welcome_window.navigate_to_section("A Propos") 
                logger.debug("DEBUG show_welcome_page: Called welcome_window.navigate_to_section('A Propos').")
                # The WelcomeWindow logic should handle activating the correct sub-tab 
                # and resetting the flag self.navigate_to_notes_after_welcome to False.
            except AttributeError:
                logger.error("ERROR show_welcome_page: WelcomeWindow does not have method 'navigate_to_section'.")
            except Exception as e:
                 logger.error(f"ERROR show_welcome_page: Exception during navigation call: {e}", exc_info=True)
        else:
             logger.debug("DEBUG show_welcome_page: Flag is False, no automatic navigation needed.")

    def _ensure_main_window_exists(self):
        """Crée la MainWindow si elle n'existe pas et établit les connexions."""
        logger.debug(">>> Entering _ensure_main_window_exists method...")
        logger.debug(f"--- Checking if self.main_window is None (Current value: {self.main_window is None})...")
        if self.main_window is None:
            logger.debug("--- Condition self.main_window is None PASSED. Attempting to create MainWindow instance...")
            try:
                # --- AJOUT TRY/EXCEPT ET LOGGING ---
                logger.debug("--- BEFORE MainWindow() instantiation ---")
                # --- Import local pour être sûr (peut-être redondant mais sûr) ---
                from ui.main_window import MainWindow
                self.main_window = MainWindow() # <--- Potential failure point
                logger.debug(f"--- AFTER MainWindow() instantiation. self.main_window is None: {self.main_window is None} ---")
                # ------------------------------------

                # --- DÉFINIR LA RÉFÉRENCE DU MainController DANS MainWindow ---
                # (Seulement si l'instantiation a réussi)
                logger.debug("--- Calling main_window.set_main_controller(self) ---")
                self.main_window.set_main_controller(self)
                # ------------------------------------------------------------

                # --- Définir l'icône de la fenêtre principale ---
                try:
                    icon_path = get_resource_path("resources/images/logo-gdj.ico")
                    if os.path.exists(icon_path):
                        self.main_window.setWindowIcon(QIcon(icon_path))
                    else:
                         logger.warning(f"Avertissement: Icône de fenêtre non trouvée à {icon_path}")
                except Exception as e_icon:
                     logger.error(f"Erreur lors de la définition de l'icône pour MainWindow: {e_icon}", exc_info=True)

                # Connecter les actions du menu de la MainWindow au contrôleur
                logger.debug("--- Connecting MainWindow menu actions ---")
                self.main_window.action_new.triggered.connect(self.create_new_document_from_menu)
                self.main_window.action_open.triggered.connect(self.open_document_from_menu)
                self.main_window.action_close.triggered.connect(self.close_current_document)
                try:
                    self.main_window.actionAfficherNotesVersion.triggered.connect(self.show_release_notes_dialog)
                except AttributeError:
                    logger.warning("Avertissement : L'action 'actionAfficherNotesVersion' n'a pas été trouvée dans l'UI.")
                logger.debug("--- MainWindow menu actions connected ---")

            except Exception as e_init:
                # --- CAPTURER L'ERREUR D'INITIALISATION ---
                logger.critical(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                logger.critical(f"CRITICAL ERROR: Exception during MainWindow instantiation: {e_init}")
                import traceback
                traceback.print_exc() # Afficher la trace complète de l'erreur
                logger.critical(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                # S'assurer que main_window reste None en cas d'échec
                self.main_window = None
            # --- FIN AJOUT ---

        # On continue seulement si main_window a été créé avec succès
        if self.main_window:
            # Fermer la fenêtre de bienvenue si elle est ouverte
            if self.welcome_window and self.welcome_window.isVisible():
                 logger.debug("--- Closing WelcomeWindow as MainWindow is ensured ---")
                 self.welcome_window.close()

            # Afficher la fenêtre principale si elle était cachée
            if not self.main_window.isVisible():
                 logger.debug("--- Showing MainWindow as it was not visible ---")
                 self.main_window.show()
        else:
             logger.debug("--- MainWindow is still None after creation attempt. Cannot proceed. --- ")

        logger.debug(f"--- Final check before exiting _ensure_main_window_exists. self.main_window is None: {self.main_window is None} ---")
        logger.debug("<<< Exiting _ensure_main_window_exists method...")

    def _read_version_file(self, file_path):
        """ Lit un fichier de version (reçoit le chemin complet). """
        if not os.path.exists(file_path):
            logger.warning(f"Fichier version non trouvé: {file_path}")
            return "0.0.0" # Version par défaut si non trouvé
        config = configparser.ConfigParser()
        try:
            config.read(file_path, encoding="utf-8")
            return config.get("Version", "value").strip()
        except Exception as e:
            logger.error(f"Erreur lecture {file_path}: {e}")
            return "0.0.0"

    def _write_last_run_version(self, file_path, current_version):
        """ Écrit dans un fichier de version (reçoit le chemin complet). """
        config = configparser.ConfigParser()
        config["Version"] = {"value": current_version}
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True) # Crée le dossier data si besoin
            with open(file_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            logger.debug(f"Version {current_version} écrite dans {file_path}")
        except Exception as e:
            logger.error(f"Erreur écriture {file_path}: {e}")

    def show_release_notes_dialog(self, auto_update_context=False):
        """ Affiche la boîte de dialogue modale avec les notes de version (pour action manuelle). """
        # Ne pas appeler ensure_main_window si c'est le contexte auto (géré par check_...)
        if not auto_update_context:
             self._ensure_main_window_exists()
             logger.debug("Affichage manuel des notes de version...")
        else:
             # Normalement, on ne devrait plus arriver ici dans le contexte auto
             logger.warning("show_release_notes_dialog appelée en contexte auto ?")
             return 

        notes_content = "Notes de version non trouvées."
        try:
            with open(self.release_notes_file, 'r', encoding='utf-8') as f:
                notes_content = f.read()
            # Ajouter le titre dynamiquement si lu depuis le fichier
            # (Le fichier lui-même n'a plus de v spécifiques dans le titre)
            notes_content = f"# Notes de version - v{self.current_version_str}\n\n{notes_content}"
        except FileNotFoundError:
            logger.warning(f"Erreur: {self.release_notes_file} non trouvé.")
            notes_content = f"# Notes de version - v{self.current_version_str}\n\nErreur : Fichier {os.path.basename(self.release_notes_file)} introuvable."
        except Exception as e:
            logger.error(f"Erreur lecture {self.release_notes_file}: {e}")
            notes_content = f"# Notes de version - v{self.current_version_str}\n\nErreur lors de la lecture des notes de version: {e}"

        dialog = ReleaseNotesDialog(self.current_version_str, notes_content, parent=self.main_window)
        dialog.exec_()

    def create_new_document(self):
        """Action appelée par le bouton 'Nouveau' de WelcomeWindow."""
        self._ensure_main_window_exists()
        logger.warning("Fonctionnalité 'Nouveau Document' (via WelcomeWindow) désactivée car NewDocumentDialog est supprimé.")
        pass # Ne fait rien pour l'instant

    def open_document(self):
        """Action appelée par le bouton 'Ouvrir' de WelcomeWindow."""
        self._ensure_main_window_exists()
        # Logique pour ouvrir un fichier via QFileDialog
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self.main_window, 
                                                  "Ouvrir un document GDJ", "", 
                                                  "GDJ Documents (*.gdj);;Tous les fichiers (*.*)", options=options)
        if filePath:
            logger.debug(f"Ouverture du document: {filePath}")
            # Ici, il faudrait charger le document depuis le fichier
            # Pour l'instant, on simule comme avant
            self._open_and_add_document_tab(f"Doc: {os.path.basename(filePath)}", None) # Passe le chemin ou titre
            
    def open_specific_document(self, path):
        """Action appelée par double-clic sur un item récent dans WelcomeWindow."""
        self._ensure_main_window_exists()
        logger.debug(f"Ouverture du document spécifique: {path}")
        # Ici, il faudrait charger le document depuis le `path`
        # Simulé pour l'instant
        self._open_and_add_document_tab(f"Doc: {os.path.basename(path)}", None) 
        
    def create_new_document_from_menu(self):
        """Action appelée par le menu Fichier > Nouveau."""
        # Pas besoin d'appeler _ensure_main_window_exists ici car le menu n'est visible
        # que si la fenêtre principale existe déjà.
        logger.warning("Fonctionnalité 'Nouveau Document' (via Menu) désactivée car NewDocumentDialog est supprimé.")
        pass # Ne fait rien pour l'instant
            
    def open_document_from_menu(self):
        """Action appelée par le menu Fichier > Ouvrir."""
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self.main_window, "Ouvrir un document GDJ", "", "GDJ Documents (*.gdj);;Tous les fichiers (*.*)", options=options)
        if filePath:
            logger.debug(f"Ouverture du document (menu): {filePath}")
            self._open_and_add_document_tab(f"Doc: {os.path.basename(filePath)}", None)

    def _create_and_add_document_tab(self, doc_type, data):
        """Factorisation de la logique de création d'un nouveau document et ajout d'onglet."""
        new_doc = None
        try:
            # --- CORRIGER LES COMPARAISONS DE STRING --- 
            if doc_type == "Rapport de depense": # <- Correspondre au log
                logger.debug("Importing RapportDepense...")
                # --- CORRECTION IMPORT --- 
                from models.documents.rapport_depense.rapport_depense import RapportDepense
                # -------------------------
                logger.debug("Creating RapportDepense instance...")
                new_doc = RapportDepense(title=f"{doc_type} - {data.get('nom')}", depenses=[data.get('montant')])
            elif doc_type == "Écriture Comptable":
                from models.documents.ecriture_comptable import EcritureComptable
                new_doc = EcritureComptable(title=f"{doc_type} - {data.get('titre')}", operations=[data.get('operation')])
            elif doc_type == "Rapport Temps Sup":
                from models.documents.rapport_temps_sup import RapportTempsSup
                new_doc = RapportTempsSup(title=f"{doc_type} - {data.get('titre')}", heures=float(data.get('heures', 0)))
            elif doc_type == "CSA":
                from models.documents.csa import CSA
                new_doc = CSA(title=f"{doc_type} - {data.get('titre')}", details=data.get('details'))
            elif doc_type == "Système Vision":
                from models.documents.systeme_vision import SystemeVision
                new_doc = SystemeVision(title=f"{doc_type} - {data.get('titre')}", vision_params=data.get('vision_params'))
            elif doc_type == "Robot":
                from models.documents.robot import Robot
                new_doc = Robot(title=f"{doc_type} - {data.get('titre')}", config=data.get('config'))
            else: # Ajout d'un cas par défaut ou log
                logger.debug(f"Type de document inconnu ou non géré: {doc_type}")
                return
            
            if new_doc:
                doc_page = DocumentPage(title=new_doc.title, document=new_doc)
                idx = self.main_window.tab_widget.addTab(doc_page, doc_page.title)
                self.main_window.tab_widget.setCurrentIndex(idx)
                self.documents[new_doc.title] = doc_page
        except Exception as e:
            logger.error(f"Erreur lors de la création du document: {e}")

    def _open_and_add_document_tab(self, title, document_data):
        """Factorisation de la logique d'ouverture d'un document et ajout d'onglet."""
        # Ici, il faudrait implémenter la logique de chargement du document
        # à partir de document_data (qui pourrait être un chemin de fichier)
        # Pour l'instant, on crée une page vide avec le titre
        doc_page = DocumentPage(title=title, document=None) # Passer les données chargées ici
        idx = self.main_window.tab_widget.addTab(doc_page, doc_page.title)
        self.main_window.tab_widget.setCurrentIndex(idx)
        self.documents[title] = doc_page # Utiliser un identifiant unique si le titre n'est pas fiable

    def close_current_document(self):
        """Ferme l'onglet de document actif (inchangé, mais s'assure que main_window existe)."""
        if not self.main_window or self.main_window.tab_widget.count() == 0: # Vérif si fenêtre/onglets existent
            return
        idx = self.main_window.tab_widget.currentIndex()
        widget = self.main_window.tab_widget.widget(idx)
        if widget: # S'assurer qu'on a bien récupéré un widget
            title_to_remove = widget.title # Utiliser le titre stocké dans le widget si possible
            self.main_window.tab_widget.removeTab(idx)
            if title_to_remove in self.documents:
                del self.documents[title_to_remove]

    def navigate_to_about_page(self):
        """S'assure que la page 'À Propos' existe et la montre."""
        self._ensure_main_window_exists() # Assure que la MainWindow est prête
        
        if self.about_page is None:
            logger.debug("Création de la page À Propos et de son contrôleur...")
            self.about_page = AboutPage()
            # Créer et garder la référence au contrôleur
            self.about_controller_instance = AboutController(self.about_page) 
            
            # Ajouter l'onglet s'il n'existe pas déjà (double sécurité)
            if self.main_window.tab_widget.indexOf(self.about_page) == -1:
                 self.main_window.tab_widget.addTab(self.about_page, "À Propos")
            else:
                 logger.warning("Avertissement: La page À Propos existait déjà dans les onglets ?")
        
        # Sélectionner l'onglet 'À Propos'
        idx = self.main_window.tab_widget.indexOf(self.about_page)
        if idx != -1:
            self.main_window.tab_widget.setCurrentIndex(idx)
            logger.debug("Navigation vers l'onglet À Propos effectuée.")
        else:
            logger.error("Erreur: Impossible de trouver l'index de la page À Propos après création/vérification.")

    # --- NOUVELLE MÉTHODE POUR LA VÉRIFICATION AU DÉMARRAGE ---
    def _perform_startup_update_check(self):
        """Vérifie les MàJ au démarrage et planifie l'action si confirmée."""
        logger.info("Performing startup update check...")
        try:
            status, update_info = check_for_updates()
            logger.info(f"Startup update check status: {status}")
            if status == "USER_CONFIRMED_UPDATE":
                logger.info("User confirmed update from startup prompt. Scheduling navigation within WelcomeWindow...")
                self.pending_update_info = update_info
                # --- APPELER LA NOUVELLE MÉTHODE VIA QTIMER --- 
                QTimer.singleShot(0, self._navigate_welcome_to_settings_and_update)
            elif status == "UPDATE_DECLINED":
                 logger.info("Startup update declined by user.")
            elif update_info and not update_info.get('available') and status != "À jour":
                 logger.info(f"Startup update check notice: {status}") # Affiche les erreurs etc.

        except Exception as e:
            logger.error(f"Error during startup update check: {e}")
            if hasattr(self, 'pending_update_info'):
                 del self.pending_update_info

    # --- NOUVELLE MÉTHODE POUR GÉRER DANS WELCOMEWINDOW --- 
    def _navigate_welcome_to_settings_and_update(self):
        """Navigue vers les paramètres DANS WelcomeWindow et lance la MàJ."""
        logger.info("Navigating WelcomeWindow to settings and initiating update...")
        if hasattr(self, 'pending_update_info') and self.pending_update_info:
            update_info = self.pending_update_info.copy() # Prendre une copie
            if hasattr(self, 'pending_update_info'):
                del self.pending_update_info # Nettoyer

            if self.welcome_window:
                try:
                    # 1. Naviguer dans WelcomeWindow
                    logger.debug("Calling welcome_window.navigate_to_section('Paramètres')...")
                    # Assumons True pour succès, False/Exception pour échec
                    navigation_successful = self.welcome_window.navigate_to_section("Paramètres") 

                    if navigation_successful:
                         logger.debug("Navigation to WelcomeWindow settings section successful.")
                         # 2. Récupérer le SettingsController de WelcomeWindow
                         logger.debug("Getting SettingsController from WelcomeWindow...")
                         settings_controller = self.welcome_window.get_settings_controller()

                         if settings_controller:
                              logger.debug("Got SettingsController instance from WelcomeWindow.")
                              # 3. Lancer le téléchargement
                              logger.debug("Calling initiate_update_from_prompt on WelcomeWindow's SettingsController...")
                              settings_controller.initiate_update_from_prompt(update_info)
                         else:
                              logger.error("ERROR: welcome_window.get_settings_controller() returned None.")
                    else:
                         logger.error("ERROR: welcome_window.navigate_to_section('Paramètres') failed or returned False.")

                except AttributeError as ae:
                     logger.error(f"ERROR: WelcomeWindow is missing a required method (navigate_to_section or get_settings_controller): {ae}")
                except Exception as e:
                     logger.error(f"ERROR: An unexpected error occurred during WelcomeWindow navigation/update initiation: {e}", exc_info=True)
            else:
                logger.error("ERROR: WelcomeWindow instance is None. Cannot navigate.")
        else:
            logger.warning("Warning: _navigate_welcome_to_settings_and_update called but no pending update info found.")

    # --- NOUVELLE MÉTHODE POUR APPLIQUER LE THÈME ---
    def apply_theme(self, theme_name):
        """Recharge et applique la feuille de style globale et met à jour le thème des icônes."""
        logger.info(f"Attempting to apply theme: '{theme_name}'")
        # --- D'abord appliquer le style QSS --- 
        style_applied = False
        try:
            qss_files = ["resources/styles/global.qss", "resources/styles/frame.qss"]
            combined_stylesheet = load_stylesheet(qss_files, theme_name=theme_name)
            app_instance = QApplication.instance()
            if app_instance:
                app_instance.setStyleSheet(combined_stylesheet)
                logger.info(f"Theme '{theme_name}' style applied successfully.")
                style_applied = True # Marquer le succès
            else:
                logger.error("Could not get QApplication instance to apply theme style.")
        except Exception as e:
            logger.error(f"Error applying theme style '{theme_name}': {e}", exc_info=True)
            
        # --- Ensuite, mettre à jour le thème des icônes (même si le style a échoué?) ---
        # Ou seulement si style_applied est True ? Décision: Mettre à jour quand même
        # car le thème logique a changé.
        try:
            from utils import icon_loader # S'assurer de l'import localement?
            icon_loader.set_active_theme(theme_name)
            logger.debug(f"Icon theme set to '{theme_name}'")
        except Exception as e_icon:
             logger.error(f"Error setting icon theme for '{theme_name}': {e_icon}", exc_info=True)

    # --- FIN NOUVELLE MÉTHODE ---

    def _ensure_main_window_exists(self):
        """Crée la MainWindow si elle n'existe pas et établit les connexions."""
        logger.debug(">>> Entering _ensure_main_window_exists method...")
        logger.debug(f"--- Checking if self.main_window is None (Current value: {self.main_window is None})...")
        if self.main_window is None:
            logger.debug("--- Condition self.main_window is None PASSED. Attempting to create MainWindow instance...")
            try:
                # --- AJOUT TRY/EXCEPT ET LOGGING ---
                logger.debug("--- BEFORE MainWindow() instantiation ---")
                # --- Import local pour être sûr (peut-être redondant mais sûr) ---
                from ui.main_window import MainWindow
                self.main_window = MainWindow() # <--- Potential failure point
                logger.debug(f"--- AFTER MainWindow() instantiation. self.main_window is None: {self.main_window is None} ---")
                # ------------------------------------

                # --- DÉFINIR LA RÉFÉRENCE DU MainController DANS MainWindow ---
                # (Seulement si l'instantiation a réussi)
                logger.debug("--- Calling main_window.set_main_controller(self) ---")
                self.main_window.set_main_controller(self)
                # ------------------------------------------------------------

                # --- Définir l'icône de la fenêtre principale ---
                try:
                    icon_path = get_resource_path("resources/images/logo-gdj.ico")
                    if os.path.exists(icon_path):
                        self.main_window.setWindowIcon(QIcon(icon_path))
                    else:
                         logger.warning(f"Avertissement: Icône de fenêtre non trouvée à {icon_path}")
                except Exception as e_icon:
                     logger.error(f"Erreur lors de la définition de l'icône pour MainWindow: {e_icon}", exc_info=True)

                # Connecter les actions du menu de la MainWindow au contrôleur
                logger.debug("--- Connecting MainWindow menu actions ---")
                self.main_window.action_new.triggered.connect(self.create_new_document_from_menu)
                self.main_window.action_open.triggered.connect(self.open_document_from_menu)
                self.main_window.action_close.triggered.connect(self.close_current_document)
                try:
                    self.main_window.actionAfficherNotesVersion.triggered.connect(self.show_release_notes_dialog)
                except AttributeError:
                    logger.warning("Avertissement : L'action 'actionAfficherNotesVersion' n'a pas été trouvée dans l'UI.")
                logger.debug("--- MainWindow menu actions connected ---")

            except Exception as e_init:
                # --- CAPTURER L'ERREUR D'INITIALISATION ---
                logger.critical(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                logger.critical(f"CRITICAL ERROR: Exception during MainWindow instantiation: {e_init}")
                import traceback
                traceback.print_exc() # Afficher la trace complète de l'erreur
                logger.critical(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                # S'assurer que main_window reste None en cas d'échec
                self.main_window = None
            # --- FIN AJOUT ---

        # On continue seulement si main_window a été créé avec succès
        if self.main_window:
            # Fermer la fenêtre de bienvenue si elle est ouverte
            if self.welcome_window and self.welcome_window.isVisible():
                 logger.debug("--- Closing WelcomeWindow as MainWindow is ensured ---")
                 self.welcome_window.close()

            # Afficher la fenêtre principale si elle était cachée
            if not self.main_window.isVisible():
                 logger.debug("--- Showing MainWindow as it was not visible ---")
                 self.main_window.show()
        else:
             logger.debug("--- MainWindow is still None after creation attempt. Cannot proceed. --- ")

        logger.debug(f"--- Final check before exiting _ensure_main_window_exists. self.main_window is None: {self.main_window is None} ---")
        logger.debug("<<< Exiting _ensure_main_window_exists method...")

    # --- NOUVELLE MÉTHODE pour afficher la DocumentWindow --- 
    def show_new_document_window(self, doc_type: str, data: dict):
        """Crée et affiche une nouvelle instance de DocumentWindow avec les données spécifiées."""
        logger.info(f"MainController: Création et affichage de DocumentWindow pour type='{doc_type}'...")
        
        # --- Fermer la fenêtre de bienvenue si elle est ouverte --- 
        if self.welcome_window and self.welcome_window.isVisible():
            logger.debug("MainController: Fermeture de WelcomeWindow avant d'ouvrir DocumentWindow.")
            self.welcome_window.close()
        # --------------------------------------------------------
        
        try:
            # Créer une nouvelle instance avec les données fournies
            # Utiliser une variable locale pour éviter d'écraser une éventuelle instance précédente immédiatement
            # --- MODIFICATION: Passer les arguments à DocumentWindow --- 
            new_window = DocumentWindow(main_controller=self, initial_doc_type=doc_type, initial_doc_data=data)
            # --- Stocker la référence (optionnel, si on ne veut qu'une seule DocumentWindow) --- 
            self.new_doc_window = new_window # Mettre à jour la référence
            # ----------------------------------------------------------------------------------
            
            # Afficher la fenêtre maximisée
            new_window.showMaximized()
            # Optionnel: la rendre active
            new_window.activateWindow()
            new_window.raise_()
            logger.info("MainController: DocumentWindow affichée.")
            
            # --- Connexion des signaux (reste pareil, utilise self.new_doc_window) --- 
            try:
                # --- RÉINTRODUIRE LA CONNEXION DU SIGNAL --- 
                if hasattr(self.new_doc_window, 'request_main_action'):
                    self.new_doc_window.request_main_action.connect(self.handle_main_action_request)
                    logger.info("MainController: Connecté new_doc_window.request_main_action -> handle_main_action_request")
                else:
                    logger.warning("MainController: new_doc_window n'a pas le signal 'request_main_action'.")
                # ---------------------------------------------
                # --- Connecter le signal des paramètres (inchangé) --- 
                if hasattr(self.new_doc_window.title_bar, 'settings_requested'):
                    self.new_doc_window.title_bar.settings_requested.connect(self.show_settings_window)
                    logger.info("MainController: Signal settings_requested connecté.")
                else:
                     logger.warning("MainController: title_bar n'a pas le signal 'settings_requested'.")
            except AttributeError as e_connect:
                 logger.error(f"ERREUR connexion signal(s) DocumentWindow: {e_connect}")
            # ----------------------------------------------------------------------
        except Exception as e:
            logger.error(f"ERREUR lors de la création/affichage de DocumentWindow: {e}")
            import traceback
            traceback.print_exc()
    # --------------------------------------------------------

    # --- AJOUT: Méthode pour afficher la fenêtre des paramètres ---
    def show_settings_window(self):
        """Crée (si nécessaire) et affiche la fenêtre des paramètres."""
        logger.info("MainController: Demande d'affichage de SettingsWindow...")
        if self.settings_window is None or not self.settings_window.isVisible():
            try:
                # Créer une nouvelle instance si elle n'existe pas ou a été fermée
                # --- Passer self (main_controller) et la version --- 
                self.settings_window = SettingsWindow(main_controller=self, version_str=self.current_version_str)
                # ----------------------------------------------------
                # Optionnel: Centrer la fenêtre ou positionner par rapport à une autre
                # self.settings_window.show() # Afficher normalement
                # Ou centrer sur l'écran principal
                screen_geometry = QCoreApplication.instance().primaryScreen().availableGeometry()
                window_size = self.settings_window.size()
                self.settings_window.move(
                    (screen_geometry.width() - window_size.width()) // 2,
                    (screen_geometry.height() - window_size.height()) // 2
                )
                self.settings_window.show()
                self.settings_window.activateWindow()
                self.settings_window.raise_()
                logger.info("MainController: SettingsWindow créée et affichée.")
            except Exception as e:
                logger.error(f"ERREUR lors de la création/affichage de SettingsWindow: {e}")
                self.settings_window = None # Assurer que la référence est nulle en cas d'erreur
        else:
            # Si la fenêtre existe déjà et est visible, la mettre au premier plan
            logger.debug("MainController: SettingsWindow existe déjà, activation...")
            self.settings_window.activateWindow()
            self.settings_window.raise_()
    # -------------------------------------------------------------

    # --- AJOUT SLOT POUR GÉRER LES ACTIONS DE DocumentWindow --- 
    @pyqtSlot(str)
    def handle_main_action_request(self, action_name):
        logger.info(f"MainController: Reçu request_main_action avec action: '{action_name}'")
        if action_name == 'new_document':
            logger.info("Action 'new_document' reçue, appel de show_type_selection_window...")
            self.show_type_selection_window()
        elif action_name == 'settings': # Exemple si on gérait les paramètres aussi via ce signal
             logger.info("Action 'settings' reçue, appel de show_settings_window...")
             self.show_settings_window() # Appeler la méthode existante
        else:
             logger.warning(f"Action inconnue reçue via request_main_action: {action_name}")
    # ------------------------------------------------------

    # --- AJOUT: Méthode pour afficher la fenêtre de sélection de type --- 
    def show_type_selection_window(self):
        """Crée et affiche la fenêtre TypeSelectionWindow."""
        # --- Vérifier/Importer TypeSelectionWindow --- 
        try:
            from windows.type_selection_window import TypeSelectionWindow
        except ImportError:
            logger.error("Impossible d'importer TypeSelectionWindow.")
            QMessageBox.critical(None, "Erreur Interne", "Composant manquant: TypeSelectionWindow.")
            return
            
        logger.info("MainController: Création et affichage de TypeSelectionWindow...")
        try:
            # --- Créer une instance (garder référence pour la connexion/gestion?) --- 
            # Pour l'instant, on crée une nouvelle instance à chaque fois.
            # Si on veut une seule instance, ajouter logique avec self.type_selection_win
            self.type_selection_window_instance = TypeSelectionWindow(preferences_controller=self.preferences_controller)
            
            # --- Connecter le signal de création --- 
            if hasattr(self.type_selection_window_instance, 'document_creation_requested'):
                 self.type_selection_window_instance.document_creation_requested.connect(self._handle_creation_from_selection_window)
                 logger.info("Connecté TypeSelectionWindow.document_creation_requested -> _handle_creation_from_selection_window")
            else:
                 logger.warning("TypeSelectionWindow n'a pas de signal 'document_creation_requested'.")
                 
            self.type_selection_window_instance.show()
            self.type_selection_window_instance.activateWindow()
            self.type_selection_window_instance.raise_()
            logger.info("TypeSelectionWindow affichée.")
        except Exception as e_tsw:
             logger.error(f"Erreur lors de la création/affichage de TypeSelectionWindow: {e_tsw}", exc_info=True)
             QMessageBox.critical(None, "Erreur", f"Impossible d'ouvrir la fenêtre de sélection de type.\n{e_tsw}")
    # ---------------------------------------------------------------------

    # --- AJOUT: Slot pour gérer la création depuis TypeSelectionWindow --- 
    @pyqtSlot(str, dict)
    def _handle_creation_from_selection_window(self, doc_type: str, data: dict):
        logger.info(f"MainController: Reçu demande de création depuis TypeSelectionWindow: Type='{doc_type}'")
        # Fermer la fenêtre de sélection AVANT d'ouvrir la nouvelle DocumentWindow
        if hasattr(self, 'type_selection_window_instance') and self.type_selection_window_instance:
             logger.info("Fermeture de TypeSelectionWindow...")
             self.type_selection_window_instance.close()
             # Optionnel: Supprimer la référence pour permettre une nouvelle instance plus tard
             # del self.type_selection_window_instance 
             
        # Appeler la méthode qui crée et affiche DocumentWindow
        self.show_new_document_window(doc_type, data)
    # -------------------------------------------------------------------

# --- SECTION PRINCIPALE (FIN DU FICHIER) --- 
def main():
    pass # <<< AJOUT D\'UN BLOC INDENTÉ POUR CORRIGER L\'ERREUR
    # ... le reste du code original de main() devrait être ici ...
