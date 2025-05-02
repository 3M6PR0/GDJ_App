# --- Ajout de la liste des mois --- 
MONTHS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]
# --------------------------------

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame as QtFrame, QSpacerItem, QSizePolicy,
                             QStackedWidget, QButtonGroup, QAbstractButton,
                             QTabWidget, QFormLayout)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot as Slot, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPalette
from utils.theme import get_theme_vars
from utils.icon_loader import get_icon_path
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
        
        # --- Initialiser les labels de la sidebar --- 
        self.sidebar_title_label = None
        self.sidebar_info_layout = None # Layout pour les détails
        self.sidebar_labels = {} # Dictionnaire pour stocker les labels de valeur
        # ------------------------------------------
        
        # Stocker les données initiales (pourraient être utilisées plus tard)
        self.initial_doc_type = initial_doc_type
        self.initial_doc_data = initial_doc_data if initial_doc_data is not None else {}

        self._setup_ui()
        # --- Créer le premier onglet --- 
        if self.initial_doc_type:
            self._create_tab(self.initial_doc_type, self.initial_doc_data)
        else:
            # Mettre à jour le titre même si aucun onglet n'est créé initialement
            self._update_sidebar(self.tab_widget.currentIndex()) 
        # -----------------------------
    # -----------------------------

    def _setup_ui(self):
        # Layout principal Horizontal pour Sidebar + Contenu
        page_layout = QHBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        # --- Barre Latérale Gauche ---
        sidebar_widget = QtFrame()
        sidebar_widget.setObjectName("Sidebar") # Pour hériter du style global
        sidebar_widget.setFixedWidth(200) 

        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(10, 15, 10, 15) 
        sidebar_layout.setSpacing(10)

        # Label pour le titre du document actif (initialement vide)
        self.sidebar_title_label = QLabel("Aucun document ouvert")
        self.sidebar_title_label.setObjectName("SidebarTitleLabel")
        self.sidebar_title_label.setStyleSheet("font-weight: bold; font-size: 14px;") # Garder le style du texte
        self.sidebar_title_label.setWordWrap(True)
        self.sidebar_title_label.setAlignment(Qt.AlignCenter) # Centrer le titre
        sidebar_layout.addWidget(self.sidebar_title_label) # Titre en premier

        # --- Ajouter un stretch avant le premier item --- 
        sidebar_layout.addStretch(1)
        # ------------------------------------------------

        # Créer les labels pour chaque champ (initialement vides)
        info_fields = {
            "nom_employe": "Nom:",
            "prenom_employe": "Prénom:",
            "date_rapport": "Date Rapport:",
            "emplacement": "Emplacement:",
            "departement": "Département:",
            "superviseur": "Superviseur:",
            "plafond_deplacement": "Plafond Dép.:"
        }

        # --- Ajouter les informations spécifiques verticalement --- 
        for key, item_text in info_fields.items():
            item_label = QLabel(item_text)
            item_label.setObjectName("SidebarInfoItemLabel") # Style pour l'item
            # --- Distinguer l'item: Mettre en gras --- 
            item_label.setStyleSheet("font-weight: bold;")
            # -----------------------------------------

            value_label = QLabel("-") # Placeholder initial pour la valeur
            value_label.setObjectName("SidebarInfoValue")
            value_label.setWordWrap(True)
            self.sidebar_labels[key] = value_label # Stocker la référence au label de valeur

            sidebar_layout.addWidget(item_label)    # Ajouter "Nom:"
            sidebar_layout.addWidget(value_label)  # Ajouter "-" (sera mis à jour)
            # --- Ajouter un stretch entre les paires --- 
            sidebar_layout.addStretch(1)
            # -------------------------------------------

        sidebar_layout.addStretch() # Pousse le tout vers le haut
        # ---------------------------------------------------------

        page_layout.addWidget(sidebar_widget) # Ajouter la sidebar

        # --- Séparateur Vertical ---
        separator = QtFrame()
        separator.setFrameShape(QtFrame.VLine)
        separator.setFrameShadow(QtFrame.Sunken)
        page_layout.addWidget(separator)
        
        # --- Zone Contenu Droite (avec le TabWidget) ---
        content_widget = QWidget() # Widget conteneur pour le TabWidget
        content_widget.setObjectName("DocumentContentArea")
        # Essayer de définir le fond via QPalette
        try:
            theme = get_theme_vars()
            bg_color_hex = theme.get("COLOR_PRIMARY_DARK", "#313335")
            palette = content_widget.palette()
            palette.setColor(QPalette.Window, QColor(bg_color_hex))
            content_widget.setPalette(palette)
            content_widget.setAutoFillBackground(True) # Nécessaire avec setPalette
        except Exception as e:
            print(f"WARN: Erreur application palette à DocumentContentArea: {e}")
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0) # Pas d'espacement avant le TabWidget

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("DocumentTabWidget")
        self.tab_widget.setDocumentMode(True) 
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        # Connecter le changement d'onglet à la mise à jour du titre
        self.tab_widget.currentChanged.connect(self._update_sidebar) 
        
        content_layout.addWidget(self.tab_widget) # Ajouter QTabWidget au layout de contenu
        page_layout.addWidget(content_widget, 1) # Ajouter zone de contenu, prend l'espace restant

    @Slot(int)
    def _update_sidebar(self, index):
        """Met à jour la barre latérale avec les informations du document de l'onglet courant."""
        current_widget = self.tab_widget.widget(index)
        
        doc_type_display = "Aucun document"
        is_rapport_depense = False
        active_document = None
        
        if current_widget:
            # Essayer de récupérer l'objet document lui-même
            if hasattr(current_widget, 'document'):
                active_document = current_widget.document
                if isinstance(active_document, RapportDepense):
                    is_rapport_depense = True
                    # --- Correction Titre: Utiliser le type explicitement ---
                    doc_type_display = "Rapport de dépense" 
                    # ------------------------------------------------------
                elif active_document is not None:
                    # Utiliser le nom de la classe pour les autres types
                    doc_type_display = type(active_document).__name__.replace('_', ' ').capitalize() 
            else:
                 # Fallback sur le texte de l'onglet si pas d'objet document
                 tab_text = self.tab_widget.tabText(index)
                 # Essayer d'extraire un type plus propre du texte de l'onglet si possible
                 if tab_text and " - " in tab_text:
                     doc_type_display = tab_text.split(" - ")[0]
                 elif tab_text:
                     doc_type_display = tab_text
                 else:
                      doc_type_display = "Onglet" # Dernier recours
        
        # Mettre à jour le label titre (peut-être sans le gras si ça pose problème)
        # self.sidebar_title_label.setText(f"<b>{doc_type_display}</b>") 
        self.sidebar_title_label.setText(doc_type_display) # Version simple

        # --- Mettre à jour les labels d'information spécifiques --- 
        if is_rapport_depense and active_document:
            # Formater la date
            date_text = active_document.date_rapport.strftime('%B %Y')
            
            # Mettre à jour chaque label
            self.sidebar_labels.get("nom_employe").setText(active_document.nom_employe or "-")
            self.sidebar_labels.get("prenom_employe").setText(active_document.prenom_employe or "-")
            self.sidebar_labels.get("date_rapport").setText(date_text or "-")
            self.sidebar_labels.get("emplacement").setText(active_document.emplacement or "-")
            self.sidebar_labels.get("departement").setText(active_document.departement or "-")
            self.sidebar_labels.get("superviseur").setText(active_document.superviseur or "-")
            self.sidebar_labels.get("plafond_deplacement").setText(str(active_document.plafond_deplacement) or "-") # Assurer str

        else:
            # Vider les labels si ce n'est pas un RapportDepense
            for label in self.sidebar_labels.values():
                label.setText("-")

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
                # --- Stocker le type de document sur le widget de page ---
                page_widget.setProperty("doc_type", doc_type)
                # ----------------------------------------------------------
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
        self.tab_widget.setCurrentIndex(index)
        # --- Coloration spécifique pour RapportDepensePage (différée) ---
        if isinstance(page_widget, RapportDepensePage):
            # Utiliser QTimer.singleShot pour appliquer la couleur après le cycle d'événements actuel
            QTimer.singleShot(0, lambda idx=index, tab_title=title: self._apply_tab_color(idx, tab_title))
        # ------------------------------------------------------------

    def _apply_tab_color(self, index, title):
        """Applique la couleur de fond et texte à un onglet spécifique."""
        try:
            theme = get_theme_vars()
            accent_color_hex = theme.get("COLOR_ACCENT", "#007ACC")
            text_color_hex = theme.get("COLOR_TEXT_ON_ACCENT", "#ffffff")
            
            # Vérifier si l'index est toujours valide (l'onglet pourrait avoir été fermé)
            if index < self.tab_widget.count():
                # Appliquer le style directement au tabBar avec !important
                style_str = f"""QTabBar::tab:selected {{ 
                                     background-color: {accent_color_hex} !important; 
                                     color: {text_color_hex} !important; 
                                 }}
                                 QTabBar::tab:!selected {{ 
                                     /* Peut-être une couleur différente pour non sélectionné? */ 
                                     /* background-color: {theme.get('COLOR_PRIMARY_MEDIUM', '#3c3f41')} !important; */ 
                                     /* color: {theme.get('COLOR_TEXT_SECONDARY', '#808080')} !important; */ 
                                 }}"""
                # Note: Appliquer au tabBar affectera potentiellement TOUS les onglets
                # si on ne trouve pas un moyen de cibler via QSS. 
                # Tentons de ne changer que la couleur de l'onglet courant via l'index
                # comme avant, mais sur le tabBar lui-même.
                try:
                    # Cibler via index ne marche pas dans setStyleSheet
                    # Essayons de définir des propriétés et utiliser QSS?
                    # self.tab_widget.widget(index).setProperty("isSpecialTab", True)
                    # self.tab_widget.tabBar().setStyleSheet("QTabBar::tab[isSpecialTab="true"] { background-color: ... }")
                    # Ne fonctionne probablement pas.
                    
                    # Revenir à la tentative sur l'index avec QColor
                    self.tab_widget.tabBar().setTabBackgroundColor(index, QColor(accent_color_hex))
                    self.tab_widget.tabBar().setTabTextColor(index, QColor(accent_color_hex)) # Texte accent sur fond indéfini
                    print(f"Tentative de setTabBackgroundColor/TextColor sur index {index}")

                    # Garder l'icône
                    icon_name = "round_receipt_long.png" # Icône pour rapport
                    icon_path = get_icon_path(icon_name)
                    if icon_path:
                        self.tab_widget.setTabIcon(index, QIcon(icon_path))
                        print(f"Icône {icon_name} appliquée à l'onglet {index} ({title})")
                    else:
                        print(f"WARN: Icône {icon_name} non trouvée pour l'onglet.")

                except Exception as e_color:
                    print(f"WARN: Erreur application couleur/icône onglet Rapport Dépense (Index): {e_color}")

                # Laisser l'icône appliquée même si la couleur échoue

            else:
                print(f"WARN: Impossible d'appliquer style différé, onglet {index} n'existe plus.")
        except Exception as e:
            print(f"WARN: Erreur application couleur différée onglet Rapport Dépense: {e}")

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