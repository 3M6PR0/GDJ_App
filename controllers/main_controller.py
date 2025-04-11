from PyQt5.QtWidgets import QDialog
from dialogs.new_document_dialog import NewDocumentDialog
from pages.home_page import HomePage
from pages.document_page import DocumentPage
from pages.profile_page import ProfilePage
from models.profile import Profile

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

        # Connecter les actions du menu
        self.main_window.action_new.triggered.connect(self.create_new_document)
        self.main_window.action_open.triggered.connect(self.open_document)
        self.main_window.action_close.triggered.connect(self.close_current_document)
        self.main_window.action_profile.triggered.connect(self.open_profile_page)

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
