from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSlot as Slot, QSize
from PyQt5.QtGui import QIcon
from utils.icon_loader import get_icon_path # Assumer que utils est accessible depuis widgets
from utils.theme import get_theme_vars, RADIUS_BOX 

# --- Widget Card (Reconstruit, héritant de QFrame) --- 
class CardWidget(QFrame):
    def __init__(self, entry_data, entry_type, parent=None):
        super().__init__(parent)
        # Donner un nom d'objet pour le ciblage QSS global ou interne
        self.setObjectName("CardWidget") 
        self.entry_data = entry_data
        self.entry_type = entry_type

        # --- Obtenir les variables de thème POUR le style inline --- 
        theme = get_theme_vars()
        card_bg_color = theme.get("COLOR_PRIMARY_LIGHT", "#4a4d4f")
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
        self.expand_button.setObjectName("CardExpandButton") # Important pour QSS
        # Style de base pour que QSS global puisse le styler plus facilement
        self.expand_button.setStyleSheet("background-color: transparent; border: none;") 
        self.expand_button.toggled.connect(self._toggle_details)

        summary_layout.addWidget(info_label)        # Info à gauche
        summary_layout.addStretch(1)                # Espace extensible
        summary_layout.addWidget(self.expand_button) # Bouton à droite
        
        # Assurer que le widget de résumé est transparent
        summary_widget.setStyleSheet("background-color: transparent; border: none;")

        # 2. Widget de détails (initialement caché)
        self.details_widget = QWidget()
        details_layout = QFormLayout(self.details_widget)
        details_layout.setContentsMargins(10, 5, 10, 10) # Marges pour les détails
        details_layout.setSpacing(5)

        # --- AJOUT: Séparateur horizontal pour les détails ---
        details_separator = QFrame()
        details_separator.setFrameShape(QFrame.HLine)
        # --- Remettre le style explicite pour la visibilité ---
        details_separator.setFrameShadow(QFrame.Sunken) # Optionnel, peut aider
        details_separator.setMinimumHeight(1) # Donner une hauteur minimale
        separator_color = get_theme_vars().get("COLOR_TEXT_SECONDARY", "#888888") # Utiliser une couleur du thème ou un gris
        details_separator.setStyleSheet(f"border: none; border-top: 1px solid {separator_color}; background-color: transparent;")
        # --- Supprimer setObjectName si présent ---
        # details_separator.setObjectName("CustomFrameSeparator") # <- DELETE if exists from previous step
        # ---------------------------------------------------
        details_layout.addRow(details_separator) # Ajouter comme première ligne du FormLayout
        # -----------------------------------------------------

        # Peupler les détails avec toutes les informations pertinentes
        # Exclure les attributs non pertinents ou déjà dans le résumé (ou internes)
        excluded_attrs = ['date', 'total', 'montant', 'totale_apres_taxes', '_sa_instance_state', 
                          'date_repas', 'date_deplacement', 'date_depense']
        try:
             attributes = vars(self.entry_data)
        except TypeError:
             attributes = {k: getattr(self.entry_data, k) for k in dir(self.entry_data) if not k.startswith('__') and not callable(getattr(self.entry_data, k))}

        for attr, value in attributes.items():
            if attr not in excluded_attrs:
                label_text = attr.replace('_', ' ').capitalize()
                value_label = QLabel(str(value))
                value_label.setStyleSheet("background-color: transparent; border: none;") # Forcer transparence
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

# --- Fin Widget Card --- 