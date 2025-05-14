from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QMessageBox, QFileDialog, QWidget
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSlot, QCoreApplication
# --- AJOUT DE L'IMPORT QIcon ---
from PyQt5.QtGui import QIcon
# --- AJOUT DE L'IMPORT Optional ---
from typing import Optional
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
import functools # <<< AJOUT IMPORT
logger = logging.getLogger('GDJ_App')

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path, get_user_data_path

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
# --- AJOUT IMPORT PreferencesController ---
from controllers.preferences.preferences_controller import PreferencesController
# ------------------------------------------
# --- AJOUTS POUR LA SAUVEGARDE ---
import json
import zipfile
import tempfile
import shutil
from pathlib import Path
# QFileDialog est déjà importé plus haut
# os est déjà importé plus haut
# RapportDepense sera importé dynamiquement ou via une vérification de type
from models.documents.rapport_depense import RapportDepense # Pour vérification de type
# ---------------------------------
from datetime import date # Ajout import date pour _load_and_display_rdj_document
# ---------------------------------

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
        # --- Initialisation PreferencesController ---
        try:
            self.preferences_controller = PreferencesController(main_controller=self)
            logger.info("MainController: PreferencesController instance created.")
        except ImportError as e_imp:
            logger.critical(f"CRITICAL ERROR: Cannot import PreferencesController: {e_imp}")
            self.preferences_controller = None
        except Exception as e_prefs_init:
            logger.critical(f"CRITICAL ERROR: Cannot initialize PreferencesController: {e_prefs_init}")
            self.preferences_controller = None
        # ------------------------------------------------------
        self.navigate_to_notes_after_welcome = False 
        self._startup_update_check_done = False
        # --- MODIFICATION: Utiliser une liste pour les fenêtres de documents --- 
        # self.new_doc_window = None # ANCIEN
        self.open_document_windows = [] # NOUVEAU: Liste pour stocker les fenêtres ouvertes
        # --------------------------------------------------------------------
        self.settings_window = None # <<< AJOUT: Référence à SettingsWindow
        self.type_selection_window_instance = None # Pour garder une référence si besoin
        self.doc_creation_source_window = None # << AJOUT pour la fenêtre source
        # --- AJOUT FLAG ---
        self._expecting_welcome_after_close = False
        # ------------------

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
        logger.critical(">>> ENTERING show_welcome_page <<< START") # Log critique entrée
        
        if self.welcome_window is None:
            logger.info("show_welcome_page: self.welcome_window is None, creating new instance...") # Log info
            app_name = CONFIG.get('APP_NAME', 'MonApp')
            try:
                self.welcome_window = WelcomeWindow(self, app_name, self.current_version_str)
                logger.info("show_welcome_page: New WelcomeWindow instance created.") # Log info
                # --- DÉFINIR L'ICÔNE DE LA FENÊTRE DE BIENVENUE ---
                try:
                    icon_path = get_resource_path("resources/images/logo-gdj.ico")
                    if os.path.exists(icon_path):
                        self.welcome_window.setWindowIcon(QIcon(icon_path))
                    else:
                        logger.warning(f"Avertissement: Icône de fenêtre non trouvée à {icon_path}")
                except Exception as e:
                    logger.error(f"Erreur lors de la définition de l'icône pour WelcomeWindow: {e}", exc_info=True)
            except Exception as e_create_welcome:
                logger.critical(f"CRITICAL ERROR creating WelcomeWindow instance: {e_create_welcome}", exc_info=True)
                # Peut-être afficher une QMessageBox ici?
                logger.critical("<<< EXITING show_welcome_page DUE TO CREATION ERROR <<<")
                return # Sortir si la création échoue
        else:
             logger.info("show_welcome_page: self.welcome_window exists, attempting to show it.") # Log info

        # Tentative d'affichage (peut échouer si l'objet C++ est détruit)
        try:
            self.welcome_window.show()
            self.welcome_window.raise_()
            self.welcome_window.activateWindow()
            logger.debug("DEBUG show_welcome_page: WelcomeWindow shown, raised, and activated.")
            # --- AJOUT POUR LOGGING GÉOMÉTRIE ---
            if self.welcome_window:
                logger.debug(f"WelcomeWindow geometry: {self.welcome_window.geometry()}")
                logger.debug(f"WelcomeWindow isVisible: {self.welcome_window.isVisible()}")
                logger.debug(f"WelcomeWindow isMinimized: {self.welcome_window.isMinimized()}")
                logger.debug(f"WelcomeWindow windowState: {self.welcome_window.windowState()}")
            # ------------------------------------

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

            # --- RÉTABLIR LA FERMETURE AUTOMATIQUE DE L'APPLICATION ---
            app = QApplication.instance()
            if app:
                logger.info("MainController: Rétablissement de app.setQuitOnLastWindowClosed(True) après affichage WelcomeWindow.")
                app.setQuitOnLastWindowClosed(True)
            # -----------------------------------------------------------

            logger.critical("<<< EXITING show_welcome_page <<< END") # Log critique sortie

        except RuntimeError as e_show:
             logger.critical(f"RUNTIME ERROR calling show() on WelcomeWindow: {e_show}. Instance might be deleted.", exc_info=True)
             logger.info("Attempting to recreate WelcomeWindow because show() failed...")
             self.welcome_window = None
             # --- ASSURER LE RÉTABLISSEMENT MÊME EN CAS D'ERREUR ---
             app = QApplication.instance()
             if app:
                 logger.warning("MainController: Rétablissement de app.setQuitOnLastWindowClosed(True) après échec affichage WelcomeWindow (RuntimeError).")
                 app.setQuitOnLastWindowClosed(True)
             # ------------------------------------------------------
             logger.critical("<<< EXITING show_welcome_page DUE TO SHOW() ERROR <<<")
             return
        except Exception as e_show_other:
             logger.critical(f"UNEXPECTED ERROR calling show() on WelcomeWindow: {e_show_other}", exc_info=True)
             # --- ASSURER LE RÉTABLISSEMENT MÊME EN CAS D'ERREUR ---
             app = QApplication.instance()
             if app:
                 logger.warning("MainController: Rétablissement de app.setQuitOnLastWindowClosed(True) après échec affichage WelcomeWindow (Exception).")
                 app.setQuitOnLastWindowClosed(True)
             # ------------------------------------------------------
             logger.critical("<<< EXITING show_welcome_page DUE TO UNEXPECTED SHOW() ERROR <<<")
             return

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
                 self.welcome_window = None

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

    def open_document(self, initiated_by_window: Optional[QWidget] = None):
        logger.info(f"MainController: open_document appelée. Initiée par: {initiated_by_window}")

        options = QFileDialog.Options()
        # Parent pour le dialogue : la fenêtre initiatrice si c'est une QWidget, sinon fallback.
        parent_for_file_dialog = initiated_by_window if isinstance(initiated_by_window, QWidget) else (self._get_active_document_window() or self.welcome_window or None)

        file_path, _ = QFileDialog.getOpenFileName(
            parent_for_file_dialog,
            "Ouvrir un Rapport de Dépenses Jacmar",
            os.path.expanduser("~"), # Répertoire initial
            "Rapports de Dépenses Jacmar (*.rdj);;Tous les fichiers (*.*)",
            options=options
        )

        if file_path:
            logger.info(f"Fichier .rdj sélectionné: {file_path}")
            
            target_for_new_tab = None
            if isinstance(initiated_by_window, DocumentWindow) and initiated_by_window.isVisible() and initiated_by_window in self.open_document_windows:
                target_for_new_tab = initiated_by_window

            if target_for_new_tab:
                logger.info(f"DocumentWindow source ({target_for_new_tab}) détectée pour décision onglet/fenêtre.")
                msg_box = QMessageBox(target_for_new_tab) # Parent pour centrage
                msg_box.setWindowTitle("Ouvrir le Document")
                msg_box.setText(f"Ouvrir: {Path(file_path).name}")
                msg_box.setInformativeText("Où souhaitez-vous ouvrir ce document ?")
                btn_new_tab = msg_box.addButton("Nouvel Onglet", QMessageBox.AcceptRole)
                btn_new_window = msg_box.addButton("Nouvelle Fenêtre", QMessageBox.DestructiveRole)
                btn_cancel = msg_box.addButton("Annuler", QMessageBox.RejectRole)
                msg_box.setDefaultButton(btn_new_tab)
                
                msg_box.exec_()

                if msg_box.clickedButton() == btn_new_tab:
                    logger.info("Utilisateur a choisi d'ouvrir dans un NOUVEL ONGLET.")
                    self._load_and_display_rdj_document(file_path, target_window=target_for_new_tab)
                elif msg_box.clickedButton() == btn_new_window:
                    logger.info("Utilisateur a choisi d'ouvrir dans une NOUVELLE FENÊTRE.")
                    self._load_and_display_rdj_document(file_path, target_window=None)
                elif msg_box.clickedButton() == btn_cancel:
                    logger.info("Ouverture de document annulée par l'utilisateur après sélection.")
                else:
                    logger.info("Dialogue de choix fermé sans sélection, annulation.")
            else:
                # Pas de DocumentWindow source valide (ex: depuis WelcomeWindow), ouvrir dans une nouvelle fenêtre directement.
                logger.info("Aucune DocumentWindow source valide pour décision onglet/fenêtre, ouverture dans une nouvelle fenêtre.")
                self._load_and_display_rdj_document(file_path, target_window=None)
        else:
            logger.info("Ouverture de fichier annulée par l'utilisateur (dialogue de fichier).")

    def open_specific_document(self, path):
        """Action appelée par double-clic sur un item récent dans WelcomeWindow.
           Charge directement le fichier .rdj spécifié.
        """
        # self._ensure_main_window_exists() # Pas besoin, _load_and_display_rdj_document s'en chargera si besoin
        logger.info(f"Ouverture du document spécifique (récent): {path}")
        if Path(path).exists() and path.lower().endswith('.rdj'):
            self._load_and_display_rdj_document(path)
        else:
            logger.error(f"Le chemin du document récent '{path}' n'existe pas ou n'est pas un .rdj.")
            QMessageBox.warning(None, "Erreur Fichier Récent", f"Impossible d'ouvrir le fichier récent:\n{path}\nIl n'existe peut-être plus ou n'est pas un fichier valide.")

    def create_new_document_from_menu(self):
        """Action appelée par le menu Fichier > Nouveau."""
        # Pas besoin d'appeler _ensure_main_window_exists ici car le menu n'est visible
        # que si la fenêtre principale existe déjà.
        logger.warning("Fonctionnalité 'Nouveau Document' (via Menu) désactivée car NewDocumentDialog est supprimé.")
        pass # Ne fait rien pour l'instant
            
    def open_document_from_menu(self):
        """Action appelée par le menu Fichier > Ouvrir d'une DocumentWindow."""
        logger.info("MainController: open_document_from_menu appelée.")
        active_doc_window = self._get_active_document_window()
        if not active_doc_window:
            logger.warning("open_document_from_menu: Aucune DocumentWindow active trouvée pour parenter QFileDialog. Utilisation de None.")
            # Si on arrive ici, c'est probablement une erreur de logique car le menu
            # ne devrait être accessible que depuis une DocumentWindow.
            # Cependant, pour la robustesse :
            # On pourrait appeler self.open_document() qui a une logique de fallback pour le parent.
            self.open_document() # Utilise la logique plus générique avec fallback de parent
            return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            active_doc_window, # Parent est la DocumentWindow active
            "Ouvrir un Rapport de Dépenses Jacmar", 
            os.path.expanduser("~"), 
            "Rapports de Dépenses Jacmar (*.rdj);;Tous les fichiers (*.*)", 
            options=options
        )
        
        if file_path:
            logger.info(f"Fichier .rdj sélectionné pour ouverture (via menu): {file_path}")
            self._load_and_display_rdj_document(file_path)
        else:
            logger.info("Ouverture de fichier (via menu) annulée par l'utilisateur.")

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
                 self.welcome_window = None

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
        """Crée et affiche une nouvelle instance de DocumentWindow, l'ajoute à la liste gérée."""
        logger.info(f"MainController: Création et affichage de DocumentWindow pour type='{doc_type}'...")
        
        # Masquer WelcomeWindow si elle est visible
        if self.welcome_window and self.welcome_window.isVisible():
            logger.debug("MainController: Masquage de WelcomeWindow avant d'ouvrir DocumentWindow.")
            self.welcome_window.hide() # Correct : hide()
            # Ligne self.welcome_window = None est supprimée ici : Correct

        try:
            new_window = DocumentWindow(main_controller=self, initial_doc_type=doc_type, initial_doc_data=data)
            
            # --- MODIFICATION: Ajouter à la liste --- 
            self.open_document_windows.append(new_window)
            logger.debug(f"Nouvelle DocumentWindow ajoutée à la liste. Nombre total: {len(self.open_document_windows)}")
            # --------------------------------------
            
            # --- Connexion du signal destroyed pour le nettoyage --- 
            # Utiliser functools.partial pour passer la référence de la fenêtre au slot
            new_window.destroyed.connect(functools.partial(self._handle_document_window_closed, new_window))
            logger.debug(f"Signal 'destroyed' de la nouvelle DocumentWindow connecté à _handle_document_window_closed.")
            # ------------------------------------------------------

            # Afficher la fenêtre maximisée
            new_window.showMaximized()
            new_window.activateWindow()
            new_window.raise_()
            logger.info("MainController: DocumentWindow affichée.")
            
            # --- Connexion des autres signaux (utilise new_window) --- 
            try:
                if hasattr(new_window, 'request_main_action'):
                    new_window.request_main_action.connect(self.handle_main_action_request)
                    logger.info("MainController: Connecté new_window.request_main_action -> handle_main_action_request")
                else:
                    logger.warning("MainController: new_window n'a pas le signal 'request_main_action'.")
                
                if hasattr(new_window.title_bar, 'settings_requested'):
                    new_window.title_bar.settings_requested.connect(self.show_settings_window)
                    logger.info("MainController: Signal settings_requested connecté.")
                else:
                     logger.warning("MainController: title_bar n'a pas le signal 'settings_requested'.")
            except AttributeError as e_connect:
                 logger.error(f"ERREUR connexion signal(s) DocumentWindow: {e_connect}")
            # ----------------------------------------------------------
        except Exception as e:
            logger.error(f"ERREUR lors de la création/affichage de DocumentWindow: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            # --- AJOUT: Essayer de retirer de la liste si l'ajout a eu lieu mais que l'affichage échoue --- 
            if 'new_window' in locals() and new_window in self.open_document_windows:
                 try:
                      self.open_document_windows.remove(new_window)
                      logger.debug("Fenêtre retirée de la liste suite à une erreur d'affichage.")
                 except ValueError:
                      pass # Ignore si déjà retirée (par exemple par le slot destroyed)
            # --------------------------------------------------------------------------------------------
    # --------------------------------------------------------

    # --- MÉTHODE MODIFIÉE --- 
    @pyqtSlot(QWidget)
    def _handle_document_window_closed(self, closed_window: QWidget):
        """Slot appelé quand une DocumentWindow est détruite (fermée). Retire la fenêtre de la liste.
        Si c'était la dernière fenêtre ET que la fermeture était due au dernier onglet, ré-affiche WelcomeWindow.
        """
        logger.info(f"Début _handle_document_window_closed pour: {closed_window}")
        window_was_in_list = False
        try:
            if closed_window in self.open_document_windows:
                self.open_document_windows.remove(closed_window)
                window_was_in_list = True
                logger.info(f"DocumentWindow retirée de la liste. Restantes: {len(self.open_document_windows)}")
            else:
                 logger.warning(f"Signal 'destroyed' reçu pour une DocumentWindow ({closed_window}) non trouvée lors de l'appel _handle_document_window_closed.")

            # --- LOGIQUE MODIFIÉE --- 
            if not self.open_document_windows: # Si la liste est maintenant vide
                should_show_welcome = self._expecting_welcome_after_close # Lire le flag
                self._expecting_welcome_after_close = False # Réinitialiser DANS TOUS LES CAS où la liste est vide
                
                if should_show_welcome:
                    logger.info("C'était la dernière DocumentWindow ET la fermeture était attendue (dernier onglet). Affichage WelcomeWindow...")
                    # --- APPEL DIRECT (sans QTimer) ---
                    self.show_welcome_page() 
                    # -----------------------------------
                else:
                     logger.info("C'était la dernière DocumentWindow, mais fermeture non attendue (probablement clic 'X'). L'application devrait quitter via QApplication.")
                     # Ne rien faire ici, laisser quitOnLastWindowClosed (qui est True) agir.
            else:
                 # S'il reste des fenêtres, le flag doit être False aussi
                 if self._expecting_welcome_after_close: # Log si on le réinitialise ici
                      logger.debug("_handle_document_window_closed: Réinitialisation du flag car il reste d'autres fenêtres.")
                 self._expecting_welcome_after_close = False 
            # --- FIN LOGIQUE MODIFIÉE --- 

        except ValueError:
             logger.warning(f"Tentative de retrait d'une DocumentWindow ({closed_window}) non trouvée via .remove().")
             window_was_in_list = False
             self._expecting_welcome_after_close = False # Reset flag en cas d'erreur
        except Exception as e:
             logger.error(f"Erreur inattendue lors du retrait de {closed_window} de la liste: {e}", exc_info=True)
             window_was_in_list = False
             self._expecting_welcome_after_close = False # Reset flag en cas d'erreur

        logger.info(f"Fin _handle_document_window_closed pour: {closed_window}")
    # ----------------------------------------------------

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
    @pyqtSlot(str, object) # MODIFIÉ: QWidget -> object
    def handle_main_action_request(self, action_name, source_window=None):
        logger.debug(f"MainController: Action '{action_name}' reçue. Source: {source_window}")
        # Déterminer la fenêtre source appropriée si non fournie directement pour certaines actions
        
        # --- MODIFICATION: Le paramètre 'source_window' de handle_main_action_request
        # peut être un dict pour certaines actions comme 'open_document_from_path'
        # ou 'create_document_from_selection'.
        # Nous devons obtenir la 'vraie' fenêtre source pour les actions standard si source_window est un dict.
        
        action_data = None
        actual_source_window = None

        if isinstance(source_window, dict):
            action_data = source_window
            # Essayez d'obtenir 'target_window' ou 'source_window' du dictionnaire de données
            # pour déterminer la fenêtre réelle à utiliser pour le contexte.
            if 'target_window' in action_data and isinstance(action_data['target_window'], QWidget):
                actual_source_window = action_data['target_window']
            elif 'source_window' in action_data and isinstance(action_data['source_window'], QWidget): # cas pour show_type_selection_window
                actual_source_window = action_data['source_window']
            else:
                # Si aucune fenêtre cible/source n'est dans les données, essayez d'obtenir la fenêtre active.
                actual_source_window = self._get_active_document_window()
        elif isinstance(source_window, QWidget):
            actual_source_window = source_window
        else: # Si source_window est None ou autre chose
            actual_source_window = self._get_active_document_window()

        logger.debug(f"MainController: actual_source_window déterminée: {actual_source_window}, action_data: {action_data}")


        if action_name == "new_document":
            logger.debug("MainController: Action 'new_document' reçue.")
            # Utiliser actual_source_window (qui peut être WelcomeWindow ou DocumentWindow)
            self.show_type_selection_window(source_window=actual_source_window)
        elif action_name == "open_document":
            logger.debug("MainController: Action 'open_document' reçue.")
            self.open_document(initiated_by_window=actual_source_window)
        elif action_name == "settings":
            logger.debug("MainController: Action 'settings' reçue.")
            self.show_settings_window()
        elif action_name == "save_document":
            logger.debug("MainController: Action 'save_document' reçue.")
            if actual_source_window and isinstance(actual_source_window, DocumentWindow): # S'assurer que c'est une DocumentWindow
                self._handle_save_document_action(actual_source_window, save_as=False)
            else:
                logger.warning(f"MainController: 'save_document' demandée mais pas de DocumentWindow active/source valide. Fenêtre source: {actual_source_window}")
        elif action_name == "save_document_as":
            logger.debug("MainController: Action 'save_document_as' reçue.")
            if actual_source_window and isinstance(actual_source_window, DocumentWindow): # S'assurer que c'est une DocumentWindow
                self._handle_save_document_action(actual_source_window, save_as=True)
            else:
                logger.warning(f"MainController: 'save_document_as' demandée mais pas de DocumentWindow active/source valide. Fenêtre source: {actual_source_window}")
        # --- AJOUT NOUVELLE ACTION ---
        elif action_name == "open_document_from_path":
            logger.debug("MainController: Action 'open_document_from_path' reçue (drag & drop).")
            if action_data and 'file_path' in action_data and 'target_window' in action_data:
                file_path_to_open = action_data['file_path']
                target_drop_window = action_data['target_window']
                
                if isinstance(target_drop_window, DocumentWindow) and target_drop_window.isVisible():
                    logger.info(f"Ouverture de '{file_path_to_open}' par drag & drop dans la DocumentWindow existante: {target_drop_window}")
                    # La méthode _load_and_display_rdj_document gère déjà l'ajout à une fenêtre existante
                    # ou la création d'une nouvelle si target_window est None.
                    # Ici, nous voulons explicitement l'ouvrir comme un nouvel onglet dans la fenêtre cible du drop.
                    self._load_and_display_rdj_document(file_path_to_open, target_window=target_drop_window)
                else:
                    # Si la target_window n'est pas valide (ex: a été fermée entre-temps),
                    # ouvrir dans une nouvelle fenêtre.
                    logger.warning(f"Target window pour drag & drop n'est pas une DocumentWindow valide ou visible. Ouverture dans une nouvelle fenêtre. Path: {file_path_to_open}")
                    self._load_and_display_rdj_document(file_path_to_open, target_window=None)
            else:
                logger.error(f"MainController: 'open_document_from_path' - données d'action manquantes ou incorrectes: {action_data}")
        # --- FIN AJOUT NOUVELLE ACTION ---
        else:
            logger.warning(f"MainController: Action '{action_name}' non reconnue.")

    def _get_active_document_window(self) -> Optional[DocumentWindow]:
        """Tente de trouver la DocumentWindow active ou la première si plusieurs."""
        if self.open_document_windows:
            for window in self.open_document_windows:
                if window.isActiveWindow():
                    return window
            return self.open_document_windows[0] # Retourne la première si aucune n'est active explicitement
        return None

    def _handle_save_document_action(self, source_window: QWidget, save_as: bool):
        logger.info(f"Début sauvegarde. save_as={save_as}")
        if not isinstance(source_window, DocumentWindow): # Assurez-vous que DocumentWindow est importé ou utilisez QWidget et vérifiez les attributs
            logger.error("Source pour sauvegarde n'est pas une DocumentWindow valide.")
            QMessageBox.warning(source_window, "Erreur Sauvegarde", "Fenêtre source invalide pour la sauvegarde.")
            return

        document_object = source_window.get_active_document()

        if not document_object:
            logger.warning("Aucun document actif trouvé pour la sauvegarde.")
            QMessageBox.information(source_window, "Sauvegarde", "Aucun document actif à sauvegarder.")
            return

        if not isinstance(document_object, RapportDepense): # Vérifier le type spécifique
            logger.warning(f"Le document actif n'est pas un RapportDepense (type: {type(document_object)}). Sauvegarde non supportée pour ce type.")
            QMessageBox.warning(source_window, "Sauvegarde non supportée", f"La sauvegarde n'est pas supportée pour le type de document actif ({type(document_object).__name__}).")
            return

        file_path_destination = None
        doc_original_filename = getattr(document_object, 'nom_fichier', None)
        
        # Utiliser le titre du document ou un nom par défaut pour la suggestion
        default_base_name = document_object.title if document_object.title else "NouveauRapport"
        # Nettoyer le nom de base pour éviter les caractères invalides dans les noms de fichiers (simplification)
        safe_base_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in default_base_name).rstrip()
        if not safe_base_name: safe_base_name = "Rapport" # Fallback si le titre ne contient que des char invalides

        suggested_filename_for_dialog = f"{safe_base_name}.rdj"

        if save_as or not doc_original_filename or not Path(doc_original_filename).exists():
            start_dir = str(Path(doc_original_filename).parent) if doc_original_filename and Path(doc_original_filename).exists() else os.path.expanduser("~")
            dialog_suggested_path = os.path.join(start_dir, suggested_filename_for_dialog)

            dialog = QFileDialog(source_window, "Enregistrer le rapport de dépenses", dialog_suggested_path)
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setNameFilter("Rapports de Dépenses Jacmar (*.rdj);;Tous les fichiers (*)")
            dialog.setDefaultSuffix("rdj") 
            
            if dialog.exec_() == QFileDialog.Accepted:
                file_path_destination = dialog.selectedFiles()[0]
            else:
                logger.info("Sauvegarde annulée par l'utilisateur.")
                return
        else:
            file_path_destination = doc_original_filename

        # --- Nettoyage du nom de fichier pour assurer la terminaison .rdj ---
        if file_path_destination:
            p = Path(file_path_destination)
            name_part = p.name 
            base_name_part = name_part
            while Path(base_name_part).suffix: # Enlève toutes les extensions existantes
                base_name_part = Path(base_name_part).stem
            
            file_path_destination = str(p.parent / (base_name_part + ".rdj"))
            logger.info(f"Chemin de destination final nettoyé: {file_path_destination}")
            # Mettre à jour nom_fichier dans l'objet si différent (surtout après Save As ou premier Save)
            if doc_original_filename != file_path_destination:
                 document_object.nom_fichier = file_path_destination
                 # Mettre à jour le titre de la fenêtre
                 new_window_title = Path(file_path_destination).name
                 if hasattr(source_window, 'set_window_title_from_document_name'): # Méthode préférée
                     source_window.set_window_title_from_document_name(new_window_title)
                 elif hasattr(source_window.title_bar, 'setTitle'): 
                     source_window.title_bar.setTitle(new_window_title)

        else: # Ne devrait pas arriver si la logique ci-dessus est correcte (car on return si annulé)
            logger.error("file_path_destination est None après la sélection/détermination du chemin.")
            QMessageBox.critical(source_window, "Erreur Interne", "Impossible de déterminer le chemin de sauvegarde.")
            return
        
        logger.info(f"Chemin de destination pour la sauvegarde (après nettoyage): {file_path_destination}")

        try:
            rapport_data, facture_dossiers_sources = document_object.save()
            logger.debug(f"Données du rapport préparées: {list(rapport_data.keys())}")
            logger.debug(f"Dossiers de factures sources: {facture_dossiers_sources}")

            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)
                logger.debug(f"Répertoire temporaire créé: {tmpdir_path}")

                # Écrire le fichier JSON principal
                json_file_path = tmpdir_path / "rapport_data.json"
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(rapport_data, f, ensure_ascii=False, indent=4)
                logger.debug(f"Fichier JSON écrit dans le répertoire temporaire: {json_file_path}")

                # Copier les dossiers de factures
                if facture_dossiers_sources:
                    factures_dir_in_tmp = tmpdir_path / "factures"
                    factures_dir_in_tmp.mkdir()
                    logger.debug(f"Sous-dossier 'factures' créé dans tmp: {factures_dir_in_tmp}")
                    for src_folder_path_str in facture_dossiers_sources:
                        src_folder = Path(src_folder_path_str)
                        if src_folder.exists() and src_folder.is_dir():
                            dest_folder_in_tmp = factures_dir_in_tmp / src_folder.name
                            shutil.copytree(src_folder, dest_folder_in_tmp)
                            logger.debug(f"Dossier facture copié: {src_folder} -> {dest_folder_in_tmp}")
                        else:
                            logger.warning(f"Dossier facture source non trouvé ou n'est pas un dossier: {src_folder_path_str}")
                else:
                    logger.debug("Aucun dossier de facture source à copier.")

                # Créer l'archive ZIP
                # shutil.make_archive attend base_name SANS extension pour le zip
                archive_base_name = str(Path(file_path_destination).with_suffix(''))
                shutil.make_archive(base_name=archive_base_name, format='zip', root_dir=tmpdir_path)
                logger.debug(f"Archive ZIP créée: {archive_base_name}.zip")
                
                # Renommer .zip en .rdj
                zip_file_path = archive_base_name + '.zip'
                if os.path.exists(file_path_destination) and str(Path(zip_file_path).resolve()) != str(Path(file_path_destination).resolve()):
                     os.remove(file_path_destination) # Supprimer l'ancien .rdj s'il existe et est différent du .zip (cas overwrite)
                os.rename(zip_file_path, file_path_destination)
                logger.info(f"Fichier sauvegardé avec succès sous: {file_path_destination}")
                QMessageBox.information(source_window, "Sauvegarde Réussie", f"Le document a été sauvegardé avec succès sous:\n{file_path_destination}")
                document_object.is_modified = False # Supposant un indicateur de modification
                if hasattr(source_window, 'update_window_title_modified_indicator'):
                    source_window.update_window_title_modified_indicator(False)

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du document: {e}", exc_info=True)
            QMessageBox.critical(source_window, "Erreur de Sauvegarde", f"Une erreur est survenue lors de la sauvegarde du document:\n{e}")

    def show_type_selection_window(self, source_window=None):
        """Crée et affiche la fenêtre TypeSelectionWindow."""
        self.doc_creation_source_window = source_window
        logger.info(f"MainController: show_type_selection_window appelée, source_window: {source_window}")
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
        """Gère le signal de création provenant de TypeSelectionWindow."""
        logger.info(f"MainController: Handling creation request from TypeSelectionWindow. Type: '{doc_type}'")
        # === AJOUT LOG DATE ===
        logger.debug(f"[DATE_DEBUG] MC._handle_creation - Data received: {data}")
        logger.debug(f"[DATE_DEBUG] MC._handle_creation - Date value received: {data.get('date')}")
        # ========================
        
        # Fermer la fenêtre de sélection, peu importe la suite
        if self.type_selection_window_instance:
            logger.info("Fermeture de TypeSelectionWindow...")
            self.type_selection_window_instance.close()

        # Déterminer la fenêtre cible pour un nouvel onglet
        target_window_for_new_tab = None
        if self.doc_creation_source_window and \
           isinstance(self.doc_creation_source_window, DocumentWindow) and \
           self.doc_creation_source_window.isVisible() and \
           self.doc_creation_source_window in self.open_document_windows:
            target_window_for_new_tab = self.doc_creation_source_window
            logger.info(f"Utilisation de doc_creation_source_window comme cible pour onglet: {target_window_for_new_tab}")
        elif self.open_document_windows: # Fallback si la source n'est pas une DocumentWindow valide/visible
            target_window_for_new_tab = self.open_document_windows[-1]
            logger.info(f"Fallback: Utilisation de la dernière DocumentWindow ouverte comme cible pour onglet: {target_window_for_new_tab}")

        if target_window_for_new_tab and target_window_for_new_tab.isVisible(): # Vérifier si une cible pour onglet existe
            logger.info(f"DocumentWindow cible ({target_window_for_new_tab}) détectée. Demande à l'utilisateur...")
            msg_box = QMessageBox(target_window_for_new_tab) # Parent pour centrage
            msg_box.setWindowTitle("Nouveau Document")
            msg_box.setText("Une fenêtre de document est déjà ouverte.")
            msg_box.setInformativeText("Où souhaitez-vous ouvrir le nouveau document ?")
            btn_new_tab = msg_box.addButton("Nouvel Onglet", QMessageBox.AcceptRole)
            btn_new_window = msg_box.addButton("Nouvelle Fenêtre", QMessageBox.DestructiveRole) 
            btn_cancel = msg_box.addButton("Annuler", QMessageBox.RejectRole)
            msg_box.setDefaultButton(btn_new_tab)
            
            msg_box.exec_()

            if msg_box.clickedButton() == btn_new_tab:
                logger.info("Utilisateur a choisi d'ouvrir dans un NOUVEL ONGLET.")
                if hasattr(target_window_for_new_tab, 'add_document_in_new_tab'):
                    target_window_for_new_tab.add_document_in_new_tab(doc_type, data)
                    target_window_for_new_tab.activateWindow() 
                    target_window_for_new_tab.raise_()
                else:
                    logger.error(f"L'instance {target_window_for_new_tab} n'a pas de méthode 'add_document_in_new_tab'. Création d'une nouvelle fenêtre par défaut.")
                    self.show_new_document_window(doc_type, data) # Fallback
            elif msg_box.clickedButton() == btn_new_window:
                logger.info("Utilisateur a choisi d'ouvrir une NOUVELLE FENÊTRE de document.")
                self.show_new_document_window(doc_type, data)
            elif msg_box.clickedButton() == btn_cancel:
                logger.info("Création de document annulée par l'utilisateur.")
            else:
                logger.info("Dialogue de choix fermé sans sélection, annulation.")
        else:
            # Pas de DocumentWindow existante appropriée pour un onglet, en créer une nouvelle
            logger.info("Aucune DocumentWindow cible pour un onglet. Création d'une nouvelle fenêtre.")
            self.show_new_document_window(doc_type, data)
        
        self.doc_creation_source_window = None # Réinitialiser la source après usage
    # -------------------------------------------------------------------

    # --- AJOUT METHODE ---
    def request_welcome_after_close(self, closing_window):
        """
        Appelé par DocumentWindow juste avant de se fermer car le dernier onglet
        a été fermé. Met un flag si c'est la dernière fenêtre.
        """
        # Vérification supplémentaire pour robustesse
        if not isinstance(closing_window, QWidget): 
             logger.warning("request_welcome_after_close received non-QWidget object.")
             return
             
        if closing_window in self.open_document_windows and len(self.open_document_windows) == 1:
            logger.info("MainController: request_welcome_after_close reçue pour la dernière DocumentWindow. Flag activé.")
            self._expecting_welcome_after_close = True
        else:
             # Log plus détaillé si la fenêtre n'est pas trouvée ou s'il y en a plusieurs
             count = len(self.open_document_windows)
             found = closing_window in self.open_document_windows
             logger.debug(f"MainController: request_welcome_after_close reçue. Fenêtre trouvée: {found}, Nombre total: {count}. Flag inchangé.")
    # --------------------

    # --- AJOUT IMPORTS POUR LA LOGIQUE D'OUVERTURE RDJ ---
    # (Certains peuvent être redondants avec la section sauvegarde, mais c'est pour s'assurer qu'ils sont là)
    # import json # Déjà présent
    # import zipfile # Déjà présent
    # import tempfile # Déjà présent
    # import shutil # Déjà présent
    # from pathlib import Path # Déjà présent
    # import os # Déjà présent
    from utils.paths import get_user_data_path # Assurer que get_user_data_path est importé
    # -----------------------------------------------------

    def _load_and_display_rdj_document(self, rdj_file_path: str, target_window: Optional[DocumentWindow] = None): # AJOUT target_window
        logger.info(f"MainController: Tentative de chargement du document .rdj: {rdj_file_path}. Cible: {target_window}") # MOD log
        temp_dir_obj = None

        try:
            # Créer un répertoire temporaire unique pour l'extraction
            temp_dir_obj = tempfile.TemporaryDirectory(prefix="rdj_extract_")
            temp_extract_path = Path(temp_dir_obj.name)
            logger.info(f"_load_and_display_rdj_document: Fichier .rdj '{rdj_file_path}' sera extrait vers '{temp_extract_path}'")

            # Étape 1: Décompresser l'archive .rdj dans le répertoire temporaire
            with zipfile.ZipFile(rdj_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_path)
            logger.info(f"_load_and_display_rdj_document: Contenu de .rdj extrait dans {temp_extract_path}")

            # Étape 2: Lire le fichier rapport_data.json
            json_file_path = temp_extract_path / "rapport_data.json"
            if not json_file_path.exists():
                logger.error(f"_load_and_display_rdj_document: Fichier rapport_data.json non trouvé dans l'archive à {json_file_path}")
                QMessageBox.critical(self.main_window if self.main_window else None, "Erreur d'Ouverture", 
                                     f"Le fichier 'rapport_data.json' est manquant dans l'archive {Path(rdj_file_path).name}.")
                return

            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            logger.info(f"_load_and_display_rdj_document: Contenu de rapport_data.json chargé.")

            doc_type_from_json = json_data.get('type_document', 'Inconnu')
            logger.info(f"_load_and_display_rdj_document: Type de document lu depuis JSON: {doc_type_from_json}")

            # --- AJOUT DE LA NORMALISATION DU TYPE DE DOCUMENT ---
            doc_type_standardized = doc_type_from_json
            if doc_type_from_json.lower() == "rapport de depense" or doc_type_from_json == "RapportDepense":
                doc_type_standardized = "Rapport de depense" # La forme attendue par DocumentsOpenPage
                logger.info(f"_load_and_display_rdj_document: Type de document normalisé en: '{doc_type_standardized}'")
            # --- FIN DE L'AJOUT ---

            # Vérifier si le type de document est supporté (pour l'instant, seulement Rapport de depense)
            if doc_type_standardized != "Rapport de depense":
                logger.error(f"_load_and_display_rdj_document: Type de document '{doc_type_standardized}' non supporté pour le chargement.")
                QMessageBox.critical(self.main_window if self.main_window else None, "Type Non Supporté", 
                                     f"Le type de document '{doc_type_standardized}' n'est pas supporté pour l'ouverture directe.")
                return

            # Étape 3: Créer un dossier de destination unique pour les factures de cette session d'ouverture
            factures_entrees_base_path = Path(get_user_data_path()) / "FacturesEntrees"
            factures_entrees_base_path.mkdir(parents=True, exist_ok=True)
            
            original_rdj_name = Path(rdj_file_path).stem
            timestamp = date.today().strftime("%Y%m%d") # Format YYYYMMDD
            # Utiliser seulement les 8 premiers caractères d'un UUID pour la concision
            # import uuid # Assurez-vous que uuid est importé au début du fichier si ce n'est pas déjà fait
            # unique_id = str(uuid.uuid4())[:8]
            # Pour éviter l'import, on peut se baser sur un timestamp plus précis si nécessaire
            # ou simplement un compteur si on gère plusieurs ouvertures simultanées de manière robuste
            # Pour l'instant, on va simplifier et utiliser un nom basé sur le fichier et la date.
            # Il faut s'assurer de l'unicité si plusieurs fichiers avec le même nom sont ouverts le même jour.
            # Un compteur ou un timestamp plus précis pourrait être nécessaire.
            # Pour l'instant, le risque de collision est faible pour un usage typique.
            target_factures_folder_name = f"{original_rdj_name}_factures_{timestamp}" 
            final_factures_path_for_session = factures_entrees_base_path / target_factures_folder_name
            
            # Gérer les conflits de noms de dossier (par exemple, si ouvert plusieurs fois)
            counter = 1
            temp_path = final_factures_path_for_session
            while temp_path.exists():
                logger.warning(f"_load_and_display_rdj_document: Dossier de factures '{temp_path}' existe déjà. Tentative avec suffixe.")
                target_factures_folder_name = f"{original_rdj_name}_factures_{timestamp}_{counter}"
                temp_path = factures_entrees_base_path / target_factures_folder_name
                counter += 1
            final_factures_path_for_session = temp_path
            final_factures_path_for_session.mkdir(parents=True, exist_ok=True)
            logger.info(f"_load_and_display_rdj_document: Dossier de destination pour les factures de cette session: {final_factures_path_for_session}")

            # Étape 4: Copier les dossiers de factures depuis temp/factures vers le dossier unique
            source_factures_in_zip_path = temp_extract_path / "factures"
            if source_factures_in_zip_path.exists() and source_factures_in_zip_path.is_dir():
                for item in source_factures_in_zip_path.iterdir():
                    if item.is_dir(): # On s'attend à des dossiers individuels par facture
                        try:
                            shutil.copytree(item, final_factures_path_for_session / item.name)
                            logger.info(f"_load_and_display_rdj_document: Dossier de facture '{item.name}' copié vers '{final_factures_path_for_session / item.name}'.")
                        except Exception as e_copy:
                            logger.error(f"Erreur lors de la copie du dossier de facture '{item.name}': {e_copy}", exc_info=True)
                            # Continuer avec les autres factures si possible
            else:
                logger.info(f"_load_and_display_rdj_document: Aucun dossier 'factures' trouvé dans l'archive ou ce n'est pas un répertoire.")

            # Étape 5: Appeler RapportDepense.from_dict
            # Le original_rdj_filepath est rdj_file_path
            # Le base_path_for_factures est final_factures_path_for_session
            try:
                rapport_objet = RapportDepense.from_dict(json_data, str(final_factures_path_for_session), rdj_file_path)
                rapport_objet.original_file_path = rdj_file_path # Stocker le chemin d'origine
                rapport_objet.factures_session_path = str(final_factures_path_for_session) # Stocker où les factures ont été copiées pour cette session
                logger.info(f"_load_and_display_rdj_document: Objet RapportDepense créé à partir de from_dict.")
            except Exception as e_from_dict:
                logger.error(f"Erreur lors de la reconstruction de l'objet RapportDepense via from_dict: {e_from_dict}", exc_info=True)
                QMessageBox.critical(self.main_window if self.main_window else None, "Erreur de Chargement",
                                     f"""Impossible de reconstruire le rapport à partir des données du fichier.
Détail: {e_from_dict}""")
                return
            
            # Étape 6: Afficher le RapportDepense chargé
            # Utiliser doc_type_standardized ici
            doc_creation_data = {
                'loaded_object': rapport_objet,
                'doc_type': doc_type_standardized, 
                'original_path': rdj_file_path, # Peut être utile pour le titre ou la sauvegarde
                'factures_session_path': str(final_factures_path_for_session) # Chemin où les factures sont pour cette session
            }
            logger.info(f"_load_and_display_rdj_document: Données pour création de DocumentWindow: {doc_creation_data}")
            
            # MODIFIÉ: Logique pour utiliser target_window ou créer une nouvelle fenêtre
            if target_window and hasattr(target_window, 'add_document_in_new_tab'):
                logger.info(f"Tentative d'ajout du document dans un onglet de la fenêtre cible: {target_window}")
                target_window.add_document_in_new_tab(doc_type_standardized, doc_creation_data)
                target_window.activateWindow() # S'assurer qu'elle est au premier plan
                target_window.raise_()
                logger.info(f"_load_and_display_rdj_document: Document '{rdj_file_path}' chargé et affiché dans un onglet de {target_window}.")
            else:
                if target_window: # target_window a été fourni mais n'a pas la méthode attendue
                    logger.warning(f"La fenêtre cible {target_window} n'a pas la méthode add_document_in_new_tab. Ouverture dans une nouvelle fenêtre par défaut.")
                self.show_new_document_window(doc_type_standardized, doc_creation_data)
                # Le logger existant dans show_new_document_window ou après son appel devrait suffire
                # logger.info(f"_load_and_display_rdj_document: Document '{rdj_file_path}' chargé et affiché dans une nouvelle fenêtre.") # Redondant

        except zipfile.BadZipFile:
            logger.error(f"_load_and_display_rdj_document: Le fichier '{rdj_file_path}' n'est pas une archive ZIP valide ou est corrompu.")
            QMessageBox.critical(self.main_window if self.main_window else None, "Erreur d'Ouverture", 
                                 f"Le fichier '{Path(rdj_file_path).name}' n'est pas un fichier de rapport valide (.rdj) ou est corrompu.")
        except json.JSONDecodeError:
            logger.error(f"_load_and_display_rdj_document: Erreur de décodage JSON pour rapport_data.json dans '{rdj_file_path}'.")
            QMessageBox.critical(self.main_window if self.main_window else None, "Erreur d'Ouverture", 
                                 f"Les données internes du rapport '{Path(rdj_file_path).name}' sont corrompues (erreur JSON).")
        except Exception as e:
            logger.error(f"Erreur inattendue lors du chargement du document .rdj {rdj_file_path}: {e}", exc_info=True)
            QMessageBox.critical(self.main_window if self.main_window else None, "Erreur Inconnue", 
                                 f"""Une erreur inattendue est survenue lors de l'ouverture du fichier '{Path(rdj_file_path).name}'.
Consultez les logs pour plus de détails.""")
        finally:
            # Nettoyer le répertoire temporaire, même en cas d'erreur
            if temp_dir_obj:
                try:
                    temp_dir_obj.cleanup()
                    logger.info(f"_load_and_display_rdj_document: Répertoire temporaire '{temp_extract_path}' nettoyé.")
                except Exception as e_cleanup:
                    logger.error(f"Erreur lors du nettoyage du répertoire temporaire '{temp_extract_path}': {e_cleanup}", exc_info=True)

    # --- NOUVELLE MÉTHODE POUR GÉRER L'OUVERTURE D'UN FICHIER AU DÉMARRAGE ---
    def handle_startup_file_argument(self, file_path: str):
        logger.info(f"MainController: Traitement du fichier de démarrage: {file_path}")
        
        # S'assurer que la fenêtre de bienvenue est fermée si elle existe et est visible
        if self.welcome_window and self.welcome_window.isVisible():
            logger.info("Fermeture de la WelcomeWindow car un fichier est ouvert au démarrage.")
            self.welcome_window.close()
            # Il peut être nécessaire de s'assurer que les événements de fermeture sont traités
            # avant de continuer, par exemple avec app.processEvents()
            app = QApplication.instance()
            if app:
                app.processEvents()

        # Appeler la méthode existante pour charger et afficher le document .rdj
        # Cette méthode créera une nouvelle DocumentWindow ou utilisera une existante (selon sa logique actuelle)
        # Pour un lancement direct de fichier, on ne spécifie pas de target_window, 
        # donc une nouvelle DocumentWindow sera créée.
        self._load_and_display_rdj_document(file_path, target_window=None)
        logger.info(f"MainController: Traitement du fichier de démarrage {file_path} terminé.")
    # --- FIN NOUVELLE MÉTHODE ---

# --- SECTION PRINCIPALE (FIN DU FICHIER) ---
def main():
    pass # <<< AJOUT D\'UN BLOC INDENTÉ POUR CORRIGER L\'ERREUR
    # ... le reste du code original de main() devrait être ici ...
