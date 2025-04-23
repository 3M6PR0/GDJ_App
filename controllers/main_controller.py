from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, QTimer
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

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

# --- Import des nouvelles pages/fenêtres ---
from pages.welcome_page import WelcomePage
from ui.main_window import MainWindow
# --- AJOUT IMPORTS POUR ABOUT ---
from pages.about.about_page import AboutPage
from controllers.about.about_controller import AboutController

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

class MainController:
    def __init__(self):
        print("--- Entering MainController __init__ ---")
        self.main_window = None
        self.welcome_page = None
        self.documents = {}
        self.about_page = None
        self.about_controller_instance = None
        self.navigate_to_notes_after_welcome = False 
        self._startup_update_check_done = False

        # --- Corrected Logic AGAIN (Focus on Version Comparison) --- 
        self.version_file = get_resource_path("data/version.txt")
        self.release_notes_file = get_resource_path("RELEASE_NOTES.md")
        self.current_version_str = self._read_version_file(self.version_file)
        
        last_run_version_file = get_resource_path("data/last_run_version.txt")
        last_run_version_str = self._read_version_file(last_run_version_file) 
        print(f"DEBUG __init__: Current Version='{self.current_version_str}', Last Run Version Read='{last_run_version_str}'")

        do_navigate_on_startup = False
        try:
            current_v = version.parse(self.current_version_str)
            last_run_v = version.parse(last_run_version_str) 
            # Navigate if current version is strictly greater than the last run version
            if current_v > last_run_v:
                do_navigate_on_startup = True
                print(f"DEBUG __init__: Update detected (current {current_v} > last run {last_run_v}). Setting navigation flag.")
            else:
                 print(f"DEBUG __init__: No update detected (current {current_v} <= last run {last_run_v}).")
        except version.InvalidVersion:
            # Treat parse error (like first run "0.0.0") as needing navigation
            print(f"DEBUG __init__: InvalidVersion detected. Setting navigation flag for first run/update.")
            try:
                 version.parse(self.current_version_str) # Check current is valid
                 do_navigate_on_startup = True
            except version.InvalidVersion:
                 print("ERROR __init__: Current version is also invalid. Navigation flag set to False.")
                 do_navigate_on_startup = False

        # Set the flag for later use in show_welcome_page
        self.navigate_to_notes_after_welcome = do_navigate_on_startup

        # If navigation is needed, update the last_run_version file NOW
        if do_navigate_on_startup:
            print("DEBUG __init__: Writing current version to last_run_version.txt because navigation flag is set.")
            self._write_last_run_version(last_run_version_file, self.current_version_str)
            
        # --- Exiting MainController __init__ --- 
        print("--- Exiting MainController __init__ --- ")

    def show_welcome_page(self):
        """Crée et affiche la page de bienvenue, et lance la vérif MàJ."""
        if self.welcome_page is None:
            app_name = CONFIG.get('APP_NAME', 'MonApp')
            self.welcome_page = WelcomePage(self, app_name, self.current_version_str)
            # --- DÉFINIR L'ICÔNE DE LA FENÊTRE DE BIENVENUE ---
            try:
                icon_path = get_resource_path("resources/images/logo-gdj.ico")
                if os.path.exists(icon_path):
                    self.welcome_page.setWindowIcon(QIcon(icon_path))
                else:
                    print(f"Avertissement: Icône de fenêtre non trouvée à {icon_path}")
            except Exception as e:
                print(f"Erreur lors de la définition de l'icône pour WelcomePage: {e}")
        
        self.welcome_page.show()
        print("DEBUG show_welcome_page: WelcomePage shown.")

        # --- MODIFICATION : Appeler la vérification SEULEMENT si pas déjà faite --- 
        if not self._startup_update_check_done:
             print("DEBUG show_welcome_page: Performing startup update check (first time)...")
             self._perform_startup_update_check()
             self._startup_update_check_done = True # Marquer comme fait
        else:
             print("DEBUG show_welcome_page: Startup update check already performed.")
        # --------------------------------------------------------------------

        # --- Gestion de la navigation vers les notes (reste pareil) ---
        if self.navigate_to_notes_after_welcome:
            print("DEBUG show_welcome_page: Flag is True, attempting navigation to 'A Propos' section...")
            try:
                # Assume welcome_page has this method
                self.welcome_page.navigate_to_section("A Propos") 
                print("DEBUG show_welcome_page: Called welcome_page.navigate_to_section('A Propos').")
                # The WelcomePage logic should handle activating the correct sub-tab 
                # and resetting the flag self.navigate_to_notes_after_welcome to False.
            except AttributeError:
                print("ERROR show_welcome_page: WelcomePage does not have method 'navigate_to_section'.")
            except Exception as e:
                 print(f"ERROR show_welcome_page: Exception during navigation call: {e}")
        else:
             print("DEBUG show_welcome_page: Flag is False, no automatic navigation needed.")

    def _ensure_main_window_exists(self):
        """Crée la MainWindow si elle n'existe pas et établit les connexions."""
        print(">>> Entering _ensure_main_window_exists method...")
        print(f"--- Checking if self.main_window is None (Current value: {self.main_window is None})...")
        if self.main_window is None:
            print("--- Condition self.main_window is None PASSED. Attempting to create MainWindow instance...")
            try:
                # --- AJOUT TRY/EXCEPT ET LOGGING ---
                print("--- BEFORE MainWindow() instantiation ---")
                # --- Import local pour être sûr (peut-être redondant mais sûr) ---
                from ui.main_window import MainWindow
                self.main_window = MainWindow() # <--- Potential failure point
                print(f"--- AFTER MainWindow() instantiation. self.main_window is None: {self.main_window is None} ---")
                # ------------------------------------

                # --- DÉFINIR LA RÉFÉRENCE DU MainController DANS MainWindow ---
                # (Seulement si l'instantiation a réussi)
                print("--- Calling main_window.set_main_controller(self) ---")
                self.main_window.set_main_controller(self)
                # ------------------------------------------------------------

                # --- Définir l'icône de la fenêtre principale ---
                try:
                    icon_path = get_resource_path("resources/images/logo-gdj.ico")
                    if os.path.exists(icon_path):
                        self.main_window.setWindowIcon(QIcon(icon_path))
                    else:
                         print(f"Avertissement: Icône de fenêtre non trouvée à {icon_path}")
                except Exception as e_icon:
                     print(f"Erreur lors de la définition de l'icône pour MainWindow: {e_icon}")

                # Connecter les actions du menu de la MainWindow au contrôleur
                print("--- Connecting MainWindow menu actions ---")
                self.main_window.action_new.triggered.connect(self.create_new_document_from_menu)
                self.main_window.action_open.triggered.connect(self.open_document_from_menu)
                self.main_window.action_close.triggered.connect(self.close_current_document)
                try:
                    self.main_window.actionAfficherNotesVersion.triggered.connect(self.show_release_notes_dialog)
                except AttributeError:
                    print("Avertissement : L'action 'actionAfficherNotesVersion' n'a pas été trouvée dans l'UI.")
                print("--- MainWindow menu actions connected ---")

            except Exception as e_init:
                # --- CAPTURER L'ERREUR D'INITIALISATION ---
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print(f"CRITICAL ERROR: Exception during MainWindow instantiation: {e_init}")
                import traceback
                traceback.print_exc() # Afficher la trace complète de l'erreur
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                # S'assurer que main_window reste None en cas d'échec
                self.main_window = None
            # --- FIN AJOUT ---

        # On continue seulement si main_window a été créé avec succès
        if self.main_window:
            # Fermer la fenêtre de bienvenue si elle est ouverte
            if self.welcome_page and self.welcome_page.isVisible():
                 print("--- Closing WelcomePage as MainWindow is ensured ---")
                 self.welcome_page.close()

            # Afficher la fenêtre principale si elle était cachée
            if not self.main_window.isVisible():
                 print("--- Showing MainWindow as it was not visible ---")
                 self.main_window.show()
        else:
             print("--- MainWindow is still None after creation attempt. Cannot proceed. --- ")

        print(f"--- Final check before exiting _ensure_main_window_exists. self.main_window is None: {self.main_window is None} ---")
        print("<<< Exiting _ensure_main_window_exists method...")

    def _read_version_file(self, file_path):
        """ Lit un fichier de version (reçoit le chemin complet). """
        if not os.path.exists(file_path):
            print(f"Fichier version non trouvé: {file_path}")
            return "0.0.0" # Version par défaut si non trouvé
        config = configparser.ConfigParser()
        try:
            config.read(file_path, encoding="utf-8")
            return config.get("Version", "value").strip()
        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")
            return "0.0.0"

    def _write_last_run_version(self, file_path, current_version):
        """ Écrit dans un fichier de version (reçoit le chemin complet). """
        config = configparser.ConfigParser()
        config["Version"] = {"value": current_version}
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True) # Crée le dossier data si besoin
            with open(file_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            print(f"Version {current_version} écrite dans {file_path}")
        except Exception as e:
            print(f"Erreur écriture {file_path}: {e}")

    def show_release_notes_dialog(self, auto_update_context=False):
        """ Affiche la boîte de dialogue modale avec les notes de version (pour action manuelle). """
        # Ne pas appeler ensure_main_window si c'est le contexte auto (géré par check_...)
        if not auto_update_context:
             self._ensure_main_window_exists()
             print("Affichage manuel des notes de version...")
        else:
             # Normalement, on ne devrait plus arriver ici dans le contexte auto
             print("Avertissement: show_release_notes_dialog appelée en contexte auto ?")
             return 

        notes_content = "Notes de version non trouvées."
        try:
            with open(self.release_notes_file, 'r', encoding='utf-8') as f:
                notes_content = f.read()
            # Ajouter le titre dynamiquement si lu depuis le fichier
            # (Le fichier lui-même n'a plus de v spécifiques dans le titre)
            notes_content = f"# Notes de version - v{self.current_version_str}\n\n{notes_content}"
        except FileNotFoundError:
            print(f"Erreur: {self.release_notes_file} non trouvé.")
            notes_content = f"# Notes de version - v{self.current_version_str}\n\nErreur : Fichier {os.path.basename(self.release_notes_file)} introuvable."
        except Exception as e:
            print(f"Erreur lecture {self.release_notes_file}: {e}")
            notes_content = f"# Notes de version - v{self.current_version_str}\n\nErreur lors de la lecture des notes de version: {e}"

        dialog = ReleaseNotesDialog(self.current_version_str, notes_content, parent=self.main_window)
        dialog.exec_()

    def create_new_document(self):
        """Action appelée par le bouton 'Nouveau' de WelcomePage."""
        self._ensure_main_window_exists()
        print("Fonctionnalité 'Nouveau Document' (via WelcomePage) désactivée car NewDocumentDialog est supprimé.")
        pass # Ne fait rien pour l'instant

    def open_document(self):
        """Action appelée par le bouton 'Ouvrir' de WelcomePage."""
        self._ensure_main_window_exists()
        # Logique pour ouvrir un fichier via QFileDialog
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self.main_window, 
                                                  "Ouvrir un document GDJ", "", 
                                                  "GDJ Documents (*.gdj);;Tous les fichiers (*.*)", options=options)
        if filePath:
            print(f"Ouverture du document: {filePath}")
            # Ici, il faudrait charger le document depuis le fichier
            # Pour l'instant, on simule comme avant
            self._open_and_add_document_tab(f"Doc: {os.path.basename(filePath)}", None) # Passe le chemin ou titre
            
    def open_specific_document(self, path):
        """Action appelée par double-clic sur un item récent dans WelcomePage."""
        self._ensure_main_window_exists()
        print(f"Ouverture du document spécifique: {path}")
        # Ici, il faudrait charger le document depuis le `path`
        # Simulé pour l'instant
        self._open_and_add_document_tab(f"Doc: {os.path.basename(path)}", None) 
        
    def create_new_document_from_menu(self):
        """Action appelée par le menu Fichier > Nouveau."""
        # Pas besoin d'appeler _ensure_main_window_exists ici car le menu n'est visible
        # que si la fenêtre principale existe déjà.
        print("Fonctionnalité 'Nouveau Document' (via Menu) désactivée car NewDocumentDialog est supprimé.")
        pass # Ne fait rien pour l'instant
            
    def open_document_from_menu(self):
        """Action appelée par le menu Fichier > Ouvrir."""
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self.main_window, "Ouvrir un document GDJ", "", "GDJ Documents (*.gdj);;Tous les fichiers (*.*)", options=options)
        if filePath:
            print(f"Ouverture du document (menu): {filePath}")
            self._open_and_add_document_tab(f"Doc: {os.path.basename(filePath)}", None)

    def _create_and_add_document_tab(self, doc_type, data):
        """Factorisation de la logique de création d'un nouveau document et ajout d'onglet."""
        new_doc = None
        if doc_type == "Rapport Dépense":
            from models.documents.rapport_depense import RapportDepense
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
            print(f"Type de document inconnu ou non géré: {doc_type}")
            return
            
        if new_doc:
            doc_page = DocumentPage(title=new_doc.title, document=new_doc)
            idx = self.main_window.tab_widget.addTab(doc_page, doc_page.title)
            self.main_window.tab_widget.setCurrentIndex(idx)
            self.documents[new_doc.title] = doc_page

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
            print("Création de la page À Propos et de son contrôleur...")
            self.about_page = AboutPage()
            # Créer et garder la référence au contrôleur
            self.about_controller_instance = AboutController(self.about_page) 
            
            # Ajouter l'onglet s'il n'existe pas déjà (double sécurité)
            if self.main_window.tab_widget.indexOf(self.about_page) == -1:
                 self.main_window.tab_widget.addTab(self.about_page, "À Propos")
            else:
                 print("Avertissement: La page À Propos existait déjà dans les onglets ?")
        
        # Sélectionner l'onglet 'À Propos'
        idx = self.main_window.tab_widget.indexOf(self.about_page)
        if idx != -1:
            self.main_window.tab_widget.setCurrentIndex(idx)
            print("Navigation vers l'onglet À Propos effectuée.")
        else:
            print("Erreur: Impossible de trouver l'index de la page À Propos après création/vérification.")

    # --- NOUVELLE MÉTHODE POUR LA VÉRIFICATION AU DÉMARRAGE ---
    def _perform_startup_update_check(self):
        """Vérifie les MàJ au démarrage et planifie l'action si confirmée."""
        try:
            status, update_info = check_for_updates()
            print(f"Startup update check status: {status}")
            if status == "USER_CONFIRMED_UPDATE":
                print("User confirmed update from startup prompt. Scheduling navigation within WelcomePage...")
                self._pending_update_info = update_info
                # --- APPELER LA NOUVELLE MÉTHODE VIA QTIMER --- 
                QTimer.singleShot(0, self._navigate_welcome_to_settings_and_update)
            elif status == "UPDATE_DECLINED":
                 print("Startup update declined by user.")
            elif update_info and not update_info.get('available') and status != "À jour":
                 print(f"Startup update check notice: {status}") # Affiche les erreurs etc.

        except Exception as e:
            print(f"Error during startup update check: {e}")
            if hasattr(self, '_pending_update_info'):
                 del self._pending_update_info

    # --- NOUVELLE MÉTHODE POUR GÉRER DANS WELCOMEPAGE --- 
    def _navigate_welcome_to_settings_and_update(self):
        """Navigue vers les paramètres DANS WelcomePage et lance la MàJ."""
        print("Navigating WelcomePage to settings and initiating update...")
        if hasattr(self, '_pending_update_info') and self._pending_update_info:
            update_info = self._pending_update_info.copy() # Prendre une copie
            if hasattr(self, '_pending_update_info'):
                del self._pending_update_info # Nettoyer

            if self.welcome_page:
                try:
                    # 1. Naviguer dans WelcomePage
                    print("Calling welcome_page.navigate_to_section('Paramètres')...")
                    # Assumons True pour succès, False/Exception pour échec
                    navigation_successful = self.welcome_page.navigate_to_section("Paramètres") 

                    if navigation_successful:
                         print("Navigation to WelcomePage settings section successful.")
                         # 2. Récupérer le SettingsController de WelcomePage
                         print("Getting SettingsController from WelcomePage...")
                         settings_controller = self.welcome_page.get_settings_controller()

                         if settings_controller:
                              print("Got SettingsController instance from WelcomePage.")
                              # 3. Lancer le téléchargement
                              print("Calling initiate_update_from_prompt on WelcomePage's SettingsController...")
                              settings_controller.initiate_update_from_prompt(update_info)
                         else:
                              print("ERROR: welcome_page.get_settings_controller() returned None.")
                    else:
                         print("ERROR: welcome_page.navigate_to_section('Paramètres') failed or returned False.")

                except AttributeError as ae:
                     print(f"ERROR: WelcomePage is missing a required method (navigate_to_section or get_settings_controller): {ae}")
                except Exception as e:
                     print(f"ERROR: An unexpected error occurred during WelcomePage navigation/update initiation: {e}")
            else:
                print("ERROR: WelcomePage instance is None. Cannot navigate.")
        else:
            print("Warning: _navigate_welcome_to_settings_and_update called but no pending update info found.")

    def _ensure_main_window_exists(self):
        """Crée la MainWindow si elle n'existe pas et établit les connexions."""
        print(">>> Entering _ensure_main_window_exists method...")
        print(f"--- Checking if self.main_window is None (Current value: {self.main_window is None})...")
        if self.main_window is None:
            print("--- Condition self.main_window is None PASSED. Attempting to create MainWindow instance...")
            try:
                # --- AJOUT TRY/EXCEPT ET LOGGING ---
                print("--- BEFORE MainWindow() instantiation ---")
                # --- Import local pour être sûr (peut-être redondant mais sûr) ---
                from ui.main_window import MainWindow
                self.main_window = MainWindow() # <--- Potential failure point
                print(f"--- AFTER MainWindow() instantiation. self.main_window is None: {self.main_window is None} ---")
                # ------------------------------------

                # --- DÉFINIR LA RÉFÉRENCE DU MainController DANS MainWindow ---
                # (Seulement si l'instantiation a réussi)
                print("--- Calling main_window.set_main_controller(self) ---")
                self.main_window.set_main_controller(self)
                # ------------------------------------------------------------

                # --- Définir l'icône de la fenêtre principale ---
                try:
                    icon_path = get_resource_path("resources/images/logo-gdj.ico")
                    if os.path.exists(icon_path):
                        self.main_window.setWindowIcon(QIcon(icon_path))
                    else:
                         print(f"Avertissement: Icône de fenêtre non trouvée à {icon_path}")
                except Exception as e_icon:
                     print(f"Erreur lors de la définition de l'icône pour MainWindow: {e_icon}")

                # Connecter les actions du menu de la MainWindow au contrôleur
                print("--- Connecting MainWindow menu actions ---")
                self.main_window.action_new.triggered.connect(self.create_new_document_from_menu)
                self.main_window.action_open.triggered.connect(self.open_document_from_menu)
                self.main_window.action_close.triggered.connect(self.close_current_document)
                try:
                    self.main_window.actionAfficherNotesVersion.triggered.connect(self.show_release_notes_dialog)
                except AttributeError:
                    print("Avertissement : L'action 'actionAfficherNotesVersion' n'a pas été trouvée dans l'UI.")
                print("--- MainWindow menu actions connected ---")

            except Exception as e_init:
                # --- CAPTURER L'ERREUR D'INITIALISATION ---
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print(f"CRITICAL ERROR: Exception during MainWindow instantiation: {e_init}")
                import traceback
                traceback.print_exc() # Afficher la trace complète de l'erreur
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                # S'assurer que main_window reste None en cas d'échec
                self.main_window = None
            # --- FIN AJOUT ---

        # On continue seulement si main_window a été créé avec succès
        if self.main_window:
            # Fermer la fenêtre de bienvenue si elle est ouverte
            if self.welcome_page and self.welcome_page.isVisible():
                 print("--- Closing WelcomePage as MainWindow is ensured ---")
                 self.welcome_page.close()

            # Afficher la fenêtre principale si elle était cachée
            if not self.main_window.isVisible():
                 print("--- Showing MainWindow as it was not visible ---")
                 self.main_window.show()
        else:
             print("--- MainWindow is still None after creation attempt. Cannot proceed. --- ")

        print(f"--- Final check before exiting _ensure_main_window_exists. self.main_window is None: {self.main_window is None} ---")
        print("<<< Exiting _ensure_main_window_exists method...")
