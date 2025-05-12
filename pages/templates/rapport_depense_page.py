from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout, 
                           QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox, 
                           QPushButton, QHBoxLayout, QMessageBox,
                           QGridLayout, QFrame, QCheckBox, QRadioButton, QButtonGroup,
                           QSizePolicy, QFileDialog, QScrollArea, QSpacerItem)
from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QDoubleValidator, QIcon, QColor, QPalette, QFont, QPixmap, QIntValidator, QImage
from datetime import date # <--- Ajout import
import calendar # AJOUT IMPORT
from ui.components.frame import Frame # Correction: Chemin d'importation correct
from models.documents.rapport_depense import RapportDepense, Deplacement, Repas, Depense, Facture # Importer les modèles
from utils.theme import get_theme_vars, RADIUS_BOX # Importer les variables de thème
from utils.icon_loader import get_icon_path # Importer la fonction pour obtenir le chemin de l'icône
from utils.signals import signals
from widgets.custom_date_edit import CustomDateEdit
from widgets.numeric_input_with_unit import NumericInputWithUnit # <<< S'ASSURER QUE CET IMPORT EST PRÉSENT ET CORRECT
from ui.components.card import CardWidget # Importer le widget card renommé
from widgets.thumbnail_widget import ThumbnailWidget
import traceback # Importer traceback pour débogage
# --- AJOUT: Tentative d'import de fitz et définition de PYMUPDF_AVAILABLE --- 
try:
    import fitz # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None # Définir fitz à None si l'import échoue
    PYMUPDF_AVAILABLE = False
    # print("Avertissement: PyMuPDF (fitz) n'est pas installé. Les miniatures PDF ne seront pas disponibles.") # MODIFICATION
    logger.warning("PyMuPDF (fitz) n'est pas installé. Les miniatures PDF ne seront pas disponibles.") # MODIFICATION
# --------------------------------------------------------------------------
import os # Pour manipuler les chemins
# --- AJOUT: Import MediaViewer --- 
from windows.media_viewer import MediaViewer
# ---------------------------------
import functools # <--- AJOUT
import copy       # <--- AJOUT pour deepcopy
import logging

# --- AJOUT IMPORT CONFIGDATA ---
from models.config_data import ConfigData # DÉCOMMENTÉ & CORRIGÉ CHEMIN
# -----------------------------

# --- AJOUT IMPORT QMESSAGEBOX ---
from PyQt5.QtWidgets import QMessageBox # AJOUT
# -------------------------------

# Supposer qu'une classe RapportDepense existe dans vos modèles
# from models.documents.rapport_depense import RapportDepense

logger = logging.getLogger('GDJ_App')

class RapportDepensePage(QWidget):
    def __init__(self, document: RapportDepense, parent=None):
        super().__init__(parent)
        self.setObjectName("RapportDepensePage")
        self.document = document # Garder une référence au modèle de données
        self.num_commande_repas_label = None
        self.num_commande_repas_field = None
        self.num_commande_container = None
        self.payeur_group = None # Pour groupe Payeur
        self.refacturer_group = None # Pour groupe Refacturer
        self.editing_entry = None # Garde la référence de l'entrée en cours d'édition
        self.cancel_button = None # Référence au bouton Annuler (créé si besoin)
        self._original_frame_style = "" # Pour sauvegarder le style du frame en mode édition
        
        self.total_rembourse_deplacement_label_value = QLabel("0.00 $")
        self.total_rembourse_deplacement_label_value.setStyleSheet("font-weight: bold;") # CORRECTION: Application du style gras

        # AJOUT: Initialisation des labels pour les nouveaux frames Repas et Dépenses Diverses
        self.total_repas_valeur_label = QLabel("0.00 $")
        self.total_repas_valeur_label.setStyleSheet("font-weight: bold;")
        self.total_depenses_diverses_valeur_label = QLabel("0.00 $")
        self.total_depenses_diverses_valeur_label.setStyleSheet("font-weight: bold;")
        
        # --- Stockage des miniatures --- 
        self.current_facture_thumbnails = {} # { file_path: ThumbnailWidget }
        # --- AJOUT: Liste pour garder références viewers (si non modaux) --- 
        # self.open_viewers = [] # Décommenter si on passe en non-modal
        # ---------------------------------------------------------------
        
        # --- Styles spécifiques pour les RadioButton --- 
        self.setStyleSheet("""
            /* Seuls les styles RadioButton restent ici */
            QRadioButton#FormRadioButton {
                spacing: 5px; /* Espace entre indicateur et texte */
                color: #D0D0D0; /* Couleur du texte (exemple gris clair) - À AJUSTER */
            }
            QRadioButton#FormRadioButton::indicator {
                width: 16px; /* Taille légèrement plus grande */
                height: 16px;
            }
            QRadioButton#FormRadioButton::indicator::unchecked {
                /* Apparence quand non coché */
                border: 1px solid #555; /* Bordure grise foncée - À AJUSTER */
                background-color: #333; /* Fond gris très foncé - À AJUSTER */
                border-radius: 4px; /* Coins arrondis (carré) - Ajustez si besoin */
            }
            QRadioButton#FormRadioButton::indicator::checked {
                /* Apparence quand coché */
                border: 1px solid #1E88E5; /* Bordure bleue (exemple) - À AJUSTER */
                background-color: #1E88E5; /* Fond bleu - À AJUSTER */
                border-radius: 4px; /* Coins arrondis */
                /* Optionnel: petit point intérieur ou icône */
                /* image: url(:/icons/radio_checked.png); */ 
            }
            QRadioButton#FormRadioButton::indicator::checked::hover {
                border: 1px solid #42A5F5; /* Bleu plus clair au survol si coché - À AJUSTER */
                background-color: #42A5F5; /* À AJUSTER */
            }
            QRadioButton#FormRadioButton::indicator::unchecked::hover {
                border: 1px solid #777; /* Gris plus clair au survol si non coché - À AJUSTER */
            }
        """)
        # -------------------------------------------------------------

        logger.debug("RapportDepensePage initialized.")

        self._setup_ui()
        # self._load_data() # Pas besoin avec le QLabel simple
        self._update_deplacement_info_display() # DÉCOMMENTÉ: Appel initial pour peupler le cadre déplacement
        self._update_repas_info_display() # AJOUT: Appel initial
        self._update_depenses_diverses_info_display() # AJOUT: Appel initial
        self._update_frame_titles_with_counts()

    def _setup_ui(self):
        # Layout vertical principal pour la page
        content_layout = QVBoxLayout(self)
        content_layout.setContentsMargins(15, 15, 15, 15) 
        content_layout.setSpacing(15)

        # --- Section Supérieure: Totaux ---
        # Créer le header personnalisé
        header_container_total = QWidget()
        header_container_total.setObjectName("FrameHeaderContainer")
        header_layout_total = QHBoxLayout(header_container_total)
        header_layout_total.setContentsMargins(15, 8, 15, 8)
        header_layout_total.setSpacing(8)
        title_label_total = QLabel("Totaux")
        title_label_total.setObjectName("CustomFrameTitle") # Garder le nom pour le style QSS
        # MODIFIÉ: QLabel -> QPushButton
        self.totals_frame_count_button = QPushButton("(0)") # Créer et stocker le bouton compteur
        self.totals_frame_count_button.setObjectName("FrameCountButton") # MODIFIÉ: Retour au nom spécifique
        # self.totals_frame_count_button.setFlat(True) # SUPPRIMÉ: Style géré par QSS
        self.totals_frame_count_button.setFixedSize(28, 28) # CONSERVÉ: Rendre carré
        # self.totals_frame_count_button.setStyleSheet("QPushButton#TopNavButton { padding: 0px; }") # SUPPRIMÉ: Forcer padding
        self.totals_frame_count_button.setCursor(Qt.PointingHandCursor) # Curseur main
        self.totals_frame_count_button.setToolTip("Filtrer pour Tout afficher")
        # Connecter le clic
        self.totals_frame_count_button.clicked.connect(functools.partial(self._set_filter_from_button, "Tout"))
        header_layout_total.addWidget(title_label_total)
        header_layout_total.addStretch()
        header_layout_total.addWidget(self.totals_frame_count_button) # MODIFIÉ: Ajouter le bouton
        # Créer le Frame avec le header personnalisé
        self.totals_frame = Frame(header_widget=header_container_total, parent=self)
        totals_content_layout = self.totals_frame.get_content_layout()
        
        # Utiliser un QFormLayout pour les totaux
        totals_form_layout = QFormLayout()
        totals_form_layout.setSpacing(8)
        totals_form_layout.setLabelAlignment(Qt.AlignRight)
        totals_content_layout.addLayout(totals_form_layout)

        # Labels Placeholder pour les totaux
        self.total_deplacements_label = QLabel("0.00 $")
        self.total_repas_label = QLabel("0.00 $")
        self.total_depenses_label = QLabel("0.00 $")
        self.total_general_label = QLabel("0.00 $")
        self.total_general_label.setStyleSheet("font-weight: bold;") # Mettre le total général en gras
        
        totals_form_layout.addRow("Déplacements:", self.total_deplacements_label)
        totals_form_layout.addRow("Repas:", self.total_repas_label)
        totals_form_layout.addRow("Dépenses diverses:", self.total_depenses_label)
        
        # AJOUT: Stretch avant le séparateur du total général
        stretch_widget_totals = QWidget()
        stretch_widget_totals.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        stretch_widget_totals.setStyleSheet("background-color: transparent;") # AJOUT: Rendre transparent
        totals_form_layout.addRow(stretch_widget_totals)
        
        # Ajouter un séparateur avant le total général
        separator = QFrame() # Utiliser QFrame standard ici
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        totals_form_layout.addRow(separator)
        totals_form_layout.addRow("Total Général:", self.total_general_label)
        
        # totals_content_layout.addStretch() # SUPPRIMÉ: Le stretch est maintenant interne au QFormLayout
        # Pas de largeur fixe ici

        # content_layout.addWidget(self.totals_frame) # <-- SUPPRIMER ICI SI PRÉSENT, OU S'ASSURER QU'IL N'Y EST PAS

        # --- Section Milieu: Ajout (Gauche) + Liste (Droite) ---
        # (Anciennement 'bottom_section_layout', renommé pour clarté)
        middle_section_layout = QHBoxLayout()
        middle_section_layout.setSpacing(15)

        # --- Frame Gauche (Section Milieu): Ajouter une Entrée ---
        # 1. Créer le contenu de l'en-tête (Label + ComboBox)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 2, 5, 2) # Marges harmonisées
        header_layout.setSpacing(8) # <--- Ajout de l'espacement
        header_label = QLabel("Ajouter un(e) :") 
        header_label.setObjectName("FormLabel") 
        header_layout.addWidget(header_label)
        self.entry_type_combo = QComboBox()
        self.entry_type_combo.setObjectName("HeaderComboBox") 
        # --- MODIFICATION: Utiliser addItem avec icônes ---
        # self.entry_type_combo.addItems(["Déplacement", "Repas", "Dépense"]) # Ancienne méthode
        entry_types = {
            "Déplacement": "round_directions_car.png",
            "Repas": "round_restaurant.png",
            "Dépense": "round_payments.png"
        }
        fallback_icon_name = "round_receipt_long.png" # Icône si une autre n'est pas trouvée
        
        for text, icon_name in entry_types.items():
            icon_path = get_icon_path(icon_name)
            icon = QIcon()
            if icon_path:
                icon = QIcon(icon_path)
            else:
                # print(f"WARNING: Icon '{icon_name}' not found for ComboBox item '{text}'. Trying fallback.") # MODIFICATION
                logger.warning(f"Icon '{icon_name}' not found for ComboBox item '{text}'. Trying fallback.") # MODIFICATION
                fallback_path = get_icon_path(fallback_icon_name)
                if fallback_path:
                    icon = QIcon(fallback_path)
                else:
                     # print(f"ERROR: Fallback icon '{fallback_icon_name}' also not found.") # MODIFICATION
                     logger.error(f"Fallback icon '{fallback_icon_name}' also not found.") # MODIFICATION
            self.entry_type_combo.addItem(icon, text)
        # --- Fin Modification ---
        self.entry_type_combo.currentIndexChanged.connect(self._update_entry_form)
        header_layout.addWidget(self.entry_type_combo, 1)
        self.header_container = QWidget()
        self.header_container.setObjectName("FrameHeaderContainer")
        self.header_container.setLayout(header_layout)

        # 2. Créer le Frame principal d'ajout
        self.add_entry_frame = Frame(header_widget=self.header_container, parent=self) 
        add_entry_content_layout = self.add_entry_frame.get_content_layout()
        add_entry_content_layout.setSpacing(8)
        # --- Retrait de l'ancienne structure directe --- 
        # add_entry_content_layout.addLayout(buttons_layout) <-- Fait plus bas
        # add_entry_content_layout.addWidget(self.dynamic_form_widget) <-- Fait via _update_entry_form

        # --- Le Conteneur du formulaire dynamique est ajouté DIRECTEMENT au layout principal du frame d'ajout ---
        self.dynamic_form_container = QWidget() # Widget qui contiendra le formulaire dynamique
        self.dynamic_form_container.setStyleSheet("background-color: transparent;")
        add_entry_content_layout.addWidget(self.dynamic_form_container) # Stretch par défaut (0)
        self.dynamic_form_widget = None # Sera le QWidget AVEC le layout dedans
        self.dynamic_form_layout = None # Sera le QFormLayout
        self.form_fields = {}
        self.total_apres_taxes_field = None # Pour lier à montant_display_label

        # --- RECREATION: Section Montant (en bas du formulaire) ---
        montant_section_layout = QHBoxLayout()
        montant_section_layout.setContentsMargins(0, 10, 0, 5) # Ajouter un peu d'espace au-dessus
        self.dynamic_montant_label = QLabel("Montant:") # RENOMMÉ et stocké dans self
        self.dynamic_montant_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # AlignLeft
        self.montant_value_label = QLabel("0.00 $") # RENOMMÉ et stocké dans self
        self.montant_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter) # AlignRight
        self.montant_value_label.setStyleSheet("font-weight: bold;") 
        montant_section_layout.addWidget(self.dynamic_montant_label) # Ajout du label dynamique
        montant_section_layout.addStretch(1) # Pousse la valeur vers la droite
        montant_section_layout.addWidget(self.montant_value_label) # Ajout du label valeur
        # Ajouter cette section au layout principal du frame d'ajout
        add_entry_content_layout.addLayout(montant_section_layout) 
        # ---------------------------------------------------------

        # --- RECREATION: Boutons (tout en bas) ---
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 5, 0, 0) # Ajouter un peu d'espace au-dessus
        self.clear_button = QPushButton("Effacer")
        self.add_button = QPushButton("Ajouter")
        self.clear_button.setObjectName("TopNavButton")
        self.add_button.setObjectName("TopNavButton")
        self.clear_button.clicked.connect(self._clear_entry_form)
        self.add_button.clicked.connect(self._add_entry)
        
        buttons_layout.addWidget(self.clear_button) # Effacer à gauche
        # Le bouton Annuler sera inséré ici en mode édition (index 1)
        buttons_layout.addStretch(1) # Stretch pour pousser Ajouter/Appliquer à droite
        buttons_layout.addWidget(self.add_button)   # Ajouter/Appliquer à droite

        # Ajouter les boutons au layout principal du frame d'ajout
        add_entry_content_layout.addLayout(buttons_layout) 
        # ----------------------------------------
        
        # --- AJOUT DU FRAME D'AJOUT À LA SECTION MILIEU (GAUCHE) ---\
        middle_section_layout.addWidget(self.add_entry_frame, 1)

        # --- Frame Droite (Section Milieu): Affichage des Entrées --- 
        # --- NOUVEAU: Création de l'en-tête personnalisé ---
        entries_header_widget = QWidget()
        entries_header_widget.setObjectName("FrameHeaderContainer")
        entries_header_layout = QHBoxLayout(entries_header_widget)
        entries_header_layout.setContentsMargins(5, 2, 5, 2) 
        entries_header_layout.setSpacing(8)

        # Contrôles de Tri
        sort_label1 = QLabel("Trier par:")
        sort_label1.setObjectName("FormLabel")
        self.sort_primary_combo = QComboBox()
        self.sort_primary_combo.setObjectName("HeaderComboBox")
        self.sort_primary_combo.addItems([
            "Date (Décroissant)", "Date (Croissant)", 
            "Type (A-Z)", "Type (Z-A)", 
            "Montant (Décroissant)", "Montant (Croissant)"
        ])
        # self.sort_primary_combo.currentIndexChanged.connect(self._apply_sorting_and_filtering)
        self.sort_primary_combo.currentIndexChanged.connect(self._apply_sorting_and_filtering)
        self.sort_primary_combo.currentIndexChanged.connect(self._update_secondary_sort_options) # <-- Connexion ajoutée

        sort_label2 = QLabel("Puis par:")
        sort_label2.setObjectName("FormLabel")
        self.sort_secondary_combo = QComboBox()
        self.sort_secondary_combo.setObjectName("HeaderComboBox")
        self.sort_secondary_combo.addItem("Aucun") # Option par défaut
        self.sort_secondary_combo.addItems([
             "Date (Décroissant)", "Date (Croissant)", 
             "Type (A-Z)", "Type (Z-A)", 
             "Montant (Décroissant)", "Montant (Croissant)"
        ])
        # self.sort_secondary_combo.currentIndexChanged.connect(self._apply_sorting_and_filtering)
        self.sort_secondary_combo.currentIndexChanged.connect(self._apply_sorting_and_filtering)
        # TODO: Ajouter logique pour désactiver/lier les options entre les deux combos

        # Contrôle de Filtre
        filter_label = QLabel("Filtrer:")
        filter_label.setObjectName("FormLabel") # <--- Ajout nom objet
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.setObjectName("HeaderComboBox") # <--- Ajout nom objet
        # self.filter_type_combo.addItems(["Tout", "Déplacements", "Repas", "Dépenses"]) # Ancienne méthode
        # --- NOUVEAU: Ajouter items avec icônes ---
        filter_options = {
            "Tout": "round_all_inclusive.png", # MODIFIÉ: Nouvelle icône pour Tout
            "Déplacements": "round_directions_car.png",
            "Repas": "round_restaurant.png",
            "Dépenses": "round_payments.png"
        }
        fallback_icon_name = "round_receipt_long.png" # Même fallback que l'autre combo

        for text, icon_name in filter_options.items():
            icon_path = get_icon_path(icon_name)
            icon = QIcon()
            if icon_path:
                icon = QIcon(icon_path)
            else:
                # print(f"WARNING: Icon '{icon_name}' not found for ComboBox item '{text}'. Trying fallback.") # MODIFICATION
                logger.warning(f"Icon '{icon_name}' not found for ComboBox item '{text}'. Trying fallback.") # MODIFICATION
                fallback_path = get_icon_path(fallback_icon_name)
                if fallback_path:
                    icon = QIcon(fallback_path)
                else:
                     # print(f"ERROR: Fallback icon '{fallback_icon_name}' also not found.") # MODIFICATION
                     logger.error(f"Fallback icon '{fallback_icon_name}' also not found.") # MODIFICATION
            self.filter_type_combo.addItem(icon, text)
        # --- Fin ajout avec icônes ---
        # self.filter_type_combo.currentIndexChanged.connect(self._apply_sorting_and_filtering)
        self.filter_type_combo.currentIndexChanged.connect(self._apply_sorting_and_filtering)

        # Bouton Expand/Collapse
        self.expand_collapse_button = QPushButton()
        # --- MODIFICATION: Utiliser l'icône expand par défaut --- 
        expand_icon_path = get_icon_path("round_expand_all.png") 
        if expand_icon_path:
            self.expand_collapse_button.setIcon(QIcon(expand_icon_path))
        else:
             self.expand_collapse_button.setText("↔") # Fallback texte différent?
        # ------------------------------------------------------
        self.expand_collapse_button.setFixedSize(28, 28)
        self.expand_collapse_button.setCheckable(True)
        self.expand_collapse_button.setToolTip("Déplier/Replier tout")
        # self.expand_collapse_button.setObjectName("HeaderToolButton") # Ancien nom
        self.expand_collapse_button.setObjectName("TopNavButton") # Nouveau nom, comme Effacer/Ajouter
        # --- MODIFICATION: Décommenter la connexion --- 
        self.expand_collapse_button.toggled.connect(self._toggle_all_cards)
        # --------------------------------------------

        # Ajouter les éléments au layout de l'en-tête
        entries_header_layout.addWidget(sort_label1)
        entries_header_layout.addWidget(self.sort_primary_combo)
        entries_header_layout.addSpacing(15)
        entries_header_layout.addWidget(sort_label2)
        entries_header_layout.addWidget(self.sort_secondary_combo)
        entries_header_layout.addSpacing(15)
        entries_header_layout.addWidget(filter_label)
        entries_header_layout.addWidget(self.filter_type_combo)
        entries_header_layout.addStretch(1) # Pousse le bouton à droite
        entries_header_layout.addWidget(self.expand_collapse_button)
        # --- Fin Création En-tête ---

        self.entries_display_frame = Frame(header_widget=entries_header_widget, parent=self) # Utiliser le widget d'en-tête
        entries_display_frame_content_layout = self.entries_display_frame.get_content_layout()
        entries_display_frame_content_layout.setContentsMargins(0, 0, 0, 0) # Pas de marges internes au frame
        entries_display_frame_content_layout.setSpacing(0)

        # Créer la ScrollArea
        self.entries_scroll_area = QScrollArea()
        self.entries_scroll_area.setWidgetResizable(True)
        self.entries_scroll_area.setObjectName("EntriesScrollArea") # Pour QSS si besoin
        self.entries_scroll_area.setFrameShape(QFrame.NoFrame) # Pas de bordure pour la scroll area elle-même

        # Widget conteneur pour la ScrollArea
        scroll_content_widget = QWidget()
        scroll_content_widget.setObjectName("EntriesScrollContent")
        # --- Donner explicitement un fond au conteneur --- 
        theme = get_theme_vars() # Récupérer le thème
        scroll_bg_color = theme.get("COLOR_PRIMARY_MEDIUM", "#333333") # Couleur des frames
        scroll_content_widget.setStyleSheet(f"QWidget#EntriesScrollContent {{ background-color: {scroll_bg_color}; }}")
        # -----------------------------------------------

        # Layout pour la liste des vignettes
        self.entries_list_layout = QVBoxLayout(scroll_content_widget)
        self.entries_list_layout.setContentsMargins(5, 10, 5, 5) # Augmenter la marge supérieure de 5px
        self.entries_list_layout.setSpacing(10) # Espacement entre les vignettes
        self.entries_list_layout.setAlignment(Qt.AlignTop) # Aligner les vignettes en haut

        # Mettre le widget conteneur dans la ScrollArea
        self.entries_scroll_area.setWidget(scroll_content_widget)

        # Ajouter la ScrollArea au layout du frame
        entries_display_frame_content_layout.addWidget(self.entries_scroll_area)

        # --- AJOUT DU FRAME D'AFFICHAGE À LA SECTION INFÉRIEURE (DROITE) ---
        middle_section_layout.addWidget(self.entries_display_frame, 4) # Retour à l'alignement par défaut

        # --- AJOUT DE LA SECTION INFÉRIEURE AU LAYOUT PRINCIPAL ---
        content_layout.addLayout(middle_section_layout, 1) # MODIFIÉ: Ajout du facteur d'étirement 1

        # --- NOUVELLE SECTION BASSE: Totaux (Gauche) + Déplacement (Droite) ---
        bottom_frames_layout = QHBoxLayout()
        bottom_frames_layout.setSpacing(15)

        # Cadre Totaux (déjà initialisé plus haut)
        bottom_frames_layout.addWidget(self.totals_frame, 1) # Stretch factor 1

        # --- Nouveau Cadre: Déplacement ---
        header_container_depl = QWidget()
        header_container_depl.setObjectName("FrameHeaderContainer")
        header_layout_depl = QHBoxLayout(header_container_depl)
        header_layout_depl.setContentsMargins(15, 8, 15, 8)
        header_layout_depl.setSpacing(8)
        # AJOUT: Icône
        icon_path_depl = get_icon_path("round_directions_car.png")
        if icon_path_depl:
            icon_label_depl = QLabel()
            pixmap_depl = QPixmap(icon_path_depl).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label_depl.setPixmap(pixmap_depl)
            icon_label_depl.setFixedSize(20, 20)
            header_layout_depl.addWidget(icon_label_depl)
        # Titre
        title_label_depl = QLabel("Déplacement")
        title_label_depl.setObjectName("CustomFrameTitle")
        # MODIFIÉ: QLabel -> QPushButton
        self.deplacement_frame_count_button = QPushButton("(0)")
        self.deplacement_frame_count_button.setObjectName("FrameCountButton") # MODIFIÉ: Retour au nom spécifique
        # self.deplacement_frame_count_button.setFlat(True) # SUPPRIMÉ: Style géré par QSS
        self.deplacement_frame_count_button.setFixedSize(28, 28) # CONSERVÉ: Rendre carré
        # self.deplacement_frame_count_button.setStyleSheet("QPushButton#TopNavButton { padding: 0px; }") # SUPPRIMÉ: Forcer padding
        self.deplacement_frame_count_button.setCursor(Qt.PointingHandCursor)
        self.deplacement_frame_count_button.setToolTip("Filtrer par Déplacements")
        self.deplacement_frame_count_button.clicked.connect(functools.partial(self._set_filter_from_button, "Déplacements"))
        header_layout_depl.addWidget(title_label_depl)
        header_layout_depl.addStretch()
        header_layout_depl.addWidget(self.deplacement_frame_count_button) # MODIFIÉ: Ajouter le bouton
        self.deplacement_frame = Frame(header_widget=header_container_depl, parent=self)
        deplacement_content_layout = self.deplacement_frame.get_content_layout()
        
        deplacement_form_layout = QFormLayout()
        deplacement_form_layout.setSpacing(8)
        deplacement_form_layout.setLabelAlignment(Qt.AlignRight)
        deplacement_content_layout.addLayout(deplacement_form_layout)

        # Labels dynamiques pour Plafond et Taux
        self.plafond_label_value = QLabel("N/A")
        self.taux_remboursement_label_value = QLabel("N/A")
        # AJOUT: Label pour Kilométrage Total
        self.total_kilometrage_label_value = QLabel("0.0 km")

        deplacement_form_layout.addRow("Plafond:", self.plafond_label_value)
        deplacement_form_layout.addRow("Taux de Remboursement:", self.taux_remboursement_label_value)
        # AJOUT: Ligne pour Kilométrage Total
        deplacement_form_layout.addRow("Distance parcourue:", self.total_kilometrage_label_value) # MODIFIÉ: Texte du label
        
        # AJOUT: Stretch avant le séparateur du total remboursé
        stretch_widget_deplacement = QWidget()
        stretch_widget_deplacement.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        stretch_widget_deplacement.setStyleSheet("background-color: transparent;") # AJOUT: Rendre transparent
        deplacement_form_layout.addRow(stretch_widget_deplacement)
        
        # AJOUT: Séparateur avant le total remboursé
        separator_deplacement = QFrame()
        separator_deplacement.setFrameShape(QFrame.HLine)
        separator_deplacement.setFrameShadow(QFrame.Sunken)
        deplacement_form_layout.addRow(separator_deplacement)
        
        deplacement_form_layout.addRow("Total Remboursé:", self.total_rembourse_deplacement_label_value) 
        
        # deplacement_content_layout.addStretch() # SUPPRIMÉ: Le stretch est maintenant interne au QFormLayout

        bottom_frames_layout.addWidget(self.deplacement_frame, 1) # Stretch factor 1 pour équilibrer avec Totaux

        # --- Nouveau Cadre: Repas ---
        header_container_repas = QWidget()
        header_container_repas.setObjectName("FrameHeaderContainer")
        header_layout_repas = QHBoxLayout(header_container_repas)
        header_layout_repas.setContentsMargins(15, 8, 15, 8)
        header_layout_repas.setSpacing(8)
        # AJOUT: Icône
        icon_path_repas = get_icon_path("round_restaurant.png")
        if icon_path_repas:
            icon_label_repas = QLabel()
            pixmap_repas = QPixmap(icon_path_repas).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label_repas.setPixmap(pixmap_repas)
            icon_label_repas.setFixedSize(20, 20)
            header_layout_repas.addWidget(icon_label_repas)
        # Titre
        title_label_repas = QLabel("Repas")
        title_label_repas.setObjectName("CustomFrameTitle")
        # MODIFIÉ: QLabel -> QPushButton
        self.repas_frame_count_button = QPushButton("(0)")
        self.repas_frame_count_button.setObjectName("FrameCountButton") # MODIFIÉ: Retour au nom spécifique
        # self.repas_frame_count_button.setFlat(True) # SUPPRIMÉ: Style géré par QSS
        self.repas_frame_count_button.setFixedSize(28, 28) # CONSERVÉ: Rendre carré
        # self.repas_frame_count_button.setStyleSheet("QPushButton#TopNavButton { padding: 0px; }") # SUPPRIMÉ: Forcer padding
        self.repas_frame_count_button.setCursor(Qt.PointingHandCursor)
        self.repas_frame_count_button.setToolTip("Filtrer par Repas")
        self.repas_frame_count_button.clicked.connect(functools.partial(self._set_filter_from_button, "Repas"))
        header_layout_repas.addWidget(title_label_repas)
        header_layout_repas.addStretch()
        header_layout_repas.addWidget(self.repas_frame_count_button) # MODIFIÉ: Ajouter le bouton
        self.repas_frame = Frame(header_widget=header_container_repas, parent=self)
        repas_content_layout = self.repas_frame.get_content_layout()
        repas_form_layout = QFormLayout()
        repas_form_layout.setSpacing(8)
        repas_form_layout.setLabelAlignment(Qt.AlignRight)
        repas_content_layout.addLayout(repas_form_layout)

        stretch_widget_repas = QWidget()
        stretch_widget_repas.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        stretch_widget_repas.setStyleSheet("background-color: transparent;")
        repas_form_layout.addRow(stretch_widget_repas)

        separator_repas = QFrame()
        separator_repas.setFrameShape(QFrame.HLine)
        separator_repas.setFrameShadow(QFrame.Sunken)
        repas_form_layout.addRow(separator_repas)

        repas_form_layout.addRow("Total Remboursé:", self.total_repas_valeur_label) # MODIFIÉ: Changement de l'étiquette
        bottom_frames_layout.addWidget(self.repas_frame, 1) # Stretch factor 1

        # --- Nouveau Cadre: Dépenses Diverses ---
        header_container_depdiv = QWidget()
        header_container_depdiv.setObjectName("FrameHeaderContainer")
        header_layout_depdiv = QHBoxLayout(header_container_depdiv)
        header_layout_depdiv.setContentsMargins(15, 8, 15, 8)
        header_layout_depdiv.setSpacing(8)
        # AJOUT: Icône
        icon_path_depdiv = get_icon_path("round_payments.png")
        if icon_path_depdiv:
            icon_label_depdiv = QLabel()
            pixmap_depdiv = QPixmap(icon_path_depdiv).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label_depdiv.setPixmap(pixmap_depdiv)
            icon_label_depdiv.setFixedSize(20, 20)
            header_layout_depdiv.addWidget(icon_label_depdiv)
        # Titre
        title_label_depdiv = QLabel("Dépenses Diverses")
        title_label_depdiv.setObjectName("CustomFrameTitle")
        # MODIFIÉ: QLabel -> QPushButton
        self.depenses_diverses_frame_count_button = QPushButton("(0)")
        self.depenses_diverses_frame_count_button.setObjectName("FrameCountButton") # MODIFIÉ: Retour au nom spécifique
        # self.depenses_diverses_frame_count_button.setFlat(True) # SUPPRIMÉ: Style géré par QSS
        self.depenses_diverses_frame_count_button.setFixedSize(28, 28) # CONSERVÉ: Rendre carré
        # self.depenses_diverses_frame_count_button.setStyleSheet("QPushButton#TopNavButton { padding: 0px; }") # SUPPRIMÉ: Forcer padding
        self.depenses_diverses_frame_count_button.setCursor(Qt.PointingHandCursor)
        self.depenses_diverses_frame_count_button.setToolTip("Filtrer par Dépenses")
        self.depenses_diverses_frame_count_button.clicked.connect(functools.partial(self._set_filter_from_button, "Dépenses"))
        header_layout_depdiv.addWidget(title_label_depdiv)
        header_layout_depdiv.addStretch()
        header_layout_depdiv.addWidget(self.depenses_diverses_frame_count_button) # MODIFIÉ: Ajouter le bouton
        self.depenses_diverses_frame = Frame(header_widget=header_container_depdiv, parent=self)
        depenses_diverses_content_layout = self.depenses_diverses_frame.get_content_layout()
        depenses_diverses_form_layout = QFormLayout()
        depenses_diverses_form_layout.setSpacing(8)
        depenses_diverses_form_layout.setLabelAlignment(Qt.AlignRight)
        depenses_diverses_content_layout.addLayout(depenses_diverses_form_layout)

        stretch_widget_depenses_div = QWidget()
        stretch_widget_depenses_div.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        stretch_widget_depenses_div.setStyleSheet("background-color: transparent;")
        depenses_diverses_form_layout.addRow(stretch_widget_depenses_div)

        separator_depenses_div = QFrame()
        separator_depenses_div.setFrameShape(QFrame.HLine)
        separator_depenses_div.setFrameShadow(QFrame.Sunken)
        depenses_diverses_form_layout.addRow(separator_depenses_div)

        depenses_diverses_form_layout.addRow("Total Remboursé:", self.total_depenses_diverses_valeur_label) # MODIFIÉ: Changement de l'étiquette
        bottom_frames_layout.addWidget(self.depenses_diverses_frame, 1) # Stretch factor 1

        # --- AJOUT DE LA SECTION BASSE (TOTAUX + DÉPLACEMENT + REPAS + DEPENSES DIVERSES) AU LAYOUT PRINCIPAL ---
        content_layout.addLayout(bottom_frames_layout)
        
        # Initialisation du formulaire dynamique (appel original)
        self._update_entry_form()

    # --- NOUVELLE MÉTHODE POUR METTRE À JOUR LES INFOS DU CADRE DÉPLACEMENT --- # DÉCOMMENTÉE
    def _update_deplacement_info_display(self):
        logger.debug("Mise à jour des informations du cadre Déplacement.")
        config_data = ConfigData.get_instance()
        
        current_taux_remboursement = 0.0 # Variable pour stocker le taux actuel

        # Taux de remboursement (logique existante conservée)
        try:
            # --- MODIFICATION: Accéder au taux via la structure de config_data.json ---
            documents_config = config_data.get_top_level_key("documents", {})
            rapport_depense_config = documents_config.get("rapport_depense", [{}])
            if rapport_depense_config and isinstance(rapport_depense_config, list) and len(rapport_depense_config) > 0:
                taux_remboursement_str = str(rapport_depense_config[0].get('Taux_remboursement', '0.0'))
            else:
                taux_remboursement_str = '0.0'
            # --- FIN MODIFICATION ---
            current_taux_remboursement = float(taux_remboursement_str) # Stocker le taux
            self.taux_remboursement_label_value.setText(f"{current_taux_remboursement:.2f} $/km") # MODIFIÉ: Affichage décimal et unité $/km
        except ValueError:
            self.taux_remboursement_label_value.setText("Erreur (taux)")
            logger.error("Valeur invalide ou chemin incorrect pour Taux_remboursement dans ConfigData.")
        except Exception as e:
            self.taux_remboursement_label_value.setText("Erreur (cfg taux)")
            logger.error(f"Erreur inattendue lors de la récupération du taux de remboursement: {e}")

        # Plafond spécifique au document
        try:
            # 1. Obtenir la clé du plafond à partir de l'objet RapportDepense
            cle_plafond_document = self.document.plafond_deplacement # Ex: "Cap 1"
            
            if not cle_plafond_document: # Si la clé est vide ou None
                self.plafond_label_value.setText("N/A (clé manquante)")
                logger.warning("La clé 'plafond_deplacement' est manquante dans l'objet document.")
                # Ne pas retourner ici pour permettre la mise à jour du total remboursé
            else:
                # 2. Accéder au dictionnaire des plafonds depuis ConfigData
                jacmar_config = config_data.get_top_level_key("jacmar", {})
                plafonds_liste = jacmar_config.get("plafond_deplacement", [])
                
                valeur_plafond_num = None
                if plafonds_liste and isinstance(plafonds_liste, list) and len(plafonds_liste) > 0:
                    plafonds_dict = plafonds_liste[0] # Le premier élément est le dictionnaire des plafonds
                    if isinstance(plafonds_dict, dict):
                        # 3. Utiliser la clé pour trouver la valeur numérique
                        valeur_plafond_num = plafonds_dict.get(cle_plafond_document)

                if valeur_plafond_num is not None:
                    try:
                        plafond_affiche = float(valeur_plafond_num)
                        self.plafond_label_value.setText(f"{plafond_affiche:.2f} $")
                        logger.info(f"Plafond '{cle_plafond_document}' appliqué: {plafond_affiche:.2f} $")
                    except ValueError:
                        self.plafond_label_value.setText("Erreur (val num)")
                        logger.error(f"La valeur du plafond '{cle_plafond_document}' n'est pas un nombre valide: {valeur_plafond_num}")
                else:
                    self.plafond_label_value.setText(f"Non trouvé ({cle_plafond_document})")
                    logger.warning(f"La clé de plafond '{cle_plafond_document}' du document n'a pas été trouvée dans config_data.json.")

        except AttributeError as e:
            self.plafond_label_value.setText("Erreur (doc)")
            logger.error(f"Erreur d'attribut en accédant à 'plafond_deplacement' sur self.document: {e}")
        except Exception as e: # Capture générique pour autres erreurs inattendues
            self.plafond_label_value.setText("Erreur (gén.)")
            logger.error(f"Erreur inattendue lors de la mise à jour de l'affichage du plafond: {e}", exc_info=True)

        # AJOUT: Logique de mise à jour du total remboursé
        try:
            total_kilometrage = 0.0
            if hasattr(self.document, 'deplacements') and isinstance(self.document.deplacements, list):
                for deplacement_obj in self.document.deplacements:
                    if hasattr(deplacement_obj, 'kilometrage'):
                        try:
                            total_kilometrage += float(deplacement_obj.kilometrage)
                        except (ValueError, TypeError):
                            logger.warning(f"Kilométrage invalide pour un déplacement: {deplacement_obj.kilometrage}")
            
            # AJOUT: Mettre à jour le label du kilométrage total
            if hasattr(self, 'total_kilometrage_label_value'):
                self.total_kilometrage_label_value.setText(f"{total_kilometrage:.1f} km")

            total_rembourse = total_kilometrage * current_taux_remboursement
            self.total_rembourse_deplacement_label_value.setText(f"{total_rembourse:.2f} $")
            logger.info(f"Total remboursé calculé: {total_rembourse:.2f} $ (Km: {total_kilometrage}, Taux: {current_taux_remboursement})")

        except Exception as e:
            self.total_rembourse_deplacement_label_value.setText("Erreur (calcul)")
            logger.error(f"Erreur lors du calcul du total remboursé pour les déplacements: {e}", exc_info=True)

        # La partie Calcul du Montant Remboursable est supprimée car non demandée
        # logger.debug(f"Déplacement - Taux: ..., Plafond Doc: ...") # Log simplifié ou à ajuster si besoin

    # --- FIN NOUVELLE MÉTHODE --- # DÉCOMMENTÉE

    # AJOUT: Méthode pour mettre à jour les infos du cadre Repas
    def _update_repas_info_display(self):
        logger.debug("Mise à jour des informations du cadre Repas.")
        # Pour l'instant, s'assurer que le label affiche 0.00 $
        # La logique de calcul réelle du total des repas sera ajoutée plus tard si besoin.
        try:
            # Exemple: Calculer le total des repas à partir de self.document.repas
            # total_repas_val = sum(r.totale_apres_taxes for r in self.document.repas if hasattr(r, 'totale_apres_taxes'))
            # self.total_repas_valeur_label.setText(f"{total_repas_val:.2f} $")
            self.total_repas_valeur_label.setText("0.00 $") # Initialisation/Placeholder
        except Exception as e:
            self.total_repas_valeur_label.setText("Erreur")
            logger.error(f"Erreur lors de la mise à jour de l'affichage du total repas: {e}", exc_info=True)

    # AJOUT: Méthode pour mettre à jour les infos du cadre Dépenses Diverses
    def _update_depenses_diverses_info_display(self):
        logger.debug("Mise à jour des informations du cadre Dépenses Diverses.")
        # Pour l'instant, s'assurer que le label affiche 0.00 $
        # La logique de calcul réelle du total des dépenses diverses sera ajoutée plus tard.
        try:
            # Exemple: Calculer le total des dépenses diverses à partir de self.document.depenses_diverses
            # total_dep_div_val = sum(d.totale_apres_taxes for d in self.document.depenses_diverses if hasattr(d, 'totale_apres_taxes'))
            # self.total_depenses_diverses_valeur_label.setText(f"{total_dep_div_val:.2f} $")
            self.total_depenses_diverses_valeur_label.setText("0.00 $") # Initialisation/Placeholder
        except Exception as e:
            self.total_depenses_diverses_valeur_label.setText("Erreur")
            logger.error(f"Erreur lors de la mise à jour de l'affichage du total dépenses diverses: {e}", exc_info=True)

    def _create_vertical_separator(self):
        """ Crée un QFrame configuré comme séparateur vertical. """
        separator = QFrame()
        separator.setObjectName("VerticalFormSeparator") # Donner un nom d'objet
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        # --- Style sera géré via QSS via objectName --- 
        # separator.setStyleSheet(...) # Supprimé
        return separator

    # --- AJOUT: Mettre à jour les options de tri secondaire --- 
    def _update_secondary_sort_options(self):
        """Met à jour les options du ComboBox de tri secondaire pour exclure le critère primaire."""
        primary_option_text = self.sort_primary_combo.currentText()
        current_secondary_text = self.sort_secondary_combo.currentText()

        # Déterminer le critère primaire (Date, Type, Montant)
        primary_criterion = ""
        if "Date" in primary_option_text: primary_criterion = "Date"
        elif "Type" in primary_option_text: primary_criterion = "Type"
        elif "Montant" in primary_option_text: primary_criterion = "Montant"

        self.sort_secondary_combo.blockSignals(True) # Bloquer signaux pendant modif
        self.sort_secondary_combo.clear()
        self.sort_secondary_combo.addItem("Aucun")

        all_options = [
            "Date (Décroissant)", "Date (Croissant)", 
            "Type (A-Z)", "Type (Z-A)", 
            "Montant (Décroissant)", "Montant (Croissant)"
        ]

        for option in all_options:
            # Ajouter si le critère est différent du critère primaire
            if primary_criterion not in option:
                self.sort_secondary_combo.addItem(option)

        # Essayer de remettre l'ancienne sélection si elle est toujours valide
        index = self.sort_secondary_combo.findText(current_secondary_text)
        if index != -1:
            self.sort_secondary_combo.setCurrentIndex(index)
        else:
            self.sort_secondary_combo.setCurrentIndex(0) # Défaut "Aucun"
            
        self.sort_secondary_combo.blockSignals(False) # Réactiver signaux
    # ------------------------------------------------------

    def _update_entry_form(self):
        """ Met à jour le formulaire dynamique (partie gauche) selon le type d'entrée. """
        # --- RÉINITIALISER LE MONTANT AFFICHÉ EN BAS DU FORMULAIRE ---
        if hasattr(self, 'montant_display_label') and self.montant_display_label:
            self.montant_display_label.setText("0.00 $")
        # --------------------------------------------------------------

        # --- Réinitialiser la référence --- 
        self.total_apres_taxes_field = None
        self.num_commande_repas_label = None
        self.num_commande_repas_field = None
        self.num_commande_container = None
        self.payeur_group = None # Réinitialiser
        self.refacturer_group = None # Réinitialiser
        parent_container = self.dynamic_form_container
        if self.dynamic_form_widget is not None:
            self.dynamic_form_widget.deleteLater()
            self.dynamic_form_widget = None
            self.dynamic_form_layout = None 
            self.form_fields = {} 
        self.dynamic_form_widget = QWidget(parent_container)
        self.dynamic_form_widget.setStyleSheet("background-color: transparent;") 
        self.dynamic_form_layout = QGridLayout(self.dynamic_form_widget) 
        self.dynamic_form_layout.setColumnStretch(1, 1) # Colonne 1 (champ) s\'étire de nouveau
        
        # Obtenir les variables du thème actuel
        theme = get_theme_vars() # Utilise le thème par défaut (Sombre)
        frame_bg_color = theme.get("COLOR_PRIMARY_LIGHT", "#4a4d4f") # Utiliser LIGHT et ajuster fallback

        # --- Revenir à une largeur minimale fixe (plus généreuse) ---
        self.dynamic_form_layout.setColumnMinimumWidth(0, 120) 
        # -----------------------------------------------------------

        self.dynamic_form_layout.setSpacing(8) 
        self.dynamic_form_layout.setContentsMargins(0, 0, 0, 0) 

        # --- RESTAURER la logique d'ajout du widget au conteneur --- 
        # Assurer que le conteneur a un layout
        if parent_container.layout() is None:
            # Utiliser un QVBoxLayout simple pour le conteneur
            container_layout = QVBoxLayout(parent_container)
            container_layout.setContentsMargins(0,0,0,0)
            # Le layout est maintenant défini sur parent_container

        # Retirer l'ancien widget du layout s'il existe
        old_layout = parent_container.layout()
        if old_layout.count() > 0:
             old_widget = old_layout.takeAt(0).widget()
             if old_widget and old_widget != self.dynamic_form_widget: 
                 old_widget.deleteLater()

        # Ajouter le nouveau widget au layout du conteneur
        parent_container.layout().addWidget(self.dynamic_form_widget)
        # -------------------------------------------------------------

        current_row = 0 # Suivre la ligne actuelle du grid

        # --- Champs communs (toujours présents) - Déplacé ici ---
        # Utiliser le premier jour du mois du rapport comme date par défaut
        date_document = self.document.date_rapport
        q_date_document = QDate(date_document.year, date_document.month, date_document.day)
        self.form_fields['date'] = CustomDateEdit(q_date_document) # Utiliser la date du rapport pour init
        
        # --- AJOUT: Restreindre la plage de dates au mois du rapport --- 
        try:
            year = date_document.year
            month = date_document.month
            # Trouver le premier jour du mois
            min_date_obj = date(year, month, 1)
            q_min_date = QDate(min_date_obj)
            # Trouver le dernier jour du mois
            _, num_days = calendar.monthrange(year, month)
            max_date_obj = date(year, month, num_days)
            q_max_date = QDate(max_date_obj)
            
            # Appliquer les restrictions au CustomDateEdit
            self.form_fields['date'].setMinimumDate(q_min_date)
            self.form_fields['date'].setMaximumDate(q_max_date)
            logger.debug(f"Plage de dates pour le sélecteur limitée à: {q_min_date.toString('yyyy-MM-dd')} - {q_max_date.toString('yyyy-MM-dd')}")
        except Exception as e_date_range:
            logger.error(f"Erreur lors de la définition de la plage de dates: {e_date_range}")
        # --- FIN AJOUT ---
        
        date_label = QLabel("Date:")
        self.dynamic_form_layout.addWidget(date_label, current_row, 0, Qt.AlignLeft)
        self.dynamic_form_layout.addWidget(self.form_fields['date'], current_row, 1)
        current_row += 1
        
        # --- Champs spécifiques par type --- 
        entry_type = self.entry_type_combo.currentText()

        if entry_type == "Déplacement":
            self.form_fields['client'] = QLineEdit()
            self.form_fields['client'].setPlaceholderText("\"Jacmar\"")
            self.form_fields['client'].setStyleSheet(
                "QLineEdit { color: white; }"
                "QLineEdit:!focus { color: white; }"
                "QLineEdit::placeholder { color: gray; font-style: italic; }"
            )
            client_label = QLabel("Client:")
            self.dynamic_form_layout.addWidget(client_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['client'], current_row, 1)
            current_row += 1
            
            self.form_fields['ville'] = QLineEdit()
            self.form_fields['ville'].setPlaceholderText("\"Mascouche\"")
            self.form_fields['ville'].setStyleSheet(
                "QLineEdit { color: white; }"
                "QLineEdit:!focus { color: white; }"
                "QLineEdit::placeholder { color: gray; font-style: italic; }"
            )
            ville_label = QLabel("Ville:")
            self.dynamic_form_layout.addWidget(ville_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['ville'], current_row, 1)
            current_row += 1

            self.form_fields['numero_commande'] = QLineEdit()
            self.form_fields['numero_commande'].setPlaceholderText("\"123456\"")
            self.form_fields['numero_commande'].setStyleSheet(
                "QLineEdit { color: white; }"
                "QLineEdit:!focus { color: white; }"
                "QLineEdit::placeholder { color: gray; font-style: italic; }"
            )
            num_cmd_label = QLabel("N° Commande:")
            self.dynamic_form_layout.addWidget(num_cmd_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['numero_commande'], current_row, 1)
            current_row += 1

            self.form_fields['kilometrage'] = NumericInputWithUnit(unit_text="km", initial_value=0.0, max_decimals=1)
            # --- AJOUT LOGS DE DÉBOGAGE --- 
            km_widget = self.form_fields['kilometrage']
            logger.debug(f"DEBUG STYLE: Kilometrage widget objectName: {km_widget.objectName()}")
            logger.debug(f"DEBUG STYLE: Kilometrage widget styleSheet: {km_widget.styleSheet()}")
            # --- FIN AJOUT LOGS ---
            km_label = QLabel("Kilométrage:")
            self.dynamic_form_layout.addWidget(km_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['kilometrage'], current_row, 1)
            current_row += 1
            # Ajouter un stretch à la fin pour pousser les champs vers le haut
            self.dynamic_form_layout.setRowStretch(current_row, 1)
            # --- CONNEXION SPÉCIFIQUE DÉPLACEMENT (AVEC DÉCONNEXION) ---
            if 'kilometrage' in self.form_fields and self.form_fields['kilometrage']:
                try: 
                    self.form_fields['kilometrage'].valueChanged.disconnect(self._update_montant_display)
                    logger.debug("Ancienne connexion kilometrage.valueChanged déconnectée.")
                except TypeError: 
                    logger.debug("Aucune ancienne connexion kilometrage.valueChanged à déconnecter ou déjà déconnectée.")
                except Exception as e_disconnect:
                    logger.warning(f"Erreur lors de la déconnexion de kilometrage.valueChanged: {e_disconnect}")
                
                try:
                    self.form_fields['kilometrage'].valueChanged.connect(self._update_montant_display)
                    logger.debug("Nouvelle connexion kilometrage.valueChanged établie vers _update_montant_display.")
                except Exception as e_connect:
                    logger.error(f"Erreur lors de la connexion de kilometrage.valueChanged: {e_connect}")
            else:
                logger.warning("Champ 'kilometrage' non trouvé dans form_fields pour connexion du signal.")
            # -----------------------------------------------------------

        elif entry_type == "Repas":
            # --- AJOUT: Ajuster le stretch pour la nouvelle colonne ---
            self.dynamic_form_layout.setColumnStretch(1, 1) # Colonne 1 (QHBoxLayout) s\'étire
            # --------------------------------------------------------
            self.form_fields['restaurant'] = QLineEdit()
            self.form_fields['restaurant'].setPlaceholderText("\"McDonald's\"")
            self.form_fields['restaurant'].setStyleSheet(
                "QLineEdit { color: white; }"
                "QLineEdit:!focus { color: white; }"
                "QLineEdit::placeholder { color: gray; font-style: italic; }"
            )
            resto_label = QLabel("Restaurant:")
            self.dynamic_form_layout.addWidget(resto_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['restaurant'], current_row, 1)
            current_row += 1
            
            self.form_fields['client_repas'] = QLineEdit()
            self.form_fields['client_repas'].setPlaceholderText("\"Jacmar\"")
            self.form_fields['client_repas'].setStyleSheet(
                "QLineEdit { color: white; }"
                "QLineEdit:!focus { color: white; }"
                "QLineEdit::placeholder { color: gray; font-style: italic; }"
            )
            client_repas_label = QLabel("Client:")
            self.dynamic_form_layout.addWidget(client_repas_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['client_repas'], current_row, 1)
            current_row += 1
            
            # --- Payeur --- 
            self.payeur_frame = QFrame() # NOUVEAU QFrame parent
            self.payeur_frame.setObjectName("RadioGroupFrame")
            payeur_frame_layout = QVBoxLayout(self.payeur_frame) # Layout pour le QFrame
            payeur_frame_layout.setContentsMargins(0,0,0,0) # Le padding sera sur le QFrame via QSS

            payeur_container = QWidget() # L'ancien conteneur, maintenant enfant du QFrame
            payeur_container.setStyleSheet("background-color: transparent;") # Assurer la transparence
            payeur_grid = QGridLayout(payeur_container)
            payeur_grid.setContentsMargins(0,0,0,0)
            payeur_grid.setSpacing(10)
            self.payeur_group = QButtonGroup(self.dynamic_form_widget)
            self.form_fields['payeur_employe'] = QRadioButton("Employé")
            self.form_fields['payeur_employe'].setObjectName("FormRadioButton")
            self.form_fields['payeur_employe'].setStyleSheet("background-color: transparent;")
            self.form_fields['payeur_jacmar'] = QRadioButton("Jacmar")
            self.form_fields['payeur_jacmar'].setObjectName("FormRadioButton")
            self.form_fields['payeur_jacmar'].setStyleSheet("background-color: transparent;")
            self.form_fields['payeur_employe'].setChecked(True)
            self.payeur_group.addButton(self.form_fields['payeur_employe'])
            self.payeur_group.addButton(self.form_fields['payeur_jacmar'])
            # --- AJOUT CONNEXION PAYEUR (Repas) ---
            self.form_fields['payeur_employe'].toggled.connect(self._update_montant_display)
            # -------------------------------------
            payeur_grid.addWidget(self.form_fields['payeur_employe'], 0, 0)
            payeur_grid.addWidget(self.form_fields['payeur_jacmar'], 0, 1)
            payeur_grid.setColumnStretch(0, 1)
            payeur_grid.setColumnStretch(1, 1)
            
            payeur_frame_layout.addWidget(payeur_container) # Ajouter l'ancien conteneur au layout du QFrame

            payeur_label = QLabel("Payeur:")
            self.dynamic_form_layout.addWidget(payeur_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.payeur_frame, current_row, 1) # Ajouter le QFrame au layout principal
            current_row += 1

            # --- Refacturer --- 
            self.refacturer_frame = QFrame() # NOUVEAU QFrame parent
            self.refacturer_frame.setObjectName("RadioGroupFrame")
            refacturer_frame_layout = QVBoxLayout(self.refacturer_frame) # Layout pour le QFrame
            refacturer_frame_layout.setContentsMargins(0,0,0,0)

            refacturer_container = QWidget() # L'ancien conteneur
            refacturer_container.setStyleSheet("background-color: transparent;")
            refacturer_grid = QGridLayout(refacturer_container)
            refacturer_grid.setContentsMargins(0,0,0,0)
            refacturer_grid.setSpacing(10)
            self.refacturer_group = QButtonGroup(self.dynamic_form_widget)
            self.form_fields['refacturer_non'] = QRadioButton("Non")
            self.form_fields['refacturer_non'].setObjectName("FormRadioButton")
            self.form_fields['refacturer_non'].setStyleSheet("background-color: transparent;")
            self.form_fields['refacturer_oui'] = QRadioButton("Oui")
            self.form_fields['refacturer_oui'].setObjectName("FormRadioButton")
            self.form_fields['refacturer_oui'].setStyleSheet("background-color: transparent;")
            self.refacturer_group.addButton(self.form_fields['refacturer_non'])
            self.refacturer_group.addButton(self.form_fields['refacturer_oui'])
            self.form_fields['refacturer_non'].setChecked(True)
            self.form_fields['refacturer_oui'].toggled.connect(self._toggle_num_commande_row_visibility)
            refacturer_grid.addWidget(self.form_fields['refacturer_non'], 0, 0)
            refacturer_grid.addWidget(self.form_fields['refacturer_oui'], 0, 1)
            refacturer_grid.setColumnStretch(0, 1)
            refacturer_grid.setColumnStretch(1, 1)

            refacturer_frame_layout.addWidget(refacturer_container)

            refacturer_label = QLabel("Refacturer:")
            self.dynamic_form_layout.addWidget(refacturer_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.refacturer_frame, current_row, 1)
            current_row += 1
            # --------------------------------------------------------------------------

            # --- N° Commande (label colonne 0, champ colonne 1) --- 
            self.num_commande_repas_field = QLineEdit()
            self.form_fields['numero_commande_repas'] = self.num_commande_repas_field
            self.num_commande_repas_label = QLabel("N° Commande:") # Le label existe déjà comme variable membre
            # Ajouter le label et le champ au grid principal
            self.dynamic_form_layout.addWidget(self.num_commande_repas_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.num_commande_repas_field, current_row, 1)
            # La ligne suivante est enregistrée pour _toggle_num_commande_row_visibility
            self.num_commande_row_index = current_row 
            current_row += 1
            # Appeler la méthode de visibilité pour la ligne
            self._toggle_num_commande_row_visibility(self.form_fields['refacturer_oui'].isChecked()) 
            # ------------------------------------------------------
            
            # --- Montants (label colonne 0, champ colonne 1) --- 
            # Remplacer les QLineEdit par NumericInputWithUnit
            self.form_fields['total_avant_taxes'] = NumericInputWithUnit(unit_text="$", initial_value=0.0, max_decimals=2)
            total_avtx_label = QLabel("Total avant Tx:")
            # --- AJOUT BOUTON CALCUL ---
            self.form_fields['total_avant_taxes_btn'] = QPushButton()
            calc_icon_path = get_icon_path("round_calculate.png")
            if calc_icon_path: self.form_fields['total_avant_taxes_btn'].setIcon(QIcon(calc_icon_path))
            else: self.form_fields['total_avant_taxes_btn'].setText("C") # Fallback
            self.form_fields['total_avant_taxes_btn'].setIconSize(QSize(18, 18))
            self.form_fields['total_avant_taxes_btn'].setFixedSize(22, 22)
            self.form_fields['total_avant_taxes_btn'].setObjectName("CalcButton")
            self.form_fields['total_avant_taxes_btn'].setToolTip("Calculer le total avant taxes")
            # --- AJOUT: Style direct Python --- 
            try:
                theme = get_theme_vars()
                accent_color = theme.get("COLOR_ACCENT", "#007ACC")
                accent_pressed = theme.get("COLOR_ACCENT_PRESSED", "#005A9E")
                text_on_accent = theme.get("COLOR_TEXT_ON_ACCENT", "#FFFFFF")
                radius = theme.get("RADIUS_DEFAULT", "4px")
                
                style_sheet = f"""
                    QPushButton#CalcButton {{ 
                        background-color: transparent; 
                        border: none; 
                        padding: 0px; 
                        border-radius: {radius};
                    }}
                    QPushButton#CalcButton:hover {{ 
                        background-color: {accent_color}; 
                        color: {text_on_accent}; 
                    }}
                    QPushButton#CalcButton:pressed {{ 
                        background-color: {accent_pressed}; 
                        color: {text_on_accent}; 
                    }}
                """
                self.form_fields['total_avant_taxes_btn'].setStyleSheet(style_sheet)
            except Exception as e:
                logger.warning(f"Impossible d'appliquer le style direct au bouton calcul (total_avant_taxes): {e}")
            # --- FIN AJOUT Style --- 
            # --- AJOUT CONNEXION (Repas Av Tx) ---
            self.form_fields['total_avant_taxes_btn'].clicked.connect(self._calculate_total_avant_taxes)
            # -------------------------------------
            # --- NOUVEAU: Utiliser QHBoxLayout ---
            total_avtx_layout = QHBoxLayout()
            total_avtx_layout.setContentsMargins(0,0,0,0)
            total_avtx_layout.setSpacing(5) # Espace entre champ et bouton
            total_avtx_layout.addWidget(self.form_fields['total_avant_taxes'], 1) # Champ s'étire
            total_avtx_layout.addWidget(self.form_fields['total_avant_taxes_btn']) # Bouton à droite
            # --- FIN NOUVEAU ---
            self.dynamic_form_layout.addWidget(total_avtx_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addLayout(total_avtx_layout, current_row, 1) # Ajouter le QHBoxLayout en colonne 1
            current_row += 1
            
            self.form_fields['pourboire'] = NumericInputWithUnit(unit_text="$", initial_value=0.0, max_decimals=2)
            pourboire_label = QLabel("Pourboire:")
            # --- AJOUT BOUTON CALCUL POUR POURBOIRE ---
            self.form_fields['pourboire_btn'] = QPushButton()
            calc_icon_path_pb = get_icon_path("round_calculate.png")
            if calc_icon_path_pb: self.form_fields['pourboire_btn'].setIcon(QIcon(calc_icon_path_pb))
            else: self.form_fields['pourboire_btn'].setText("C") # Fallback
            self.form_fields['pourboire_btn'].setIconSize(QSize(18, 18))
            self.form_fields['pourboire_btn'].setFixedSize(22, 22)
            self.form_fields['pourboire_btn'].setObjectName("CalcButton")
            self.form_fields['pourboire_btn'].setToolTip("Calculer le pourboire")
            # --- AJOUT: Style direct Python --- 
            try:
                theme = get_theme_vars()
                accent_color = theme.get("COLOR_ACCENT", "#007ACC")
                accent_pressed = theme.get("COLOR_ACCENT_PRESSED", "#005A9E")
                text_on_accent = theme.get("COLOR_TEXT_ON_ACCENT", "#FFFFFF")
                radius = theme.get("RADIUS_DEFAULT", "4px")
                
                style_sheet = f"""
                    QPushButton#CalcButton {{ 
                        background-color: transparent; 
                        border: none; 
                        padding: 0px; 
                        border-radius: {radius};
                    }}
                    QPushButton#CalcButton:hover {{ 
                        background-color: {accent_color}; 
                        color: {text_on_accent}; 
                    }}
                    QPushButton#CalcButton:pressed {{ 
                        background-color: {accent_pressed}; 
                        color: {text_on_accent}; 
                    }}
                """
                self.form_fields['pourboire_btn'].setStyleSheet(style_sheet)
            except Exception as e:
                logger.warning(f"Impossible d'appliquer le style direct au bouton calcul (pourboire): {e}")
            # --- FIN AJOUT Style --- 
            # TODO: Connecter signal self.form_fields['pourboire_btn'].clicked
            # -----------------------------------------
            # --- NOUVEAU: Utiliser QHBoxLayout pour Pourboire ---
            pourboire_layout = QHBoxLayout()
            pourboire_layout.setContentsMargins(0,0,0,0)
            pourboire_layout.setSpacing(5)
            pourboire_layout.addWidget(self.form_fields['pourboire'], 1) # Champ s'étire
            pourboire_layout.addWidget(self.form_fields['pourboire_btn']) # Bouton à droite
            # --- FIN NOUVEAU ---
            self.dynamic_form_layout.addWidget(pourboire_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addLayout(pourboire_layout, current_row, 1) # Ajouter le QHBoxLayout en colonne 1
            current_row += 1

            # --- Taxes (label colonne 0, champ colonne 1) --- 
            tax_field_keys = ['tps', 'tvq', 'tvh']
            tax_labels = ["TPS:", "TVQ:", "TVH:"]
            for i, key in enumerate(tax_field_keys):
                self.form_fields[key] = NumericInputWithUnit(unit_text="$", initial_value=0.0, max_decimals=2)
                label_widget = QLabel(tax_labels[i])
                # --- AJOUT BOUTON CALCUL ---
                btn_key = f"{key}_btn"
                self.form_fields[btn_key] = QPushButton()
                calc_icon_path = get_icon_path("round_calculate.png")
                if calc_icon_path: self.form_fields[btn_key].setIcon(QIcon(calc_icon_path))
                else: self.form_fields[btn_key].setText("C") # Fallback
                self.form_fields[btn_key].setIconSize(QSize(18, 18))
                self.form_fields[btn_key].setFixedSize(22, 22)
                self.form_fields[btn_key].setObjectName("CalcButton")
                self.form_fields[btn_key].setToolTip(f"Calculer la {tax_labels[i][:-1]}")
                # --- AJOUT CONNEXION (Repas) ---
                if key == 'tps':
                    self.form_fields[btn_key].clicked.connect(functools.partial(self._calculate_tax, 'tps'))
                elif key == 'tvq':
                    self.form_fields[btn_key].clicked.connect(functools.partial(self._calculate_tax, 'tvq'))
                # -------------------------------
                # --- AJOUT: Style direct Python --- 
                try:
                    theme = get_theme_vars()
                    accent_color = theme.get("COLOR_ACCENT", "#007ACC")
                    accent_pressed = theme.get("COLOR_ACCENT_PRESSED", "#005A9E")
                    text_on_accent = theme.get("COLOR_TEXT_ON_ACCENT", "#FFFFFF")
                    radius = theme.get("RADIUS_DEFAULT", "4px")
                    
                    style_sheet = f"""
                        QPushButton#CalcButton {{ 
                            background-color: transparent; 
                            border: none; 
                            padding: 0px; 
                            border-radius: {radius};
                        }}
                        QPushButton#CalcButton:hover {{ 
                            background-color: {accent_color}; 
                            color: {text_on_accent}; 
                        }}
                        QPushButton#CalcButton:pressed {{ 
                            background-color: {accent_pressed}; 
                            color: {text_on_accent}; 
                        }}
                    """
                    self.form_fields[btn_key].setStyleSheet(style_sheet)
                except Exception as e:
                    logger.warning(f"Impossible d'appliquer le style direct au bouton calcul ({btn_key}): {e}")
                # --- FIN AJOUT Style --- 
                # TODO: Connecter signal self.form_fields[btn_key].clicked
                # -------------------------
                # --- NOUVEAU: Utiliser QHBoxLayout ---
                tax_layout = QHBoxLayout()
                tax_layout.setContentsMargins(0,0,0,0)
                tax_layout.setSpacing(5)
                tax_layout.addWidget(self.form_fields[key], 1) # Champ s'étire
                tax_layout.addWidget(self.form_fields[btn_key]) # Bouton à droite
                # --- FIN NOUVEAU ---
                self.dynamic_form_layout.addWidget(label_widget, current_row, 0, Qt.AlignLeft)
                self.dynamic_form_layout.addLayout(tax_layout, current_row, 1) # Ajouter le QHBoxLayout en colonne 1
                current_row += 1
            # --------------------------------------------------

            # Total après taxe
            self.form_fields['total_apres_taxes'] = NumericInputWithUnit(unit_text="$", initial_value=0.0, max_decimals=2)
            total_aptx_label = QLabel("Total après Tx:")
            # --- AJOUT BOUTON CALCUL ---
            self.form_fields['total_apres_taxes_btn'] = QPushButton()
            calc_icon_path = get_icon_path("round_calculate.png")
            if calc_icon_path: self.form_fields['total_apres_taxes_btn'].setIcon(QIcon(calc_icon_path))
            else: self.form_fields['total_apres_taxes_btn'].setText("C") # Fallback
            self.form_fields['total_apres_taxes_btn'].setIconSize(QSize(18, 18))
            self.form_fields['total_apres_taxes_btn'].setFixedSize(22, 22)
            self.form_fields['total_apres_taxes_btn'].setObjectName("CalcButton")
            self.form_fields['total_apres_taxes_btn'].setToolTip("Calculer le total après taxes")
            # --- AJOUT: Style direct Python --- 
            try:
                theme = get_theme_vars()
                accent_color = theme.get("COLOR_ACCENT", "#007ACC")
                accent_pressed = theme.get("COLOR_ACCENT_PRESSED", "#005A9E")
                text_on_accent = theme.get("COLOR_TEXT_ON_ACCENT", "#FFFFFF")
                radius = theme.get("RADIUS_DEFAULT", "4px")
                
                style_sheet = f"""
                    QPushButton#CalcButton {{ 
                        background-color: transparent; 
                        border: none; 
                        padding: 0px; 
                        border-radius: {radius};
                    }}
                    QPushButton#CalcButton:hover {{ 
                        background-color: {accent_color}; 
                        color: {text_on_accent}; 
                    }}
                    QPushButton#CalcButton:pressed {{ 
                        background-color: {accent_pressed}; 
                        color: {text_on_accent}; 
                    }}
                """
                self.form_fields['total_apres_taxes_btn'].setStyleSheet(style_sheet)
            except Exception as e:
                logger.warning(f"Impossible d'appliquer le style direct au bouton calcul (total_apres_taxes): {e}")
            # --- FIN AJOUT Style --- 
            # --- AJOUT CONNEXION (Repas Ap Tx) ---
            self.form_fields['total_apres_taxes_btn'].clicked.connect(self._calculate_total_apres_taxes)
            # -------------------------------------
            # --- NOUVEAU: Utiliser QHBoxLayout ---
            total_aptx_layout = QHBoxLayout()
            total_aptx_layout.setContentsMargins(0,0,0,0)
            total_aptx_layout.setSpacing(5)
            total_aptx_layout.addWidget(self.form_fields['total_apres_taxes'], 1) # Champ s'étire
            total_aptx_layout.addWidget(self.form_fields['total_apres_taxes_btn']) # Bouton à droite
            # --- FIN NOUVEAU ---
            self.dynamic_form_layout.addWidget(total_aptx_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addLayout(total_aptx_layout, current_row, 1) # Ajouter le QHBoxLayout en colonne 1
            current_row += 1
            # --- Le reste (connexion signal) est inchangé --- 
            self.total_apres_taxes_field = self.form_fields['total_apres_taxes']
            # MODIFIÉ: Connecter valueChanged au lieu de textChanged
            try: self.total_apres_taxes_field.valueChanged.disconnect() # Déconnecter ancien signal d'abord
            except TypeError: pass
            self.total_apres_taxes_field.valueChanged.connect(self._update_montant_display) 

            # --- MODIFICATION: Section Facture UTILISANT le Frame Existant --- 
            self.form_fields['facture_frame'] = QFrame()
            self.form_fields['facture_frame'].setObjectName("FactureFrame") # <-- AJOUT objectName
            self.form_fields['facture_frame'].setAutoFillBackground(True) # <-- AJOUT
            self.form_fields['facture_frame'].setFrameShape(QFrame.StyledPanel)
            # --- SUPPRIMER le setStyleSheet direct --- 
            # try:
            #     theme = get_theme_vars()
            #     frame_bg_color = theme.get("COLOR_PRIMARY_MEDIUM", "#3c3f41") # Utiliser MEDIUM
            #     radius = theme.get("RADIUS_BOX", "6px")
            #     self.form_fields['facture_frame'].setStyleSheet(f"background-color: {frame_bg_color}; border-radius: {radius}; border: none;")
            # except Exception as e:
            #     print(f"WARN: Erreur application style au frame facture: {e}")
            # -----------------------------------------
            
            # Layout interne du frame
            frame_content_layout = QVBoxLayout(self.form_fields['facture_frame'])
            frame_content_layout.setContentsMargins(0, 0, 0, 0) # MODIFIÉ: Le padding est géré par QSS
            frame_content_layout.setSpacing(8)

            # Layout horizontal pour Label + Bouton Icône
            label_button_layout = QHBoxLayout()
            label_button_layout.setContentsMargins(0,0,0,0)
            label_button_layout.setSpacing(5)

            facture_label_in_frame = QLabel("Facture(s):")
            label_button_layout.addWidget(facture_label_in_frame)
            label_button_layout.addStretch(1) # Pousse le bouton vers la droite
            
            # NOUVEAU Bouton remplacé par icône
            self.add_facture_button = QPushButton() # Créer sans texte
            add_icon_path = get_icon_path("round_add_circle.png")
            if add_icon_path:
                self.add_facture_button.setIcon(QIcon(add_icon_path))
                self.add_facture_button.setIconSize(QSize(22, 22)) # Taille icône (ajustable)
            else:
                self.add_facture_button.setText("+") # Fallback texte si icône non trouvée
            self.add_facture_button.setFixedSize(30, 30)
            self.add_facture_button.setToolTip("Ajouter une facture (Image ou PDF)")
            self.add_facture_button.setObjectName("TopNavButton") # <-- Nouveau nom, comme Effacer/Ajouter
            # --- Appliquer le style :hover directement --- 
            try:
                theme = get_theme_vars()
                accent_color = theme.get("COLOR_ACCENT", "#007ACC")
                text_on_accent = theme.get("COLOR_TEXT_ON_ACCENT", "#ffffff")
                # Récupérer le style de base et forcer les dimensions
                base_style = "QPushButton#TopNavButton { background-color: transparent; border: none; padding: 0px; border-radius: {{RADIUS_DEFAULT}}; min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px; }" 
                hover_style = f"QPushButton#TopNavButton:hover {{ background-color: {accent_color}; color: {text_on_accent}; }}"
                pressed_style = f"QPushButton#TopNavButton:pressed {{ background-color: {theme.get('COLOR_ACCENT_PRESSED', '#003d82')}; color: {text_on_accent}; }}"
                # Combiner les styles
                combined_style = f"{base_style}\n{hover_style}\n{pressed_style}"
                # Remplacer les placeholders si présents dans base_style
                combined_style = combined_style.replace("{{RADIUS_DEFAULT}}", theme.get("RADIUS_DEFAULT", "4px")) 
                self.add_facture_button.setStyleSheet(combined_style)
            except Exception as e:
                # print(f"WARN: Impossible d'appliquer le style hover/pressed direct au bouton facture: {e}") # MODIFICATION
                logger.warning(f"Impossible d'appliquer le style hover/pressed direct au bouton facture: {e}") # MODIFICATION
                # Fallback : appliquer juste le :hover rouge pour voir si ça marche
                # self.add_facture_button.setStyleSheet("QPushButton#TopNavButton:hover { background-color: red; }")
            # -----------------------------------------
            self.add_facture_button.clicked.connect(self._select_factures)
            label_button_layout.addWidget(self.add_facture_button) # Ajouter le nouveau bouton
            
            # Ajouter le HBox (Label + Bouton) au VBox du frame
            frame_content_layout.addLayout(label_button_layout)

            # ScrollArea pour les miniatures (ajoutée SOUS le label+bouton)
            self.facture_scroll_area = QScrollArea()
            self.facture_scroll_area.setWidgetResizable(True)
            self.facture_scroll_area.setFrameShape(QFrame.NoFrame)
            # --- RESTAURATION: Hauteur MINIMALE pour miniature + scrollbar --- 
            self.facture_scroll_area.setMinimumHeight(ThumbnailWidget.THUMBNAIL_SIZE + 45)
            # ----------------------------------------------------------------
            self.facture_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.facture_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 

            # Widget conteneur interne pour la scroll area
            self.facture_container_widget = QWidget()
            self.facture_thumbnails_layout = QHBoxLayout(self.facture_container_widget)
            self.facture_thumbnails_layout.setContentsMargins(5, 0, 5, 0)
            self.facture_thumbnails_layout.setSpacing(10) 
            self.facture_thumbnails_layout.setAlignment(Qt.AlignLeft) 
            self.facture_scroll_area.setWidget(self.facture_container_widget)
            
            # Ajouter la ScrollArea au layout du frame
            frame_content_layout.addWidget(self.facture_scroll_area) 
            # frame_content_layout.addStretch(1) # Pousse le contenu vers le haut si besoin

            # Ajouter le frame ENTIER au grid principal, sur 2 colonnes
            self.dynamic_form_layout.addWidget(self.form_fields['facture_frame'], current_row, 0, 1, 2)
            current_row += 1
            # ----------------------------------------------------------------

            # Ajouter un stretch à la fin pour pousser les champs vers le haut
            self.dynamic_form_layout.setRowStretch(current_row, 1)
            
        elif entry_type == "Dépense":
            # --- AJOUT: Ajuster le stretch pour la nouvelle colonne ---
            self.dynamic_form_layout.setColumnStretch(1, 1) # Colonne 1 (QHBoxLayout ou champ) s\'étire
            # --------------------------------------------------------
            # --- Champs pour Dépense --- 
            # Type (ComboBox) - Déjà géré par les champs communs si on le déplace plus haut
            # Date: est déjà ajouté en premier comme champ commun.

            # Type (ComboBox)
            self.form_fields['type_depense'] = QComboBox()
            type_label = QLabel("Type:") # Conserver ceci
            
            # --- AJOUT: Peupler le ComboBox des types de dépense depuis ConfigData ---
            try:
                config = ConfigData.get_instance()
                # Chemin exact vers les codes GL de dépense dans config_data.json
                # documents -> Global (liste, prendre premier élément) -> codes_gl -> depenses (liste de dictionnaires)
                codes_gl_depenses = config.get_top_level_key("documents", {}).get("Global", [{}])[0].get("codes_gl", {}).get("depenses", [])
                
                self.form_fields['type_depense'].clear() # Vider les items précédents
                if codes_gl_depenses:
                    for gl_code_info in codes_gl_depenses:
                        description = gl_code_info.get("description")
                        code = gl_code_info.get("code")
                        if description: # S'assurer qu'il y a une description
                            self.form_fields['type_depense'].addItem(description, userData=code) # Stocker le code GL comme userData
                        else:
                            logger.warning(f"Code GL de dépense trouvé sans description: {gl_code_info}")
                else:
                    logger.warning("Aucun code GL de dépense trouvé dans ConfigData pour peupler le ComboBox.")
                    self.form_fields['type_depense'].addItem("Erreur: Aucun code GL", userData=None) # Fallback
            except Exception as e:
                logger.error(f"Erreur lors du peuplement du ComboBox des types de dépense: {e}", exc_info=True)
                self.form_fields['type_depense'].clear()
                self.form_fields['type_depense'].addItem("Erreur chargement codes", userData=None) # Fallback
            # --- FIN AJOUT ---
            
            self.dynamic_form_layout.addWidget(type_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['type_depense'], current_row, 1)
            current_row += 1

            # Description
            self.form_fields['description_dep'] = QLineEdit() # Clé unique: description_dep
            self.form_fields['description_dep'].setPlaceholderText("\"Cafe, Batterie, etc\"")
            self.form_fields['description_dep'].setStyleSheet(
                "QLineEdit { color: white; }"
                "QLineEdit:!focus { color: white; }"
                "QLineEdit::placeholder { color: gray; font-style: italic; }"
            )
            desc_label = QLabel("Description:")
            self.dynamic_form_layout.addWidget(desc_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['description_dep'], current_row, 1)
            current_row += 1
            
            # Fournisseur
            self.form_fields['fournisseur_dep'] = QLineEdit() # Clé unique: fournisseur_dep
            self.form_fields['fournisseur_dep'].setPlaceholderText("\"Amazon, Bell, etc\"")
            self.form_fields['fournisseur_dep'].setStyleSheet(
                "QLineEdit { color: white; }"
                "QLineEdit:!focus { color: white; }"
                "QLineEdit::placeholder { color: gray; font-style: italic; }"
            )
            fourn_label = QLabel("Fournisseur:")
            self.dynamic_form_layout.addWidget(fourn_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['fournisseur_dep'], current_row, 1)
            current_row += 1

            # Payeur (Radio)
            self.payeur_frame_dep = QFrame() 
            self.payeur_frame_dep.setObjectName("RadioGroupFrame")
            payeur_frame_layout_dep = QVBoxLayout(self.payeur_frame_dep)
            payeur_frame_layout_dep.setContentsMargins(0,0,0,0)
            
            payeur_container_dep = QWidget()
            payeur_container_dep.setStyleSheet("background-color: transparent;")
            payeur_grid_dep = QGridLayout(payeur_container_dep)
            payeur_grid_dep.setContentsMargins(0,0,0,0)
            payeur_grid_dep.setSpacing(10)
            
            self.depense_payeur_group = QButtonGroup(self.dynamic_form_widget) 
            self.form_fields['payeur_employe_dep'] = QRadioButton("Employé")
            self.form_fields['payeur_employe_dep'].setObjectName("FormRadioButton")
            self.form_fields['payeur_employe_dep'].setStyleSheet("background-color: transparent;")
            self.form_fields['payeur_jacmar_dep'] = QRadioButton("Jacmar")
            self.form_fields['payeur_jacmar_dep'].setObjectName("FormRadioButton")
            self.form_fields['payeur_jacmar_dep'].setStyleSheet("background-color: transparent;")
            
            self.form_fields['payeur_employe_dep'].setChecked(True)
            self.depense_payeur_group.addButton(self.form_fields['payeur_employe_dep'])
            self.depense_payeur_group.addButton(self.form_fields['payeur_jacmar_dep'])
            # --- AJOUT CONNEXION PAYEUR (Dépense) ---
            self.form_fields['payeur_employe_dep'].toggled.connect(self._update_montant_display)
            # -------------------------------------
            
            payeur_grid_dep.addWidget(self.form_fields['payeur_employe_dep'], 0, 0)
            payeur_grid_dep.addWidget(self.form_fields['payeur_jacmar_dep'], 0, 1)
            payeur_grid_dep.setColumnStretch(0, 1)
            payeur_grid_dep.setColumnStretch(1, 1)
            payeur_frame_layout_dep.addWidget(payeur_container_dep)
            
            payeur_label_dep = QLabel("Payeur:")
            self.dynamic_form_layout.addWidget(payeur_label_dep, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.payeur_frame_dep, current_row, 1)
            current_row += 1
            
            # Total avant taxe
            self.form_fields['total_avant_taxes_dep'] = NumericInputWithUnit(unit_text="$", initial_value=0.0, max_decimals=2)
            total_avtx_label_dep = QLabel("Total avant Tx:")
            # --- AJOUT BOUTON CALCUL ---
            self.form_fields['total_avant_taxes_dep_btn'] = QPushButton()
            calc_icon_path = get_icon_path("round_calculate.png")
            if calc_icon_path: self.form_fields['total_avant_taxes_dep_btn'].setIcon(QIcon(calc_icon_path))
            else: self.form_fields['total_avant_taxes_dep_btn'].setText("C") # Fallback
            self.form_fields['total_avant_taxes_dep_btn'].setIconSize(QSize(18, 18))
            self.form_fields['total_avant_taxes_dep_btn'].setFixedSize(22, 22)
            self.form_fields['total_avant_taxes_dep_btn'].setObjectName("CalcButton")
            self.form_fields['total_avant_taxes_dep_btn'].setToolTip("Calculer le total avant taxes")
            # --- AJOUT: Style direct Python --- 
            try:
                theme = get_theme_vars()
                accent_color = theme.get("COLOR_ACCENT", "#007ACC")
                accent_pressed = theme.get("COLOR_ACCENT_PRESSED", "#005A9E")
                text_on_accent = theme.get("COLOR_TEXT_ON_ACCENT", "#FFFFFF")
                radius = theme.get("RADIUS_DEFAULT", "4px")
                
                style_sheet = f"""
                    QPushButton#CalcButton {{ 
                        background-color: transparent; 
                        border: none; 
                        padding: 0px; 
                        border-radius: {radius};
                    }}
                    QPushButton#CalcButton:hover {{ 
                        background-color: {accent_color}; 
                        color: {text_on_accent}; 
                    }}
                    QPushButton#CalcButton:pressed {{ 
                        background-color: {accent_pressed}; 
                        color: {text_on_accent}; 
                    }}
                """
                self.form_fields['total_avant_taxes_dep_btn'].setStyleSheet(style_sheet)
            except Exception as e:
                logger.warning(f"Impossible d'appliquer le style direct au bouton calcul (total_avant_taxes_dep): {e}")
            # --- FIN AJOUT Style --- 
            # --- AJOUT CONNEXION (Dépense Av Tx) ---
            self.form_fields['total_avant_taxes_dep_btn'].clicked.connect(self._calculate_total_avant_taxes)
            # -------------------------------------
            # --- NOUVEAU: Utiliser QHBoxLayout ---
            total_avtx_dep_layout = QHBoxLayout()
            total_avtx_dep_layout.setContentsMargins(0,0,0,0)
            total_avtx_dep_layout.setSpacing(5)
            total_avtx_dep_layout.addWidget(self.form_fields['total_avant_taxes_dep'], 1) # Champ s'étire
            total_avtx_dep_layout.addWidget(self.form_fields['total_avant_taxes_dep_btn']) # Bouton à droite
            # --- FIN NOUVEAU ---
            self.dynamic_form_layout.addWidget(total_avtx_label_dep, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addLayout(total_avtx_dep_layout, current_row, 1) # Ajouter le QHBoxLayout en colonne 1
            current_row += 1

            # TPS
            self.form_fields['tps_dep'] = NumericInputWithUnit(unit_text="$", initial_value=0.0, max_decimals=2)
            tps_label_dep = QLabel("TPS:")
            # --- AJOUT BOUTON CALCUL ---
            self.form_fields['tps_dep_btn'] = QPushButton()
            calc_icon_path = get_icon_path("round_calculate.png")
            if calc_icon_path: self.form_fields['tps_dep_btn'].setIcon(QIcon(calc_icon_path))
            else: self.form_fields['tps_dep_btn'].setText("C") # Fallback
            self.form_fields['tps_dep_btn'].setIconSize(QSize(18, 18))
            self.form_fields['tps_dep_btn'].setFixedSize(22, 22)
            self.form_fields['tps_dep_btn'].setObjectName("CalcButton")
            self.form_fields['tps_dep_btn'].setToolTip("Calculer la TPS")
            # --- AJOUT CONNEXION (Dépense TPS) ---
            self.form_fields['tps_dep_btn'].clicked.connect(functools.partial(self._calculate_tax, 'tps'))
            # -------------------------------------
            # --- AJOUT: Style direct Python --- 
            try:
                theme = get_theme_vars()
                accent_color = theme.get("COLOR_ACCENT", "#007ACC")
                accent_pressed = theme.get("COLOR_ACCENT_PRESSED", "#005A9E")
                text_on_accent = theme.get("COLOR_TEXT_ON_ACCENT", "#FFFFFF")
                radius = theme.get("RADIUS_DEFAULT", "4px")
                
                style_sheet = f"""
                    QPushButton#CalcButton {{ 
                        background-color: transparent; 
                        border: none; 
                        padding: 0px; 
                        border-radius: {radius};
                    }}
                    QPushButton#CalcButton:hover {{ 
                        background-color: {accent_color}; 
                        color: {text_on_accent}; 
                    }}
                    QPushButton#CalcButton:pressed {{ 
                        background-color: {accent_pressed}; 
                        color: {text_on_accent}; 
                    }}
                """
                self.form_fields['tps_dep_btn'].setStyleSheet(style_sheet)
            except Exception as e:
                logger.warning(f"Impossible d'appliquer le style direct au bouton calcul (tps_dep): {e}")
            # --- FIN AJOUT Style --- 
            # TODO: Connecter signal
            # -------------------------
            # --- NOUVEAU: Utiliser QHBoxLayout ---
            tps_dep_layout = QHBoxLayout()
            tps_dep_layout.setContentsMargins(0,0,0,0)
            tps_dep_layout.setSpacing(5)
            tps_dep_layout.addWidget(self.form_fields['tps_dep'], 1) # Champ s'étire
            tps_dep_layout.addWidget(self.form_fields['tps_dep_btn']) # Bouton à droite
            # --- FIN NOUVEAU ---
            self.dynamic_form_layout.addWidget(tps_label_dep, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addLayout(tps_dep_layout, current_row, 1) # Ajouter le QHBoxLayout en colonne 1
            current_row += 1

            # TVQ
            self.form_fields['tvq_dep'] = NumericInputWithUnit(unit_text="$", initial_value=0.0, max_decimals=2)
            tvq_label_dep = QLabel("TVQ:")
            # --- AJOUT BOUTON CALCUL ---
            self.form_fields['tvq_dep_btn'] = QPushButton()
            calc_icon_path = get_icon_path("round_calculate.png")
            if calc_icon_path: self.form_fields['tvq_dep_btn'].setIcon(QIcon(calc_icon_path))
            else: self.form_fields['tvq_dep_btn'].setText("C") # Fallback
            self.form_fields['tvq_dep_btn'].setIconSize(QSize(18, 18))
            self.form_fields['tvq_dep_btn'].setFixedSize(22, 22)
            self.form_fields['tvq_dep_btn'].setObjectName("CalcButton")
            self.form_fields['tvq_dep_btn'].setToolTip("Calculer la TVQ")
            # --- AJOUT CONNEXION (Dépense TVQ) ---
            self.form_fields['tvq_dep_btn'].clicked.connect(functools.partial(self._calculate_tax, 'tvq'))
            # -------------------------------------
            # --- AJOUT: Style direct Python --- 
            try:
                theme = get_theme_vars()
                accent_color = theme.get("COLOR_ACCENT", "#007ACC")
                accent_pressed = theme.get("COLOR_ACCENT_PRESSED", "#005A9E")
                text_on_accent = theme.get("COLOR_TEXT_ON_ACCENT", "#FFFFFF")
                radius = theme.get("RADIUS_DEFAULT", "4px")
                
                style_sheet = f"""
                    QPushButton#CalcButton {{ 
                        background-color: transparent; 
                        border: none; 
                        padding: 0px; 
                        border-radius: {radius};
                    }}
                    QPushButton#CalcButton:hover {{ 
                        background-color: {accent_color}; 
                        color: {text_on_accent}; 
                    }}
                    QPushButton#CalcButton:pressed {{ 
                        background-color: {accent_pressed}; 
                        color: {text_on_accent}; 
                    }}
                """
                self.form_fields['tvq_dep_btn'].setStyleSheet(style_sheet)
            except Exception as e:
                logger.warning(f"Impossible d'appliquer le style direct au bouton calcul (tvq_dep): {e}")
            # --- FIN AJOUT Style --- 
            # TODO: Connecter signal
            # -------------------------
            # --- NOUVEAU: Utiliser QHBoxLayout ---
            tvq_dep_layout = QHBoxLayout()
            tvq_dep_layout.setContentsMargins(0,0,0,0)
            tvq_dep_layout.setSpacing(5)
            tvq_dep_layout.addWidget(self.form_fields['tvq_dep'], 1) # Champ s'étire
            tvq_dep_layout.addWidget(self.form_fields['tvq_dep_btn']) # Bouton à droite
            # --- FIN NOUVEAU ---
            self.dynamic_form_layout.addWidget(tvq_label_dep, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addLayout(tvq_dep_layout, current_row, 1) # Ajouter le QHBoxLayout en colonne 1
            current_row += 1

            # TVH
            self.form_fields['tvh_dep'] = NumericInputWithUnit(unit_text="$", initial_value=0.0, max_decimals=2)
            tvh_label_dep = QLabel("TVH:")
            # --- AJOUT BOUTON CALCUL ---
            self.form_fields['tvh_dep_btn'] = QPushButton()
            calc_icon_path = get_icon_path("round_calculate.png")
            if calc_icon_path: self.form_fields['tvh_dep_btn'].setIcon(QIcon(calc_icon_path))
            else: self.form_fields['tvh_dep_btn'].setText("C") # Fallback
            self.form_fields['tvh_dep_btn'].setIconSize(QSize(18, 18))
            self.form_fields['tvh_dep_btn'].setFixedSize(22, 22)
            self.form_fields['tvh_dep_btn'].setObjectName("CalcButton")
            self.form_fields['tvh_dep_btn'].setToolTip("Calculer la TVH")
            # --- AJOUT: Style direct Python --- 
            try:
                theme = get_theme_vars()
                accent_color = theme.get("COLOR_ACCENT", "#007ACC")
                accent_pressed = theme.get("COLOR_ACCENT_PRESSED", "#005A9E")
                text_on_accent = theme.get("COLOR_TEXT_ON_ACCENT", "#FFFFFF")
                radius = theme.get("RADIUS_DEFAULT", "4px")
                
                style_sheet = f"""
                    QPushButton#CalcButton {{ 
                        background-color: transparent; 
                        border: none; 
                        padding: 0px; 
                        border-radius: {radius};
                    }}
                    QPushButton#CalcButton:hover {{ 
                        background-color: {accent_color}; 
                        color: {text_on_accent}; 
                    }}
                    QPushButton#CalcButton:pressed {{ 
                        background-color: {accent_pressed}; 
                        color: {text_on_accent}; 
                    }}
                """
                self.form_fields['tvh_dep_btn'].setStyleSheet(style_sheet)
            except Exception as e:
                logger.warning(f"Impossible d'appliquer le style direct au bouton calcul (tvh_dep): {e}")
            # --- FIN AJOUT Style --- 
            # TODO: Connecter signal
            # -------------------------
            # --- NOUVEAU: Utiliser QHBoxLayout ---
            tvh_dep_layout = QHBoxLayout()
            tvh_dep_layout.setContentsMargins(0,0,0,0)
            tvh_dep_layout.setSpacing(5)
            tvh_dep_layout.addWidget(self.form_fields['tvh_dep'], 1) # Champ s'étire
            tvh_dep_layout.addWidget(self.form_fields['tvh_dep_btn']) # Bouton à droite
            # --- FIN NOUVEAU ---
            self.dynamic_form_layout.addWidget(tvh_label_dep, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addLayout(tvh_dep_layout, current_row, 1) # Ajouter le QHBoxLayout en colonne 1
            current_row += 1

            # Total apres taxe
            self.form_fields['total_apres_taxes_dep'] = NumericInputWithUnit(unit_text="$", initial_value=0.0, max_decimals=2)
            total_aptx_label_dep = QLabel("Total après Tx:")
            # --- AJOUT BOUTON CALCUL ---
            self.form_fields['total_apres_taxes_dep_btn'] = QPushButton()
            calc_icon_path = get_icon_path("round_calculate.png")
            if calc_icon_path: self.form_fields['total_apres_taxes_dep_btn'].setIcon(QIcon(calc_icon_path))
            else: self.form_fields['total_apres_taxes_dep_btn'].setText("C") # Fallback
            self.form_fields['total_apres_taxes_dep_btn'].setIconSize(QSize(18, 18))
            self.form_fields['total_apres_taxes_dep_btn'].setFixedSize(22, 22)
            self.form_fields['total_apres_taxes_dep_btn'].setObjectName("CalcButton")
            self.form_fields['total_apres_taxes_dep_btn'].setToolTip("Calculer le total après taxes")
            # --- AJOUT: Style direct Python --- 
            try:
                theme = get_theme_vars()
                accent_color = theme.get("COLOR_ACCENT", "#007ACC")
                accent_pressed = theme.get("COLOR_ACCENT_PRESSED", "#005A9E")
                text_on_accent = theme.get("COLOR_TEXT_ON_ACCENT", "#FFFFFF")
                radius = theme.get("RADIUS_DEFAULT", "4px")
                
                style_sheet = f"""
                    QPushButton#CalcButton {{ 
                        background-color: transparent; 
                        border: none; 
                        padding: 0px; 
                        border-radius: {radius};
                    }}
                    QPushButton#CalcButton:hover {{ 
                        background-color: {accent_color}; 
                        color: {text_on_accent}; 
                    }}
                    QPushButton#CalcButton:pressed {{ 
                        background-color: {accent_pressed}; 
                        color: {text_on_accent}; 
                    }}
                """
                self.form_fields['total_apres_taxes_dep_btn'].setStyleSheet(style_sheet)
            except Exception as e:
                logger.warning(f"Impossible d'appliquer le style direct au bouton calcul (total_apres_taxes_dep): {e}")
            # --- FIN AJOUT Style --- 
            # --- AJOUT CONNEXION (Dépense Ap Tx) ---
            self.form_fields['total_apres_taxes_dep_btn'].clicked.connect(self._calculate_total_apres_taxes)
            # -------------------------------------
            # --- NOUVEAU: Utiliser QHBoxLayout ---
            total_aptx_dep_layout = QHBoxLayout()
            total_aptx_dep_layout.setContentsMargins(0,0,0,0)
            total_aptx_dep_layout.setSpacing(5)
            total_aptx_dep_layout.addWidget(self.form_fields['total_apres_taxes_dep'], 1) # Champ s'étire
            total_aptx_dep_layout.addWidget(self.form_fields['total_apres_taxes_dep_btn']) # Bouton à droite
            # --- FIN NOUVEAU ---
            self.dynamic_form_layout.addWidget(total_aptx_label_dep, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addLayout(total_aptx_dep_layout, current_row, 1) # Ajouter le QHBoxLayout en colonne 1
            # Connecter le signal valueChanged pour mettre à jour le montant affiché en bas
            self.total_apres_taxes_field = self.form_fields['total_apres_taxes_dep'] # Réassigner le champ à connecter
            self.total_apres_taxes_field.valueChanged.connect(self._update_montant_display)
            current_row += 1

            # Section Facture (similaire à Repas)
            self.form_fields['facture_frame_dep'] = QFrame() # Clé unique: facture_frame_dep
            self.form_fields['facture_frame_dep'].setObjectName("FactureFrame") 
            self.form_fields['facture_frame_dep'].setAutoFillBackground(True)
            self.form_fields['facture_frame_dep'].setFrameShape(QFrame.StyledPanel)
            
            frame_content_layout_dep = QVBoxLayout(self.form_fields['facture_frame_dep'])
            frame_content_layout_dep.setContentsMargins(0, 0, 0, 0) 
            frame_content_layout_dep.setSpacing(8)

            label_button_layout_dep = QHBoxLayout()
            label_button_layout_dep.setContentsMargins(0,0,0,0)
            label_button_layout_dep.setSpacing(5)

            facture_label_in_frame_dep = QLabel("Facture(s):")
            label_button_layout_dep.addWidget(facture_label_in_frame_dep)
            label_button_layout_dep.addStretch(1)
            
            self.add_facture_button_dep = QPushButton() # Bouton unique: add_facture_button_dep
            add_icon_path = get_icon_path("round_add_circle.png")
            if add_icon_path:
                self.add_facture_button_dep.setIcon(QIcon(add_icon_path))
                self.add_facture_button_dep.setIconSize(QSize(22, 22))
            else:
                self.add_facture_button_dep.setText("+")
            self.add_facture_button_dep.setFixedSize(30, 30)
            self.add_facture_button_dep.setToolTip("Ajouter une facture (Image ou PDF)")
            self.add_facture_button_dep.setObjectName("TopNavButton")
            try: # Style du bouton
                theme = get_theme_vars()
                accent_color = theme.get("COLOR_ACCENT", "#007ACC")
                text_on_accent = theme.get("COLOR_TEXT_ON_ACCENT", "#ffffff")
                base_style = "QPushButton#TopNavButton { background-color: transparent; border: none; padding: 0px; border-radius: {{RADIUS_DEFAULT}}; min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px; }" 
                hover_style = f"QPushButton#TopNavButton:hover {{ background-color: {accent_color}; color: {text_on_accent}; }}"
                pressed_style = f"QPushButton#TopNavButton:pressed {{ background-color: {theme.get('COLOR_ACCENT_PRESSED', '#003d82')}; color: {text_on_accent}; }}"
                combined_style = f"{base_style}\n{hover_style}\n{pressed_style}"
                combined_style = combined_style.replace("{{RADIUS_DEFAULT}}", theme.get("RADIUS_DEFAULT", "4px")) 
                self.add_facture_button_dep.setStyleSheet(combined_style)
            except Exception as e:
                logger.warning(f"Impossible d'appliquer le style au bouton facture (dépense): {e}")
            self.add_facture_button_dep.clicked.connect(self._select_factures) # Réutilise la même méthode pour sélectionner
            label_button_layout_dep.addWidget(self.add_facture_button_dep)
            
            frame_content_layout_dep.addLayout(label_button_layout_dep)

            # ScrollArea pour les miniatures
            # On réutilise les mêmes membres self.facture_scroll_area etc. car ils sont nettoyés
            # et reconstruits à chaque _update_entry_form, y compris les miniatures via self.current_facture_thumbnails
            self.facture_scroll_area = QScrollArea() 
            self.facture_scroll_area.setWidgetResizable(True)
            self.facture_scroll_area.setFrameShape(QFrame.NoFrame)
            self.facture_scroll_area.setMinimumHeight(ThumbnailWidget.THUMBNAIL_SIZE + 45)
            self.facture_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.facture_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 

            self.facture_container_widget = QWidget() # Nouveau conteneur pour cette instance
            self.facture_thumbnails_layout = QHBoxLayout(self.facture_container_widget) # Nouveau layout pour cette instance
            self.facture_thumbnails_layout.setContentsMargins(5, 0, 5, 0)
            self.facture_thumbnails_layout.setSpacing(10) 
            self.facture_thumbnails_layout.setAlignment(Qt.AlignLeft) 
            self.facture_scroll_area.setWidget(self.facture_container_widget)
            
            frame_content_layout_dep.addWidget(self.facture_scroll_area)
            
            self.dynamic_form_layout.addWidget(self.form_fields['facture_frame_dep'], current_row, 0, 1, 2)
            current_row += 1
            # Fin Section Facture

            # Retrait des champs "Refacturer" et "N° Commande" qui étaient précédemment copiés de Repas
            # Les champs suivants sont retirés de la version Dépense :
            # self.form_fields['refacturer_non'] / self.form_fields['refacturer_oui']
            # self.num_commande_repas_field / self.form_fields['numero_commande_repas']
            # La logique _toggle_num_commande_row_visibility n'est plus nécessaire ici.
            # L'ancien code pour "Pourboire" est aussi omis car non demandé pour Dépense.

            # Ajouter un stretch à la fin pour pousser les champs vers le haut
            self.dynamic_form_layout.setRowStretch(current_row, 1)
            
        # --- Réinitialiser la liste des miniatures --- 
        # Ceci est déjà fait à la fin de _update_entry_form, pas besoin de le répéter ici.

        # --- Réinitialiser la liste des miniatures --- 
        # --- APPEL INITIAL pour mettre à jour le montant après création du formulaire --- 
        self._update_montant_display()
        # ----------------------------------------------------------------------------
        
        # Ajouter un espace vertical avant le montant total
        self.dynamic_form_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding), current_row, 0, 1, 2)
        current_row += 1
        
        # ... (reste _update_entry_form: montant, politique taille) ...

    def _update_montant_display(self, _=None): # L'argument est ignoré, on lit directement les champs
        """ Met à jour le label montant en bas du formulaire selon le type d'entrée et les valeurs. """
        # Vérifier si les nouveaux labels existent
        if not hasattr(self, 'dynamic_montant_label') or not self.dynamic_montant_label or \
           not hasattr(self, 'montant_value_label') or not self.montant_value_label:
            logger.warning("_update_montant_display: Labels non trouvés (dynamic_montant_label ou montant_value_label).")
            return

        entry_type = self.entry_type_combo.currentText()
        label_text = "Montant:" # Texte par défaut pour le label
        montant_val = 0.0
        tolerance = 1e-6

        try:
            if entry_type == "Déplacement":
                label_text = "Montant (Employé):"
                logger.debug("Entrée dans _update_montant_display pour type Déplacement.")
                kilometrage_widget = self.form_fields.get('kilometrage')
                if kilometrage_widget and hasattr(kilometrage_widget, 'value'):
                    kilometrage = kilometrage_widget.value()
                    logger.debug(f"  Kilométrage lu depuis widget: {kilometrage}")
                    
                    taux_remboursement = 0.0
                    try:
                        config_instance = ConfigData.get_instance()
                        config = config_instance.all_data
                        documents_config = config.get("documents", {})
                        rapport_depense_config = documents_config.get("rapport_depense", [{}])
                        if rapport_depense_config and isinstance(rapport_depense_config, list) and len(rapport_depense_config) > 0:
                            taux_remboursement_str = str(rapport_depense_config[0].get('Taux_remboursement', '0.0'))
                            taux_remboursement = float(taux_remboursement_str)
                            logger.debug(f"  Taux de remboursement récupéré: {taux_remboursement} (str: '{taux_remboursement_str}')")
                        else:
                            logger.warning("  rapport_depense_config est vide ou non conforme pour Taux_remboursement.")
                    except Exception as e_taux:
                        logger.error(f"  Erreur récupération taux remboursement pour _update_montant_display: {e_taux}", exc_info=True)
                    
                    montant_val = kilometrage * taux_remboursement
                    logger.debug(f"  Montant calculé (Déplacement): {kilometrage} * {taux_remboursement} = {montant_val}")
                else:
                    logger.warning("_update_montant_display (Déplacement): widget kilometrage non trouvé ou sans méthode .value().")

            elif entry_type == "Repas":
                total_apres_taxes_widget = self.form_fields.get('total_apres_taxes')
                payeur_employe_widget = self.form_fields.get('payeur_employe')

                if total_apres_taxes_widget and hasattr(total_apres_taxes_widget, 'value'):
                    montant_val = total_apres_taxes_widget.value()
                else:
                    logger.debug("_update_montant_display (Repas): widget total_apres_taxes non trouvé.")
                
                # Déterminer le texte du label
                if payeur_employe_widget and hasattr(payeur_employe_widget, 'isChecked'):
                    payeur = "Employé" if payeur_employe_widget.isChecked() else "Jacmar"
                    label_text = f"Montant ({payeur}):"
                else:
                    label_text = "Montant:" # Fallback
                    logger.debug("_update_montant_display (Repas): widget payeur_employe non trouvé.")

            elif entry_type == "Dépense":
                total_apres_taxes_widget_dep = self.form_fields.get('total_apres_taxes_dep')
                payeur_employe_widget_dep = self.form_fields.get('payeur_employe_dep')

                if total_apres_taxes_widget_dep and hasattr(total_apres_taxes_widget_dep, 'value'):
                    montant_val = total_apres_taxes_widget_dep.value()
                else:
                    logger.debug("_update_montant_display (Dépense): widget total_apres_taxes_dep non trouvé.")
                
                # Déterminer le texte du label
                if payeur_employe_widget_dep and hasattr(payeur_employe_widget_dep, 'isChecked'):
                    payeur = "Employé" if payeur_employe_widget_dep.isChecked() else "Jacmar"
                    label_text = f"Montant ({payeur}):"
                else:
                    label_text = "Montant:" # Fallback
                    logger.debug("_update_montant_display (Dépense): widget payeur_employe_dep non trouvé.")
            else:
                 # Cas où le formulaire n'est pas encore complètement initialisé ou type inconnu
                 self.dynamic_montant_label.setText("Montant:")
                 self.montant_value_label.setText("0.00 $")
                 return

            # Mettre à jour les deux labels séparément
            self.dynamic_montant_label.setText(label_text)
            self.montant_value_label.setText(f"{montant_val:.2f} $")

        except Exception as e:
            logger.error(f"Erreur dans _update_montant_display: {e}", exc_info=True)
            # Mettre les deux labels en état d'erreur
            self.dynamic_montant_label.setText("Montant (Erreur):") 
            self.montant_value_label.setText("--- $")

    def _clear_entry_form(self):
        """ Efface les champs du formulaire actuel (gauche ET reset le label montant). """
        # Effacer les champs du formulaire dynamique (gauche)
        for field_key, widget in self.form_fields.items():
            if isinstance(widget, QLineEdit):
                # --- Pour les champs monétaires, mettre "0.00" --- 
                if widget.validator() and isinstance(widget.validator(), QDoubleValidator):
                    widget.setText("0.00")
                else:
                    widget.clear() # Pour les autres QLineEdit
                # ----------------------------------------------
            elif isinstance(widget, QDoubleSpinBox):
                # Si c'est le champ total_apres_taxes, sa valeur sera reset par valueChanged(0) - Obsolète
                # Les autres spinbox prennent leur minimum (souvent 0)
                widget.setValue(widget.minimum()) 
            # --- Vérifier si c'est notre CustomDateEdit --- 
            elif isinstance(widget, CustomDateEdit):
                widget.setDate(QDate.currentDate())
            # --- AJOUT POUR NumericInputWithUnit ---
            elif isinstance(widget, NumericInputWithUnit):
                widget.setValue(0.0) # Ou la valeur par défaut/minimale souhaitée
            # --- AJOUT POUR CHECKBOX --- 
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)
            # --- AJOUT POUR RADIOBUTTON --- 
            # Vérifier les clés spécifiques pour remettre les défauts
            elif field_key == 'payeur_employe': # Pour Repas
                widget.setChecked(True)
            elif field_key == 'payeur_jacmar': # Pour Repas
                widget.setChecked(False)
            elif field_key == 'refacturer_non':
                widget.setChecked(True)
            elif field_key == 'refacturer_oui':
                widget.setChecked(False)
            elif field_key == 'payeur_employe_dep': # Pour Dépense
                 widget.setChecked(True)
            elif field_key == 'payeur_jacmar_dep': # Pour Dépense
                 widget.setChecked(False)
            # --- AJOUT POUR COMBOBOX --- 
            elif isinstance(widget, QComboBox) and field_key == 'type_depense':
                 widget.setCurrentIndex(0) # Remettre au premier item
            # --- Nettoyage Facture: Plus de bouton à gérer ici ---
            # ------------------------------

        # Réinitialiser le label montant dédié (droite)
        if hasattr(self, 'montant_display_label') and self.montant_display_label:
             self.montant_display_label.setText("0.00 $")

        # Effacer les miniatures
        for path in list(self.current_facture_thumbnails.keys()): 
             self._remove_facture_thumbnail(path, update_model=False)
        self.current_facture_thumbnails = {}
        
        # --- AJOUT: Mettre à jour l'affichage du montant après effacement ---
        self._update_montant_display()
        # -----------------------------------------------------------------

    def _add_entry(self):
        """ Ajoute l'entrée en lisant les champs du formulaire. """
        entry_type = self.entry_type_combo.currentText()
        
        # --- DÉFINITION DE LA FONCTION HELPER get_float_from_field ICI ---
        def get_float_from_field(key):
            try:
                widget = self.form_fields[key]
                if isinstance(widget, NumericInputWithUnit):
                    return widget.value()
                else: # Fallback for other types, e.g. QLineEdit
                    return float(widget.text().replace(',', '.'))
            except (KeyError, ValueError, AttributeError): # Added AttributeError
                # Si clé non trouvée ou conversion impossible, retourner 0.0
                logger.warning(f"Clé '{key}' non trouvée dans form_fields ou valeur invalide lors de la conversion en float.")
                return 0.0
        # --- FIN DÉFINITION HELPER ---

        # --- AJOUT: Appel de la validation --- 
        if not self._validate_form_data(entry_type):
            return # Stopper si la validation échoue
        # -------------------------------------
        
        try:
            # Récupérer les valeurs communes (Date et Description)
            date_val = self.form_fields['date'].date().toPyDate()

            new_entry = None
            if entry_type == "Déplacement":
                 client_val = self.form_fields['client'].text()
                 ville_val = self.form_fields['ville'].text()
                 num_commande_val = self.form_fields['numero_commande'].text()
                 kilometrage_val = self.form_fields['kilometrage'].value()
                 # --- Calcul du montant pour Déplacement (réintroduit et corrigé) ---
                 taux_remboursement = 0.0
                 try:
                     config_instance = ConfigData.get_instance()
                     config = config_instance.all_data
                     documents_config = config.get("documents", {})
                     rapport_depense_config = documents_config.get("rapport_depense", [{}])
                     if rapport_depense_config and isinstance(rapport_depense_config, list) and len(rapport_depense_config) > 0:
                         taux_remboursement_str = str(rapport_depense_config[0].get('Taux_remboursement', '0.0'))
                         taux_remboursement = float(taux_remboursement_str)
                 except Exception as e_taux:
                     logger.error(f"Erreur récupération taux remboursement dans _add_entry: {e_taux}")
                     # Optionnel: Afficher une erreur à l'utilisateur?
                 
                 montant_calculé = kilometrage_val * taux_remboursement
                 # -------------------------------------------------------------------
                 new_entry = Deplacement(date_deplacement=date_val, 
                                         client=client_val, ville=ville_val, 
                                         numero_commande=num_commande_val,
                                         kilometrage=kilometrage_val, 
                                         montant=montant_calculé) # Utiliser le montant calculé
                 self.document.ajouter_deplacement(new_entry)
                 # print(f"Déplacement ajouté: {new_entry}") # MODIFICATION
                 logger.info(f"Déplacement ajouté: {new_entry}") # MODIFICATION

            elif entry_type == "Repas":
                 # Récupérer les valeurs spécifiques depuis self.form_fields
                 restaurant_val = self.form_fields['restaurant'].text()
                 client_repas_val = self.form_fields['client_repas'].text()
                 # --- Lire l'état des RadioButtons --- 
                 payeur_val = self.form_fields['payeur_employe'].isChecked()
                 refacturer_val = self.form_fields['refacturer_oui'].isChecked()
                 # ------------------------------------
                 num_commande_repas_val = self.form_fields['numero_commande_repas'].text()
                 # --- Lire et convertir les QLineEdit monétaires --- 
                 total_avant_taxes_val = get_float_from_field('total_avant_taxes')
                 pourboire_val = get_float_from_field('pourboire')
                 tps_val = get_float_from_field('tps')
                 tvq_val = get_float_from_field('tvq')
                 tvh_val = get_float_from_field('tvh')
                 total_apres_taxes_val = get_float_from_field('total_apres_taxes')
                 # ---------------------------------------------------
                 # --- Ajout: Lire employe/jacmar s'ils existent, sinon 0 --- 
                 employe_val = get_float_from_field('employe') # TODO: Ajouter champ si nécessaire
                 jacmar_val = get_float_from_field('jacmar') # TODO: Ajouter champ si nécessaire

                 # --- AJOUT: Création de l'objet Facture --- 
                 facture_obj = None
                 if self.current_facture_thumbnails: # Si des miniatures existent
                     all_paths = list(self.current_facture_thumbnails.keys())
                     if all_paths:
                         # Utiliser le dossier du premier fichier comme référence
                         # ATTENTION: Ceci suppose que tous les fichiers sont dans le même dossier
                         first_path = all_paths[0]
                         folder_path = os.path.dirname(first_path)
                         # Extraire juste les noms de fichiers
                         filenames = [os.path.basename(p) for p in all_paths]
                         try:
                              facture_obj = Facture(folder_path=folder_path, filenames=filenames)
                              # print(f"[TEMP] Objet Facture créé: {facture_obj}") # MODIFICATION
                              logger.debug(f"Objet Facture créé: {facture_obj}") # MODIFICATION
                         except (TypeError, ValueError) as fact_err:
                              QMessageBox.warning(self, "Erreur Facture", f"Impossible de créer l'objet Facture:\\n{fact_err}")
                              # Continuer sans facture en cas d'erreur
                              facture_obj = None 
                 # -------------------------------------------
                 
                 # --- Créer l'objet Repas --- 
                 new_entry = Repas(
                     date_repas=date_val, 
                     description="Repas", # Description générique ou à ajouter au form?
                     restaurant=restaurant_val, 
                     client=client_repas_val,
                     payeur=payeur_val, # Passer le booléen directement (True=Employé)
                     refacturer=refacturer_val, # True si Oui
                     numero_commande=num_commande_repas_val if refacturer_val else "", # Num cmd si refacturer
                                    totale_avant_taxes=total_avant_taxes_val, 
                     pourboire=pourboire_val, 
                     tps=tps_val, 
                     tvq=tvq_val, 
                     tvh=tvh_val,
                                    totale_apres_taxes=total_apres_taxes_val,
                     employe=employe_val, # À vérifier si nécessaire
                     jacmar=jacmar_val,   # À vérifier si nécessaire
                     facture=facture_obj # <--- MODIFICATION: Passer l'objet Facture (ou None)
                 )
                 # self.document.entries.append(new_entry)
                 self.document.ajouter_repas(new_entry) # Utiliser la méthode dédiée
                 # print(f"Ajout Repas: {new_entry}") # Garder pour info # MODIFICATION
                 logger.info(f"Ajout Repas: {new_entry}") # MODIFICATION
                 
            elif entry_type == "Dépense":
                 # --- Lire les valeurs du formulaire Dépense --- 
                 type_val = self.form_fields['type_depense'].currentText()
                 description_val = self.form_fields['description_dep'].text() # MODIFIÉ: _dep
                 fournisseur_val = self.form_fields['fournisseur_dep'].text() # MODIFIÉ: _dep
                 payeur_val = self.form_fields['payeur_employe_dep'].isChecked() # True si Employé
                 
                 # Utiliser le helper pour les montants avec les clés _dep
                 total_avant_taxes_val = get_float_from_field('total_avant_taxes_dep')
                 tps_val = get_float_from_field('tps_dep')
                 tvq_val = get_float_from_field('tvq_dep')
                 tvh_val = get_float_from_field('tvh_dep')
                 total_apres_taxes_val = get_float_from_field('total_apres_taxes_dep')
                 
                 # Validation (exemple simple)
                 if not description_val: # Validation pour la nouvelle clé
                     QMessageBox.warning(self, "Champ manquant", "La description est requise.")
                     return
                 if total_apres_taxes_val <= 0: # Validation pour la nouvelle clé
                     QMessageBox.warning(self, "Montant invalide", "Le total après taxes doit être positif.")
                     return # MODIFIÉ: Retourner ici pour stopper

                 # --- AJOUT: Création de l'objet Facture pour Dépense --- 
                 facture_obj_dep = None
                 if self.current_facture_thumbnails: 
                     all_paths = list(self.current_facture_thumbnails.keys())
                     if all_paths:
                         first_path = all_paths[0]
                         folder_path = os.path.dirname(first_path)
                         filenames = [os.path.basename(p) for p in all_paths]
                         try:
                              facture_obj_dep = Facture(folder_path=folder_path, filenames=filenames)
                              logger.debug(f"Objet Facture (Dépense) créé: {facture_obj_dep}")
                         except (TypeError, ValueError) as fact_err:
                              QMessageBox.warning(self, "Erreur Facture", f"Impossible de créer l'objet Facture (Dépense):\n{fact_err}")
                              facture_obj_dep = None 
                 # -------------------------------------------

                 # --- AJOUT: Déterminer les montants employe et jacmar pour Dépense ---
                 employe_val_dep = 0.0
                 jacmar_val_dep = 0.0
                 if payeur_val: # True si Employé a payé
                     employe_val_dep = total_apres_taxes_val
                 else: # Jacmar a payé
                     jacmar_val_dep = total_apres_taxes_val
                 # ---------------------------------------------------------------------

                 new_entry = Depense(
                     date_depense=date_val, 
                     type_depense=type_val, 
                     description=description_val, 
                     fournisseur=fournisseur_val, 
                     payeur=payeur_val, 
                     # refacturer=False, # RETIRÉ: Non applicable pour Dépense
                     # numero_commande="", # RETIRÉ: Non applicable
                     totale_avant_taxes=total_avant_taxes_val,
                     tps=tps_val, 
                     tvq=tvq_val, 
                     tvh=tvh_val,
                     totale_apres_taxes=total_apres_taxes_val,
                     employe=employe_val_dep, # AJOUTÉ
                     jacmar=jacmar_val_dep,   # AJOUTÉ
                     facture=facture_obj_dep 
                 )
                 self.document.ajouter_depense(new_entry)

            if new_entry: # Si une entrée a été créée
                logger.debug(f"Entrée ajoutée au document: {new_entry}")
                self._clear_entry_form()
                self._apply_sorting_and_filtering() # Rafraîchir la liste affichée
                self._update_totals_display()
                self._update_frame_titles_with_counts()  # MAJ titres après ajout
                # print(f"Entrée ajoutée au document: {new_entry}") # MODIFICATION
                logger.info(f"Entrée ajoutée au document: {new_entry}") # MODIFICATION
                signals.document_modified.emit()
                # AJOUT: Mettre à jour spécifiquement le cadre déplacement si besoin
                if isinstance(new_entry, Deplacement):
                    self._update_deplacement_info_display()

        except KeyError as e:
             QMessageBox.critical(self, "Erreur Interne", f"Erreur de clé de formulaire: {e}. Le formulaire pour '{entry_type}' est peut-être incomplet.")
        except Exception as e:
             QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter l'entrée: {e}")
             # traceback.print_exc() # MODIFICATION
             logger.exception(f"Impossible d'ajouter l'entrée:") # MODIFICATION

    def _update_totals_display(self):
        # TODO: Lire self.document.get_totals() ou équivalent et mettre à jour les labels
        pass 

    def _toggle_num_commande_row_visibility(self, checked):
        """ Affiche ou cache la ligne (label + champ) N° Commande dans le QGridLayout. """
        logger.debug(f"_toggle_num_commande_row_visibility appelé avec checked={checked}") # MODIFICATION
        if hasattr(self, 'num_commande_repas_field') and self.num_commande_repas_field and \
           hasattr(self, 'num_commande_repas_label') and self.num_commande_repas_label and \
           hasattr(self, 'num_commande_row_index') and self.dynamic_form_layout: # Vérifier layout et index
            try:
                # Cacher/Montrer le label (colonne 0)
                self.num_commande_repas_label.setVisible(checked)
                # Cacher/Montrer le champ (colonne 1)
                self.num_commande_repas_field.setVisible(checked)

                # --- Ajuster la visibilité de la LIGNE ENTIÈRE dans le grid (Optionnel mais propre) ---
                # Note: Ceci cache toute la ligne, ce qui est l'effet désiré.
                # Il n'y a pas de setRowVisible direct, on cache les widgets. 
                # Si besoin de réorganiser, il faudrait retirer/réajouter les widgets.
                
                logger.debug(f"  Label et Field N° Commande setVisible({checked}) effectué pour la ligne {self.num_commande_row_index}.") # MODIFICATION
            except Exception as e:
                 logger.error(f"  Erreur lors de la modification de visibilité de la ligne N° Commande ({self.num_commande_row_index}): {e}") # MODIFICATION
        else:
            logger.error("  Erreur: Widgets N° Commande, index de ligne, ou layout non trouvés.") # MODIFICATION

    def _populate_entries_list(self):
        """Appelle la méthode centrale pour initialiser la liste des entrées."""
        # L'ancien code de peuplement est maintenant dans _apply_sorting_and_filtering
        self._apply_sorting_and_filtering()

    # --- Méthode _add_card_widget SUPPRIMÉE --- 

    # --- NOUVEAU HELPER: Générer Miniature ---
    def _generate_thumbnail_pixmap(self, file_path, size=QSize(64, 64)):
        """Génère un QPixmap miniature pour un fichier image ou PDF."""
        pixmap = QPixmap()
        is_image = any(file_path.lower().endswith(ext) for ext in
                       ['.png', '.jpg', '.jpeg', '.bmp', '.gif']) # Simplifié pour l'exemple

        try:
            if is_image:
                img = QImage(file_path)
                if not img.isNull():
                    pixmap = QPixmap.fromImage(img).scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            elif file_path.lower().endswith('.pdf') and PYMUPDF_AVAILABLE:
                doc = fitz.open(file_path)
                if len(doc) > 0:
                    page = doc.load_page(0)
                    # Rendu à une résolution légèrement supérieure pour meilleure qualité de réduction
                    zoom = 2.0
                    mat = fitz.Matrix(zoom, zoom)
                    pdf_pix = page.get_pixmap(matrix=mat, alpha=False)
                    qimage = QImage(pdf_pix.samples, pdf_pix.width, pdf_pix.height, pdf_pix.stride, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimage).scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                doc.close()
            else:
                # Fichier non trouvé ou type non supporté, utiliser une icône placeholder
                placeholder_path = get_icon_path("round_description.png") # Ou une autre icône
                if placeholder_path:
                    pixmap = QPixmap(placeholder_path).scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        except Exception as e:
            # print(f"Erreur génération miniature pour {file_path}: {e}") # MODIFICATION
            logger.error(f"Erreur génération miniature pour {file_path}: {e}") # MODIFICATION
            # Utiliser l'icône placeholder en cas d'erreur aussi
            placeholder_path = get_icon_path("round_description.png")
            if placeholder_path:
                 pixmap = QPixmap(placeholder_path).scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Créer un pixmap vide si tout a échoué
        if pixmap.isNull():
            pixmap = QPixmap(size)
            pixmap.fill(Qt.gray) # Remplir avec une couleur pour indiquer l'échec

        return pixmap
    # -----------------------------------------

    # --- NOUVEAUX Slots pour gérer les factures --- 
    def _select_factures(self):
        image_extensions = "*.png *.jpg *.jpeg *.bmp *.gif"
        pdf_extension = "*.pdf"
        all_files_filter = f"Fichiers supportés ({image_extensions} {pdf_extension});;Images ({image_extensions});;PDF ({pdf_extension});;Tous les fichiers (*)"
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Sélectionner Facture(s)",
            "", 
            all_files_filter
        )

        if file_paths:
            for file_path in file_paths:
                if file_path not in self.current_facture_thumbnails:
                     self._create_and_add_thumbnail(file_path)
                     # print(f"[TEMP] Facture ajoutée UI: {file_path}") # MODIFICATION
                     logger.debug(f"Facture ajoutée UI: {file_path}") # MODIFICATION

    def _create_and_add_thumbnail(self, file_path):
        pixmap = None
        # --- PyMuPDF check (mis en global pour éviter répétition) ---
        global PYMUPDF_AVAILABLE, fitz 
        # ---------------------------------------------------------
        try:
            # --- Génération Pixmap (Image) ---
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                pixmap = QPixmap(file_path)
                if pixmap.isNull():
                     # print(f"Erreur: Impossible de charger l'image {file_path}") # MODIFICATION
                     logger.error(f"Impossible de charger l'image {file_path}") # MODIFICATION
                     return
            # --- Génération Pixmap (PDF) ---
            elif file_path.lower().endswith('.pdf'):
                 if not PYMUPDF_AVAILABLE:
                     QMessageBox.warning(self, "Module manquant", 
                                           "PyMuPDF est requis pour les miniatures PDF. Veuillez l'installer (pip install pymupdf).")
                     return
                 try:
                     doc = fitz.open(file_path)
                     if len(doc) > 0:
                         page = doc.load_page(0) 
                         # Rendu à résolution plus élevée
                         zoom = 2.0 
                         mat = fitz.Matrix(zoom, zoom)
                         fitz_pix = page.get_pixmap(matrix=mat, alpha=False)
                         qimage = QImage(fitz_pix.samples, fitz_pix.width, fitz_pix.height, fitz_pix.stride, QImage.Format_RGB888)
                         pixmap = QPixmap.fromImage(qimage)
                     else:
                          # print(f"Erreur: PDF vide {file_path}") # MODIFICATION
                          logger.error(f"PDF vide {file_path}") # MODIFICATION
                          # Créer un pixmap placeholder gris?
                          pixmap = QPixmap(ThumbnailWidget.THUMBNAIL_SIZE, ThumbnailWidget.THUMBNAIL_SIZE)
                          pixmap.fill(Qt.darkGray)
                     doc.close()
                 except Exception as pdf_error:
                      logger.error(f"Erreur PyMuPDF pour {file_path}: {pdf_error}") # MODIFICATION
                      QMessageBox.warning(self, "Erreur PDF", f"Impossible de générer la miniature pour {file_path}.\n{pdf_error}")
                      # Créer un pixmap placeholder rouge?
                      pixmap = QPixmap(ThumbnailWidget.THUMBNAIL_SIZE, ThumbnailWidget.THUMBNAIL_SIZE)
                      pixmap.fill(Qt.red)
            # --- Format non supporté --- 
            else:
                # print(f"Format non supporté: {file_path}") # MODIFICATION
                logger.warning(f"Format de fichier non supporté pour la miniature: {file_path}") # MODIFICATION
                pixmap = QPixmap(ThumbnailWidget.THUMBNAIL_SIZE, ThumbnailWidget.THUMBNAIL_SIZE) # CORRECTION: Alignement
                pixmap.fill(Qt.lightGray) # CORRECTION: Alignement

            # --- Création et ajout du widget --- 
            if pixmap:
                thumbnail_widget = ThumbnailWidget(file_path, pixmap)
                thumbnail_widget.delete_requested.connect(self._remove_facture_thumbnail)
                # --- AJOUT: Connecter le signal clic --- 
                thumbnail_widget.clicked.connect(self._open_media_viewer_from_form)
                # ----------------------------------------
                self.facture_thumbnails_layout.addWidget(thumbnail_widget)
                self.current_facture_thumbnails[file_path] = thumbnail_widget
                # self.current_facture_paths.append(file_path) # <-- SUPPRESSION
                # Assurer visibilité
                QTimer.singleShot(0, lambda w=thumbnail_widget: self.facture_scroll_area.ensureWidgetVisible(w, 50, 0))
        
        except Exception as e:
            # print(f"Erreur inattendue création miniature pour {file_path}: {e}") # MODIFICATION
            # traceback.print_exc() # MODIFICATION
            logger.exception(f"Erreur inattendue création miniature pour {file_path}:") # MODIFICATION

    def _remove_facture_thumbnail(self, file_path, update_model=True):
        if file_path in self.current_facture_thumbnails:
            widget = self.current_facture_thumbnails[file_path]
            # Déconnecter signal peut être une bonne pratique
            try: widget.delete_requested.disconnect(self._remove_facture_thumbnail) 
            except TypeError: pass # Ignore si déjà déconnecté
            self.facture_thumbnails_layout.removeWidget(widget)
            widget.deleteLater()
            del self.current_facture_thumbnails[file_path]
            # --- SUPPRESSION: Retrait de current_facture_paths --- 
            # if file_path in self.current_facture_paths:
            #     self.current_facture_paths.remove(file_path)
            # else:
            #      print(f"WARN: Chemin {file_path} non trouvé dans current_facture_paths lors de la suppression.")
            # ------------------------------------------------------
            # if update_model: # Le flag update_model devient moins pertinent ici
            #      pass 
        else:
             logger.warning(f"Tentative suppression miniature non trouvée: {file_path}") # MODIFICATION
    # ------------------------------------------------

    # --- MODIFICATION Signature et Logique _open_media_viewer ---
    def _open_media_viewer(self, all_files: list, initial_index: int):
        """Ouvre MediaViewer avec la liste de fichiers et l'index initial."""
        if not all_files:
            QMessageBox.warning(self, "Aucun Fichier", "Aucun fichier associé à cette facture.")
            return

        # Filtrer les fichiers inexistants (sécurité)
        valid_files = [f for f in all_files if f and os.path.exists(f)] # Ajout check 'f is not None'
        if not valid_files:
             QMessageBox.critical(self, "Erreur Fichiers", "Aucun des fichiers de la facture n'a été trouvé.")
             return

        # Recalculer l'index initial basé sur la liste valide
        clicked_file_path = all_files[initial_index] # Chemin original cliqué
        valid_initial_index = 0 # Défaut à 0
        if clicked_file_path in valid_files:
             try:
                 valid_initial_index = valid_files.index(clicked_file_path)
             except ValueError:
                 # print(f"WARN: Fichier cliqué {clicked_file_path} était dans all_files mais pas trouvé dans valid_files après vérification existance. Bizarre. Ouverture index 0.") # MODIFICATION
                 logger.warning(f"Fichier cliqué {clicked_file_path} était dans all_files mais pas trouvé dans valid_files après vérification existance. Ouverture index 0.") # MODIFICATION
                 # Garde valid_initial_index à 0
        else:
             # Si le fichier cliqué n'existe pas/plus, on prend le premier valide (index 0)
              if valid_files: # Assure qu'il y a au moins un fichier valide
                  # print(f"WARN: Fichier cliqué {clicked_file_path} non trouvé ou invalide, ouverture du premier fichier valide ({valid_files[0]}).") # MODIFICATION
                  logger.warning(f"Fichier cliqué {clicked_file_path} non trouvé ou invalide, ouverture du premier fichier valide ({valid_files[0]}).") # MODIFICATION
                  # Garde valid_initial_index à 0
              else:
                   # Ne devrait pas arriver car vérifié plus haut, mais par sécurité
                   return


        try:
            # S'assurer que l'instance précédente est fermée si modale
            # (Si on passe en non-modal, gérer la liste self.open_viewers)

            # Passer la liste valide et l'index recalculé
             viewer = MediaViewer(media_source=valid_files, initial_index=valid_initial_index, parent=self.window()) # Parent = fenêtre principale
             # Rendre la fenêtre modale à l'application

             # --- CORRECTION: Définir les flags pour l'affichage en fenêtre séparée --- 
             viewer.setWindowFlags(viewer.windowFlags() | Qt.Window | Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
             # ------------------------------------------------------------------------

             viewer.setWindowModality(Qt.ApplicationModal) # Garder modal
             viewer.show()
             # Si non-modal:
             # viewer.setAttribute(Qt.WA_DeleteOnClose) # Optionnel: nettoyer mémoire

        except FileNotFoundError as e:
             QMessageBox.critical(self, "Erreur Fichier", str(e))
        except ValueError as e:
             QMessageBox.critical(self, "Erreur Données", str(e))
        except TypeError as e:
             QMessageBox.critical(self, "Erreur Type", str(e))
        except Exception as e:
            # print(f"Erreur inattendue ouverture MediaViewer: {e}") # MODIFICATION
            # traceback.print_exc() # MODIFICATION
            logger.exception(f"Erreur inattendue ouverture MediaViewer:") # MODIFICATION
            QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur est survenue lors de l'ouverture du visualiseur: {e}")
    # --- FIN MODIFICATION ---

    # --- NOUVEAU Slot pour gérer clic depuis FORMULAIRE --- 
    def _open_media_viewer_from_form(self, clicked_file_path: str):
        """Prépare les arguments et appelle _open_media_viewer pour un clic venant du formulaire."""
        all_paths = list(self.current_facture_thumbnails.keys())
        if not all_paths:
            # print("WARN: _open_media_viewer_from_form appelé mais self.current_facture_thumbnails est vide.") # MODIFICATION
            logger.warning("_open_media_viewer_from_form appelé mais self.current_facture_thumbnails est vide.") # MODIFICATION
            return

        try:
            clicked_index = all_paths.index(clicked_file_path)
            # Appeler la méthode principale avec la liste complète et l'index trouvé
            self._open_media_viewer(all_files=all_paths, initial_index=clicked_index)
        except ValueError:
            # print(f"ERROR: Chemin cliqué '{clicked_file_path}' non trouvé dans self.current_facture_thumbnails.keys().") # MODIFICATION
            logger.error(f"Chemin cliqué '{clicked_file_path}' non trouvé dans self.current_facture_thumbnails.keys().") # MODIFICATION
            QMessageBox.critical(self, "Erreur Interne", f"Le fichier cliqué ({os.path.basename(clicked_file_path)}) ne correspond à aucune miniature actuellement affichée.")
        except Exception as e:
            # print(f"Erreur inattendue dans _open_media_viewer_from_form: {e}") # MODIFICATION
            # traceback.print_exc() # MODIFICATION
            logger.exception(f"Erreur inattendue dans _open_media_viewer_from_form:") # MODIFICATION
            QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur interne est survenue avant d'ouvrir le visualiseur: {e}")
    # ------------------------------------------------------

    def _toggle_all_cards(self, checked):
        """Déplie ou replie toutes les CardWidget dans la liste."""
        # Changer l'icône du bouton principal
        icon_name = "round_collapse_all.png" if checked else "round_expand_all.png"
        icon_path = get_icon_path(icon_name)
        if icon_path:
            self.expand_collapse_button.setIcon(QIcon(icon_path))
        else:
            # Fallback texte si icône non trouvée
            self.expand_collapse_button.setText("↕" if checked else "↔") 

        # Parcourir les widgets dans le layout de la liste
        for i in range(self.entries_list_layout.count()):
            widget = self.entries_list_layout.itemAt(i).widget()
            if isinstance(widget, CardWidget):
                # Définir l'état 'checked' du bouton interne de la carte
                # Ceci déclenchera la méthode _toggle_details de la carte elle-même
                widget.expand_button.setChecked(checked)

    # --- Méthode _apply_filters SUPPRIMÉE --- 

    # --- NOUVELLE MÉTHODE CENTRALE --- 
    def _apply_sorting_and_filtering(self):
        """Récupère les options, filtre, trie et repeuple la liste des cartes."""
        # 1. Lire les options
        primary_sort_option = self.sort_primary_combo.currentText()
        secondary_sort_option = self.sort_secondary_combo.currentText()
        filter_option = self.filter_type_combo.currentText()

        # print(f"Applying sort/filter: Primary='{primary_sort_option}', Secondary='{secondary_sort_option}', Filter='{filter_option}'") # MODIFICATION
        logger.debug(f"Applying sort/filter: Primary='{primary_sort_option}', Secondary='{secondary_sort_option}', Filter='{filter_option}'") # MODIFICATION

        # 2. Récupérer toutes les entrées
        try:
            all_entries = self.document.deplacements + self.document.repas + self.document.depenses_diverses
        except Exception as e:
            # print(f"Erreur récupération entrées: {e}") # MODIFICATION
            logger.error(f"Erreur récupération entrées: {e}") # MODIFICATION
            all_entries = []

        # 3. Filtrer les entrées
        filtered_entries = []
        if filter_option == "Tout":
            filtered_entries = all_entries
        else:
            for entry in all_entries:
                entry_type_str = ""
                if isinstance(entry, Deplacement): entry_type_str = "Déplacements"
                elif isinstance(entry, Repas): entry_type_str = "Repas"
                elif isinstance(entry, Depense): entry_type_str = "Dépenses"
                
                if entry_type_str == filter_option:
                    filtered_entries.append(entry)
        
        # print(f"  {len(filtered_entries)} entries after filtering.") # MODIFICATION
        logger.debug(f"  {len(filtered_entries)} entries after filtering.") # MODIFICATION

        # --- 4. Logique de Tri avec functools.cmp_to_key --- 
        
        def get_comparable_value(entry, criterion):
            """Retourne la valeur comparable pour un critère donné."""
            if criterion == 'Date':
                val = getattr(entry, 'date_repas', getattr(entry, 'date_deplacement', getattr(entry, 'date_depense', getattr(entry, 'date', None))))
                # Retourner une date très ancienne pour les None pour qu'ils soient groupés
                return val if val is not None else date(1900, 1, 1) 
            elif criterion == 'Type':
                if isinstance(entry, Deplacement): return "Déplacement"
                if isinstance(entry, Repas): return "Repas"
                if isinstance(entry, Depense): return "Dépense"
                return "ZZZ" # Fallback pour tri
            elif criterion == 'Montant':
                amount_val = getattr(entry, 'totale_apres_taxes', getattr(entry, 'montant', 0.0))
                try: return float(amount_val)
                except (ValueError, TypeError): return 0.0 # Fallback
            return None # Critère inconnu ou "Aucun"

        def compare_entries(entry1, entry2):
            """Fonction de comparaison pour cmp_to_key."""
            
            # --- Comparaison Primaire --- 
            primary_criterion = ""
            primary_reverse = False
            if "Date" in primary_sort_option: primary_criterion = "Date"; primary_reverse = "Décroissant" in primary_sort_option
            elif "Type" in primary_sort_option: primary_criterion = "Type"; primary_reverse = "Z-A" in primary_sort_option
            elif "Montant" in primary_sort_option: primary_criterion = "Montant"; primary_reverse = "Décroissant" in primary_sort_option
            
            val1_1 = get_comparable_value(entry1, primary_criterion)
            val2_1 = get_comparable_value(entry2, primary_criterion)

            # Gérer les None (ne devrait pas arriver avec le fallback date, mais par sécurité)
            if val1_1 is None and val2_1 is None: cmp1 = 0
            elif val1_1 is None: cmp1 = -1 if not primary_reverse else 1
            elif val2_1 is None: cmp1 = 1 if not primary_reverse else -1
            else:
                if val1_1 < val2_1: cmp1 = -1
                elif val1_1 > val2_1: cmp1 = 1
                else: cmp1 = 0
            
            if primary_reverse: cmp1 *= -1

            if cmp1 != 0: return cmp1 # Différent sur le critère primaire

            # --- Comparaison Secondaire (si primaire égal et secondaire défini) --- 
            secondary_criterion = ""
            secondary_reverse = False
            if secondary_sort_option != "Aucun":
                 if "Date" in secondary_sort_option: secondary_criterion = "Date"; secondary_reverse = "Décroissant" in secondary_sort_option
                 elif "Type" in secondary_sort_option: secondary_criterion = "Type"; secondary_reverse = "Z-A" in secondary_sort_option
                 elif "Montant" in secondary_sort_option: secondary_criterion = "Montant"; secondary_reverse = "Décroissant" in secondary_sort_option
            
            if not secondary_criterion: return 0 # Pas de tri secondaire

            val1_2 = get_comparable_value(entry1, secondary_criterion)
            val2_2 = get_comparable_value(entry2, secondary_criterion)

            if val1_2 is None and val2_2 is None: cmp2 = 0
            elif val1_2 is None: cmp2 = -1 if not secondary_reverse else 1
            elif val2_2 is None: cmp2 = 1 if not secondary_reverse else -1
            else:
                if val1_2 < val2_2: cmp2 = -1
                elif val1_2 > val2_2: cmp2 = 1
                else: cmp2 = 0

            if secondary_reverse: cmp2 *= -1
            
            return cmp2
        
        # Trier en utilisant la fonction de comparaison
        try:
            sorted_entries = sorted(filtered_entries, key=functools.cmp_to_key(compare_entries))
            # print(f"  Sorted {len(sorted_entries)} entries using cmp_to_key.") # MODIFICATION
            logger.debug(f"  Sorted {len(sorted_entries)} entries using cmp_to_key.") # MODIFICATION
        except Exception as e:
            # print(f"Erreur de tri (cmp_to_key): {e}") # MODIFICATION
            # traceback.print_exc() # MODIFICATION
            logger.exception(f"Erreur de tri (cmp_to_key):") # MODIFICATION
            sorted_entries = filtered_entries # Fallback
        # --------------------------------------------------

        # --- AJOUT: Sauvegarde de l'état d'expansion des cartes --- 
        card_expansion_states = {}
        for i in range(self.entries_list_layout.count()):
            item = self.entries_list_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, CardWidget):
                # Assumer que CardWidget a un attribut entry_data et un bouton expand_button
                # Ou une méthode comme is_expanded()
                if hasattr(widget, 'entry_data') and hasattr(widget, 'expand_button'):
                    entry = widget.entry_data
                    is_expanded = widget.expand_button.isChecked()
                    # Utiliser l'objet entry lui-même comme clé (doit être hashable)
                    # Si les entrées n'ont pas d'ID unique stable, ceci pourrait poser problème
                    # si l'objet lui-même change d'identité (peu probable ici)
                    card_expansion_states[entry] = is_expanded
        # ------------------------------------------------------------

        # 5. Vider le layout
        while self.entries_list_layout.count():
            child = self.entries_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 6. Repeupler avec les cartes triées/filtrées
        if not sorted_entries:
            # Optionnel: Afficher un message si la liste est vide après filtrage/tri
            empty_label = QLabel("Aucune entrée ne correspond aux critères.")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("font-style: italic; color: gray;")
            self.entries_list_layout.addWidget(empty_label)
        else:
            for entry in sorted_entries:
                entry_type_str = "Inconnu"
                if isinstance(entry, Repas): entry_type_str = "Repas"
                elif isinstance(entry, Deplacement): entry_type_str = "Déplacement"
                elif isinstance(entry, Depense): entry_type_str = "Dépense"
                
                card = CardWidget(
                    entry_data=entry,
                    entry_type=entry_type_str,
                    parent=self
                )
                card.thumbnail_clicked.connect(self._open_media_viewer)
                # --- AJOUT: Connecter signaux options ---
                card.delete_requested.connect(functools.partial(self._handle_delete_entry, entry))
                card.duplicate_requested.connect(functools.partial(self._handle_duplicate_entry, entry))
                card.edit_requested.connect(functools.partial(self._handle_edit_entry, entry))
                # card.copy_requested.connect(functools.partial(self._handle_copy_entry, entry)) # Pour plus tard
                # ----------------------------------------
                self.entries_list_layout.addWidget(card)

                # --- AJOUT: Restauration de l'état d'expansion --- 
                if entry in card_expansion_states:
                    # Assumer que l'état est contrôlé par le check state du bouton
                    if hasattr(card, 'expand_button'):
                        card.expand_button.setChecked(card_expansion_states[entry])
                        # Il faut aussi potentiellement appeler la méthode qui gère l'affichage
                        # des détails si setChecked ne le fait pas automatiquement.
                        # Ceci dépend de l'implémentation de CardWidget._toggle_details
                        if hasattr(card, '_toggle_details'):
                            # Appeler directement peut causer des problèmes si lié à toggled.
                            # Il est préférable que setChecked déclenche la logique interne.
                            # card._toggle_details(card_expansion_states[entry]) # À vérifier
                            pass # Supposer que setChecked suffit
                # ----------------------------------------------------

        # Ajouter le stretch final
        self.entries_list_layout.addStretch(1)
        # print("  List repopulated.") # MODIFICATION
        logger.debug("  List repopulated.") # MODIFICATION

    def _handle_delete_entry(self, entry_to_delete):
        """Supprime une entrée (déplacement, repas, dépense) du document et rafraîchit l'interface."""
        entry_type = type(entry_to_delete)
        removed = False

        try:
            if entry_type is Deplacement and entry_to_delete in self.document.deplacements:
                self.document.deplacements.remove(entry_to_delete)
                removed = True
                # print(f"Déplacement supprimé: {entry_to_delete}") # Log de débogage # MODIFICATION
                logger.info(f"Déplacement supprimé: {entry_to_delete}") # MODIFICATION
            elif entry_type is Repas and entry_to_delete in self.document.repas:
                self.document.repas.remove(entry_to_delete)
                removed = True
                # print(f"Repas supprimé: {entry_to_delete}") # Log de débogage # MODIFICATION
                logger.info(f"Repas supprimé: {entry_to_delete}") # MODIFICATION
            elif entry_type is Depense and hasattr(self.document, 'depenses_diverses') and entry_to_delete in self.document.depenses_diverses:
                self.document.depenses_diverses.remove(entry_to_delete) # MODIFIÉ: Utilise depenses_diverses
                removed = True
                logger.info(f"Dépense (diverse) supprimée: {entry_to_delete}")
            elif entry_type is Depense and hasattr(self.document, 'depenses') and entry_to_delete in self.document.depenses:
                # Fallback si 'depenses' existe et 'depenses_diverses' n'a pas fonctionné
                self.document.depenses.remove(entry_to_delete)
                removed = True
                logger.info(f"Dépense (fallback 'depenses') supprimée: {entry_to_delete}")
            else:
                # print(f"WARN: Tentative de suppression d'une entrée non trouvée ou de type inconnu: {entry_to_delete}") # MODIFICATION
                logger.warning(f"Tentative de suppression d'une entrée non trouvée ou de type inconnu: {entry_to_delete}") # MODIFICATION

            if removed:
                self._update_totals_display()
                self._apply_sorting_and_filtering()
                signals.document_modified.emit()
                self._update_frame_titles_with_counts()  # MAJ titres après suppression
                # AJOUT: Mettre à jour spécifiquement le cadre déplacement si besoin
                if isinstance(entry_to_delete, Deplacement):
                    self._update_deplacement_info_display()
            else:
                QMessageBox.warning(self, "Erreur", "L'entrée à supprimer n'a pas été trouvée dans le document.")

        except Exception as e:
            # print(f"Erreur lors de la suppression de l'entrée: {e}") # MODIFICATION
            # traceback.print_exc() # MODIFICATION
            logger.exception(f"Erreur lors de la suppression de l'entrée:") # MODIFICATION
            QMessageBox.critical(self, "Erreur Critique", f"Une erreur est survenue lors de la suppression de l'entrée:\\n{e}")

    def _handle_duplicate_entry(self, entry_to_duplicate):
        """Crée une copie profonde d'une entrée et l'ajoute au document."""
        try:
            # Utiliser deepcopy pour une copie totalement indépendante
            new_entry = copy.deepcopy(entry_to_duplicate)
            # print(f"Duplication de: {entry_to_duplicate}") # MODIFICATION
            logger.debug(f"Duplication de: {entry_to_duplicate}") # MODIFICATION
            # print(f"  Copie créée: {new_entry}") # MODIFICATION
            logger.debug(f"  Copie créée: {new_entry}") # MODIFICATION

            # Optionnel: Ajuster des attributs de la copie si nécessaire
            # Par exemple, réinitialiser un ID ou mettre la date à aujourd'hui
            # if hasattr(new_entry, 'id'):
            #     new_entry.id = None # Ou générer un nouvel ID
            # if hasattr(new_entry, 'date'): # Adapter aux noms d'attributs réels
            #     today = date.today()
            #     if hasattr(new_entry, 'date_repas'): new_entry.date_repas = today
            #     elif hasattr(new_entry, 'date_deplacement'): new_entry.date_deplacement = today
            #     elif hasattr(new_entry, 'date_depense'): new_entry.date_depense = today

            entry_type = type(new_entry)
            added = False

            if entry_type is Deplacement:
                self.document.ajouter_deplacement(new_entry)
                added = True
            elif entry_type is Repas:
                self.document.ajouter_repas(new_entry)
                added = True
            elif entry_type is Depense:
                self.document.ajouter_depense(new_entry)
                added = True
            else:
                # print(f"WARN: Type d'entrée inconnu lors de la duplication: {entry_type}") # MODIFICATION
                logger.warning(f"Type d'entrée inconnu lors de la duplication: {entry_type}") # MODIFICATION
                QMessageBox.warning(self, "Type Inconnu", f"Impossible de dupliquer l'entrée de type {entry_type}.")

            if added:
                logger.info(f"Entrée dupliquée ajoutée au document: {new_entry}")
                self._update_totals_display()
                self._apply_sorting_and_filtering()
                signals.document_modified.emit()
                self._update_frame_titles_with_counts() # MAJ titres après duplication
                # AJOUT: Mettre à jour spécifiquement le cadre déplacement si besoin
                if isinstance(new_entry, Deplacement):
                    self._update_deplacement_info_display()
                # Optionnel: Sélectionner/scroller vers la nouvelle carte?

        except Exception as e:
            # print(f"Erreur lors de la duplication de l'entrée: {e}") # MODIFICATION
            # traceback.print_exc() # MODIFICATION
            logger.exception(f"Erreur lors de la duplication de l'entrée:") # MODIFICATION
            QMessageBox.critical(self, "Erreur Critique", f"Une erreur est survenue lors de la duplication de l'entrée:\\n{e}")

    # --- Méthodes pour le Mode Édition ---

    def _handle_edit_entry(self, entry_to_edit):
        """Lance le mode édition pour l'entrée spécifiée."""
        if self.editing_entry:
            # Si déjà en mode édition, demander confirmation?
            reply = QMessageBox.question(self, "Édition en cours",
                                         "Vous éditez déjà une autre entrée. Voulez-vous annuler l'édition actuelle et éditer cette nouvelle entrée?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            else:
                self._cancel_edit() # Annuler l'édition précédente

        # print(f"Entrée en mode édition pour: {entry_to_edit}") # MODIFICATION
        logger.debug(f"Entrée en mode édition pour: {entry_to_edit}") # MODIFICATION
        self.editing_entry = entry_to_edit

        # 1. Changer le type dans le ComboBox
        entry_type_str = ""
        if isinstance(entry_to_edit, Deplacement): entry_type_str = "Déplacement"
        elif isinstance(entry_to_edit, Repas): entry_type_str = "Repas"
        elif isinstance(entry_to_edit, Depense): entry_type_str = "Dépense"

        if entry_type_str:
            self.entry_type_combo.blockSignals(True) # Empêche _update_entry_form d'effacer
            self.entry_type_combo.setCurrentText(entry_type_str)
            self.entry_type_combo.blockSignals(False)
            # S'assurer que le formulaire correspond bien (au cas où setCurrentText n'émettrait pas)
            # Normalement currentIndexChanged est émis même si l'index ne change pas vraiment
            # mais pour être sûr, on force la mise à jour si le texte est déjà le bon.
            # On appelle directement _update_entry_form pour recréer la structure.
            self._update_entry_form()
            # Il faut ensuite peupler le formulaire qui vient d'être créé
            self._populate_form_with_entry(entry_to_edit)
            # Activer l'UI du mode édition
            self._enter_edit_mode_ui()
        else:
            # print(f"ERROR: Type d'entrée inconnu pour l'édition: {type(entry_to_edit)}") # MODIFICATION
            logger.error(f"Type d'entrée inconnu pour l'édition: {type(entry_to_edit)}") # MODIFICATION
            self.editing_entry = None # Annuler l'entrée en mode édition
            QMessageBox.warning(self, "Erreur", "Type d'entrée non reconnu.")

    def _populate_form_with_entry(self, entry):
        """Remplit les champs du formulaire actuel avec les données de l'entrée."""
        # print(f"Peuplement du formulaire avec: {entry}") # MODIFICATION
        logger.debug(f"Peuplement du formulaire avec: {entry}") # MODIFICATION
        try:
            # --- Champs Communs --- 
            entry_date = getattr(entry, 'date_repas', getattr(entry, 'date_deplacement', getattr(entry, 'date_depense', getattr(entry, 'date', None))))
            if entry_date and 'date' in self.form_fields:
                self.form_fields['date'].setDate(QDate(entry_date))
            else:
                # print("WARN: Date non trouvée ou champ date inexistant dans le formulaire") # MODIFICATION
                logger.warning(f"Date non trouvée ({entry_date}) ou champ 'date' inexistant dans le formulaire pour l'entrée {entry}") # MODIFICATION

            # --- Champs Spécifiques --- 
            if isinstance(entry, Deplacement):
                if 'client' in self.form_fields: 
                    self.form_fields['client'].setText(getattr(entry, 'client', ''))
                    # self.form_fields['client'].setStyleSheet("") # RETRAIT
                if 'ville' in self.form_fields: 
                    self.form_fields['ville'].setText(getattr(entry, 'ville', ''))
                    # self.form_fields['ville'].setStyleSheet("") # RETRAIT
                if 'numero_commande' in self.form_fields: 
                    self.form_fields['numero_commande'].setText(getattr(entry, 'numero_commande', ''))
                    # self.form_fields['numero_commande'].setStyleSheet("") # RETRAIT
                if 'kilometrage' in self.form_fields: self.form_fields['kilometrage'].setValue(getattr(entry, 'kilometrage', 0.0))
                # Mettre à jour l'affichage du montant pour déplacement
                TAUX_KM = 0.50 # TODO: Externaliser
                montant_deplacement = getattr(entry, 'kilometrage', 0.0) * TAUX_KM
                self._update_montant_display(montant_deplacement)

            elif isinstance(entry, Repas):
                if 'restaurant' in self.form_fields: 
                    self.form_fields['restaurant'].setText(getattr(entry, 'restaurant', ''))
                    # self.form_fields['restaurant'].setStyleSheet("") # RETRAIT
                if 'client_repas' in self.form_fields: 
                    self.form_fields['client_repas'].setText(getattr(entry, 'client', ''))
                    # self.form_fields['client_repas'].setStyleSheet("") # RETRAIT
                
                # Payeur (True = Employé)
                is_payeur_employe = getattr(entry, 'payeur', True) 
                if 'payeur_employe' in self.form_fields: self.form_fields['payeur_employe'].setChecked(is_payeur_employe)
                if 'payeur_jacmar' in self.form_fields: self.form_fields['payeur_jacmar'].setChecked(not is_payeur_employe)

                # Refacturer (True = Oui)
                is_refacturer_oui = getattr(entry, 'refacturer', False)
                if 'refacturer_oui' in self.form_fields: self.form_fields['refacturer_oui'].setChecked(is_refacturer_oui)
                if 'refacturer_non' in self.form_fields: self.form_fields['refacturer_non'].setChecked(not is_refacturer_oui)
                # Assurer que la visibilité de N° Cmd est correcte
                self._toggle_num_commande_row_visibility(is_refacturer_oui)
                if 'numero_commande_repas' in self.form_fields: self.form_fields['numero_commande_repas'].setText(getattr(entry, 'numero_commande', '') if is_refacturer_oui else '')

                # Montants et Taxes
                def set_float_field(key, attribute_name):
                    if key in self.form_fields:
                        widget = self.form_fields[key]
                        raw_value = getattr(entry, attribute_name, 0.0)
                        try:
                            numeric_value = float(raw_value) # Ensure it's a float
                            if isinstance(widget, NumericInputWithUnit):
                                widget.setValue(numeric_value)
                            elif hasattr(widget, 'setText'): # For QLineEdit or similar
                                widget.setText(f"{numeric_value:.2f}".replace('.', ','))
                            # else: widget is of an unknown type for this operation
                        except (ValueError, TypeError): # Error converting raw_value to float
                             if isinstance(widget, NumericInputWithUnit):
                                 widget.setValue(0.0)
                             elif hasattr(widget, 'setText'):
                                 widget.setText("0,00")
                
                set_float_field('total_avant_taxes', 'totale_avant_taxes')
                set_float_field('pourboire', 'pourboire')
                set_float_field('tps', 'tps')
                set_float_field('tvq', 'tvq')
                set_float_field('tvh', 'tvh')
                set_float_field('total_apres_taxes', 'totale_apres_taxes')

                # Factures
                # 1. Nettoyer les miniatures actuelles du formulaire
                for path in list(self.current_facture_thumbnails.keys()):
                    self._remove_facture_thumbnail(path, update_model=False)
                # 2. Ajouter les miniatures de l'entrée en cours d'édition
                facture_obj = getattr(entry, 'facture', None)
                if isinstance(facture_obj, Facture) and facture_obj.folder_path and facture_obj.filenames:
                    for filename in facture_obj.filenames:
                        full_path = os.path.join(facture_obj.folder_path, filename)
                        if os.path.exists(full_path):
                            self._create_and_add_thumbnail(full_path)
                        else:
                            print(f"WARN: Fichier facture non trouvé pour l'édition: {full_path}")
                
                # Mettre à jour l'affichage du montant (devrait être déjà fait par total_apres_taxes)
                # self._update_montant_display(self.form_fields['total_apres_taxes'].text()) # ANCIENNE LIGNE ERRONÉE
                if 'total_apres_taxes' in self.form_fields and isinstance(self.form_fields['total_apres_taxes'], NumericInputWithUnit):
                    self._update_montant_display(self.form_fields['total_apres_taxes'].value())
                # else: Gérer le cas où le champ n'est pas un NumericInputWithUnit si nécessaire

            elif isinstance(entry, Depense):
                if 'type_depense' in self.form_fields: self.form_fields['type_depense'].setCurrentText(getattr(entry, 'type_depense', 'Autre'))
                if 'description_dep' in self.form_fields: 
                    self.form_fields['description_dep'].setText(getattr(entry, 'description', ''))
                    # self.form_fields['description_dep'].setStyleSheet("") # RETRAIT
                if 'fournisseur_dep' in self.form_fields: 
                    self.form_fields['fournisseur_dep'].setText(getattr(entry, 'fournisseur', ''))
                    # self.form_fields['fournisseur_dep'].setStyleSheet("") # RETRAIT
                
                # Payeur (True = Employé)
                # Le constructeur de Depense attend 'payeur_employe' (bool) ou 'payeur' (str) ?
                # Supposons que le modèle Depense a un attribut comme 'payeur_is_employe' (bool)
                # ou que 'payeur' est un str "Employé" / "Jacmar"
                # Pour l'instant, on suppose que le modèle Depense stocke un booléen pour 'payeur_employe'
                is_payeur_employe = getattr(entry, 'payeur_employe', True) # Ajuster l'attribut du modèle si besoin
                if 'payeur_employe_dep' in self.form_fields: self.form_fields['payeur_employe_dep'].setChecked(is_payeur_employe)
                if 'payeur_jacmar_dep' in self.form_fields: self.form_fields['payeur_jacmar_dep'].setChecked(not is_payeur_employe)

                # Montants et Taxes (avec suffixe _dep)
                def set_float_field_dep(key, attribute_name):
                    if key in self.form_fields:
                        widget = self.form_fields[key]
                        raw_value = getattr(entry, attribute_name, 0.0)
                        try:
                            numeric_value = float(raw_value) 
                            if isinstance(widget, NumericInputWithUnit):
                                widget.setValue(numeric_value)
                            elif hasattr(widget, 'setText'):
                                widget.setText(f"{numeric_value:.2f}".replace('.', ','))
                        except (ValueError, TypeError):
                             if isinstance(widget, NumericInputWithUnit):
                                 widget.setValue(0.0)
                             elif hasattr(widget, 'setText'):
                                 widget.setText("0,00")

                set_float_field_dep('total_avant_taxes_dep', 'totale_avant_taxes')
                set_float_field_dep('tps_dep', 'tps')
                set_float_field_dep('tvq_dep', 'tvq')
                set_float_field_dep('tvh_dep', 'tvh')
                set_float_field_dep('total_apres_taxes_dep', 'totale_apres_taxes')

                # Factures pour Dépense
                for path in list(self.current_facture_thumbnails.keys()):
                    self._remove_facture_thumbnail(path, update_model=False)
                
                facture_obj_dep = getattr(entry, 'facture', None)
                if isinstance(facture_obj_dep, Facture) and facture_obj_dep.folder_path and facture_obj_dep.filenames:
                    for filename in facture_obj_dep.filenames:
                        full_path = os.path.join(facture_obj_dep.folder_path, filename)
                        if os.path.exists(full_path):
                            self._create_and_add_thumbnail(full_path)
                        else:
                            logger.warning(f"Fichier facture (dépense édit.) non trouvé: {full_path}")
                
                if 'total_apres_taxes_dep' in self.form_fields and isinstance(self.form_fields['total_apres_taxes_dep'], NumericInputWithUnit):
                    self._update_montant_display(self.form_fields['total_apres_taxes_dep'].value())

        except Exception as e:
            # print(f"Erreur lors du peuplement du formulaire: {e}") # MODIFICATION
            # traceback.print_exc() # MODIFICATION
            logger.exception(f"Erreur lors du peuplement du formulaire:") # MODIFICATION
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données de l'entrée dans le formulaire.\\n{e}")
            self._cancel_edit() # Quitter le mode édition en cas d'erreur grave

    def _enter_edit_mode_ui(self):
        """Met à jour l'interface pour refléter le mode édition."""
        # Changer bouton Ajouter -> Appliquer
        self.add_button.setText("Appliquer")
        try: self.add_button.clicked.disconnect(self._add_entry) 
        except TypeError: pass # Ignorer si déjà déconnecté
        try: self.add_button.clicked.connect(self._apply_edit)
        except TypeError: pass # Ignorer si déjà connecté?

        # Créer et/ou afficher bouton Annuler
        if not self.cancel_button:
            self.cancel_button = QPushButton("Annuler")
            self.cancel_button.setObjectName("TopNavButton") # Même style que les autres
            # Trouver le layout des boutons (supposé être le dernier layout ajouté au frame d'ajout)
            buttons_layout = None
            add_entry_layout = self.add_entry_frame.get_content_layout()
            if add_entry_layout.count() > 0:
                 last_item = add_entry_layout.itemAt(add_entry_layout.count() - 1)
                 if isinstance(last_item, QHBoxLayout): # Vérifier si c'est bien le HBox des boutons
                     buttons_layout = last_item
            
            if buttons_layout:
                # Insérer Annuler entre Effacer et Appliquer/Ajouter
                # buttons_layout.insertWidget(2, self.cancel_button) # Index 2 si stretch, effacer, [ici], ajouter, stretch # ANCIENNE LOGIQUE
                buttons_layout.insertWidget(1, self.cancel_button) # NOUVELLE LOGIQUE: Effacer (0), Annuler (1), Stretch (2), Appliquer (3)
            else:
                 # print("ERROR: Impossible de trouver le layout des boutons pour insérer Annuler.") # MODIFICATION
                 logger.error("Impossible de trouver le layout des boutons pour insérer Annuler.") # MODIFICATION
                 self.cancel_button = None # Ne pas le garder s'il n'a pas pu être ajouté
                 return # Sortir si on ne peut pas ajouter Annuler

        if self.cancel_button:
            self.cancel_button.setVisible(True)
            try: self.cancel_button.clicked.connect(self._cancel_edit)
            except TypeError: pass # Ignorer si déjà connecté
        
        # Désactiver le choix du type
        self.entry_type_combo.setEnabled(False)
        
        # --- AJOUT: Désactiver tri/filtre/expand ET les boutons compteurs --- 
        self.sort_primary_combo.setEnabled(False)
        self.sort_secondary_combo.setEnabled(False)
        self.filter_type_combo.setEnabled(False)
        self.expand_collapse_button.setEnabled(False)
        if hasattr(self, 'totals_frame_count_button'): self.totals_frame_count_button.setEnabled(False)
        if hasattr(self, 'deplacement_frame_count_button'): self.deplacement_frame_count_button.setEnabled(False)
        if hasattr(self, 'repas_frame_count_button'): self.repas_frame_count_button.setEnabled(False)
        if hasattr(self, 'depenses_diverses_frame_count_button'): self.depenses_diverses_frame_count_button.setEnabled(False)
        # ---------------------------------------------------------------------

        # Optionnel: Mettre en évidence le frame d'ajout?
        # --- Appliquer la bordure jaune au frame --- 
        self._original_frame_style = self.add_entry_frame.styleSheet() # Sauvegarder style actuel
        # Définir SEULEMENT la bordure pour ce sélecteur spécifique
        self.add_entry_frame.setStyleSheet("QFrame#CustomFrame { border: 2px solid #FFD600; }")
        # -------------------------------------------

        # --- Mise en évidence de la carte et verrouillage des options ---
        target_card = None
        for i in range(self.entries_list_layout.count()):
            item = self.entries_list_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, CardWidget):
                widget.set_options_enabled(False) # Désactiver options sur toutes
                if widget.entry_data == self.editing_entry:
                    widget.set_editing_highlight(True) # Mettre en évidence la bonne
                    target_card = widget
        
        # Faire défiler jusqu'à la carte mise en évidence
        if target_card:
            QTimer.singleShot(0, lambda w=target_card: self.entries_scroll_area.ensureWidgetVisible(w, 0, 100)) # Marge verticale 100px
        # ------------------------------------------------------------------

    def _exit_edit_mode_ui(self):
        """Restaure l'interface après avoir quitté le mode édition."""
        self.editing_entry = None

        # Changer bouton Appliquer -> Ajouter
        self.add_button.setText("Ajouter")
        try: self.add_button.clicked.disconnect(self._apply_edit)
        except TypeError: pass
        try: self.add_button.clicked.connect(self._add_entry)
        except TypeError: pass

        # Cacher et déconnecter bouton Annuler
        if self.cancel_button:
            self.cancel_button.setVisible(False)
            try: self.cancel_button.clicked.disconnect(self._cancel_edit)
            except TypeError: pass
        
        # Réactiver le choix du type
        self.entry_type_combo.setEnabled(True)

        # Nettoyer le formulaire
        self._clear_entry_form()

        # Optionnel: Retirer la mise en évidence
        # self.add_entry_frame.setStyleSheet("") # Reset style
        # --- Restaurer le style original du frame --- 
        if self._original_frame_style is not None:
            self.add_entry_frame.setStyleSheet(self._original_frame_style)
            self._original_frame_style = "" # Réinitialiser pour la prochaine fois
        # ------------------------------------------

        # --- Restauration des cartes --- 
        for i in range(self.entries_list_layout.count()):
            item = self.entries_list_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, CardWidget):
                widget.set_options_enabled(True)     # Réactiver options
                widget.set_editing_highlight(False)  # Retirer mise en évidence
        # -------------------------------

        # --- AJOUT: Réactiver tri/filtre/expand ET les boutons compteurs --- 
        self.sort_primary_combo.setEnabled(True)
        self.sort_secondary_combo.setEnabled(True)
        self.filter_type_combo.setEnabled(True)
        self.expand_collapse_button.setEnabled(True)
        if hasattr(self, 'totals_frame_count_button'): self.totals_frame_count_button.setEnabled(True)
        if hasattr(self, 'deplacement_frame_count_button'): self.deplacement_frame_count_button.setEnabled(True)
        if hasattr(self, 'repas_frame_count_button'): self.repas_frame_count_button.setEnabled(True)
        if hasattr(self, 'depenses_diverses_frame_count_button'): self.depenses_diverses_frame_count_button.setEnabled(True)
        # ---------------------------------------------------------------------

    def _apply_edit(self):
        """Sauvegarde les modifications de l'entrée en cours et quitte le mode édition."""
        if not self.editing_entry:
            logger.error("_apply_edit appelé sans entrée en cours d'édition.")
            self._exit_edit_mode_ui() # Quitter proprement quand même
            return
        
        # --- DÉFINITION DE LA FONCTION HELPER get_float_from_field_apply ICI ---
        def get_float_from_field_apply(key):
            try:
                widget = self.form_fields[key]
                if isinstance(widget, NumericInputWithUnit):
                    return widget.value()
                else:
                    return float(widget.text().replace(',', '.'))
            except (KeyError, ValueError, AttributeError): 
                logger.warning(f"Clé '{key}' non trouvée ou valeur invalide dans _apply_edit.")
                return 0.0
        # --- FIN DÉFINITION HELPER ---

        logger.debug(f"Application des modifications pour: {self.editing_entry}")
        original_entry = self.editing_entry # Garder référence pour la fin

        try:
            # --- AJOUT: Validation avant d'appliquer --- 
            current_entry_type_str = ""
            if isinstance(self.editing_entry, Deplacement): current_entry_type_str = "Déplacement"
            elif isinstance(self.editing_entry, Repas): current_entry_type_str = "Repas"
            elif isinstance(self.editing_entry, Depense): current_entry_type_str = "Dépense"
            
            if not self._validate_form_data(current_entry_type_str):
                return # Stopper si validation échoue, RESTER en mode édition
            # -------------------------------------------

            # Récupérer les valeurs du formulaire (logique similaire à _add_entry)
            date_val = self.form_fields['date'].date().toPyDate()
            
            # --- Mise à jour des attributs de self.editing_entry --- 
            current_entry_type = type(self.editing_entry)

            # Mettre à jour la date commune
            if hasattr(self.editing_entry, 'date_repas'): self.editing_entry.date_repas = date_val
            elif hasattr(self.editing_entry, 'date_deplacement'): self.editing_entry.date_deplacement = date_val
            elif hasattr(self.editing_entry, 'date_depense'): self.editing_entry.date_depense = date_val
            elif hasattr(self.editing_entry, 'date'): self.editing_entry.date = date_val

            if current_entry_type is Deplacement:
                self.editing_entry.client = self.form_fields['client'].text()
                self.editing_entry.ville = self.form_fields['ville'].text()
                self.editing_entry.numero_commande = self.form_fields['numero_commande'].text()
                self.editing_entry.kilometrage = self.form_fields['kilometrage'].value()
                TAUX_KM = 0.50 # TODO: Externaliser
                self.editing_entry.montant = self.editing_entry.kilometrage * TAUX_KM

            elif current_entry_type is Repas:
                self.editing_entry.restaurant = self.form_fields['restaurant'].text()
                self.editing_entry.client = self.form_fields['client_repas'].text() # Attention, clé différente
                self.editing_entry.payeur = self.form_fields['payeur_employe'].isChecked()
                self.editing_entry.refacturer = self.form_fields['refacturer_oui'].isChecked()
                self.editing_entry.numero_commande = self.form_fields['numero_commande_repas'].text() if self.editing_entry.refacturer else ""
                
                # RETRAIT DE LA DÉFINITION DE get_float_from_field_apply D'ICI
                
                self.editing_entry.totale_avant_taxes = get_float_from_field_apply('total_avant_taxes')
                self.editing_entry.pourboire = get_float_from_field_apply('pourboire')
                self.editing_entry.tps = get_float_from_field_apply('tps')
                self.editing_entry.tvq = get_float_from_field_apply('tvq')
                self.editing_entry.tvh = get_float_from_field_apply('tvh')
                self.editing_entry.totale_apres_taxes = get_float_from_field_apply('total_apres_taxes')
                # self.editing_entry.employe = ... # Si nécessaire
                # self.editing_entry.jacmar = ... # Si nécessaire
                
                # Mise à jour Facture
                all_paths = list(self.current_facture_thumbnails.keys())
                if not all_paths:
                    self.editing_entry.facture = None # Aucune facture dans le formulaire
                else:
                    first_path = all_paths[0]
                    folder_path = os.path.dirname(first_path)
                    filenames = [os.path.basename(p) for p in all_paths]
                    # Vérifier si la facture existante peut être mise à jour ou s'il faut en créer une nouvelle
                    if isinstance(self.editing_entry.facture, Facture):
                        self.editing_entry.facture.folder_path = folder_path
                        self.editing_entry.facture.filenames = filenames
                    else:
                        try:
                            self.editing_entry.facture = Facture(folder_path=folder_path, filenames=filenames)
                        except Exception as fact_err:
                            # print(f"ERROR: Impossible de créer/màj l'objet Facture pendant l'édition: {fact_err}") # MODIFICATION
                            logger.error(f"Impossible de créer/màj l'objet Facture pendant l'édition: {fact_err}") # MODIFICATION
                            self.editing_entry.facture = None # Laisser à None en cas d'erreur
            
            elif current_entry_type is Depense:
                self.editing_entry.type_depense = self.form_fields['type_depense'].currentText()
                self.editing_entry.description = self.form_fields['description_dep'].text() # MODIFIÉ: _dep
                self.editing_entry.fournisseur = self.form_fields['fournisseur_dep'].text() # MODIFIÉ: _dep
                self.editing_entry.payeur_employe = self.form_fields['payeur_employe_dep'].isChecked() # Ajuster attribut modèle si besoin
                
                # Pas de refacturer ou num_commande pour Depense
                self.editing_entry.refacturer = False
                self.editing_entry.numero_commande = ""
                                
                self.editing_entry.totale_avant_taxes = get_float_from_field_apply('total_avant_taxes_dep') # MODIFIÉ: _dep
                self.editing_entry.tps = get_float_from_field_apply('tps_dep') # MODIFIÉ: _dep
                self.editing_entry.tvq = get_float_from_field_apply('tvq_dep') # MODIFIÉ: _dep
                self.editing_entry.tvh = get_float_from_field_apply('tvh_dep') # MODIFIÉ: _dep
                self.editing_entry.totale_apres_taxes = get_float_from_field_apply('total_apres_taxes_dep') # MODIFIÉ: _dep
                
                # Mise à jour Facture pour Dépense
                all_paths_dep = list(self.current_facture_thumbnails.keys())
                if not all_paths_dep:
                    self.editing_entry.facture = None
                else:
                    first_path_dep = all_paths_dep[0]
                    folder_path_dep = os.path.dirname(first_path_dep)
                    filenames_dep = [os.path.basename(p) for p in all_paths_dep]
                    if isinstance(self.editing_entry.facture, Facture):
                        self.editing_entry.facture.folder_path = folder_path_dep
                        self.editing_entry.facture.filenames = filenames_dep
                    else:
                        try:
                            self.editing_entry.facture = Facture(folder_path=folder_path_dep, filenames=filenames_dep)
                        except Exception as fact_err:
                            logger.error(f"Impossible de màj Facture (Dépense édit.): {fact_err}")
                            self.editing_entry.facture = None

            # Validation (ajouter si nécessaire)
            # ...

            # Rafraîchir l'affichage et émettre signal
            # print(f"Modifications appliquées à: {self.editing_entry}") # MODIFICATION
            logger.info(f"Modifications appliquées à: {self.editing_entry}") # MODIFICATION
            self._update_totals_display()
            self._apply_sorting_and_filtering() # Rafraîchit la liste des cartes
            signals.document_modified.emit()
            self._update_frame_titles_with_counts()  # MAJ titres après édition
            # AJOUT: Mettre à jour spécifiquement le cadre déplacement si besoin
            if isinstance(self.editing_entry, Deplacement):
                self._update_deplacement_info_display()

            # Quitter le mode édition
            self._exit_edit_mode_ui()

        except KeyError as e:
             QMessageBox.critical(self, "Erreur Interne", f"Erreur de clé de formulaire lors de l'application: {e}. Le formulaire est peut-être incomplet.")
             # Ne pas quitter le mode édition pour que l'utilisateur puisse corriger?
        except Exception as e:
             QMessageBox.critical(self, "Erreur Application", f"Impossible d'appliquer les modifications: {e}")
             # traceback.print_exc() # MODIFICATION
             logger.exception(f"Impossible d'appliquer les modifications à l'entrée {original_entry}:") # MODIFICATION
             # Ne pas quitter le mode édition ici non plus?

    def _cancel_edit(self):
        """Annule l'édition en cours et quitte le mode édition."""
        logger.debug("Annulation de l'édition.") # MODIFICATION
        self._exit_edit_mode_ui()

    # --- Fin Méthodes Mode Édition ---

    # --- Mock Class pour tests (si nécessaire) ---
    class MockRapportDepense:
        pass # Ajout pour corriger l'IndentationError # MODIFICATION

    def _validate_form_data(self, entry_type):
        """Valide les données du formulaire pour un type d'entrée donné."""
        def get_float_from_form(key):
            try:
                widget = self.form_fields[key]
                if isinstance(widget, NumericInputWithUnit):
                    return widget.value()
                else:
                    return float(widget.text().replace(',', '.'))
            except (KeyError, ValueError, AttributeError):
                return 0.0

        if entry_type == "Déplacement":
            client_val = self.form_fields['client'].text().strip() if 'client' in self.form_fields else ""
            ville_val = self.form_fields['ville'].text().strip() if 'ville' in self.form_fields else ""
            numero_commande_val = self.form_fields['numero_commande'].text().strip() if 'numero_commande' in self.form_fields else ""
            kilometrage_val = get_float_from_form('kilometrage') if 'kilometrage' in self.form_fields else 0.0
            if not client_val:
                QMessageBox.warning(self, "Champ manquant", "Le nom du client est requis pour un déplacement.")
                return False
            if not ville_val:
                QMessageBox.warning(self, "Champ manquant", "La ville est requise pour un déplacement.")
                return False
            if not numero_commande_val:
                QMessageBox.warning(self, "Champ manquant", "Le numéro de commande est requis pour un déplacement.")
                return False
            if abs(kilometrage_val) < 1e-6:
                QMessageBox.warning(self, "Kilométrage invalide", "Le kilométrage doit être différent de zéro.")
                return False

        elif entry_type == "Repas":
            restaurant_val = self.form_fields['restaurant'].text().strip() if 'restaurant' in self.form_fields else ""
            total_avant_taxes_val = get_float_from_form('total_avant_taxes') if 'total_avant_taxes' in self.form_fields else 0.0
            total_apres_taxes_val = get_float_from_form('total_apres_taxes') if 'total_apres_taxes' in self.form_fields else 0.0
            if not restaurant_val:
                QMessageBox.warning(self, "Champ manquant", "Le nom du restaurant est requis.")
                return False
            if abs(total_avant_taxes_val) < 1e-6:
                QMessageBox.warning(self, "Montant invalide", "Le total avant taxes doit être différent de zéro.")
                return False
            if abs(total_apres_taxes_val) < 1e-6:
                QMessageBox.warning(self, "Montant invalide", "Le total après taxes doit être différent de zéro.")
                return False

        elif entry_type == "Dépense":
            description_val = self.form_fields['description_dep'].text().strip() if 'description_dep' in self.form_fields else ""
            fournisseur_val = self.form_fields['fournisseur_dep'].text().strip() if 'fournisseur_dep' in self.form_fields else ""
            total_avant_taxes_val = get_float_from_form('total_avant_taxes_dep') if 'total_avant_taxes_dep' in self.form_fields else 0.0
            total_apres_taxes_val = get_float_from_form('total_apres_taxes_dep') if 'total_apres_taxes_dep' in self.form_fields else 0.0
            if not description_val:
                QMessageBox.warning(self, "Champ manquant", "La description est requise.")
                return False
            if not fournisseur_val:
                QMessageBox.warning(self, "Champ manquant", "Le fournisseur est requis.")
                return False
            if abs(total_avant_taxes_val) < 1e-6:
                QMessageBox.warning(self, "Montant invalide", "Le total avant taxes doit être différent de zéro.")
                return False
            if abs(total_apres_taxes_val) < 1e-6:
                QMessageBox.warning(self, "Montant invalide", "Le total après taxes doit être différent de zéro.")
                return False

        else:
            logger.warning(f"Validation demandée pour type inconnu: {entry_type}")
            pass

        return True # Si toutes les validations passent

    def _update_totals_display(self):
        # TODO: Lire self.document.get_totals() ou équivalent et mettre à jour les labels
        pass 

    def _update_frame_titles_with_counts(self):
        """Met à jour dynamiquement les labels de compteur des frames du bas."""
        try:
            n_depl = len(getattr(self.document, 'deplacements', []))
            n_repas = len(getattr(self.document, 'repas', []))
            n_depdiv = len(getattr(self.document, 'depenses_diverses', []))
            n_total = n_depl + n_repas + n_depdiv

            # MODIFIÉ: Mettre à jour le texte des BOUTONS
            if hasattr(self, 'totals_frame_count_button'):
                self.totals_frame_count_button.setText(f"({n_total})")
            if hasattr(self, 'deplacement_frame_count_button'):
                self.deplacement_frame_count_button.setText(f"({n_depl})")
            if hasattr(self, 'repas_frame_count_button'):
                self.repas_frame_count_button.setText(f"({n_repas})")
            if hasattr(self, 'depenses_diverses_frame_count_button'):
                self.depenses_diverses_frame_count_button.setText(f"({n_depdiv})")
        except Exception as e:
            logger.error(f"Erreur dans _update_frame_titles_with_counts: {e}", exc_info=True)

    # AJOUT: Nouvelle méthode pour gérer le clic sur les boutons compteurs
    def _set_filter_from_button(self, filter_text):
        """Met à jour le ComboBox de filtre en fonction du bouton cliqué."""
        if not hasattr(self, 'filter_type_combo'):
            logger.error("_set_filter_from_button: filter_type_combo n'existe pas.")
            return

        index = self.filter_type_combo.findText(filter_text)
        if index != -1:
            if self.filter_type_combo.currentIndex() != index:
                self.filter_type_combo.setCurrentIndex(index)
                logger.debug(f"Filtre défini sur '{filter_text}' via bouton compteur.")
            else:
                logger.debug(f"Filtre déjà sur '{filter_text}', clic ignoré.")
        else:
            logger.warning(f"Texte de filtre '{filter_text}' non trouvé dans filter_type_combo.")

    # --- AJOUT: Logique pour boutons Calculatrice --- 
    def _calculate_tax(self, tax_type: str):
        """Calcule la taxe (TPS ou TVQ) en fonction des totaux saisis."""
        entry_type = self.entry_type_combo.currentText()
        prefix = '' if entry_type == "Repas" else '_dep'

        total_avant_taxes_key = f'total_avant_taxes{prefix}'
        total_apres_taxes_key = f'total_apres_taxes{prefix}'
        tax_field_key = f'{tax_type}{prefix}'

        try:
            total_avant_taxes_widget = self.form_fields.get(total_avant_taxes_key)
            total_apres_taxes_widget = self.form_fields.get(total_apres_taxes_key)
            tax_widget = self.form_fields.get(tax_field_key)

            if not all([total_avant_taxes_widget, total_apres_taxes_widget, tax_widget]):
                logger.error(f"Erreur: Un ou plusieurs widgets n'ont pas été trouvés pour le calcul de la taxe {tax_type} pour {entry_type}.")
                QMessageBox.critical(self, "Erreur de Widget", "Impossible de trouver les champs nécessaires pour le calcul.")
                return

            total_avant_tx = total_avant_taxes_widget.value()
            total_apres_tx = total_apres_taxes_widget.value()
            tolerance = 1e-6

            # i. Si les deux totaux sont (presque) zéro, mettre la taxe à zéro
            if abs(total_avant_tx) < tolerance and abs(total_apres_tx) < tolerance:
                logger.debug(f"Calcul de {tax_type}: Total avant et après taxes sont à zéro. Mise à zéro du champ {tax_type}.")
                tax_widget.setValue(0.0) # AJOUT: Mettre le champ taxe à 0
                return

            # ii. Si seul Total Avant Taxes est saisi
            if abs(total_apres_tx) < tolerance and abs(total_avant_tx) > tolerance:
                logger.debug(f"Calcul de {tax_type}: Utilisation du Total avant taxes ({total_avant_tx}).")
                try:
                    config_instance = ConfigData.get_instance()
                    config_data = config_instance.all_data # CORRECTION: Accéder à la propriété all_data sans parenthèses
                    # Accéder aux taux globaux
                    # CORRECTION: Utiliser les clés "TPS" et "TVQ" au lieu de "taux_tps"/"taux_tvq"
                    tax_key = tax_type.upper() # Convertit 'tps' -> 'TPS', 'tvq' -> 'TVQ'
                    taux_str = config_data['documents']['Global'][0].get(tax_key)
                    if taux_str is None:
                        raise KeyError(f"Le taux '{tax_key}' n'est pas défini dans config_data.json")

                    taux = float(taux_str)
                    taxe_calculee = total_avant_tx * taux

                    tax_widget.setValue(taxe_calculee)
                    logger.info(f"{tax_type.upper()} calculée ({taxe_calculee:.2f}) à partir du total avant taxes ({total_avant_tx:.2f}) avec un taux de {taux:.2%}")

                except (KeyError, IndexError, ValueError, TypeError) as e:
                    error_msg = f"Erreur lors de la récupération ou conversion du taux de {tax_type}: {e}\nVérifiez la structure et le contenu de 'data/config_data.json' (chemin: documents.Global[0].taux_{tax_type})"
                    logger.exception(error_msg) # Utilise logger.exception pour inclure le traceback
                    QMessageBox.critical(self, f"Erreur de Configuration - Taux {tax_type.upper()}", error_msg)
                except Exception as e:
                    error_msg = f"Une erreur inattendue est survenue lors du calcul de la {tax_type}: {e}"
                    logger.exception(error_msg)
                    QMessageBox.critical(self, "Erreur Inattendue", error_msg)

            # iii. Si seul Total Après Taxes est saisi (Calcul inverse)
            elif abs(total_avant_tx) < tolerance and abs(total_apres_tx) > tolerance:
                logger.debug(f"Calcul inverse de {tax_type}: Utilisation du Total après taxes ({total_apres_tx}).")
                
                pourboire_val = 0.0
                if entry_type == "Repas":
                    pourboire_widget = self.form_fields.get('pourboire')
                    if pourboire_widget:
                        try:
                            pourboire_val = pourboire_widget.value()
                            logger.debug(f"  Pourboire récupéré: {pourboire_val}")
                        except Exception as e:
                            logger.warning(f"Impossible de lire la valeur du pourboire: {e}")
                    else:
                        logger.warning("Champ 'pourboire' non trouvé pour Repas lors du calcul inverse.")
                
                base_imposable = total_apres_tx - pourboire_val
                if base_imposable < 0:
                     logger.warning(f"Calcul inverse impossible: Base imposable négative ({base_imposable:.2f}) après déduction du pourboire.")
                     QMessageBox.warning(self, "Calcul Impossible", 
                                        f"Le total après taxes ({total_apres_tx:.2f}) est inférieur au pourboire ({pourboire_val:.2f}). Impossible de calculer la taxe.")
                     return

                try:
                    config_instance = ConfigData.get_instance()
                    config_data = config_instance.all_data
                    global_config = config_data.get('documents', {}).get('Global', [{}])[0]

                    # Récupérer les DEUX taux
                    taux_tps_str = global_config.get('TPS')
                    taux_tvq_str = global_config.get('TVQ')

                    if taux_tps_str is None or taux_tvq_str is None:
                         missing = []
                         if taux_tps_str is None: missing.append('TPS')
                         if taux_tvq_str is None: missing.append('TVQ')
                         raise KeyError(f"Le(s) taux suivant(s) ne sont pas définis dans config_data.json: {', '.join(missing)}")

                    taux_tps = float(taux_tps_str)
                    taux_tvq = float(taux_tvq_str)
                    
                    denominateur = 1 + taux_tps + taux_tvq
                    if abs(denominateur) < tolerance:
                        raise ZeroDivisionError("Le dénominateur (1 + taux_tps + taux_tvq) est trop proche de zéro.")

                    montant_avant_tout = base_imposable / denominateur
                    
                    target_rate = taux_tps if tax_type == 'tps' else taux_tvq
                    taxe_calculee = montant_avant_tout * target_rate

                    tax_widget.setValue(taxe_calculee)
                    logger.info(f"{tax_type.upper()} calculée (inverse) ({taxe_calculee:.2f}) à partir du total après taxes ({total_apres_tx:.2f}), pourboire ({pourboire_val:.2f}), et taux (TPS: {taux_tps:.2%}, TVQ: {taux_tvq:.2%})")

                except (KeyError, IndexError, ValueError, TypeError, ZeroDivisionError) as e:
                    error_msg = f"Erreur lors du calcul inverse de la {tax_type}: {e}\nVérifiez la structure et le contenu de 'data/config_data.json' (chemin: documents.Global[0].TPS/TVQ)"
                    logger.exception(error_msg) # Utilise logger.exception pour inclure le traceback
                    QMessageBox.critical(self, f"Erreur de Configuration/Calcul - Taux {tax_type.upper()} (Inverse)", error_msg)
                except Exception as e:
                    error_msg = f"Une erreur inattendue est survenue lors du calcul inverse de la {tax_type}: {e}"
                    logger.exception(error_msg)
                    QMessageBox.critical(self, "Erreur Inattendue (Inverse)", error_msg)

            # iv. Si les deux totaux sont saisis (Placeholder)
            elif abs(total_avant_tx) > tolerance and abs(total_apres_tx) > tolerance:
                logger.warning(f"Calcul de {tax_type}: Logique non implémentée lorsque les deux totaux sont saisis.")
                # TODO: Décider quelle logique appliquer (ignorer, valider, recalculer ?)
                QMessageBox.information(self, "Action non définie",
                                        f"Le calcul automatique de la {tax_type.upper()} n'est pas effectué lorsque le total avant ET après taxes sont déjà remplis.")
                pass

        except Exception as e:
            error_msg = f"Une erreur générale est survenue dans _calculate_tax pour {tax_type}: {e}"
            logger.exception(error_msg)
            QMessageBox.critical(self, "Erreur Générale", error_msg)

    def _calculate_total_apres_taxes(self):
        """Calcule le Total après taxes basé sur les autres champs monétaires."""
        entry_type = self.entry_type_combo.currentText()
        prefix = '' if entry_type == "Repas" else '_dep'
        logger.debug(f"Calcul du Total Après Taxes pour {entry_type}...")

        keys = [
            f'total_avant_taxes{prefix}',
            f'tps{prefix}',
            f'tvq{prefix}',
            f'tvh{prefix}'
        ]
        target_key = f'total_apres_taxes{prefix}'
        
        # Ajouter pourboire seulement pour Repas
        if entry_type == "Repas":
            keys.append('pourboire') 

        total = 0.0
        try:
            target_widget = self.form_fields.get(target_key)
            if not target_widget:
                logger.error(f"Widget cible '{target_key}' non trouvé pour le calcul du total après taxes.")
                QMessageBox.critical(self, "Erreur Widget", f"Impossible de trouver le champ '{target_key}'.")
                return

            widget_values = {}
            for key in keys:
                widget = self.form_fields.get(key)
                value = 0.0
                if widget and hasattr(widget, 'value'):
                    try:
                        value = widget.value()
                    except Exception as e:
                        logger.warning(f"Impossible de lire la valeur du widget '{key}': {e}")
                else:
                     # Ne pas logger si c'est TVH car il n'existe pas pour Dépense
                     if not (key == 'tvh_dep' and entry_type == "Dépense") and key != 'pourboire': # Ne pas logger pourboire absent hors repas
                          logger.warning(f"Widget '{key}' non trouvé ou sans méthode .value() pour calcul total après taxes.")
                
                widget_values[key] = value # Stocke la valeur (peut être 0.0)
                total += value

            target_widget.setValue(total)
            log_details = ", ".join([f"{k.replace(prefix, '').replace('_', ' ')}: {v:.2f}" for k, v in widget_values.items()])
            logger.info(f"Total après taxes calculé ({total:.2f}) basé sur: {log_details}")
        
        except Exception as e:
            error_msg = f"Erreur lors du calcul du total après taxes: {e}"
            logger.exception(error_msg)
            QMessageBox.critical(self, "Erreur Calcul Total Après Taxes", error_msg)

    def _calculate_total_avant_taxes(self):
        """Calcule le Total avant taxes basé sur les autres champs monétaires (inverse)."""
        entry_type = self.entry_type_combo.currentText()
        prefix = '' if entry_type == "Repas" else '_dep'
        logger.debug(f"Calcul du Total Avant Taxes pour {entry_type}...")

        # Clés des champs à soustraire
        subtract_keys = [
            f'tps{prefix}',
            f'tvq{prefix}',
            f'tvh{prefix}'
        ]
        # Clé du champ source (total après taxes)
        source_key = f'total_apres_taxes{prefix}'
        # Clé du champ cible (total avant taxes)
        target_key = f'total_avant_taxes{prefix}'

        # Ajouter pourboire seulement pour Repas
        if entry_type == "Repas":
            subtract_keys.append('pourboire')

        total_apres_taxes = 0.0
        total_to_subtract = 0.0
        try:
            target_widget = self.form_fields.get(target_key)
            source_widget = self.form_fields.get(source_key)
            
            if not target_widget or not source_widget:
                missing = []
                if not target_widget: missing.append(target_key)
                if not source_widget: missing.append(source_key)
                logger.error(f"Widget(s) essentiel(s) non trouvé(s) pour calcul total avant taxes: {', '.join(missing)}")
                QMessageBox.critical(self, "Erreur Widget", f"Impossible de trouver les champs requis: {', '.join(missing)}")
                return

            # Lire la valeur source
            try:
                total_apres_taxes = source_widget.value()
            except Exception as e:
                 logger.error(f"Impossible de lire la valeur du widget source '{source_key}': {e}")
                 QMessageBox.critical(self, "Erreur Lecture", f"Impossible de lire la valeur de {source_key}.")
                 return

            # Lire et sommer les valeurs à soustraire
            subtracted_values = {}
            for key in subtract_keys:
                widget = self.form_fields.get(key)
                value = 0.0
                if widget and hasattr(widget, 'value'):
                    try:
                        value = widget.value()
                    except Exception as e:
                        logger.warning(f"Impossible de lire la valeur du widget '{key}' à soustraire: {e}")
                else:
                    # Ne pas logger si c'est TVH car il n'existe pas pour Dépense
                    if not (key == 'tvh_dep' and entry_type == "Dépense") and key != 'pourboire':
                         logger.warning(f"Widget '{key}' non trouvé ou sans .value() pour soustraction.")
                
                subtracted_values[key] = value
                total_to_subtract += value

            # Calculer la différence
            resultat = total_apres_taxes - total_to_subtract
            target_widget.setValue(resultat)
            
            log_details_sub = ", ".join([f"{k.replace(prefix, '').replace('_', ' ')}: {v:.2f}" for k, v in subtracted_values.items()])
            logger.info(f"Total avant taxes calculé ({resultat:.2f}) = {total_apres_taxes:.2f} (Après Tx) - ({log_details_sub})")

        except Exception as e:
            error_msg = f"Erreur lors du calcul du total avant taxes: {e}"
            logger.exception(error_msg)
            QMessageBox.critical(self, "Erreur Calcul Total Avant Taxes", error_msg)

# --- Fin de la classe RapportDepensePage ---

# --- Section Test (si exécuté comme script principal) --- REMOVED MOCK CLASS DUPLICATE ---

# Bloc de test simple
if __name__ == '__main__':
    import sys
    # Configuration de base du logger pour les tests, ne devrait pas interférer
    # avec le logger principal configuré dans main.py
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    test_logger = logging.getLogger(__name__)
    test_logger.info("Lancement du test de RapportDepensePage...")
    
    from PyQt5.QtWidgets import QApplication
    
    # Simuler un objet document
    class MockRapportDepense:
        def __init__(self):
            self.nom_rapport = "Rapport Test"
            self.titre = "Déjeuner Client X"
            self.montant_total = 123.45
            
    app = QApplication(sys.argv)
    mock_doc = MockRapportDepense() # Renommer pour éviter conflit avec import potentiel
    page = RapportDepensePage(document=mock_doc)
    page.setWindowTitle("Test RapportDepensePage (Simplifié)")
    page.resize(400, 300)
    page.show()
    sys.exit(app.exec_()) 