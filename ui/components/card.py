from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QFormLayout, QGridLayout,
                             QMenu, QAction, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSlot as Slot, QSize, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon, QPainter, QColor, QFont
from datetime import date
from utils.icon_loader import get_icon_path # Assumer que utils est accessible depuis widgets
from utils.theme import get_theme_vars, RADIUS_BOX 
import os
import functools
from models.documents.rapport_depense.facture import Facture # Assumer l'import
from PyQt5.QtGui import QPixmap, QImage # Pour _generate_thumbnail_pixmap
# --- AJOUT: Importer RoundedImageWidget --- 
from widgets.thumbnail_widget import ThumbnailWidget
# ------------------------------------------
import logging # Ajout pour le logger

# Initialisation du logger
logger = logging.getLogger('GDJ_App')

# --- AJOUT: Tentative d'import de fitz et définition de PYMUPDF_AVAILABLE --- 
try:
    import fitz # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None # Définir fitz à None si l'import échoue
    PYMUPDF_AVAILABLE = False
    # Pas de print ici, pourrait être appelé souvent
# --------------------------------------------------------------------------

# --- Widget Card (Reconstruit, héritant de QFrame) --- 
class CardWidget(QFrame):
    # --- AJOUT: Signal pour clic miniature --- 
    thumbnail_clicked = pyqtSignal(list, int)
    # --- AJOUT: Signaux pour les options du menu --- 
    edit_requested = pyqtSignal()
    duplicate_requested = pyqtSignal()
    copy_requested = pyqtSignal() # Le sens de "copier" reste à définir
    delete_requested = pyqtSignal()
    # -------------------------------------------

    def __init__(self, entry_data, entry_type, parent=None):
        super().__init__(parent)
        # Donner un nom d'objet pour le ciblage QSS global ou interne
        self.setObjectName("CardWidget") 
        self.entry_data = entry_data
        self.entry_type = entry_type
        self.options_menu = None # Pour création paresseuse du menu
        self.payeur_label = QLabel("") # AJOUT: Label pour le payeur

        # --- AJOUT: Indicateur de facture (Label avec icône visible/transparente) ---
        self.facture_icon_label = QLabel() 
        self.facture_icon_label.setObjectName("FactureIndicatorLabel")
        self.facture_icon_label.setFixedSize(18, 18) # Taille fixe
        # self.facture_icon_label.setVisible(False) # SUPPRIMÉ: Toujours visible
        self.facture_icon_label.setStyleSheet("background-color: transparent; border: none;") 
        # Tooltip sera défini dynamiquement dans _setup_ui

        # --- Initialisation des pixmaps (seront créés dans _setup_ui) ---
        self.pixmap_facture_visible = None
        self.pixmap_facture_invisible = None 
        # --- FIN AJOUT Indicateur ---

        # --- Obtenir les variables de thème POUR le style inline --- 
        theme = get_theme_vars()
        card_bg_color = theme.get("COLOR_PRIMARY_LIGHTEST", "#5a5d5e") # Nouveau: plus clair
        hover_bg_color = theme.get("COLOR_PRIMARY_MEDIUM", "#5a5d5f") # Couleur pour le survol
        # --------------------------------------------------------

        self._setup_ui()

        # --- RETIRÉ: setAutoFillBackground(True) - Inutile pour QFrame ---
        # self.setAutoFillBackground(True) 
        # --------------------------------------------------

        # --- Appliquer le style CORRECT ciblant l'ID --- 
        self.setStyleSheet(f"""
            #CardWidget {{
                background-color: {card_bg_color};
                border-radius: {RADIUS_BOX};
                border: none;
                margin: 0 5px; /* AJOUT: Marge gauche/droite uniquement */
            }}
            /* Styles pour les enfants (bouton, labels) sont gérés inline dans _setup_ui 
               ou par des règles plus globales si nécessaire, 
               mais le fond/bordure de la carte elle-même est défini ici. */
        """)
        # ----------------------------------------------------

    def _setup_ui(self):
        # Layout principal vertical pour la carte (Summary + Details)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # Aucune marge externe pour le contenu
        main_layout.setSpacing(0) # Aucun espacement entre summary et details

        # 1. Widget de résumé (toujours visible)
        summary_widget = QWidget()
        summary_layout = QHBoxLayout(summary_widget)
        summary_layout.setContentsMargins(5, 5, 5, 5) # Marge interne pour le résumé
        summary_layout.setSpacing(10) # Espacement dans le résumé

        # --- AJOUT: Icône de type d'entrée ---
        icon_label = QLabel()
        icon_label.setFixedSize(20, 20) # Taille de l'icône (ajustable)
        entry_type_icon_name = ""
        if self.entry_type == "Déplacement":
            entry_type_icon_name = "round_directions_car.png"
        elif self.entry_type == "Repas":
            entry_type_icon_name = "round_restaurant.png"
        elif self.entry_type == "Dépense": # Assumer que le type est "Dépense" pour le 3ème cas
            entry_type_icon_name = "round_payments.png"
        else:
            entry_type_icon_name = "round_receipt_long.png" # Icône par défaut/fallback

        if entry_type_icon_name:
            icon_path = get_icon_path(entry_type_icon_name)
            if icon_path:
                pixmap = QIcon(icon_path).pixmap(QSize(18, 18)) # Créer QPixmap depuis QIcon pour scaling facile
                icon_label.setPixmap(pixmap)
                icon_label.setStyleSheet("background-color: transparent; border: none;")
                summary_layout.addWidget(icon_label) # Ajouter l'icône au début
                # summary_layout.addSpacing(5) # Ajouter un petit espace après l'icône (Optionnel)
            else:
                logger.warning(f"CardWidget - Icône de type '{entry_type_icon_name}' non trouvée.")
                # Optionnel: Ajouter un placeholder texte si icône non trouvée
                # icon_label.setText("?") 
                # summary_layout.addWidget(icon_label) # Ajouter même si vide/placeholder?
        # --- Fin Ajout Icône ---

        # Infos Clés pour le résumé
        date_str = "Date Inconnue"
        amount_str = "Montant Inconnu"
        # Essayer d'obtenir date et montant de manière robuste
        date_val = getattr(self.entry_data, 'date', getattr(self.entry_data, 'date_repas', getattr(self.entry_data, 'date_deplacement', getattr(self.entry_data, 'date_depense', None))))
        amount_val = getattr(self.entry_data, 'total', getattr(self.entry_data, 'totale_apres_taxes', getattr(self.entry_data, 'montant', None)))

        if date_val:
            try:
                date_str = date_val.strftime("%Y-%m-%d")
            except AttributeError:
                 date_str = str(date_val)
        if amount_val is not None:
            try:
                amount_str = f"{float(amount_val):.2f} $"
            except (ValueError, TypeError):
                amount_str = str(amount_val)

        # --- Résumé personnalisé selon le type ---
        summary_columns = []
        payeur_text = "" # Vide par défaut (pour Déplacement)
        if self.entry_type == "Repas" or self.entry_type == "Dépense":
            # Lire l'attribut 'payeur' (True=Employé, False=Jacmar), fallback à Employé
            is_employe = getattr(self.entry_data, 'payeur', True)
            payeur_text = "Employé" if is_employe else "Jacmar"
            # Mettre à jour le label directement ici (sera ajouté au layout plus bas)
            # self.payeur_label.setText(payeur_text) # Non, on l'ajoute à summary_columns

        if self.entry_type == "Déplacement":
            client = getattr(self.entry_data, 'client', "?")
            kilometrage = getattr(self.entry_data, 'kilometrage', None)
            try:
                km_str = f"{float(kilometrage):.1f} km" if kilometrage is not None else "? km"
            except (ValueError, TypeError):
                km_str = f"{kilometrage} km"
            # AJOUT: Colonne "Employé" directement dans le résumé
            summary_columns = [date_str, client, km_str, "Employé", amount_str]
        elif self.entry_type == "Repas":
            client = getattr(self.entry_data, 'client', "?")
            restaurant = getattr(self.entry_data, 'restaurant', "?")
            summary_columns = [date_str, client, restaurant, payeur_text, amount_str] # AJOUT payeur_text
        elif self.entry_type == "Dépense":
            fournisseur = getattr(self.entry_data, 'fournisseur', "?")
            description = getattr(self.entry_data, 'description', "?")
            summary_columns = [date_str, fournisseur, description, payeur_text, amount_str] # AJOUT payeur_text
        else:
            summary_columns = [date_str, self.entry_type, amount_str]

        # --- Affichage en colonnes de largeur égale ---
        summary_layout_columns = QHBoxLayout()
        summary_layout_columns.setContentsMargins(0, 0, 0, 0)
        summary_layout_columns.setSpacing(10)
        col_count = len(summary_columns)
        col_width = 180  # Largeur fixe par colonne (plus large)
        for col_text in summary_columns:
            col_label = QLabel(str(col_text))
            col_label.setStyleSheet("font-weight: bold; background-color: transparent; border: none;")
            col_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            col_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Expansion horizontale
            summary_layout_columns.addWidget(col_label)
        # --- Fin affichage en colonnes ---

        # Remplacer l'ancien info_label par le layout de colonnes
        # summary_layout.addWidget(info_label)
        summary_layout.addLayout(summary_layout_columns)

        # --- Obtenir les variables de thème POUR le style inline des boutons --- 
        theme = get_theme_vars()
        hover_bg_color = theme.get("COLOR_PRIMARY_MEDIUM", "#5a5d5f") # Couleur pour le survol
        # --- SUPPRESSION: Style pour le cadre rouge ---
        # facture_indicator_bg_color = theme.get("COLOR_ERROR", "#E53935")
        # facture_indicator_radius = "3px" 
        # self.facture_indicator_frame.setStyleSheet(...) 
        # --- FIN SUPPRESSION ---
        # --------------------------------------------------------------------

        # --- AJOUT: Bouton Options --- 
        self.options_button = QPushButton()
        options_icon_path = get_icon_path("round_more_vert.png")
        if options_icon_path:
            self.options_button.setIcon(QIcon(options_icon_path))
        self.options_button.setFixedSize(24, 24) # Taille similaire à l'autre bouton
        self.options_button.setObjectName("CardOptionsButton") # Nom pour QSS
        self.options_button.setToolTip("Options")
        # Appliquer un style similaire au bouton expand
        self.options_button.setStyleSheet(f"""
            QPushButton#CardOptionsButton {{
                background-color: transparent;
                border: none;
                border-radius: 3px;
            }}
            QPushButton#CardOptionsButton:hover {{
                background-color: {hover_bg_color};
            }}
            QPushButton#CardOptionsButton:pressed {{
                background-color: {theme.get("COLOR_PRIMARY_DARK", "#3a3d3f")}; /* Couleur légèrement plus foncée au clic */
            }}
        """)
        self.options_button.clicked.connect(self._show_options_menu)
        # --- Fin Ajout Bouton Options ---

        # Bouton pour déplier/replier
        self.expand_button = QPushButton()
        # --- Utiliser l'icône initiale correcte (état replié) ---
        # icon_path_right = get_icon_path("arrow_right.png")
        icon_path_initial = get_icon_path("round_arrow_drop_down.png") # Icône pour état replié initial
        if icon_path_initial:
             self.expand_button.setIcon(QIcon(icon_path_initial))
        # -----------------------------------------------------
        self.expand_button.setFixedSize(24, 24)
        self.expand_button.setCheckable(True) 
        # self.expand_button.setObjectName("TopNavButton") # Utiliser le même nom que les autres boutons <-- Revert
        self.expand_button.setObjectName("CardExpandButton") # Revenir au nom spécifique
        # --- Appliquer le style avec :hover directement ---
        self.expand_button.setStyleSheet(f"""
            QPushButton#CardExpandButton {{
                background-color: transparent;
                border: none;
            }}
            QPushButton#CardExpandButton:hover {{
                background-color: {hover_bg_color};
                border-radius: 3px; /* Effet visuel subtil */
            }}
            QPushButton#CardExpandButton:checked {{
                background-color: transparent; /* Ou hover_bg_color si on veut le garder en surbrillance */
                border: none; /* Empêcher la bordure d'apparaître au clic */
                outline: none; /* Empêcher le rectangle de focus d'apparaître */
            }}
            QPushButton#CardExpandButton:checked:hover {{ /* AJOUT: Gérer le survol quand coché */
                background-color: {hover_bg_color}; /* Appliquer la couleur de survol */
                border: none;                       /* Conserver sans bordure */
                outline: none;                      /* Conserver sans outline */
            }}
            QPushButton#CardExpandButton:focus {{
                border: none;
                outline: none;
            }}
        """)
        # ---------------------------------------------------
        self.expand_button.toggled.connect(self._toggle_details)

        # --- CRÉATION DES PIXMAPS ICI --- 
        icon_size = QSize(16, 16) # Taille de l'icône pour le pixmap
        
        # Pixmap visible (icône rouge ou fallback)
        icon_path = get_icon_path("round_receipt_red.png")
        if icon_path:
            try:
                self.pixmap_facture_visible = QIcon(icon_path).pixmap(icon_size)
                if self.pixmap_facture_visible.isNull():
                     raise ValueError("Pixmap créé depuis icône est null") # Forcer fallback si icône invalide
            except Exception as e_icon:
                 logger.warning(f"CardWidget: Erreur chargement icône {icon_path}, utilisation fallback: {e_icon}")
                 self.pixmap_facture_visible = None # Assurer qu'on passe au fallback
        else:
            logger.warning(f"CardWidget: Icône round_receipt_red.png non trouvée, utilisation fallback.")
            self.pixmap_facture_visible = None # Pas d'icône trouvée

        # Fallback si pixmap visible est None (icône non trouvée ou invalide)
        if self.pixmap_facture_visible is None:
            self.pixmap_facture_visible = QPixmap(icon_size) 
            self.pixmap_facture_visible.fill(Qt.transparent)
            try:
                painter = QPainter(self.pixmap_facture_visible)
                painter.setPen(QColor("red"))
                painter.setFont(QFont("Arial", 10, QFont.Bold))
                painter.drawText(self.pixmap_facture_visible.rect(), Qt.AlignCenter, "F")
                painter.end()
                logger.debug("CardWidget: Pixmap fallback 'F' créé.")
            except Exception as e_painter:
                 logger.error(f"CardWidget: Erreur création pixmap fallback avec QPainter: {e_painter}")
                 # En dernier recours, créer un pixmap rouge uni simple
                 self.pixmap_facture_visible = QPixmap(icon_size)
                 self.pixmap_facture_visible.fill(QColor("red"))

        # Pixmap invisible (toujours transparent)
        self.pixmap_facture_invisible = QPixmap(icon_size)
        self.pixmap_facture_invisible.fill(Qt.transparent)
        # --- FIN CRÉATION PIXMAPS ---

        # --- LOGGING VÉRIFICATION FINALE --- 
        logger.debug(f"CardWidget {self.entry_type} - FINAL Pixmap visible: {self.pixmap_facture_visible}, isNull: {self.pixmap_facture_visible.isNull()}")
        logger.debug(f"CardWidget {self.entry_type} - FINAL Pixmap invisible: {self.pixmap_facture_invisible}, isNull: {self.pixmap_facture_invisible.isNull()}")
        # --- FIN LOGGING ---

        # --- Logique pour choisir le pixmap et tooltip ---
        # Par défaut: placeholder invisible, pas de tooltip spécifique
        pixmap_to_set = self.pixmap_facture_invisible 
        tooltip_text = "" # Pas de tooltip pour Déplacement ou si facture présente

        if self.entry_type in ["Repas", "Dépense"]:
            # Vérifier la facture uniquement pour Repas/Dépense
            facture_obj = getattr(self.entry_data, 'facture', None)
            has_facture = False
            if facture_obj and isinstance(facture_obj, Facture):
                if facture_obj.get_full_paths():
                    has_facture = True
            
            if not has_facture:
                # Repas/Dépense SANS facture: Afficher icône rouge
                pixmap_to_set = self.pixmap_facture_visible
                tooltip_text = "Aucune facture présente"
            else:
                # Repas/Dépense AVEC facture: Garder pixmap invisible (déjà par défaut)
                tooltip_text = "Facture présente" # Mettre le tooltip ici

        # Appliquer le pixmap et le tooltip décidés
        logger.debug(f"CardWidget {self.entry_type} - Setting indicator pixmap: {'Visible (Red)' if pixmap_to_set == self.pixmap_facture_visible else 'Invisible (Placeholder)'}")
        self.facture_icon_label.setPixmap(pixmap_to_set)
        self.facture_icon_label.setToolTip(tooltip_text)
        # --- FIN Logique Indicateur ---

        # --- MODIFICATION: Insérer le QLabel avant le bouton options ---
        summary_layout.addWidget(self.facture_icon_label) # Ajouter le QLabel directement
        # --- FIN MODIFICATION ---
        summary_layout.addWidget(self.options_button)        # Bouton options à droite
        summary_layout.addWidget(self.expand_button)           # Bouton expand/collapse
        
        # Assurer que le widget de résumé est transparent
        summary_widget.setStyleSheet("background-color: transparent; border: none;")

        # 2. Widget de détails (initialement caché)
        self.details_widget = QWidget()
        # --- MODIFICATION: Choisir le layout en fonction du type ---
        if self.entry_type == "Repas":
            # --- NOUVEAU: Utiliser QGridLayout pour les Repas ---
            details_layout = QGridLayout(self.details_widget)
            details_layout.setContentsMargins(10, 5, 10, 10)
            details_layout.setVerticalSpacing(5) # Espacement vertical
            details_layout.setHorizontalSpacing(15) # Espacement horizontal
            # Définir les largeurs relatives des colonnes (Labels plus petits, Valeurs plus grandes, Factures moyennes)
            details_layout.setColumnStretch(0, 1) # Col 1 (Label 1-6)
            details_layout.setColumnStretch(1, 2) # Col 2 (Value 1-6)
            details_layout.setColumnStretch(2, 1) # Col 3 (Label 7-12)
            details_layout.setColumnStretch(3, 2) # Col 4 (Value 7-12)
            details_layout.setColumnStretch(4, 2) # Col 5 (Factures)

            # --- AJOUT: Séparateur horizontal ---
            details_separator = QFrame()
            details_separator.setFrameShape(QFrame.HLine)
            details_separator.setFrameShadow(QFrame.Sunken)
            details_separator.setMinimumHeight(1)
            separator_color = get_theme_vars().get("COLOR_TEXT_SECONDARY", "#888888")
            details_separator.setStyleSheet(f"border: none; border-top: 1px solid {separator_color}; background-color: transparent;")
            # Ajouter le séparateur sur toute la largeur en haut (ligne 0, col 0, span 1 ligne, 5 colonnes)
            details_layout.addWidget(details_separator, 0, 0, 1, 5)
            # --- Fin Séparateur ---

            # --- CORRECTION: Utiliser des listes d'attributs spécifiques pour Repas ---
            attrs_col1 = [
                ('date', 'Date'),
                ('restaurant', 'Restaurant'),
                ('client', 'Client'),
                ('payeur', 'Payeur'), # Label simplifié
                ('refacturer', 'Refacturer'), # Label simplifié
                ('numero_commande', 'Numéro Commande')
            ]
            attrs_col3 = [
                ('totale_avant_taxes', 'Total avant taxes'),
                ('pourboire', 'Pourboire'),
                ('tps', 'TPS'),
                ('tvq', 'TVQ'),
                ('tvh', 'TVH'),
                ('totale_apres_taxes', 'Total après taxes')
            ]
            facture_attr = 'facture' # Attribut pour la facture unique

            # Remplir Colonnes 1 & 2 (Label + Valeur)
            for i, (attr_name, display_name) in enumerate(attrs_col1):
                value = getattr(self.entry_data, attr_name, "N/A")
                value_str = str(value) # Affichage par défaut
                # --- Rétablir logique spécifique pour booléens Payeur/Refacturer --- 
                if attr_name == 'payeur':
                    value_str = "Employé" if value else "Jacmar"
                elif attr_name == 'refacturer':
                    value_str = "Oui" if value else "Non"
                # -----------------------------------------------------------------
                elif isinstance(value, (int, float)):
                    # Essayer de formater comme montant si c'est un float
                    try: value_str = f"{float(value):.2f}" 
                    except: pass # Garder str(value) si format échoue
                elif isinstance(value, date): # Formater la date
                    try: value_str = value.strftime("%Y-%m-%d")
                    except: pass
                
                label_widget = QLabel(f"{display_name}:")
                value_widget = QLabel(value_str)
                label_widget.setStyleSheet("background-color: transparent; border: none; font-weight: bold;")
                value_widget.setStyleSheet("background-color: transparent; border: none;")
                value_widget.setWordWrap(True)
                details_layout.addWidget(label_widget, i + 1, 0) # +1 pour ligne 0 (séparateur)

                # --- Gérer spécifiquement Numéro Commande (cacher si vide) --- 
                if attr_name == 'numero_commande' and not value_str:
                    label_widget.hide()
                    value_widget.hide()
                else:
                    details_layout.addWidget(value_widget, i + 1, 1)
                # ---------------------------------------------------------

            # Remplir Colonnes 3 & 4 (Label + Valeur)
            for i, (attr_name, display_name) in enumerate(attrs_col3):
                value = getattr(self.entry_data, attr_name, "N/A")
                value_str = str(value) # Affichage par défaut
                # --- Retirer logique booléenne ici (non applicable pour col3) ---
                # if isinstance(value, bool):
                #     value_str = "Oui" if value else "Non"
                # -------------------------------------------------------------
                if isinstance(value, (int, float)):
                    try: value_str = f"{float(value):.2f}" 
                    except: pass 
                elif isinstance(value, date):
                    try: value_str = value.strftime("%Y-%m-%d")
                    except: pass
                    
                label_widget = QLabel(f"{display_name}:")
                value_widget = QLabel(value_str)
                label_widget.setStyleSheet("background-color: transparent; border: none; font-weight: bold;")
                value_widget.setStyleSheet("background-color: transparent; border: none;")
                value_widget.setWordWrap(True)
                # --- Afficher TOUJOURS les taxes, même à zéro ---
                details_layout.addWidget(label_widget, i + 1, 2) # +1 pour ligne 0 (séparateur)
                details_layout.addWidget(value_widget, i + 1, 3)

            # --- NOUVEAU: Ajouter la section Facture Colonne 5 --- 
            facture_label = QLabel("Facture:")
            facture_label.setStyleSheet("background-color: transparent; border: none; font-weight: bold;")
            details_layout.addWidget(facture_label, 1, 4, Qt.AlignLeft | Qt.AlignTop) # Ligne 1 (sous séparateur), Col 4, Align Top

            # Widget conteneur pour les miniatures
            facture_thumbs_widget = QWidget()
            facture_thumbs_layout = QHBoxLayout(facture_thumbs_widget)
            facture_thumbs_layout.setContentsMargins(0,0,0,0)
            facture_thumbs_layout.setSpacing(4)
            facture_thumbs_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop) # Aligner en haut

            facture_obj = getattr(self.entry_data, facture_attr, None)
            has_factures = False
            if facture_obj and isinstance(facture_obj, Facture):
                all_files = facture_obj.get_full_paths()
                if all_files:
                    has_factures = True
                    for idx, file_path in enumerate(all_files):
                        thumb_pixmap = self._generate_thumbnail_pixmap(file_path) 
                        if not thumb_pixmap.isNull():
                            # --- UTILISER ThumbnailWidget SANS Bouton Delete --- 
                            thumbnail_widget = ThumbnailWidget(file_path, thumb_pixmap, show_delete_button=False)
                            # Connecter le signal clicked du ThumbnailWidget au slot interne
                            thumbnail_widget.clicked.connect(functools.partial(self._on_thumbnail_button_clicked, all_files=all_files, index=idx))
                            facture_thumbs_layout.addWidget(thumbnail_widget)
                            # -------------------------------------------------
                    facture_thumbs_layout.addStretch() # Pour pousser à gauche
                    # Ajouter le widget des miniatures, span plusieurs lignes si nécessaire
                    details_layout.addWidget(facture_thumbs_widget, 2, 4, len(attrs_col1)-1, 1, Qt.AlignLeft | Qt.AlignTop) # Ligne 2, Col 4, Span X rows, 1 Col
            
            # Si pas de factures, cacher le label et ne rien ajouter
            if not has_factures:
                facture_label.hide()
                no_facture_label = QLabel("Aucune")
                no_facture_label.setStyleSheet("background-color: transparent; border: none; font-style: italic;")
                # Ajouter à la même position que facture_thumbs_widget mais caché si has_factures est True
                details_layout.addWidget(no_facture_label, 2, 4, len(attrs_col1)-1, 1, Qt.AlignLeft | Qt.AlignTop)
            # ------------------------------------------------------

        elif self.entry_type == "Dépense":
            details_layout = QGridLayout(self.details_widget) # MODIFIÉ: QGridLayout
            details_layout.setContentsMargins(10, 5, 10, 10)
            details_layout.setVerticalSpacing(5)
            details_layout.setHorizontalSpacing(15) # Espacement horizontal comme pour Repas

            # Définir les largeurs relatives des colonnes
            details_layout.setColumnStretch(0, 1) # Label Col 1
            details_layout.setColumnStretch(1, 2) # Value Col 1
            details_layout.setColumnStretch(2, 1) # Label Col 2
            details_layout.setColumnStretch(3, 2) # Value Col 2
            details_layout.setColumnStretch(4, 2) # Factures Col 3

            details_separator = QFrame()
            details_separator.setFrameShape(QFrame.HLine)
            details_separator.setFrameShadow(QFrame.Sunken)
            details_separator.setMinimumHeight(1)
            separator_color = get_theme_vars().get("COLOR_TEXT_SECONDARY", "#888888")
            details_separator.setStyleSheet(f"border: none; border-top: 1px solid {separator_color}; background-color: transparent;")
            details_layout.addWidget(details_separator, 0, 0, 1, 5)

            depense_attrs_col1 = [
                ('date', 'Date'),
                ('type_depense', 'Type'),
                ('description', 'Description'),
                ('fournisseur', 'Fournisseur'),
                ('payeur', 'Payeur')
            ]
            depense_attrs_col2 = [
                ('totale_avant_taxes', 'Total avant taxes'),
                ('tps', 'TPS'),
                ('tvq', 'TVQ'),
                ('tvh', 'TVH'),
                ('totale_apres_taxes', 'Total après taxes')
            ]
            facture_attr_depense = 'facture'

            current_row = 1 # Commence à la ligne 1 après le séparateur

            # Remplir Colonnes 0 & 1
            for i, (attr_name, display_name) in enumerate(depense_attrs_col1):
                if not hasattr(self.entry_data, attr_name):
                    logger.warning(f"CardWidget Dépense: Attribut '{attr_name}' non trouvé.")
                    continue
                value = getattr(self.entry_data, attr_name)
                value_str = str(value)
                if attr_name == 'payeur':
                    value_str = "Employé" if value else "Jacmar"
                elif isinstance(value, date):
                    try: value_str = value.strftime("%Y-%m-%d")
                    except: pass
                
                label_widget = QLabel(f"{display_name}:")
                value_widget = QLabel(value_str)
                label_widget.setStyleSheet("background-color: transparent; border: none; font-weight: bold;")
                value_widget.setStyleSheet("background-color: transparent; border: none;")
                value_widget.setWordWrap(True)
                details_layout.addWidget(label_widget, current_row + i, 0)
                details_layout.addWidget(value_widget, current_row + i, 1)

            # Remplir Colonnes 2 & 3
            for i, (attr_name, display_name) in enumerate(depense_attrs_col2):
                if not hasattr(self.entry_data, attr_name):
                    logger.warning(f"CardWidget Dépense: Attribut '{attr_name}' non trouvé.")
                    continue
                value = getattr(self.entry_data, attr_name)
                value_str = str(value)
                if isinstance(value, (int, float)):
                    try:
                        value_str = f"{float(value):.2f}"
                    except: pass
                
                label_widget = QLabel(f"{display_name}:")
                value_widget = QLabel(value_str)
                value_widget.setStyleSheet("background-color: transparent; border: none; font-weight: bold;")
                value_widget.setStyleSheet("background-color: transparent; border: none;")
                value_widget.setWordWrap(True)
                # --- Afficher TOUJOURS les taxes, même à zéro ---
                details_layout.addWidget(label_widget, current_row + i, 2)
                details_layout.addWidget(value_widget, current_row + i, 3)

            # Section Facture Colonne 4
            facture_label_dep = QLabel("Facture(s):")
            facture_label_dep.setStyleSheet("background-color: transparent; border: none; font-weight: bold;")
            # Aligner en haut de la colonne, à la première ligne de données (current_row)
            details_layout.addWidget(facture_label_dep, current_row, 4, Qt.AlignLeft | Qt.AlignTop)

            facture_obj_dep = getattr(self.entry_data, facture_attr_depense, None)
            has_factures_dep = False
            if facture_obj_dep and isinstance(facture_obj_dep, Facture):
                all_files_dep = facture_obj_dep.get_full_paths()
                if all_files_dep:
                    has_factures_dep = True
                    facture_thumbs_widget_dep = QWidget()
                    facture_thumbs_layout_dep = QHBoxLayout(facture_thumbs_widget_dep)
                    facture_thumbs_layout_dep.setContentsMargins(0,0,0,0)
                    facture_thumbs_layout_dep.setSpacing(4)
                    facture_thumbs_layout_dep.setAlignment(Qt.AlignLeft | Qt.AlignTop)

                    for idx, file_path in enumerate(all_files_dep):
                        thumb_pixmap = self._generate_thumbnail_pixmap(file_path)
                        if not thumb_pixmap.isNull():
                            thumbnail_widget_dep = ThumbnailWidget(file_path, thumb_pixmap, show_delete_button=False)
                            thumbnail_widget_dep.clicked.connect(functools.partial(self._on_thumbnail_button_clicked, all_files=all_files_dep, index=idx))
                            facture_thumbs_layout_dep.addWidget(thumbnail_widget_dep)
                    facture_thumbs_layout_dep.addStretch()
                    # Ajouter sous le label Facture(s), span sur plusieurs lignes si nécessaire
                    details_layout.addWidget(facture_thumbs_widget_dep, current_row + 1, 4, len(depense_attrs_col1) -1 , 1, Qt.AlignLeft | Qt.AlignTop)
            
            if not has_factures_dep:
                facture_label_dep.show() # Assurer que le label est visible même si pas de facture
                no_facture_label_dep = QLabel("Aucune")
                no_facture_label_dep.setStyleSheet("background-color: transparent; border: none; font-style: italic;")
                details_layout.addWidget(no_facture_label_dep, current_row + 1, 4, Qt.AlignLeft | Qt.AlignTop)

        else:
            # --- Layout par défaut (QFormLayout) pour les autres types ---
            details_layout = QFormLayout(self.details_widget)
            details_layout.setContentsMargins(10, 5, 10, 10) # Marges pour les détails
            details_layout.setSpacing(5)

            # --- AJOUT: Séparateur horizontal ---
            details_separator = QFrame()
            details_separator.setFrameShape(QFrame.HLine)
            details_separator.setFrameShadow(QFrame.Sunken)
            details_separator.setMinimumHeight(1)
            separator_color = get_theme_vars().get("COLOR_TEXT_SECONDARY", "#888888")
            details_separator.setStyleSheet(f"border: none; border-top: 1px solid {separator_color}; background-color: transparent;")
            details_layout.addRow(details_separator)
            # --- Fin Séparateur ---

            # Exclure les attributs non pertinents ou déjà dans le résumé (ou internes)
            excluded_attrs = ['date', 'total', 'montant', 'totale_apres_taxes', '_sa_instance_state',
                              'date_repas', 'date_deplacement', 'date_depense',
                              'employe', 'jacmar'] # AJOUT: Exclure employe et jacmar ici aussi par défaut
            try:
                 attributes = vars(self.entry_data)
            except TypeError:
                 attributes = {k: getattr(self.entry_data, k, None) for k in dir(self.entry_data) if not k.startswith('__') and not callable(getattr(self.entry_data, k))}

            for attr, value in attributes.items():
                if attr not in excluded_attrs:
                    label_text = attr.replace('_', ' ').capitalize()
                    value_label = QLabel(str(value))
                    value_label.setStyleSheet("background-color: transparent; border: none;") # Forcer transparence
                    value_label.setWordWrap(True)
                    details_layout.addRow(f"{label_text}:", value_label)

        self.details_widget.setVisible(False) # Caché par défaut
        # Assurer que le widget de détails est transparent
        self.details_widget.setStyleSheet("background-color: transparent; border: none;")

        # Ajouter les widgets Summary et Details au layout principal
        main_layout.addWidget(summary_widget)
        main_layout.addWidget(self.details_widget)

    @Slot(bool)
    def _toggle_details(self, checked):
        self.details_widget.setVisible(checked)
        # --- Correction de l'inversion des icônes ---
        # Changer l'icône du bouton
        # icon_name = "round_arrow_drop_down.png" if checked else "round_arrow_drop_up.png"
        icon_name = "round_arrow_drop_up.png" if checked else "round_arrow_drop_down.png" # Inversé: UP pour déplié (checked), DOWN pour replié
        # -------------------------------------------
        icon_path = get_icon_path(icon_name)
        if icon_path:
            self.expand_button.setIcon(QIcon(icon_path))

    # --- AJOUT: Slot pour afficher le menu d'options --- 
    @Slot()
    def _show_options_menu(self, position=None):
        """Affiche le menu contextuel à la position donnée ou sous le bouton options."""
        # --- Logique de mise en évidence pendant l'ouverture du menu --- 
        original_stylesheet = self.styleSheet() # Sauvegarder le style actuel
        try:
            theme = get_theme_vars()
            accent_color = theme.get("COLOR_ACCENT", "#007ACC")
            selection_border_style = f"border: 2px solid {accent_color};"
            base_selector = f"#CardWidget[objectName=\"CardWidget\"]"
            
            # Récupérer la couleur de fond normale de la carte depuis le thème
            card_bg_color = theme.get("COLOR_PRIMARY_LIGHTEST", "#5a5d5e")
            
            # Construire la règle de style complète pour l'état "menu ouvert"
            # Fond normal + Bordure accent + autres propriétés de base
            menu_open_style_rule = f"{base_selector} {{ background-color: {card_bg_color}; {selection_border_style} border-radius: {RADIUS_BOX}; margin: 0 5px; }}"
            
            # Appliquer ce style directement. S'il y avait d'autres règles spécifiques
            # dans original_stylesheet (ex: pour des éléments enfants), elles sont perdues
            # pendant que le menu est ouvert, mais seront restaurées après.
            self.setStyleSheet(menu_open_style_rule)

        except Exception as e:
            logger.warning(f"Erreur application style menu contextuel: {e}")
            # En cas d'erreur, on ne touche pas au style
            original_stylesheet = None # Pour éviter la restauration erronée
        # -------------------------------------------------------------------

        if not self.options_menu:
            self.options_menu = QMenu(self)
            self.options_menu.setObjectName("CardOptionsMenu") # Pour QSS

            # Créer les actions
            edit_action = QAction("Modifier", self)
            duplicate_action = QAction("Dupliquer", self)
            copy_action = QAction("Copier", self)
            delete_action = QAction("Supprimer", self)
            delete_action.setObjectName("DeleteAction") # Pour style spécifique si besoin (ex: rouge)

            # Connecter les actions aux signaux
            edit_action.triggered.connect(self.edit_requested.emit)
            duplicate_action.triggered.connect(self.duplicate_requested.emit)
            copy_action.triggered.connect(self.copy_requested.emit)
            delete_action.triggered.connect(self.delete_requested.emit)

            # Ajouter les actions au menu
            self.options_menu.addAction(edit_action)
            self.options_menu.addAction(duplicate_action)
            self.options_menu.addAction(copy_action)
            self.options_menu.addSeparator()
            self.options_menu.addAction(delete_action)

            # Appliquer un style de base (inspiré de ce qui pourrait être dans recent_list_page)
            theme = get_theme_vars()
            menu_bg = theme.get("COLOR_PRIMARY_MEDIUM", "#555")
            menu_fg = theme.get("COLOR_TEXT_PRIMARY", "#EEE")
            menu_selection_bg = theme.get("COLOR_ACCENT", "#007ACC")
            menu_separator = theme.get("COLOR_PRIMARY_LIGHT", "#666")
            delete_fg = theme.get("COLOR_ERROR", "#E53935") # Couleur rouge pour supprimer

            self.options_menu.setStyleSheet(f"""
                QMenu#CardOptionsMenu {{
                    background-color: {menu_bg};
                    color: {menu_fg};
                    border: 1px solid {theme.get("COLOR_PRIMARY_DARK", "#444")};
                    border-radius: 4px;
                    padding: 4px;
                }}
                QMenu#CardOptionsMenu::item {{
                    padding: 5px 20px;
                    background-color: transparent;
                }}
                QMenu#CardOptionsMenu::item:selected {{
                    background-color: {menu_selection_bg};
                    color: {menu_fg}; /* Ou une couleur de texte contrastante si besoin */
                    border-radius: 2px;
                }}
                QMenu#CardOptionsMenu::separator {{
                    height: 1px;
                    background-color: {menu_separator};
                    margin-left: 5px;
                    margin-right: 5px;
                    margin-top: 2px;
                    margin-bottom: 2px;
                }}
                QMenu#CardOptionsMenu QAction#DeleteAction {{
                    color: {delete_fg}; /* Couleur spécifique pour Supprimer */
                }}
                QMenu#CardOptionsMenu QAction#DeleteAction:selected {{
                    color: {menu_fg}; /* Revenir couleur normale sur sélection */
                    background-color: {delete_fg}; /* Fond rouge sur sélection */
                }}
            """)

        # Afficher le menu à la position spécifiée ou sous le bouton
        if position is None:
            # Calculer la position sous le bouton si aucune position n'est fournie
            pos = self.options_button.mapToGlobal(QPoint(0, self.options_button.height()))
        else:
            # Utiliser la position fournie (ex: depuis contextMenuEvent)
            pos = position
        
        # --- Exécuter le menu (bloquant) ---
        selected_action = self.options_menu.exec_(pos)
        # -----------------------------------

        # --- Restaurer le style original (sauf si on vient de cliquer sur Modifier) --- 
        # On récupère l'action "Modifier" pour la comparaison
        edit_action = None
        for action in self.options_menu.actions():
            if action.text() == "Modifier": # Ou une meilleure façon d'identifier l'action
                edit_action = action
                break
        
        if selected_action != edit_action:
            try:
                if original_stylesheet is not None: # Vérifier si on a bien sauvegardé un style
                    self.setStyleSheet(original_stylesheet)
            except Exception as e:
                logger.warning(f"Erreur restauration style après menu contextuel: {e}")
        # else: On ne restaure pas si "Modifier" a été cliqué, car set_editing_highlight va s'en charger.
        # ----------------------------------------------------------------------------

    # --- Méthode pour générer miniature (copiée depuis rapport_depense_page) ---
    # (Avec ajustement pour être une méthode de classe)
    def _generate_thumbnail_pixmap(self, file_path, size=QSize(64, 64)):
        """Génère un QPixmap miniature pour un fichier image ou PDF."""
        # --- NE PAS PRE-SCALER ICI --- 
        # La taille par défaut du QPixmap sera la taille originale ou rendue
        pixmap = QPixmap() 
        is_image = any(file_path.lower().endswith(ext) for ext in
                       ['.png', '.jpg', '.jpeg', '.bmp', '.gif'])

        try:
            if is_image:
                img = QImage(file_path)
                if not img.isNull():
                    # Charger l'image, mais ne pas scaler ici
                    pixmap = QPixmap.fromImage(img)
            elif file_path.lower().endswith('.pdf') and PYMUPDF_AVAILABLE:
                doc = fitz.open(file_path)
                if len(doc) > 0:
                    page = doc.load_page(0)
                    zoom = 2.0
                    mat = fitz.Matrix(zoom, zoom)
                    pdf_pix = page.get_pixmap(matrix=mat, alpha=False)
                    qimage = QImage(pdf_pix.samples, pdf_pix.width, pdf_pix.height, pdf_pix.stride, QImage.Format_RGB888)
                    # Créer le pixmap depuis PDF rendu, mais ne pas scaler ici
                    pixmap = QPixmap.fromImage(qimage)
                doc.close()
            else:
                placeholder_path = get_icon_path("round_description.png")
                if placeholder_path:
                    # Charger l'icône placeholder, ne pas scaler ici (elle est petite)
                    # On pourrait la scaler à la taille THUMBNAIL_SIZE si on veut un placeholder plus grand
                    pixmap = QPixmap(placeholder_path) 

        except Exception as e:
            logger.error(f"Erreur génération miniature (CardWidget) pour {file_path}: {e}")
            placeholder_path = get_icon_path("round_description.png")
            if placeholder_path:
                 pixmap = QPixmap(placeholder_path)

        if pixmap.isNull():
            pixmap = QPixmap(size)
            
            # Créer un placeholder gris à la taille THUMBNAIL_SIZE désirée
            placeholder_size = ThumbnailWidget.THUMBNAIL_SIZE if 'ThumbnailWidget' in globals() else 100
            pixmap = QPixmap(placeholder_size, placeholder_size)
            pixmap.fill(Qt.darkGray)

        return pixmap
    # -----------------------------------------------------------------------

    # --- Slot interne pour gérer clic sur bouton miniature --- 
    @Slot(list, int)
    def _on_thumbnail_button_clicked(self, all_files, index):
        """Émet le signal thumbnail_clicked avec les données reçues."""
        logger.debug(f"CardWidget: Thumbnail clicked! Emitting signal with index {index} for list: {all_files}")
        self.thumbnail_clicked.emit(all_files, index)
    # ---------------------------------------------------------

    def set_options_enabled(self, enabled: bool):
        """Active ou désactive le bouton du menu d'options."""
        if self.options_button:
            self.options_button.setEnabled(enabled)

    def set_editing_highlight(self, is_editing: bool):
        """Applique ou retire une bordure jaune vif en définissant le style complet."""
        base_selector = f"#CardWidget[objectName=\"CardWidget\"]"
        edit_border_style = "border: 2px solid #FFD600;" # Jaune vif
        default_border_style = "border: none;"
        
        try:
            # Récupérer la couleur de fond normale de la carte depuis le thème
            theme = get_theme_vars()
            card_bg_color = theme.get("COLOR_PRIMARY_LIGHTEST", "#5a5d5e")
            bg_style = f"background-color: {card_bg_color};"
            
            # Définir les styles complets
            normal_style = f"{base_selector} {{ {bg_style} {default_border_style} border-radius: {RADIUS_BOX}; margin: 0 5px; }}"
            editing_style = f"{base_selector} {{ {bg_style} {edit_border_style} border-radius: {RADIUS_BOX}; margin: 0 5px; }}"
            
            # Appliquer le style approprié
            if is_editing:
                self.setStyleSheet(editing_style)
            else:
                self.setStyleSheet(normal_style)
        except Exception as e:
            logger.warning(f"Erreur application style édition highlight: {e}")
            # Fallback: essayer de ne rien faire pour éviter de casser plus
            pass 

    # --- Gestion Clic Droit --- 
    def contextMenuEvent(self, event):
        """Gère l'événement de clic droit pour afficher le menu d'options."""
        # Vérifier si les options sont activées avant d'afficher le menu
        if self.options_button and self.options_button.isEnabled():
            self._show_options_menu(event.globalPos())
        else:
            super().contextMenuEvent(event) # Comportement par défaut si options désactivées
    # ------------------------

    # --- Gestion Double Clic --- 
    def mouseDoubleClickEvent(self, event):
        """Gère l'événement de double-clic pour déplier/replier la carte."""
        # Simuler un clic sur le bouton expand/collapse
        if self.expand_button:
            self.expand_button.toggle()
            event.accept() # Indiquer que l'événement a été traité
        else:
            super().mouseDoubleClickEvent(event) # Comportement par défaut
    # ---------------------------

# --- Fin Widget Card --- 