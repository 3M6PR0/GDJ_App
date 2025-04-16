from PyQt5.QtWidgets import QDialog
from dialogs.new_document_dialog import NewDocumentDialog
from pages.home_page import HomePage
from pages.document_page import DocumentPage
from pages.profile_page import ProfilePage
from models.profile import Profile
import os
import sys
import configparser
from packaging import version
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox, QDialog,
                             QVBoxLayout, QTextBrowser, QPushButton, QSizePolicy)
from PyQt5.QtCore import Qt
from config import CONFIG
from updater.update_checker import check_for_updates

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
    def __init__(self, main_window):
        self.main_window = main_window
        self.documents = {}
        self.profile_page = None

        # Au démarrage, charger le profil depuis le fichier JSON.
        self.profile = Profile.load_from_file()

        # Charger la page d'accueil dans le QTabWidget
        self.home_page = HomePage(self)
        self.main_window.tab_widget.addTab(self.home_page, "Accueil")

        # --- Chemins et versions --- (Déplacé ici pour être accessible par plusieurs méthodes)
        self.app_base_path = self._get_app_base_path()
        self.data_path = os.path.join(self.app_base_path, CONFIG.get("DATA_PATH", "data"))
        self.version_file = os.path.join(self.data_path, "version.txt")
        self.release_notes_file = os.path.join(self.app_base_path, "RELEASE_NOTES.md")
        self.current_version_str = self._read_version_file(self.version_file)

        # --- Vérifications au démarrage ---
        self.check_show_release_notes_on_update() # Renommée pour clarté
        check_for_updates()

        # --- Connexions Menu --- (Ajouter la nouvelle connexion)
        self.main_window.action_new.triggered.connect(self.create_new_document)
        self.main_window.action_open.triggered.connect(self.open_document)
        self.main_window.action_close.triggered.connect(self.close_current_document)
        self.main_window.action_profile.triggered.connect(self.open_profile_page)
        # !! Assurez-vous que l'action existe dans votre UI avec le nom 'actionAfficherNotesVersion' !!
        try:
            self.main_window.actionAfficherNotesVersion.triggered.connect(self.show_release_notes_dialog)
        except AttributeError:
            print("Avertissement : L'action 'actionAfficherNotesVersion' n'a pas été trouvée dans l'UI. Ajoutez-la au menu Aide.")

    def _get_app_base_path(self):
        """ Détermine le chemin de base de l'application (installée ou dev). """
        if getattr(sys, 'frozen', False):
            # Application compilée (installée)
            return os.path.dirname(sys.executable)
        else:
            # En développement
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Remonter d'un niveau si controller est dans un sous-dossier

    def _read_version_file(self, file_path):
        """ Lit un fichier de version (version.txt ou last_run_version.txt). """
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
        """ Écrit la version actuelle dans last_run_version.txt. """
        config = configparser.ConfigParser()
        config["Version"] = {"value": current_version}
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True) # Crée le dossier data si besoin
            with open(file_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            print(f"Version {current_version} écrite dans {file_path}")
        except Exception as e:
            print(f"Erreur écriture {file_path}: {e}")

    def check_show_release_notes_on_update(self):
        """ Vérifie s'il faut afficher les notes APRES une mise à jour. """
        print("Vérification pour affichage des notes de version post-mise à jour...")
        last_run_version_file = os.path.join(self.data_path, "last_run_version.txt")
        last_run_version_str = self._read_version_file(last_run_version_file)

        print(f"  Version actuelle: {self.current_version_str}")
        print(f"  Dernière version exécutée: {last_run_version_str}")

        try:
            current_v = version.parse(self.current_version_str)
            last_run_v = version.parse(last_run_version_str)

            if current_v > last_run_v:
                print("Nouvelle version détectée, affichage des notes...")
                # On utilise la méthode show_release_notes_dialog pour éviter duplication
                self.show_release_notes_dialog(auto_update_context=True)
                # Mettre à jour le fichier last_run_version APRÈS l'affichage
                self._write_last_run_version(last_run_version_file, self.current_version_str)
            else:
                print("Pas une nouvelle version, pas d'affichage des notes post-màj.")
        except version.InvalidVersion:
            print("Erreur: Version invalide détectée lors vérif post-màj.")
            if last_run_version_str == "0.0.0":
                 self._write_last_run_version(last_run_version_file, self.current_version_str)

    def show_release_notes_dialog(self, auto_update_context=False):
        """ Affiche la boîte de dialogue avec les notes de version. """
        if not auto_update_context:
             print("Affichage manuel des notes de version...")

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

        # Afficher la boîte de dialogue
        dialog = ReleaseNotesDialog(self.current_version_str, notes_content, parent=self.main_window)
        dialog.exec_()

    def create_new_document(self):
        dialog = NewDocumentDialog(self.main_window)
        if dialog.exec_() == QDialog.Accepted:
            doc_type, data = dialog.get_data()
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
            if new_doc:
                doc_page = DocumentPage(title=new_doc.title, document=new_doc)
                idx = self.main_window.tab_widget.addTab(doc_page, doc_page.title)
                self.main_window.tab_widget.setCurrentIndex(idx)
                self.documents[new_doc.title] = doc_page

    def open_document(self):
        # Exemple de création d'un document ouvert
        doc = DocumentPage(title="Document Ouvert", document=None)
        idx = self.main_window.tab_widget.addTab(doc, doc.title)
        self.main_window.tab_widget.setCurrentIndex(idx)
        self.documents[doc.title] = doc

    def close_current_document(self):
        idx = self.main_window.tab_widget.currentIndex()
        # On empêche la fermeture de la page Accueil
        if idx == 0:
            return
        widget = self.main_window.tab_widget.widget(idx)
        self.main_window.tab_widget.removeTab(idx)
        if widget.title in self.documents:
            del self.documents[widget.title]

    def open_profile_page(self):
        if not self.profile_page:
            # Passage de l'objet profil déjà chargé à la page profil
            self.profile_page = ProfilePage(self.profile)
            idx = self.main_window.tab_widget.addTab(self.profile_page, "Profil")
        else:
            idx = self.main_window.tab_widget.indexOf(self.profile_page)
        self.main_window.tab_widget.setCurrentIndex(idx)
