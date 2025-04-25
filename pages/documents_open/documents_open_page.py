# --- Ajout de la liste des mois --- 
MONTHS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]
# --------------------------------

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from datetime import datetime, date

# --- Importer les templates --- 
# (Il faudra les importer dynamiquement ou tous les importer ici)
from pages.templates.rapport_depense_page import RapportDepensePage
# from pages.templates.ecriture_comptable_page import EcritureComptablePage # Exemple
# ... autres imports ...

# --- CORRECTION IMPORT --- 
from models.documents.rapport_depense.rapport_depense import RapportDepense
# -------------------------

class DocumentsOpenPage(QWidget):
    # --- Modifier le constructeur --- 
    def __init__(self, initial_doc_type=None, initial_doc_data=None, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentsOpenPage")
        
        # Stocker les données initiales (pourraient être utilisées plus tard)
        self.initial_doc_type = initial_doc_type
        self.initial_doc_data = initial_doc_data if initial_doc_data is not None else {}

        self._setup_ui()
        # --- Créer le premier onglet --- 
        if self.initial_doc_type:
            self._create_tab(self.initial_doc_type, self.initial_doc_data)
        # -----------------------------
    # -----------------------------

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5) # Ajouter un peu de marge
        main_layout.setSpacing(5)

        # --- Barre d'outils pour ajouter des onglets --- 
        toolbar_layout = QHBoxLayout()
        # TODO: Ajouter des boutons ici pour créer de nouveaux onglets de différents types
        # Ex: btn_new_rapport = QPushButton("Nouveau Rapport Dépense")
        #     btn_new_rapport.clicked.connect(lambda: self._create_tab("Rapport de depense", {}))
        #     toolbar_layout.addWidget(btn_new_rapport)
        #     toolbar_layout.addStretch()
        # --- Fin Barre d'outils ---
        main_layout.addLayout(toolbar_layout)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("DocumentTabWidget")
        self.tab_widget.setDocumentMode(True) 
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        main_layout.addWidget(self.tab_widget) # Ajouter le QTabWidget au layout principal

        self.setLayout(main_layout)

    # --- Nouvelle méthode pour créer un onglet --- 
    def _create_tab(self, doc_type: str, doc_data: dict):
        """Crée la page template et l'ajoute comme onglet."""
        print(f"DocumentsOpenPage: Tentative de création d'onglet type='{doc_type}'")
        page_widget = None
        tab_title = f"{doc_type} - Nouveau" # Titre par défaut

        try:
            if doc_type == "Rapport de depense":
                from models.documents.rapport_depense.rapport_depense import RapportDepense
                from datetime import datetime # Importer datetime ici aussi
                
                # --- Extraire et valider/convertir les données pour le modèle --- 
                try:
                    # Nom de fichier: pour l'instant, générique
                    nom_fichier = f"Rapport_{doc_data.get('nom', 'Inconnu')}_{doc_data.get('date','0000-00')}.json" # Exemple
                    
                    # Date: convertir "Mois-Année" en objet date (1er du mois)
                    date_str = doc_data.get("date", "")
                    date_rapport = None
                    if date_str:
                        try:
                            # Trouver le numéro du mois
                            month_name_fr = date_str.split('-')[0]
                            month_number = MONTHS.index(month_name_fr) + 1
                            year = int(date_str.split('-')[1])
                            date_rapport = date(year, month_number, 1) 
                        except (ValueError, IndexError) as e_date:
                             print(f"Erreur conversion date '{date_str}': {e_date}. Utilisation date actuelle.")
                             date_rapport = date.today().replace(day=1)
                    else:
                         date_rapport = date.today().replace(day=1) # Date par défaut
                         
                    # Autres champs (vérifiés dans le contrôleur, mais récupérer ici)
                    nom_employe = doc_data.get("nom", "")
                    prenom_employe = doc_data.get("prenom", "")
                    emplacement = doc_data.get("emplacements", "") # Clé au pluriel dans get_dynamic_data?
                    departement = doc_data.get("departements", "") # Clé au pluriel?
                    superviseur = doc_data.get("superviseurs", "") # Clé au pluriel?
                    plafond_deplacement = doc_data.get("plafond_deplacement", "")
                    
                    # Instancier le modèle avec les bonnes données
                    new_doc_model = RapportDepense(
                        nom_fichier=nom_fichier,
                        date_rapport=date_rapport,
                        nom_employe=nom_employe,
                        prenom_employe=prenom_employe,
                        emplacement=emplacement,
                        departement=departement,
                        superviseur=superviseur,
                        plafond_deplacement=plafond_deplacement
                        # title sera généré automatiquement dans __init__
                    )
                    print(f"Modèle {type(new_doc_model).__name__} créé: {new_doc_model}")
                    page_widget = RapportDepensePage(document=new_doc_model) 
                    tab_title = new_doc_model.title # Utiliser le titre généré par le modèle

                except KeyError as ke:
                    print(f"ERREUR: Clé manquante dans doc_data lors de la création de RapportDepense: {ke}")
                    raise ValueError(f"Donnée manquante : {ke}") # Propage l'erreur
                except Exception as e_model:
                    print(f"ERREUR lors de l'instanciation du modèle RapportDepense: {e_model}")
                    raise # Propage l'erreur
                    
            # elif doc_type == "Ecriture comptable":
                # from models.documents.ecriture_comptable import EcritureComptable
                # new_doc_model = EcritureComptable(...) 
                # from pages.templates.ecriture_comptable_page import EcritureComptablePage
                # page_widget = EcritureComptablePage(document=new_doc_model)
            # ... autres types ...
            else:
                print(f"Type de document '{doc_type}' non géré pour la création d'onglet.")
                page_widget = QLabel(f"Template non trouvé pour {doc_type}")
                page_widget.setAlignment(Qt.AlignCenter)
                tab_title = f"Erreur - {doc_type}"

            if page_widget:
                self.add_document_tab(page_widget, tab_title)

        except ImportError as ie:
             print(f"ERREUR D'IMPORT dans DocumentsOpenPage._create_tab: {ie}")
             # Afficher l'erreur dans un onglet?
             error_widget = QLabel(f"Erreur Import: {ie}")
             self.add_document_tab(error_widget, f"Erreur Import - {doc_type}")
        except Exception as e:
            print(f"ERREUR GÉNÉRALE dans DocumentsOpenPage._create_tab: {e}")
            import traceback
            traceback.print_exc()
            error_widget = QLabel(f"Erreur Création: {e}")
            self.add_document_tab(error_widget, f"Erreur Création - {doc_type}")
    # --------------------------------------------

    def add_document_tab(self, page_widget: QWidget, title: str):
        """Ajoute une page template de document comme nouvel onglet."""
        index = self.tab_widget.addTab(page_widget, title)
        self.tab_widget.setCurrentIndex(index) # Sélectionner le nouvel onglet
        print(f"DocumentsOpenPage: Onglet ajoutée: '{title}'")

    def close_tab(self, index):
        """Slot pour fermer l'onglet demandé."""
        widget = self.tab_widget.widget(index)
        if widget:
            print(f"DocumentsOpenPage: Fermeture de l'onglet '{self.tab_widget.tabText(index)}' (index {index})")
            # Optionnel: Logique de sauvegarde ici avant deleteLater()
            widget.deleteLater() # Supprimer le widget de la page template
            self.tab_widget.removeTab(index)

# Bloc de test
if __name__ == '__main__':
    # Le test existant fonctionne toujours mais n'utilise pas le nouveau constructeur
    # Pour tester la création initiale:
    # app = QApplication(sys.argv)
    # initial_data = {'nom': 'Test Initial', 'montant': 50}
    # container_page = DocumentsOpenPage(initial_doc_type="Rapport de depense", initial_doc_data=initial_data)
    # container_page.show()
    # sys.exit(app.exec_())
    pass # Désactiver l'ancien test pour l'instant 