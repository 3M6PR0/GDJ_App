from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QFormLayout, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSlot as Slot, QSize, pyqtSignal
from PyQt5.QtGui import QIcon
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
    # -----------------------------------------

    def __init__(self, entry_data, entry_type, parent=None):
        super().__init__(parent)
        # Donner un nom d'objet pour le ciblage QSS global ou interne
        self.setObjectName("CardWidget") 
        self.entry_data = entry_data
        self.entry_type = entry_type

        # --- Obtenir les variables de thème POUR le style inline --- 
        theme = get_theme_vars()
        card_bg_color = theme.get("COLOR_PRIMARY_LIGHT", "#4a4d4f")
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
                print(f"WARNING: CardWidget - Icône de type '{entry_type_icon_name}' non trouvée.")
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
            # Tenter de formater la date
            try:
                date_str = date_val.strftime("%Y-%m-%d")
            except AttributeError:
                 date_str = str(date_val) # Fallback si pas un objet date
        if amount_val is not None:
            try:
                amount_str = f"{float(amount_val):.2f} $"
            except (ValueError, TypeError):
                amount_str = str(amount_val) # Fallback

        summary_info = f"{date_str} - {self.entry_type} - {amount_str}"
        info_label = QLabel(summary_info)
        info_label.setStyleSheet("font-weight: bold; background-color: transparent; border: none;") # Forcer transparence

        # --- Obtenir les variables de thème POUR le style inline du bouton --- 
        theme = get_theme_vars()
        # card_bg_color = theme.get("COLOR_PRIMARY_LIGHT", "#4a4d4f") # Déjà présent pour la carte
        hover_bg_color = theme.get("COLOR_PRIMARY_MEDIUM", "#5a5d5f") # Couleur pour le survol
        # -------------------------------------------------------------------

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

        summary_layout.addWidget(info_label)        # Info à gauche
        summary_layout.addStretch(1)                # Espace extensible
        summary_layout.addWidget(self.expand_button) # Bouton à droite
        
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

                # --- Gérer spécifiquement Taxes (cacher si 0.00) --- 
                is_tax_field = attr_name in ['tps', 'tvq', 'tvh']
                try:
                    # Comparaison plus sûre pour les floats
                    is_zero_tax = is_tax_field and abs(float(value)) < 0.001 
                except (ValueError, TypeError):
                    is_zero_tax = False 
                    
                if is_zero_tax:
                    label_widget.hide()
                    value_widget.hide()
                else:
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
                              'date_repas', 'date_deplacement', 'date_depense']
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
            # --- Fin layout par défaut ---

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
            print(f"Erreur génération miniature (CardWidget) pour {file_path}: {e}")
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
        print(f"CardWidget: Thumbnail clicked! Emitting signal with index {index} for list: {all_files}") # Debug
        self.thumbnail_clicked.emit(all_files, index)
    # ---------------------------------------------------------

# --- Fin Widget Card --- 