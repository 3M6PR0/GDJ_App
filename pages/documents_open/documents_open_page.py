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
import logging # AJOUT

# --- Importer DraggableTabBar ---
from ui.components.draggable_tab_bar import DraggableTabBar
# --------------------------------

# --- Importer les templates --- 
# (Il faudra les importer dynamiquement ou tous les importer ici)
from pages.templates.rapport_depense_page import RapportDepensePage
from pages.templates.lamicoid_page import LamicoidPage # AJOUT IMPORT
from pages.documents.lamicoid_2_page import Lamicoid2Page # AJOUT IMPORT LAMICOID 2
# from pages.templates.ecriture_comptable_page import EcritureComptablePage # Exemple
# ... autres imports ...

# --- CORRECTION IMPORT --- 
from models.documents.rapport_depense.rapport_depense import RapportDepense
from models.documents.lamicoid.lamicoid import LamicoidDocument # AJOUT IMPORT
# -------------------------

logger = logging.getLogger('GDJ_App') # OBTENIR LE LOGGER

class DocumentsOpenPage(QWidget):
    # --- AJOUT SIGNAL --- 
    tab_closed_signal = pyqtSignal(int)
    # ------------------
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
        separator.setObjectName("VerticalPageSeparator")
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
            logger.warning(f"WARN: Erreur application palette à DocumentContentArea: {e}")
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0) # Pas d'espacement avant le TabWidget

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("DocumentTabWidget")
        # --- Utiliser DraggableTabBar ---
        self.tab_widget.setTabBar(DraggableTabBar(self.tab_widget))
        # --------------------------------
        self.tab_widget.setDocumentMode(True) 
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True) # Important pour le réarrangement interne et le look
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
        is_lamicoid = False # AJOUT
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
                elif isinstance(active_document, LamicoidDocument): # AJOUT
                    is_lamicoid = True # AJOUT
                    doc_type_display = "Lamicoid" # AJOUT
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
            # Formater la date manuellement en français
            try:
                month_name_fr = MONTHS[active_document.date_rapport.month - 1] # Les mois de datetime.date sont 1-12
                year_str = str(active_document.date_rapport.year)
                date_text = f"{month_name_fr} {year_str}"
                logger.debug(f"[DATE_DEBUG] Sidebar date formatted as: {date_text}") # Log ajouté pour confirmation
            except IndexError:
                # Fallback si le mois est hors limites (ne devrait pas arriver avec un objet date valide)
                date_text = active_document.date_rapport.strftime('%d/%m/%Y') # Format numérique sûr
                logger.error(f"Mois invalide ({active_document.date_rapport.month}) pour la date du rapport. Utilisation du format numérique.")
            except AttributeError:
                date_text = "Erreur date"
                logger.error("Erreur: active_document.date_rapport n'existe pas ou n'est pas un objet date.")
            
            # Mettre à jour chaque label
            self.sidebar_labels.get("nom_employe").setText(active_document.nom_employe or "-")
            self.sidebar_labels.get("prenom_employe").setText(active_document.prenom_employe or "-")
            self.sidebar_labels.get("date_rapport").setText(date_text or "-") # Utilise le date_text formaté
            self.sidebar_labels.get("emplacement").setText(active_document.emplacement or "-")
            self.sidebar_labels.get("departement").setText(active_document.departement or "-")
            self.sidebar_labels.get("superviseur").setText(active_document.superviseur or "-")
            self.sidebar_labels.get("plafond_deplacement").setText(str(active_document.plafond_deplacement) or "-") # Assurer str

        elif is_lamicoid and active_document:
            # Vider les labels si ce n'est pas un RapportDepense (ou Lamicoid avec infos spécifiques)
            for key, label in self.sidebar_labels.items():
                if key == "nom_employe": # Exemple: utiliser "nom_employe" pour afficher le profil Lamicoid
                    label.setText(active_document.profile_name or "-")
                elif key == "date_rapport": # Exemple: utiliser "date_rapport" pour la date de création
                    label.setText(active_document.date_creation_doc.strftime("%Y-%m-%d") if active_document.date_creation_doc else "-")
                else:
                    label.setText("-") # Vider les autres champs non pertinents pour Lamicoid
        else:
            # Vider les labels si ce n'est pas un RapportDepense (ou Lamicoid avec active_document, ou pas d'active_document)
            for key, label in self.sidebar_labels.items():
                label.setText("-")

    def add_new_document_to_tabs(self, doc_type: str, doc_data: dict):
        """Interface publique pour créer une page pour le document et l'ajouter comme nouvel onglet."""
        logger.info(f"DocumentsOpenPage: Demande publique d'ajout d'onglet type='{doc_type}'")
        self._create_tab(doc_type, doc_data) # Réutiliser la logique existante de _create_tab

    # --- Nouvelle méthode pour créer un onglet --- 
    def _create_tab(self, doc_type: str, doc_data: dict):
        """Crée la page template et l'ajoute comme onglet."""
        logger.info(f"DocumentsOpenPage: Tentative de création d'onglet type='{doc_type}', données: {doc_data}")
        page_widget = None
        tab_title = f"{doc_type} - Nouveau" # Titre par défaut
        document_to_pass = None # Pour stocker soit le nouvel objet, soit l'objet chargé

        try:
            if doc_type == "Rapport de depense": # Garder la casse pour correspondre aux logs/types existants
                # Vérifier si on charge un objet existant ou si on en crée un nouveau
                if 'loaded_object' in doc_data and isinstance(doc_data['loaded_object'], RapportDepense):
                    document_to_pass = doc_data['loaded_object']
                    tab_title = document_to_pass.title if document_to_pass.title else "Rapport de dépense"
                    logger.info(f"Chargement d'un RapportDepense existant: {tab_title}")
                else:
                    # Logique de création pour RapportDeDepense...
                    nom = doc_data.get('nom', '')
                    prenom = doc_data.get('prenom', '')
                    date_str = doc_data.get('date', datetime.now().strftime('%Y-%m')) # ex: "2023-12"
                    
                    # Construction du titre
                    title_parts = [doc_type]
                    if nom and prenom:
                        title_parts.append(f"{nom} {prenom}")
                    title_parts.append(date_str)
                    tab_title = " - ".join(title_parts)

                    # Convertir la date du formulaire (ex: "Décembre-2023") en objet date pour le modèle
                    try:
                        month_str, year_str = doc_data['date'].split('-')
                        month_int = MONTHS.index(month_str) + 1
                        report_date = date(int(year_str), month_int, 1) # 1er jour du mois
                    except (ValueError, KeyError, AttributeError) as e:
                        logger.warning(f"Date invalide pour nouveau Rapport de Dépense: {doc_data.get('date')}, erreur: {e}. Utilisation de la date actuelle.")
                        report_date = date.today() # Fallback

                    # Générer un nom de fichier initial pour un nouveau rapport
                    # Ce nom sera utilisé par le constructeur et pourra être mis à jour lors de la première sauvegarde réelle.
                    current_time_str = datetime.now().strftime("%Y%m%d%H%M%S")
                    initial_file_name = f"RapportDepense_{current_time_str}.rdj"

                    document_to_pass = RapportDepense(
                        nom_fichier=initial_file_name, # RESTAURÉ ET FOURNI
                        title=tab_title, 
                        nom_employe=doc_data.get('nom'),
                        prenom_employe=doc_data.get('prenom'),
                        date_rapport=report_date, 
                        emplacement=doc_data.get('emplacements'),
                        departement=doc_data.get('departements'),
                        superviseur=doc_data.get('superviseurs'),
                        plafond_deplacement=doc_data.get('plafond_deplacement'),
                    )
                page_widget = RapportDepensePage(document=document_to_pass)
            
            elif doc_type == "Lamicoid": # AJOUT DE LA LOGIQUE POUR LAMICOID
                if 'loaded_object' in doc_data and isinstance(doc_data['loaded_object'], LamicoidDocument):
                    document_to_pass = doc_data['loaded_object']
                    tab_title = document_to_pass.title if document_to_pass.title else "Lamicoid"
                else:
                    # Création d'un nouveau LamicoidDocument
                    numero_reference = doc_data.get('numero_reference', 'N/A')
                    # La date dans doc_data est déjà au format "YYYY-MM-DD" ou "Mois-Année"
                    # LamicoidDocument attend une date (objet date) pour date_creation_doc
                    # et LamicoidItem attend une chaîne "YYYY-MM-DD" pour date_item
                    date_creation_doc_obj = date.today() # Valeur par défaut
                    date_form_value = doc_data.get('date', '') # ex: "Mai-2025" ou "2025-05-15"
                    
                    try:
                        if '-' in date_form_value and any(m in date_form_value for m in MONTHS): # Format "Mois-Année"
                            month_str, year_str = date_form_value.split('-')
                            month_int = MONTHS.index(month_str) + 1
                            date_creation_doc_obj = date(int(year_str), month_int, 1)
                        elif '-' in date_form_value and len(date_form_value.split('-')) == 3 : # Format "YYYY-MM-DD"
                             date_creation_doc_obj = date.fromisoformat(date_form_value)
                        else: # Fallback ou format non reconnu
                            logger.warning(f"Format de date non reconnu pour Lamicoid: {date_form_value}. Utilisation de la date du jour.")
                    except (ValueError, KeyError, AttributeError, TypeError) as e:
                        logger.warning(f"Date invalide pour nouveau Lamicoid: {date_form_value}, erreur: {e}. Utilisation de la date du jour.")

                    # Pour l'instant, laissons Preference s'en charger.
                    
                    # Tentative de récupérer profile_name depuis les données (si passé par DocumentsTypeSelectionController)
                    # Sinon, LamicoidDocument utilisera celui des préférences par défaut.
                    profile_name_from_data = doc_data.get('profile_name', None) # Récupère profile_name s'il existe dans doc_data


                    base_file_name = f"Lamicoid_{numero_reference}_{date_creation_doc_obj.strftime('%Y-%m-%d')}.json"
                    default_title = f"Lamicoid - {numero_reference} ({date_creation_doc_obj.strftime('%Y-%m-%d')})"

                    # document_to_pass = LamicoidDocument(
                    #     file_name=base_file_name, 
                    #     title=default_title,
                    #     date_creation_doc=date_creation_doc_obj,
                    #     profile_name=profile_name_from_data 
                    # )
                    # if profile_name_from_data: 
                    #     document_to_pass.profile_name = profile_name_from_data
                    
                    # tab_title = document_to_pass.title # Devrait être default_title ici
                    tab_title = default_title # Utiliser le titre généré

                page_widget = LamicoidPage() 
                
                # On garde la création du document pour la sidebar et le titre de l'onglet
                # mais il n'est plus passé directement à LamicoidPage
                # Correction de l'instanciation de LamicoidDocument
                document_for_sidebar_and_title = LamicoidDocument(
                    file_name=base_file_name, 
                    title=tab_title, # Utiliser le tab_title généré
                    date_creation_doc=date_creation_doc_obj, # Extrait de doc_data['date']
                    profile_name=profile_name_from_data # Extrait de doc_data['profile_name'] ou None
                )
                # Associer ce document au widget pour que la sidebar puisse le trouver
                page_widget.document = document_for_sidebar_and_title

            elif doc_type == "Lamicoid 2":
                logger.debug(f"Création de la page pour: {doc_type}")
                page_widget = Lamicoid2Page()
                tab_title = "Nouveau Lamicoid"

            # --- GÉRER LES AUTRES TYPES DE DOCUMENTS (PAS ENCORE IMPLÉMENTÉ POUR LE CHARGEMENT) ---
            # elif doc_type == "Ecriture Comptable":
            #     # from pages.templates.ecriture_comptable_page import EcritureComptablePage
            #     # page_widget = EcritureComptablePage(data=doc_data)
            #     # tab_title = f"Écriture Comptable - {doc_data.get('titre', 'Nouveau')}"
            #     pass 
            else:
                logger.warning(f"Type de document '{doc_type}' non géré pour la création d'onglet.")
                # Afficher un onglet d'erreur ou placeholder
                error_label = QLabel(f"Type de document non supporté: {doc_type}")
                error_label.setAlignment(Qt.AlignCenter)
                self.add_document_tab(error_label, "Erreur Type")
                return

            if page_widget:
                self.add_document_tab(page_widget, tab_title)
            else:
                # Ce cas ne devrait pas être atteint si la logique ci-dessus est correcte
                logger.error("page_widget est None, aucun onglet n'a été créé.")
                self.add_document_tab(QLabel(f"Erreur: Impossible de créer la page pour {doc_type}"), "Erreur Inconnue")

        except ImportError as ie:
            logger.error(f"Erreur d'importation pour le type '{doc_type}': {ie}")
            error_label = QLabel(f"Erreur chargement module pour: {doc_type}.\n{ie}")
            error_label.setAlignment(Qt.AlignCenter)
            self.add_document_tab(error_label, "Erreur Module")
        except Exception as e:
            logger.error(f"Erreur générale lors de la création de l'onglet '{doc_type}': {e}", exc_info=True)
            error_label = QLabel(f"Erreur inattendue pour: {doc_type}.\n{e}")
            error_label.setAlignment(Qt.AlignCenter)
            self.add_document_tab(error_label, "Erreur Critique")

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
                    # Revenir à la tentative sur l'index avec QColor
                    # --- Supprimer les tentatives de couleur qui échouent --- 
                    # self.tab_widget.tabBar().setTabBackgroundColor(index, QColor(accent_color_hex))
                    # self.tab_widget.tabBar().setTabTextColor(index, QColor(accent_color_hex)) 
                    # print(f"Tentative de setTabBackgroundColor/TextColor sur index {index}")

                    # --- Définir l'icône PRINCIPALE de l'onglet --- 
                    main_icon_name = "round_receipt_long.png" # Icône pour rapport
                    main_icon_path = get_icon_path(main_icon_name)
                    if main_icon_path:
                        self.tab_widget.setTabIcon(index, QIcon(main_icon_path))
                        logger.info(f"Icône principale {main_icon_name} appliquée à l'onglet {index} ({title})")
                    else:
                        logger.warning(f"Icône principale {main_icon_name} non trouvée pour l'onglet.")
                    
                    # --- Tenter de définir l'icône du bouton 'X' via setStyleSheet sur tabBar --- 
                    close_icon_name = "round_close.png"
                    close_icon_path = get_icon_path(close_icon_name)
                    if close_icon_path:
                        # Échapper les backslashes pour QSS url() sur Windows
                        qss_path = close_icon_path.replace('\\', '/')
                        style_sheet_str = f"QTabBar::close-button {{ image: url('{qss_path}'); width: 16px; height: 16px; }}"
                        self.tab_widget.tabBar().setStyleSheet(style_sheet_str)
                        logger.info(f"Tentative d'appliquer setStyleSheet pour close-button icon {close_icon_name}")
                    else:
                        logger.warning(f"Icône close {close_icon_name} non trouvée.")
                    # ----------------------------------------------------------------------------

                except Exception as e_color:
                    logger.warning(f"Erreur application couleur/icône onglet Rapport Dépense (Index): {e_color}", exc_info=True)

                # Laisser l'icône appliquée même si la couleur échoue

            else:
                logger.warning(f"Impossible d'appliquer style différé, onglet {index} n'existe plus.")
        except Exception as e:
            logger.warning(f"Erreur application couleur différée onglet Rapport Dépense: {e}", exc_info=True)

    def close_tab(self, index):
        """Slot pour fermer l'onglet demandé."""
        widget = self.tab_widget.widget(index)
        if widget:
            tab_text = self.tab_widget.tabText(index)
            logger.info(f"DocumentsOpenPage: Fermeture de l'onglet '{tab_text}' (index {index})")
            # Optionnel: Logique de sauvegarde ici avant deleteLater()
            widget.deleteLater() # Supprimer le widget de la page template
            self.tab_widget.removeTab(index)
            # --- Émettre le signal avec le nombre d'onglets restants ---
            remaining_tabs = self.tab_widget.count()
            logger.debug(f"DocumentsOpenPage: Onglet fermé. Onglets restants: {remaining_tabs}. Émission de tab_closed_signal.")
            self.tab_closed_signal.emit(remaining_tabs)
            # ------------------------------------------------------------

    def close_current_tab(self):
        """Ferme l'onglet actuellement sélectionné."""
        current_index = self.tab_widget.currentIndex()
        if current_index != -1: # S'assurer qu'un onglet est bien sélectionné
            logger.info(f"DocumentsOpenPage: Demande de fermeture de l'onglet courant (index {current_index}).")
            self.close_tab(current_index) # Réutiliser la logique existante
        else:
            logger.info("DocumentsOpenPage: Aucun onglet sélectionné à fermer.")

    def close_all_tabs(self):
        """Ferme tous les onglets ouverts."""
        logger.info("DocumentsOpenPage: Demande de fermeture de tous les onglets.")
        # Boucler à l'envers pour éviter les problèmes d'indexation pendant la suppression
        for i in range(self.tab_widget.count() - 1, -1, -1):
            self.close_tab(i) # Réutiliser la logique existante
        logger.info("DocumentsOpenPage: Tous les onglets ont été fermés.")

    # --- NOUVELLE MÉTHODE POUR RÉCUPÉRER L'OBJET DOCUMENT ACTIF ---
    def get_active_document_object(self):
        """Retourne l'objet document (par exemple, RapportDepense) de l'onglet actuellement actif."""
        current_index = self.tab_widget.currentIndex()
        if current_index == -1: # Aucun onglet sélectionné ou aucun onglet
            logger.debug("DocumentsOpenPage: Aucun onglet actif, impossible de récupérer l'objet document.")
            return None

        current_page_widget = self.tab_widget.widget(current_index)
        if current_page_widget and hasattr(current_page_widget, 'document'):
            logger.debug(f"DocumentsOpenPage: Document actif récupéré: {type(current_page_widget.document).__name__}")
            return current_page_widget.document
        else:
            if not current_page_widget:
                logger.warning("DocumentsOpenPage: Aucun widget trouvé pour l'onglet actif.")
            elif not hasattr(current_page_widget, 'document'):
                logger.warning(f"DocumentsOpenPage: Le widget de l'onglet actif ({type(current_page_widget).__name__}) n'a pas d'attribut 'document'.")
            return None
    # ---------------------------------------------------------------

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