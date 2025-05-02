from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout, 
                           QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox, 
                           QPushButton, QHBoxLayout, QMessageBox,
                           QGridLayout, QFrame, QCheckBox, QRadioButton, QButtonGroup,
                           QSizePolicy, QFileDialog, QScrollArea, QSpacerItem)
from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QDoubleValidator, QIcon, QColor, QPalette, QFont, QPixmap, QIntValidator, QImage
from ui.components.frame import Frame # Correction: Chemin d'importation correct
from models.documents.rapport_depense import RapportDepense, Deplacement, Repas, Depense, Facture # Importer les modèles
from utils.theme import get_theme_vars, RADIUS_BOX # Importer les variables de thème
from utils.icon_loader import get_icon_path # Importer la fonction pour obtenir le chemin de l'icône
from utils.signals import signals
from widgets.custom_date_edit import CustomDateEdit
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
    print("Avertissement: PyMuPDF (fitz) n'est pas installé. Les miniatures PDF ne seront pas disponibles.")
# --------------------------------------------------------------------------
import os # Pour manipuler les chemins
# --- AJOUT: Import MediaViewer --- 
from windows.media_viewer import MediaViewer
# ---------------------------------
import functools # <--- AJOUT

# Supposer qu'une classe RapportDepense existe dans vos modèles
# from models.documents.rapport_depense import RapportDepense

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

        self._setup_ui()
        # self._load_data() # Pas besoin avec le QLabel simple

    def _setup_ui(self):
        # Layout vertical principal pour la page
        content_layout = QVBoxLayout(self)
        content_layout.setContentsMargins(15, 15, 15, 15) 
        content_layout.setSpacing(15)

        # --- Section Supérieure: Totaux ---
        self.totals_frame = Frame("Totaux", self)
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
        # Ajouter un séparateur avant le total général
        separator = QFrame() # Utiliser QFrame standard ici
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        totals_form_layout.addRow(separator)
        totals_form_layout.addRow("Total Général:", self.total_general_label)
        
        totals_content_layout.addStretch() # Pousser les totaux vers le haut
        # Pas de largeur fixe ici

        content_layout.addWidget(self.totals_frame) # Ajouter le frame des totaux en haut

        # --- Section Inférieure: Ajout (Gauche) + Liste (Droite) ---
        bottom_section_layout = QHBoxLayout()
        bottom_section_layout.setSpacing(15)

        # --- Frame Gauche (Section Inférieure): Ajouter une Entrée ---
        # 1. Créer le contenu de l'en-tête (Label + ComboBox)
        header_layout = QHBoxLayout()
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
                print(f"WARNING: Icon '{icon_name}' not found for ComboBox item '{text}'. Trying fallback.")
                fallback_path = get_icon_path(fallback_icon_name)
                if fallback_path:
                    icon = QIcon(fallback_path)
                else:
                     print(f"ERROR: Fallback icon '{fallback_icon_name}' also not found.")
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
        montant_section_layout.addStretch(1) # Centrer
        montant_label = QLabel("Montant:")
        montant_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.montant_display_label = QLabel("0.00 $") 
        self.montant_display_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) 
        self.montant_display_label.setStyleSheet("font-weight: bold;") 
        montant_section_layout.addWidget(montant_label)
        montant_section_layout.addSpacing(10) # Espace entre label et valeur
        montant_section_layout.addWidget(self.montant_display_label)
        montant_section_layout.addStretch(1) # Centrer
        # Ajouter cette section au layout principal du frame d'ajout
        add_entry_content_layout.addLayout(montant_section_layout) 
        # ---------------------------------------------------------

        # --- RECREATION: Boutons (tout en bas) ---
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 5, 0, 0) # Ajouter un peu d'espace au-dessus
        buttons_layout.addStretch(1) # Centrer les boutons
        self.clear_button = QPushButton("Effacer")
        self.add_button = QPushButton("Ajouter")
        self.clear_button.setObjectName("TopNavButton")
        self.add_button.setObjectName("TopNavButton")
        self.clear_button.clicked.connect(self._clear_entry_form)
        self.add_button.clicked.connect(self._add_entry)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addStretch(1) # Centrer les boutons
        # Ajouter les boutons au layout principal du frame d'ajout
        add_entry_content_layout.addLayout(buttons_layout) 
        # ----------------------------------------
        
        # --- AJOUT DU FRAME D'AJOUT À LA SECTION INFÉRIEURE (GAUCHE) ---
        bottom_section_layout.addWidget(self.add_entry_frame, 1) 

        # --- Frame Droite (Section Inférieure): Affichage des Entrées --- 
        self.entries_display_frame = Frame("Entrées existantes", self) 
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
        bottom_section_layout.addWidget(self.entries_display_frame, 4) 

        # --- AJOUT DE LA SECTION INFÉRIEURE AU LAYOUT PRINCIPAL ---
        content_layout.addLayout(bottom_section_layout)

        # --- Ajuster les stretchs verticaux du layout principal ---
        content_layout.setStretchFactor(self.totals_frame, 0) # Totaux prennent leur hauteur naturelle
        content_layout.setStretchFactor(bottom_section_layout, 1) # La section du bas prend l'espace restant

        # --- SUPPRESSION des anciennes affectations de stretch --- 
        # content_layout.setStretchFactor(self.add_entry_frame, 0)
        # content_layout.setStretchFactor(self.entries_display_frame, 1) 
        # content_layout.setStretchFactor(self.totals_frame, 0)

        # Initialiser le formulaire pour le premier type
        self._update_entry_form()

        # --- Initialiser la liste des entrées --- 
        self._populate_entries_list()
        # ---------------------------------------

    def _create_vertical_separator(self):
        """ Crée un QFrame configuré comme séparateur vertical. """
        separator = QFrame()
        separator.setObjectName("VerticalFormSeparator") # Donner un nom d'objet
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        # --- Style sera géré via QSS via objectName --- 
        # separator.setStyleSheet(...) # Supprimé
        return separator

    def _update_entry_form(self):
        """ Met à jour le formulaire dynamique (partie gauche) selon le type d'entrée. """
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
        self.dynamic_form_layout.setColumnStretch(1, 1) # La colonne des champs s'étend
        
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
        self.form_fields['date'] = CustomDateEdit(QDate.currentDate())
        date_label = QLabel("Date:")
        self.dynamic_form_layout.addWidget(date_label, current_row, 0, Qt.AlignLeft)
        self.dynamic_form_layout.addWidget(self.form_fields['date'], current_row, 1)
        current_row += 1
        
        # --- Champs spécifiques par type --- 
        entry_type = self.entry_type_combo.currentText()

        if entry_type == "Déplacement":
            self.form_fields['client'] = QLineEdit()
            client_label = QLabel("Client:")
            self.dynamic_form_layout.addWidget(client_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['client'], current_row, 1)
            current_row += 1
            
            self.form_fields['ville'] = QLineEdit()
            ville_label = QLabel("Ville:")
            self.dynamic_form_layout.addWidget(ville_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['ville'], current_row, 1)
            current_row += 1

            self.form_fields['numero_commande'] = QLineEdit()
            num_cmd_label = QLabel("N° Commande:")
            self.dynamic_form_layout.addWidget(num_cmd_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['numero_commande'], current_row, 1)
            current_row += 1

            self.form_fields['kilometrage'] = QDoubleSpinBox()
            self.form_fields['kilometrage'].setRange(0.0, 9999.9)
            self.form_fields['kilometrage'].setSuffix(" km")
            self.form_fields['kilometrage'].setAlignment(Qt.AlignRight)
            km_label = QLabel("Kilométrage:")
            self.dynamic_form_layout.addWidget(km_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['kilometrage'], current_row, 1)
            current_row += 1
            # Ajouter un stretch à la fin pour pousser les champs vers le haut
            self.dynamic_form_layout.setRowStretch(current_row, 1)

        elif entry_type == "Repas":
            self.form_fields['restaurant'] = QLineEdit()
            resto_label = QLabel("Restaurant:")
            self.dynamic_form_layout.addWidget(resto_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['restaurant'], current_row, 1)
            current_row += 1
            
            self.form_fields['client_repas'] = QLineEdit()
            client_repas_label = QLabel("Client:")
            self.dynamic_form_layout.addWidget(client_repas_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['client_repas'], current_row, 1)
            current_row += 1
            
            # --- Payeur (avec QGridLayout interne inchangé, ajouté à la colonne 1) --- 
            payeur_container = QWidget()
            payeur_grid = QGridLayout(payeur_container)
            payeur_grid.setContentsMargins(0,0,0,0)
            payeur_grid.setSpacing(10) # Espacement entre les boutons
            self.payeur_group = QButtonGroup(self.dynamic_form_widget) # Parent = le widget du formulaire
            self.form_fields['payeur_employe'] = QRadioButton("Employé")
            self.form_fields['payeur_employe'].setObjectName("FormRadioButton")
            self.form_fields['payeur_jacmar'] = QRadioButton("Jacmar")
            self.form_fields['payeur_jacmar'].setObjectName("FormRadioButton")
            self.form_fields['payeur_employe'].setChecked(True)
            self.payeur_group.addButton(self.form_fields['payeur_employe'])
            self.payeur_group.addButton(self.form_fields['payeur_jacmar'])
            payeur_grid.addWidget(self.form_fields['payeur_employe'], 0, 0)
            payeur_grid.addWidget(self.form_fields['payeur_jacmar'], 0, 1)
            payeur_grid.setColumnStretch(0, 1)
            payeur_grid.setColumnStretch(1, 1)
            # Ajouter le label et le conteneur au grid principal
            payeur_label = QLabel("Payeur:")
            self.dynamic_form_layout.addWidget(payeur_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(payeur_container, current_row, 1)
            current_row += 1
            # ----------------------------------------------------------------------

            # --- Refacturer (avec QGridLayout interne inchangé, ajouté à la colonne 1) ---
            refacturer_container = QWidget()
            refacturer_grid = QGridLayout(refacturer_container)
            refacturer_grid.setContentsMargins(0,0,0,0)
            refacturer_grid.setSpacing(10)
            self.refacturer_group = QButtonGroup(self.dynamic_form_widget) # Parent = le widget du formulaire
            self.form_fields['refacturer_non'] = QRadioButton("Non")
            self.form_fields['refacturer_non'].setObjectName("FormRadioButton")
            self.form_fields['refacturer_oui'] = QRadioButton("Oui")
            self.form_fields['refacturer_oui'].setObjectName("FormRadioButton")
            self.refacturer_group.addButton(self.form_fields['refacturer_non'])
            self.refacturer_group.addButton(self.form_fields['refacturer_oui'])
            self.form_fields['refacturer_non'].setChecked(True)
            self.form_fields['refacturer_oui'].toggled.connect(self._toggle_num_commande_row_visibility) 
            refacturer_grid.addWidget(self.form_fields['refacturer_non'], 0, 0)
            refacturer_grid.addWidget(self.form_fields['refacturer_oui'], 0, 1)
            refacturer_grid.setColumnStretch(0, 1)
            refacturer_grid.setColumnStretch(1, 1)
            # Ajouter le label et le conteneur au grid principal
            refacturer_label = QLabel("Refacturer:")
            self.dynamic_form_layout.addWidget(refacturer_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(refacturer_container, current_row, 1)
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
            total_avtx_widget = QLineEdit("0.00")
            validator_avtx = QDoubleValidator(0.0, 99999.99, 2); validator_avtx.setNotation(QDoubleValidator.StandardNotation)
            total_avtx_widget.setValidator(validator_avtx)
            total_avtx_widget.setAlignment(Qt.AlignRight)
            self.form_fields['total_avant_taxes'] = total_avtx_widget
            total_avtx_label = QLabel("Total avant Tx:")
            self.dynamic_form_layout.addWidget(total_avtx_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['total_avant_taxes'], current_row, 1)
            current_row += 1
            
            pourboire_widget = QLineEdit("0.00")
            validator_pb = QDoubleValidator(0.0, 99999.99, 2); validator_pb.setNotation(QDoubleValidator.StandardNotation)
            pourboire_widget.setValidator(validator_pb)
            pourboire_widget.setAlignment(Qt.AlignRight)
            self.form_fields['pourboire'] = pourboire_widget
            pourboire_label = QLabel("Pourboire:")
            self.dynamic_form_layout.addWidget(pourboire_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['pourboire'], current_row, 1)
            current_row += 1

            # --- Taxes (label colonne 0, champ colonne 1) ---
            tax_field_keys = ['tps', 'tvq', 'tvh']
            tax_labels = ["TPS:", "TVQ:", "TVH:"]
            for i, key in enumerate(tax_field_keys):
                widget = QLineEdit("0.00")
                validator = QDoubleValidator(0.0, 99999.99, 2); validator.setNotation(QDoubleValidator.StandardNotation)
                widget.setValidator(validator)
                widget.setAlignment(Qt.AlignRight)
                self.form_fields[key] = widget
                label_widget = QLabel(tax_labels[i])
                self.dynamic_form_layout.addWidget(label_widget, current_row, 0, Qt.AlignLeft)
                self.dynamic_form_layout.addWidget(self.form_fields[key], current_row, 1)
                current_row += 1
            # --------------------------------------------------

            # Total après taxe
            self.form_fields['total_apres_taxes'] = QLineEdit("0.00")
            validator_aptx = QDoubleValidator(0.0, 99999.99, 2); validator_aptx.setNotation(QDoubleValidator.StandardNotation)
            self.form_fields['total_apres_taxes'].setValidator(validator_aptx)
            self.form_fields['total_apres_taxes'].setAlignment(Qt.AlignRight)
            total_aptx_label = QLabel("Total après Tx:")
            self.dynamic_form_layout.addWidget(total_aptx_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['total_apres_taxes'], current_row, 1)
            current_row += 1
            # --- Le reste (connexion signal) est inchangé ---
            self.total_apres_taxes_field = self.form_fields['total_apres_taxes']
            self.total_apres_taxes_field.textChanged.connect(self._update_montant_display)

            # --- MODIFICATION: Section Facture UTILISANT le Frame Existant --- 
            self.form_fields['facture_frame'] = QFrame()
            self.form_fields['facture_frame'].setFrameShape(QFrame.StyledPanel)
            self.form_fields['facture_frame'].setFrameShadow(QFrame.Sunken)
            # Retirer le style inline, laisser QSS gérer ou définir un style cohérent ici si besoin.
            # self.form_fields['facture_frame'].setStyleSheet(f"background-color: {frame_bg_color}; border-radius: {RADIUS_BOX}; border: none;") 
            
            # Layout interne du frame
            frame_content_layout = QVBoxLayout(self.form_fields['facture_frame'])
            frame_content_layout.setContentsMargins(5, 5, 5, 5)
            frame_content_layout.setSpacing(8)
            
            # Layout horizontal pour Label + Bouton Icône
            label_button_layout = QHBoxLayout()
            label_button_layout.setContentsMargins(0,0,0,0)
            label_button_layout.setSpacing(5)

            facture_label_in_frame = QLabel("Facture(s):")
            label_button_layout.addWidget(facture_label_in_frame)
            label_button_layout.addStretch(1) # Pousse le bouton vers la droite
            
            # NOUVEAU Bouton Plus (remplace l'ancien)
            self.add_facture_button = QPushButton("+")
            self.add_facture_button.setFixedSize(30, 30)
            self.add_facture_button.setToolTip("Ajouter une facture (Image ou PDF)")
            self.add_facture_button.setObjectName("AddButtonFacture") 
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
            # --- Champs pour Dépense --- 
            # Type (ComboBox)
            self.form_fields['type_depense'] = QComboBox()
            self.form_fields['type_depense'].addItems(["Bureau", "Matériel", "Logiciel", "Voyage", "Représentation", "Autre"])
            type_label = QLabel("Type:")
            self.dynamic_form_layout.addWidget(type_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['type_depense'], current_row, 1)
            current_row += 1

            # Description
            self.form_fields['description'] = QLineEdit()
            desc_label = QLabel("Description:")
            self.dynamic_form_layout.addWidget(desc_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['description'], current_row, 1)
            current_row += 1
            
            # Fournisseur
            self.form_fields['fournisseur'] = QLineEdit()
            fourn_label = QLabel("Fournisseur:")
            self.dynamic_form_layout.addWidget(fourn_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['fournisseur'], current_row, 1)
            current_row += 1

            # Payeur (Similaire à Repas)
            payeur_container = QWidget()
            payeur_grid = QGridLayout(payeur_container)
            payeur_grid.setContentsMargins(0,0,0,0)
            payeur_grid.setSpacing(10)
            # Utiliser un nouveau ButtonGroup si self.payeur_group est déjà utilisé par Repas
            self.depense_payeur_group = QButtonGroup(self.dynamic_form_widget) 
            self.form_fields['payeur_employe_dep'] = QRadioButton("Employé")
            self.form_fields['payeur_employe_dep'].setObjectName("FormRadioButton")
            self.form_fields['payeur_jacmar_dep'] = QRadioButton("Jacmar")
            self.form_fields['payeur_jacmar_dep'].setObjectName("FormRadioButton")
            self.form_fields['payeur_employe_dep'].setChecked(True)
            self.depense_payeur_group.addButton(self.form_fields['payeur_employe_dep'])
            self.depense_payeur_group.addButton(self.form_fields['payeur_jacmar_dep'])
            payeur_grid.addWidget(self.form_fields['payeur_employe_dep'], 0, 0)
            payeur_grid.addWidget(self.form_fields['payeur_jacmar_dep'], 0, 1)
            payeur_grid.setColumnStretch(0, 1)
            payeur_grid.setColumnStretch(1, 1)
            payeur_label = QLabel("Payeur:")
            self.dynamic_form_layout.addWidget(payeur_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(payeur_container, current_row, 1)
            current_row += 1

            # Total avant Tx
            total_avtx_widget = QLineEdit("0.00")
            validator_avtx = QDoubleValidator(0.0, 99999.99, 2); validator_avtx.setNotation(QDoubleValidator.StandardNotation)
            total_avtx_widget.setValidator(validator_avtx)
            total_avtx_widget.setAlignment(Qt.AlignRight)
            self.form_fields['total_avant_taxes_dep'] = total_avtx_widget
            total_avtx_label = QLabel("Total avant Tx:")
            self.dynamic_form_layout.addWidget(total_avtx_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['total_avant_taxes_dep'], current_row, 1)
            current_row += 1

            # Taxes (Similaire à Repas, avec _dep suffix)
            tax_field_keys = ['tps_dep', 'tvq_dep', 'tvh_dep']
            tax_labels = ["TPS:", "TVQ:", "TVH:"]
            for i, key in enumerate(tax_field_keys):
                widget = QLineEdit("0.00")
                validator = QDoubleValidator(0.0, 99999.99, 2); validator.setNotation(QDoubleValidator.StandardNotation)
                widget.setValidator(validator)
                widget.setAlignment(Qt.AlignRight)
                self.form_fields[key] = widget
                label_widget = QLabel(tax_labels[i])
                self.dynamic_form_layout.addWidget(label_widget, current_row, 0, Qt.AlignLeft)
                self.dynamic_form_layout.addWidget(self.form_fields[key], current_row, 1)
                current_row += 1

            # Total après taxe
            self.form_fields['total_apres_taxes_dep'] = QLineEdit("0.00")
            validator_aptx = QDoubleValidator(0.0, 99999.99, 2); validator_aptx.setNotation(QDoubleValidator.StandardNotation)
            self.form_fields['total_apres_taxes_dep'].setValidator(validator_aptx)
            self.form_fields['total_apres_taxes_dep'].setAlignment(Qt.AlignRight)
            total_aptx_label = QLabel("Total après Tx:")
            self.dynamic_form_layout.addWidget(total_aptx_label, current_row, 0, Qt.AlignLeft)
            self.dynamic_form_layout.addWidget(self.form_fields['total_apres_taxes_dep'], current_row, 1)
            current_row += 1

            # Lier Total après Tx au display montant
            self.total_apres_taxes_field = self.form_fields['total_apres_taxes_dep'] 
            self.total_apres_taxes_field.textChanged.connect(self._update_montant_display)

        # --- Réinitialiser la liste des miniatures --- 
        self.current_facture_thumbnails = {}
        # self.current_facture_paths = [] # <-- SUPPRESSION
        # -------------------------------------------

        # Ajouter un espace vertical avant le montant total
        self.dynamic_form_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding), current_row, 0, 1, 2)
        current_row += 1
        
        # ... (reste _update_entry_form: montant, politique taille) ...
        
    def _update_montant_display(self, value):
        """ Met à jour le label montant dans la colonne de droite. """
        if hasattr(self, 'montant_display_label') and self.montant_display_label:
            # --- Lire depuis le QLineEdit et convertir --- 
            try:
                # Remplacer la virgule par un point si nécessaire pour float()
                numeric_value = float(str(value).replace(',', '.'))
                self.montant_display_label.setText(f"{numeric_value:.2f} $")
            except ValueError:
                # Si la valeur n'est pas un nombre valide (ex: vide ou '-'), afficher 0.00
                self.montant_display_label.setText("0.00 $")
            # -------------------------------------------

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
        # self.current_facture_paths = [] # <-- SUPPRESSION

    def _add_entry(self):
        """ Ajoute l'entrée en lisant les champs du formulaire. """
        entry_type = self.entry_type_combo.currentText()
        
        try:
            # Récupérer les valeurs communes (Date et Description)
            date_val = self.form_fields['date'].date().toPyDate()

            new_entry = None
            if entry_type == "Déplacement":
                 client_val = self.form_fields['client'].text()
                 ville_val = self.form_fields['ville'].text()
                 num_commande_val = self.form_fields['numero_commande'].text()
                 kilometrage_val = self.form_fields['kilometrage'].value()
                 # --- Calcul du montant pour Déplacement --- 
                 TAUX_KM = 0.50 # Exemple de taux - À METTRE DANS CONFIG
                 montant_deplacement = kilometrage_val * TAUX_KM
                 self._update_montant_display(montant_deplacement) # Met à jour l'affichage
                 # -----------------------------------------
                 new_entry = Deplacement(date_deplacement=date_val, 
                                         client=client_val, ville=ville_val, 
                                         numero_commande=num_commande_val,
                                         kilometrage=kilometrage_val, 
                                         montant=montant_deplacement)
                 self.document.ajouter_deplacement(new_entry)
                 print(f"Déplacement ajouté: {new_entry}")

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
                 def get_float_from_field(key):
                     try:
                         # Remplacer la virgule par un point si nécessaire
                         return float(self.form_fields[key].text().replace(',', '.'))
                     except (KeyError, ValueError):
                         # Si clé non trouvée ou conversion impossible, retourner 0.0
                         return 0.0
                 
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
                              print(f"[TEMP] Objet Facture créé: {facture_obj}")
                         except (TypeError, ValueError) as fact_err:
                              QMessageBox.warning(self, "Erreur Facture", f"Impossible de créer l'objet Facture:\n{fact_err}")
                              # Continuer sans facture en cas d'erreur
                              facture_obj = None 
                 # -------------------------------------------
                 
                 # Validation spécifique Repas
                 if not restaurant_val:
                     QMessageBox.warning(self, "Champ manquant", "Le nom du restaurant est requis.")
                     return
                 if total_apres_taxes_val <= 0:
                      QMessageBox.warning(self, "Montant invalide", "Le total après taxes doit être positif.")
                      return
                 
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
                 print(f"Ajout Repas: {new_entry}") # Garder pour info
                 
            elif entry_type == "Dépense":
                 # --- Lire les valeurs du formulaire Dépense --- 
                 type_val = self.form_fields['type_depense'].currentText()
                 description_val = self.form_fields['description'].text()
                 fournisseur_val = self.form_fields['fournisseur'].text()
                 payeur_val = self.form_fields['payeur_employe_dep'].isChecked() # True si Employé
                 
                 # Utiliser le helper pour les montants
                 def get_float_from_field(key):
                     try:
                         return float(self.form_fields[key].text().replace(',', '.'))
                     except (KeyError, ValueError):
                         return 0.0

                 total_avant_taxes_val = get_float_from_field('total_avant_taxes_dep')
                 tps_val = get_float_from_field('tps_dep')
                 tvq_val = get_float_from_field('tvq_dep')
                 tvh_val = get_float_from_field('tvh_dep')
                 total_apres_taxes_val = get_float_from_field('total_apres_taxes_dep')
                 
                 # Validation (exemple simple)
                 if not description_val:
                     QMessageBox.warning(self, "Champ manquant", "La description est requise.")
                     return
                 if total_apres_taxes_val <= 0:
                     QMessageBox.warning(self, "Montant invalide", "Le total après taxes doit être positif.")
                 return

                 # --- Créer l'objet Depense (Adapter selon le modèle réel) --- 
                 # Supposons que le constructeur de Depense ressemble à ça:
                 new_entry = Depense(
                     date_depense=date_val, 
                     type_depense=type_val, 
                     description=description_val, 
                     fournisseur=fournisseur_val, 
                     payeur=payeur_val, # Passer le booléen directement (True=Employé)
                     totale_avant_taxes=total_avant_taxes_val,
                     tps=tps_val, 
                     tvq=tvq_val, 
                     tvh=tvh_val,
                     totale_apres_taxes=total_apres_taxes_val,
                     facture=None # Ajouter si nécessaire
                 )
                 # -----------------------------------------------------------
                 
                 # QMessageBox.warning(self, "Type non géré", "L'ajout de 'Dépense simple' nécessite un champ Montant.")
                 # return
                 # montant_val = float(self.montant_display_label.text().replace(' $','')) # Risqué
                 # new_entry = Depense(date=date_val, description=description_val, montant=montant_val)
                 # self.document.entries.append(new_entry)
                 self.document.ajouter_depense(new_entry) # Utiliser la méthode dédiée
                 print(f"Ajout Dépense: {new_entry}") # Garder pour info

            if new_entry: # Si une entrée a été créée
                print(f"Entrée ajoutée: {new_entry}") # Répétitif
                self._clear_entry_form() 
                # --- MODIFICATION: Ne plus repeupler toute la liste ---
                # self._populate_entries_list() # Mettre à jour la liste des cartes
                self._add_card_widget(new_entry) # Ajouter seulement la nouvelle carte
                # ------------------------------------------------------
                self._update_totals_display() # TODO: Mettre à jour les totaux
                QMessageBox.information(self, "Succès", f"{entry_type} ajouté avec succès.")

        except KeyError as e:
             # Gérer le cas où un champ attendu n'existe pas dans self.form_fields
             QMessageBox.critical(self, "Erreur Interne", f"Erreur de clé de formulaire: {e}. Le formulaire pour '{entry_type}' est peut-être incomplet.")
        except Exception as e:
             # --- Message d'erreur générique --- 
             QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter l'entrée: {e}")
             traceback.print_exc() # Afficher la trace complète dans la console pour débogage
             # ----------------------------------

    # --- Méthode pour mettre à jour l'affichage des totaux (à implémenter) ---
    def _update_totals_display(self):
         # TODO: Lire self.document.get_totals() ou équivalent et mettre à jour les labels
         pass 

    # --- Méthode pour mettre à jour l'affichage des entrées (à implémenter) ---
    # def _update_entries_display(self):
    #     pass 

    # --- ADAPTATION pour QGridLayout --- 
    def _toggle_num_commande_row_visibility(self, checked):
        """ Affiche ou cache la ligne (label + champ) N° Commande dans le QGridLayout. """
        print(f"_toggle_num_commande_row_visibility appelé avec checked={checked}") # DEBUG
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
                
                print(f"  Label et Field N° Commande setVisible({checked}) effectué pour la ligne {self.num_commande_row_index}.") # DEBUG
            except Exception as e:
                 print(f"  Erreur lors de la modification de visibilité de la ligne N° Commande ({self.num_commande_row_index}): {e}") # DEBUG
        else:
            print("  Erreur: Widgets N° Commande, index de ligne, ou layout non trouvés.") # DEBUG

    def _populate_entries_list(self):
        # Vider le layout existant
        while self.entries_list_layout.count():
            child = self.entries_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Trier les entrées par date (ou autre critère si besoin)
        try:
            # Combiner toutes les listes d'entrées
            all_entries = self.document.deplacements + self.document.repas + self.document.depenses_diverses

            # Clé de tri robuste (gère les différents noms d'attributs de date)
            def get_sort_key(entry):
                if hasattr(entry, 'date_repas'): return entry.date_repas
                if hasattr(entry, 'date_deplacement'): return entry.date_deplacement
                if hasattr(entry, 'date_depense'): return entry.date_depense
                if hasattr(entry, 'date'): return entry.date # Fallback générique
                return QDate(1900, 1, 1) # Date très ancienne si aucune date trouvée

            # Trier la liste combinée
            sorted_entries = sorted(all_entries, key=get_sort_key, reverse=True)
        except Exception as e:
             print(f"Erreur de tri des entrées: {e}. Affichage non trié.")
             # Fallback: utiliser la liste combinée non triée
             sorted_entries = self.document.deplacements + self.document.repas + self.document.depenses_diverses

        for entry in sorted_entries:
            # Déterminer UNIQUEMENT le type string pour le constructeur de CardWidget
            entry_type_str = "Inconnu" # Type par défaut
            if isinstance(entry, Repas):
                entry_type_str = "Repas"
            elif isinstance(entry, Deplacement):
                entry_type_str = "Déplacement"
            elif isinstance(entry, Depense):
                entry_type_str = "Dépense"

            # CORRECTION: Instancier CardWidget avec les bons arguments
            card = CardWidget(
                entry_data=entry,          # Passer l'objet de données complet
                entry_type=entry_type_str, # Passer juste le type string
                parent=self
            )
            # Connecter le signal du CardWidget (qui gère maintenant ses propres détails)
            # au slot de cette page qui ouvre le viewer.
            card.thumbnail_clicked.connect(self._open_media_viewer)

            self.entries_list_layout.addWidget(card)

        # Ajouter un espace extensible pour pousser les cartes vers le haut
        self.entries_list_layout.addStretch(1)

    def _add_card_widget(self, new_entry):
        """Crée et insère une CardWidget pour une nouvelle entrée au début de la liste."""
        entry_type_str = "Inconnu" 
        if isinstance(new_entry, Repas):
            entry_type_str = "Repas"
        elif isinstance(new_entry, Deplacement):
            entry_type_str = "Déplacement"
        elif isinstance(new_entry, Depense):
            entry_type_str = "Dépense"

        card = CardWidget(
            entry_data=new_entry,
            entry_type=entry_type_str,
            parent=self
        )
        card.thumbnail_clicked.connect(self._open_media_viewer)

        # Insérer la nouvelle carte au début (index 0)
        self.entries_list_layout.insertWidget(0, card)

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
            print(f"Erreur génération miniature pour {file_path}: {e}")
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
                     print(f"[TEMP] Facture ajoutée UI: {file_path}")

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
                     print(f"Erreur: Impossible de charger l'image {file_path}")
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
                          print(f"Erreur: PDF vide {file_path}")
                          # Créer un pixmap placeholder gris?
                          pixmap = QPixmap(ThumbnailWidget.THUMBNAIL_SIZE, ThumbnailWidget.THUMBNAIL_SIZE)
                          pixmap.fill(Qt.darkGray)
                     doc.close()
                 except Exception as pdf_error:
                      print(f"Erreur PyMuPDF pour {file_path}: {pdf_error}")
                      QMessageBox.warning(self, "Erreur PDF", f"Impossible de générer la miniature pour {file_path}.\n{pdf_error}")
                      # Créer un pixmap placeholder rouge?
                      pixmap = QPixmap(ThumbnailWidget.THUMBNAIL_SIZE, ThumbnailWidget.THUMBNAIL_SIZE)
                      pixmap.fill(Qt.red)
            # --- Format non supporté --- 
            else:
                 print(f"Format non supporté: {file_path}")
                 # Créer un pixmap placeholder?
                 pixmap = QPixmap(ThumbnailWidget.THUMBNAIL_SIZE, ThumbnailWidget.THUMBNAIL_SIZE)
                 pixmap.fill(Qt.lightGray)

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
            print(f"Erreur inattendue création miniature pour {file_path}: {e}")
            traceback.print_exc()

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
             print(f"Avertissement: Tentative suppression miniature non trouvée: {file_path}")
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
                 print(f"WARN: Fichier cliqué {clicked_file_path} était dans all_files mais pas trouvé dans valid_files après vérification existance. Bizarre. Ouverture index 0.")
                 # Garde valid_initial_index à 0
        else:
             # Si le fichier cliqué n'existe pas/plus, on prend le premier valide (index 0)
              if valid_files: # Assure qu'il y a au moins un fichier valide
                  print(f"WARN: Fichier cliqué {clicked_file_path} non trouvé ou invalide, ouverture du premier fichier valide ({valid_files[0]}).")
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
            print(f"Erreur inattendue ouverture MediaViewer: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur est survenue lors de l'ouverture du visualiseur: {e}")
    # --- FIN MODIFICATION ---

    # --- NOUVEAU Slot pour gérer clic depuis FORMULAIRE --- 
    def _open_media_viewer_from_form(self, clicked_file_path: str):
        """Prépare les arguments et appelle _open_media_viewer pour un clic venant du formulaire."""
        all_paths = list(self.current_facture_thumbnails.keys())
        if not all_paths:
            print("WARN: _open_media_viewer_from_form appelé mais self.current_facture_thumbnails est vide.")
            return

        try:
            clicked_index = all_paths.index(clicked_file_path)
            # Appeler la méthode principale avec la liste complète et l'index trouvé
            self._open_media_viewer(all_files=all_paths, initial_index=clicked_index)
        except ValueError:
            print(f"ERROR: Chemin cliqué '{clicked_file_path}' non trouvé dans self.current_facture_thumbnails.keys().")
            QMessageBox.critical(self, "Erreur Interne", f"Le fichier cliqué ({os.path.basename(clicked_file_path)}) ne correspond à aucune miniature actuellement affichée.")
        except Exception as e:
            print(f"Erreur inattendue dans _open_media_viewer_from_form: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur interne est survenue avant d'ouvrir le visualiseur: {e}")
    # ------------------------------------------------------

# Bloc de test simple
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Simuler un objet document
    class MockRapportDepense:
        def __init__(self):
            self.nom_rapport = "Rapport Test"
            self.titre = "Déjeuner Client X"
            self.montant_total = 123.45
            
    app = QApplication(sys.argv)
    doc = MockRapportDepense()
    page = RapportDepensePage(document=doc)
    page.setWindowTitle("Test RapportDepensePage (Simplifié)")
    page.resize(400, 300)
    page.show()
    sys.exit(app.exec_()) 