from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QScrollArea, QFormLayout, QDateEdit, 
                             QLineEdit, QSpinBox, QComboBox, QSizePolicy, QMessageBox,
                             QStackedWidget, QDialog, QDoubleSpinBox, QFileDialog, QGraphicsItem,
                             QColorDialog, QStyledItemDelegate, QStyle, QInputDialog)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QSize, QPointF, QSizeF
from PyQt5.QtGui import QFont, QIcon, QColor, QStandardItemModel, QStandardItem
import logging
import os
import json

from ui.components.frame import Frame
from utils.signals import signals
from ui.editors.lamicoid_editor_widget import LamicoidEditorWidget
from utils.icon_loader import get_icon_path
from widgets.numeric_input_with_unit import NumericInputWithUnit
from dialogs.variable_config_dialog import VariableConfigDialog
from dialogs.existing_variables_dialog import ExistingVariablesDialog
from models.documents.lamicoid.lamicoid import LamicoidDocument
from models.documents.lamicoid.lamicoid_item import LamicoidItem

logger = logging.getLogger('GDJ_App')

# Conversion (peut être déplacé dans un fichier utils plus tard)
DEFAULT_DPI = 96.0
INCH_TO_MM = 25.4

def mm_to_pixels(mm: float, dpi: float = DEFAULT_DPI) -> float:
    return (mm / INCH_TO_MM) * dpi

def pixels_to_mm(pixels: float, dpi: float = DEFAULT_DPI) -> float:
    return (pixels / dpi) * INCH_TO_MM

class IconOnlyDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, render_size=QSize(28, 28), actual_icon_size=QSize(24, 24)):
        super().__init__(parent)
        self.render_size = render_size
        self.actual_icon_size = actual_icon_size

    def paint(self, painter, option, index):
        icon = index.data(Qt.DecorationRole)
        if not isinstance(icon, QIcon):
            return

        painter.save()
        rect = option.rect

        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, option.palette.highlight())

        # Dessiner l'icône (à sa taille réelle) centrée dans le rect de l'item.
        # option.rect sera la zone allouée pour l'item, que ce soit dans le popup
        # ou dans la partie affichage du QComboBox (qui sera rect total moins espace flèche).
        pixmap = icon.pixmap(self.actual_icon_size) 
        x = rect.x() + (rect.width() - pixmap.width()) // 2
        y = rect.y() + (rect.height() - pixmap.height()) // 2
        
        painter.drawPixmap(x, y, pixmap)
        painter.restore()

    def sizeHint(self, option, index):
        # La taille suggérée pour chaque item (dans le popup et pour le calcul du QComboBox)
        return self.render_size

class LamicoidPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LamicoidPage")
        self.project_variables = [] # Liste pour stocker les variables
        
        self._init_ui()
        self._connect_signals()
        self._apply_toolbar_styles()

        # Définir le mode par défaut et s'assurer que la vue est mise à jour
        default_mode = "Lamicoid"
        if self.mode_selection_combo.findText(default_mode) != -1:
            self.mode_selection_combo.setCurrentText(default_mode)
        elif self.mode_selection_combo.count() > 0: # Fallback si "Lamicoid" n'est pas trouvé
            self.mode_selection_combo.setCurrentIndex(0)
        
        self._on_mode_selected(self.mode_selection_combo.currentText()) # S'assurer que la vue initiale est correcte
        logger.debug(f"LamicoidPage initialisée.")

    def _apply_toolbar_styles(self):
        # Style pour les boutons de la barre d'outils principale (ajout d'items)
        # et les boutons d'options de texte.
        # On peut cibler par nom d'objet si besoin de plus de spécificité,
        # mais ici on va cibler les QPushButton dans EditorToolbar et les boutons d'options.
        # Pour que cela fonctionne bien, il faut s'assurer que les boutons d'options
        # sont bien enfants de self.editor_toolbar ou ont un nom d'objet distinctif.
        # Comme ils sont ajoutés au layout de self.editor_toolbar, un sélecteur descendant devrait fonctionner.

        # Donner des noms d'objet aux boutons d'options pour un ciblage QSS plus précis si nécessaire
        self.bold_button.setObjectName("toolbarOptionButton")
        self.italic_button.setObjectName("toolbarOptionButton")
        self.underline_button.setObjectName("toolbarOptionButton")
        self.color_button.setObjectName("toolbarColorButton") # Différent pour la couleur si besoin

        # Les boutons d'ajout ont déjà self.add_text_button etc. comme identifiants
        # On peut aussi leur donner un nom d'objet commun
        self.add_text_button.setObjectName("toolbarActionButton")
        self.add_rect_button.setObjectName("toolbarActionButton")
        self.add_image_button.setObjectName("toolbarActionButton")

        qss = """
            QFrame#EditorToolbar QPushButton#toolbarActionButton,
            QFrame#EditorToolbar QPushButton#toolbarOptionButton,
            QFrame#EditorToolbar QPushButton#toolbarColorButton {
                padding: 4px;
                border: 1px solid #555; /* Bordure initiale */
                background-color: #4a4d4e; /* Fond initial, similaire aux cartes */
            }
            QFrame#EditorToolbar QPushButton#toolbarActionButton:hover,
            QFrame#EditorToolbar QPushButton#toolbarOptionButton:hover,
            QFrame#EditorToolbar QPushButton#toolbarColorButton:hover {
                background-color: #5a5d5e; /* Fond au survol */
                border: 1px solid #666;
            }
            QFrame#EditorToolbar QPushButton#toolbarActionButton:pressed,
            QFrame#EditorToolbar QPushButton#toolbarOptionButton:pressed,
            QFrame#EditorToolbar QPushButton#toolbarColorButton:pressed {
                background-color: #3a3d3e; /* Fond au clic */
                border: 1px solid #444;
            }
            QFrame#EditorToolbar QPushButton#toolbarOptionButton:checked {
                background-color: #007ACC; /* Fond pour les boutons checkable cochés (ex: Gras) */
                color: white;
                border: 1px solid #005C9C;
            }
            QFrame#EditorToolbar QPushButton#toolbarOptionButton:checked:hover {
                background-color: #008AE6;
            }
        """
        self.editor_toolbar.setStyleSheet(qss)

    def _init_ui(self):
        page_layout = QHBoxLayout(self)
        page_layout.setContentsMargins(10, 10, 10, 10)
        page_layout.setSpacing(10)

        left_header_widget = QWidget()
        left_header_widget.setObjectName("FrameHeaderContainer")
        left_header_layout = QVBoxLayout(left_header_widget)
        left_header_layout.setContentsMargins(0,0,0,0)
        left_header_layout.setSpacing(5)

        self.form_title_label = QLabel("Configuration Lamicoid")
        self.form_title_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.form_title_label.setObjectName("CustomFrameTitle")
        left_header_layout.addWidget(self.form_title_label)

        type_lamicoid_combo_container = QWidget()
        type_lamicoid_combo_layout = QHBoxLayout(type_lamicoid_combo_container)
        type_lamicoid_combo_layout.setContentsMargins(0,0,0,0)
        type_lamicoid_label = QLabel("Nouveau:")
        self.mode_selection_combo = QComboBox()
        self.mode_selection_combo.addItem("Modele")
        self.mode_selection_combo.addItem("Lamicoid")
        self.mode_selection_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        type_lamicoid_combo_layout.addWidget(type_lamicoid_label)
        type_lamicoid_combo_layout.addWidget(self.mode_selection_combo, 1)
        left_header_layout.addWidget(type_lamicoid_combo_container)
        
        left_panel = Frame(header_widget=left_header_widget, parent=self)
        left_panel.setFixedWidth(350)
        left_panel_content_layout = left_panel.get_content_layout()

        # --- Cadre pour les Variables ---
        self.variables_frame = QFrame(self)
        self.variables_frame.setObjectName("VariablesFrame")
        self.variables_frame.setAutoFillBackground(False) 

        variables_layout = QVBoxLayout(self.variables_frame)
        variables_layout.setContentsMargins(8, 8, 8, 8) 
        variables_layout.setSpacing(6)

        variables_title_label = QLabel("Variables")
        variables_title_label.setObjectName("VariablesTitle") 
        
        self.variables_placeholder_label = QLabel("Aucune variable à afficher pour le moment.")
        # self.variables_placeholder_label.setAlignment(Qt.AlignCenter) # Optionnel

        variables_layout.addWidget(variables_title_label)
        variables_layout.addWidget(self.variables_placeholder_label)
        # variables_layout.addStretch(1) # Ne pas ajouter de stretch pour que le cadre s'adapte au contenu

        self.variables_frame.setStyleSheet("""
            QFrame#VariablesFrame {
                background-color: rgba(0,0,0,0);
                border: 1px solid #4A4D4E; /* Même bordure que LamicoidParamsFrame */
                border-radius: 6px;
                margin-bottom: 8px; /* Espacement avec le QStackedWidget en dessous */
            }
            QLabel#VariablesTitle {
                font-weight: bold;
                /* color: #ddeeff; */ /* Décommentez et ajustez pour une couleur de titre spécifique */
                margin-bottom: 4px; /* Petit espace sous le titre */
            }
        """)
        # --- Fin Cadre pour les Variables ---

        self.left_content_stack = QStackedWidget(self)

        self.lamicoid_params_frame = QFrame(self)
        self.lamicoid_params_frame.setObjectName("LamicoidParamsFrame")
        self.lamicoid_params_frame.setAutoFillBackground(False)
        params_layout = QVBoxLayout(self.lamicoid_params_frame)
        params_layout.setContentsMargins(5,5,5,5) # Marges internes du cadre des paramètres
        params_layout.setSpacing(8)

        # --- Titre pour le cadre des paramètres ---
        params_title_label = QLabel("Paramètres Lamicoid")
        params_title_label.setObjectName("ParamsTitle")
        params_layout.addWidget(params_title_label)
        # --- Fin Titre ---

        params_form_layout = QFormLayout()
        params_form_layout.setSpacing(8)
        params_form_layout.setLabelAlignment(Qt.AlignLeft)

        self.width_spinbox = NumericInputWithUnit(unit_text="mm", initial_value=100.0, max_decimals=0, parent=self)
        params_form_layout.addRow("Largeur:", self.width_spinbox)

        self.height_spinbox = NumericInputWithUnit(unit_text="mm", initial_value=50.0, max_decimals=0, parent=self)
        params_form_layout.addRow("Hauteur:", self.height_spinbox)

        self.radius_spinbox = NumericInputWithUnit(unit_text="mm", initial_value=2.0, max_decimals=0, parent=self)
        params_form_layout.addRow("Rayon Coins:", self.radius_spinbox)

        self.margin_spinbox = NumericInputWithUnit(unit_text="mm", initial_value=2.0, max_decimals=0, parent=self)
        params_form_layout.addRow("Marge Intérieure:", self.margin_spinbox)

        self.grid_spacing_spinbox = NumericInputWithUnit(unit_text="mm", initial_value=1.0, max_decimals=0, parent=self)
        params_form_layout.addRow("Espacement Grille:", self.grid_spacing_spinbox)

        params_layout.addLayout(params_form_layout)
        params_layout.addStretch(1)
        
        self.left_content_stack.addWidget(self.lamicoid_params_frame)

        # --- Nouveau Cadre pour la sélection de modèle en mode Lamicoid ---
        self.lamicoid_mode_frame = QFrame(self)
        self.lamicoid_mode_frame.setObjectName("LamicoidModeFrame")
        lamicoid_mode_layout = QVBoxLayout(self.lamicoid_mode_frame)
        lamicoid_mode_layout.setContentsMargins(5, 5, 5, 5)
        lamicoid_mode_layout.setSpacing(8)

        template_selection_label = QLabel("Sélectionner Modèle:")
        lamicoid_mode_layout.addWidget(template_selection_label)

        self.template_selection_combo = QComboBox()
        self.template_selection_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lamicoid_mode_layout.addWidget(self.template_selection_combo)
        lamicoid_mode_layout.addStretch(1) # Pour pousser les éléments vers le haut

        self.left_content_stack.addWidget(self.lamicoid_mode_frame)
        # --- Fin Nouveau Cadre ---

        self.left_placeholder_widget = QLabel("Sélectionnez une action.")
        self.left_placeholder_widget.setAlignment(Qt.AlignCenter)
        self.left_content_stack.addWidget(self.left_placeholder_widget)

        # Inverser l'ordre d'ajout: d'abord le stack des paramètres, ensuite le frame des variables
        left_panel_content_layout.addWidget(self.left_content_stack)
        left_panel_content_layout.addWidget(self.variables_frame) 

        # --- Cadre pour les Actions (Effacer, Créer) ---
        self.actions_frame = QFrame(self)
        self.actions_frame.setObjectName("ActionsFrame")
        actions_layout = QHBoxLayout(self.actions_frame) # Utiliser QHBoxLayout pour les boutons sur une ligne
        actions_layout.setContentsMargins(8, 8, 8, 8) 
        actions_layout.setSpacing(6)

        self.clear_button = QPushButton("Effacer")
        self.clear_button.setIcon(QIcon(get_icon_path("round_delete_sweep.png"))) # Exemple d'icône
        self.clear_button.setObjectName("ActionButton")
        actions_layout.addWidget(self.clear_button)

        self.create_button = QPushButton("Créer")
        self.create_button.setIcon(QIcon(get_icon_path("round_add_circle.png"))) # Exemple d'icône
        self.create_button.setObjectName("ActionButton")
        actions_layout.addWidget(self.create_button)
        
        # Style pour actions_frame similaire à variables_frame
        self.actions_frame.setStyleSheet("""
            QFrame#ActionsFrame {
                background-color: rgba(0,0,0,0);
                border: 1px solid #4A4D4E;
                border-radius: 6px;
                margin-top: 8px; /* Espacement avec le frame des variables au-dessus */
            }
            QPushButton#ActionButton {
                /* Style pour les boutons si nécessaire, sinon ils prendront le style global */
                padding: 5px; 
            }
        """)
        left_panel_content_layout.addWidget(self.actions_frame)
        # --- Fin Cadre pour les Actions ---

        page_layout.addWidget(left_panel)

        # Assurer que le QStackedWidget est aussi transparent
        self.left_content_stack.setStyleSheet("QStackedWidget { background-color: transparent; }")

        left_panel.setStyleSheet("") # Assure que left_panel utilise son style par défaut ou celui de Frame.

        # Style pour self.lamicoid_params_frame (DANS le left_panel) :
        # fond transparent ET une bordure arrondie.
        self.lamicoid_params_frame.setStyleSheet("""
            QFrame#LamicoidParamsFrame {
                background-color: rgba(0,0,0,0); /* Fond transparent explicite */
                border: 1px solid #4A4D4E; /* Couleur de bordure souhaitée */
                border-radius: 6px;       /* Rayon des coins souhaité */
            }
            QLabel#ParamsTitle { /* Style pour le titre des paramètres */
                font-weight: bold;
                margin-bottom: 4px; 
            }
        """)

        # Style pour self.lamicoid_mode_frame
        self.lamicoid_mode_frame.setStyleSheet("""
            QFrame#LamicoidModeFrame {
                background-color: rgba(0,0,0,0);
                border: 1px solid #4A4D4E; 
                border-radius: 6px;
            }
        """)

        right_header_widget = QWidget()
        right_header_widget.setObjectName("FrameHeaderContainer")
        right_header_layout = QHBoxLayout(right_header_widget)
        right_header_layout.setContentsMargins(0,0,0,0)
        
        self.right_panel_title_label = QLabel("Éditeur Lamicoid")
        self.right_panel_title_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.right_panel_title_label.setObjectName("CustomFrameTitle")
        right_header_layout.addWidget(self.right_panel_title_label)
        right_header_layout.addStretch()

        right_panel = Frame(header_widget=right_header_widget, parent=self)
        right_panel_content_layout = right_panel.get_content_layout()

        # Réinitialiser le style du right_panel pour qu'il utilise son style par défaut (de Frame)
        # et que ses composants internes (comme EditorToolbar) utilisent leurs styles définis ailleurs.
        right_panel.setStyleSheet("")

        # Il est important que _apply_toolbar_styles() soit appelé APRÈS 
        # que le style de right_panel et de self.editor_toolbar ait été potentiellement "nettoyé"
        # pour que les styles spécifiques des boutons de la toolbar s'appliquent correctement.
        # L'appel à _apply_toolbar_styles est déjà dans __init__ après _init_ui, ce qui est bien.

        # --- Barre d'outils pour l'éditeur ---
        self.editor_toolbar = QFrame(self)
        self.editor_toolbar.setObjectName("EditorToolbar")
        # self.editor_toolbar.setFixedHeight(40) # Optionnel, pour une hauteur fixe
        editor_toolbar_layout = QHBoxLayout(self.editor_toolbar)
        editor_toolbar_layout.setContentsMargins(5, 2, 5, 2) # Marges fines
        editor_toolbar_layout.setSpacing(5)

        self.add_text_button = QPushButton("") # Texte initial vide
        add_text_icon_path = get_icon_path("round_abc.png") # Utilisation de round_abc.png
        if add_text_icon_path:
            self.add_text_button.setIcon(QIcon(add_text_icon_path))
            self.add_text_button.setToolTip("Ajouter Texte") # Info-bulle pour indiquer l'action
        else:
            self.add_text_button.setText("Texte") # Fallback si l'icône n'est pas trouvée
        editor_toolbar_layout.addWidget(self.add_text_button)

        self.add_rect_button = QPushButton("") # Texte initial vide
        add_rect_icon_path = get_icon_path("round_rectangle.png")
        if add_rect_icon_path:
            self.add_rect_button.setIcon(QIcon(add_rect_icon_path))
            self.add_rect_button.setToolTip("Ajouter Rectangle")
        else:
            self.add_rect_button.setText("Rectangle")
        editor_toolbar_layout.addWidget(self.add_rect_button)

        self.add_image_button = QPushButton("") # Texte initial vide
        add_image_icon_path = get_icon_path("round_image.png")
        if add_image_icon_path:
            self.add_image_button.setIcon(QIcon(add_image_icon_path))
            self.add_image_button.setToolTip("Ajouter Image")
        else:
            self.add_image_button.setText("Image")
        editor_toolbar_layout.addWidget(self.add_image_button)

        self.add_variable_button = QPushButton("") # Texte initial vide
        add_variable_icon_path = get_icon_path("round_data_object.png") # Suggestion d'icône
        if add_variable_icon_path:
            self.add_variable_button.setIcon(QIcon(add_variable_icon_path))
            self.add_variable_button.setToolTip("Ajouter Variable")
        else:
            self.add_variable_button.setText("Var") # Fallback
        self.add_variable_button.setObjectName("toolbarActionButton") # Utiliser le même style
        editor_toolbar_layout.addWidget(self.add_variable_button)

        editor_toolbar_layout.addStretch() # Pousse les boutons à gauche
        
        # --- Séparateur vertical (initialement masqué) ---
        self.text_options_separator = QFrame(self)
        self.text_options_separator.setFrameShape(QFrame.VLine)
        self.text_options_separator.setFrameShadow(QFrame.Sunken)
        editor_toolbar_layout.addWidget(self.text_options_separator)
        self.text_options_separator.setVisible(False)

        # --- Widgets d'options de texte (ajoutés à editor_toolbar, initialement masqués) ---
        self.bold_button = QPushButton("") # Texte initial vide
        self.bold_button.setCheckable(True)
        bold_icon_path = get_icon_path("round_format_bold.png")
        if bold_icon_path:
            self.bold_button.setIcon(QIcon(bold_icon_path))
            self.bold_button.setToolTip("Gras")
        else:
            self.bold_button.setText("Gras") # Fallback
        editor_toolbar_layout.addWidget(self.bold_button)
        self.bold_button.setVisible(False)

        self.italic_button = QPushButton("") # Texte initial vide
        self.italic_button.setCheckable(True)
        italic_icon_path = get_icon_path("round_format_italic.png")
        if italic_icon_path:
            self.italic_button.setIcon(QIcon(italic_icon_path))
            self.italic_button.setToolTip("Italique")
        else:
            self.italic_button.setText("Italique") # Fallback
        editor_toolbar_layout.addWidget(self.italic_button)
        self.italic_button.setVisible(False)

        self.underline_button = QPushButton("") # Texte initial vide
        self.underline_button.setCheckable(True)
        underline_icon_path = get_icon_path("round_format_underlined.png")
        if underline_icon_path:
            self.underline_button.setIcon(QIcon(underline_icon_path))
            self.underline_button.setToolTip("Souligné")
        else:
            self.underline_button.setText("Souligné") # Fallback
        editor_toolbar_layout.addWidget(self.underline_button)
        self.underline_button.setVisible(False)

        self.font_combo = QComboBox(self)
        self.font_combo.addItems(["Arial", "Times New Roman", "Verdana", "Courier New", "Tahoma"])
        editor_toolbar_layout.addWidget(self.font_combo)
        self.font_combo.setVisible(False)

        self.size_spinbox = QSpinBox(self)
        self.size_spinbox.setMinimum(6)
        self.size_spinbox.setMaximum(72)
        self.size_spinbox.setValue(10)
        editor_toolbar_layout.addWidget(self.size_spinbox)
        self.size_spinbox.setVisible(False)

        self.color_button = QPushButton("Couleur")
        editor_toolbar_layout.addWidget(self.color_button)
        self.color_button.setVisible(False)

        self.align_combo = QComboBox(self)
        
        combobox_square_size = QSize(30, 30) # Taille carrée cible pour le QComboBox
        actual_icon_internal_size = QSize(24, 24) # Taille réelle de l'icône

        # Le délégué utilisera la taille carrée pour le rendu des items
        self.icon_only_delegate = IconOnlyDelegate(self.align_combo, 
                                                 render_size=combobox_square_size, 
                                                 actual_icon_size=actual_icon_internal_size)
        self.align_combo.setItemDelegate(self.icon_only_delegate)

        # Forcer le QComboBox à avoir une taille fixe carrée
        self.align_combo.setObjectName("AlignCombo") # Donner un nom d'objet pour le QSS
        self.align_combo.setFixedSize(combobox_square_size)
        # self.align_combo.setIconSize(actual_icon_internal_size) # Commenté: le délégué gère le dessin

        # Les politiques de taille et setSizeAdjustPolicy sont moins pertinentes avec setFixedSize
        # self.align_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # self.align_combo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Appliquer QSS pour minimiser la flèche et le padding
        self.align_combo.setStyleSheet("""
            QComboBox#AlignCombo {
                padding: 1px; /* Garder un petit padding pour l'icône */
            }
            QComboBox#AlignCombo::drop-down {
                /* subcontrol-origin: padding; */ /* Moins pertinent si width est 0 */
                /* subcontrol-position: top right; */ /* Moins pertinent si width est 0 */
                width: 0px;  /* Rendre la zone de la flèche invisible */
                border: none;
            }
            QComboBox#AlignCombo::down-arrow {
                image: none; /* Aucune image pour la flèche */
                width: 0px;
                height: 0px;
                border: none;
            }
        """)

        align_model = QStandardItemModel(self.align_combo)

        align_options = [
            ("round_format_align_left.png", "Aligner à Gauche", Qt.AlignLeft),
            ("round_format_align_center.png", "Aligner au Centre", Qt.AlignCenter),
            ("round_format_align_right.png", "Aligner à Droite", Qt.AlignRight)
        ]

        for icon_file, tooltip, align_flag in align_options:
            icon_path = get_icon_path(icon_file)
            if icon_path:
                item = QStandardItem()
                # Important: L'icône est mise via setData avec Qt.DecorationRole
                # pour que le délégué puisse la récupérer.
                item.setData(QIcon(icon_path), Qt.DecorationRole)
                item.setData(align_flag, Qt.UserRole) # Stocker la valeur d'alignement
                item.setToolTip(tooltip)
                align_model.appendRow(item)
            # Si l'icône n'est pas trouvée, l'item n'est pas ajouté.

        self.align_combo.setModel(align_model)
        # self.align_combo.view().setTextElideMode(Qt.ElideNone) # Moins pertinent avec le délégué qui ne dessine pas de texte.
        # self.align_combo.adjustSize() # Supprimé car setFixedSize est utilisé
            
        editor_toolbar_layout.addWidget(self.align_combo)
        self.align_combo.setVisible(False)
        # --- Fin des options de texte ---
        
        right_panel_content_layout.addWidget(self.editor_toolbar) # Barre d'outils principale
        # --- Fin Barre d'outils ---

        self.right_display_stack = QStackedWidget(self)
        self.lamicoid_editor_widget = LamicoidEditorWidget(self)
        self.right_display_stack.addWidget(self.lamicoid_editor_widget)
        
        right_panel_content_layout.addWidget(self.right_display_stack)
        page_layout.addWidget(right_panel)
        
        self.setLayout(page_layout)
        self._ensure_correct_view_for_mode(self.mode_selection_combo.currentText())

    def _connect_signals(self):
        self.mode_selection_combo.currentTextChanged.connect(self._on_mode_selected)
        self.width_spinbox.valueChanged.connect(self._update_lamicoid_editor_params)
        self.height_spinbox.valueChanged.connect(self._update_lamicoid_editor_params)
        self.radius_spinbox.valueChanged.connect(self._update_lamicoid_editor_params)
        self.margin_spinbox.valueChanged.connect(self._update_lamicoid_editor_params)
        self.grid_spacing_spinbox.valueChanged.connect(self._update_lamicoid_editor_params)
        self.add_text_button.clicked.connect(self._add_text_item_to_editor)
        self.add_rect_button.clicked.connect(self._add_rect_item_to_editor)
        self.add_image_button.clicked.connect(self._add_image_item_to_editor)
        self.add_variable_button.clicked.connect(self._open_variables_manager_dialog)

        # Connexion du signal de l'éditeur Lamicoid
        if self.lamicoid_editor_widget:
            self.lamicoid_editor_widget.text_item_selected_signal.connect(self._handle_text_item_selected)
        
        # Connexions pour la barre d'outils contextuelle du texte
        self.bold_button.toggled.connect(self._apply_text_bold)
        self.italic_button.toggled.connect(self._apply_text_italic)
        self.underline_button.toggled.connect(self._apply_text_underline)
        self.font_combo.currentTextChanged.connect(self._apply_text_font_family)
        self.size_spinbox.valueChanged.connect(self._apply_text_font_size)
        self.color_button.clicked.connect(self._select_text_color)
        self.align_combo.currentIndexChanged.connect(self._apply_text_alignment)

        # Connexion pour le nouveau bouton Créer (template)
        self.create_button.clicked.connect(self._save_lamicoid_template)
        self.template_selection_combo.currentTextChanged.connect(self._on_template_selected)

    def _on_mode_selected(self, selected_mode: str):
        logger.debug(f"Mode sélectionné: {selected_mode}")

        if selected_mode == "Modele":
            if self.lamicoid_editor_widget: # S'assurer que l'widget existe
                self.lamicoid_editor_widget.clear() # Vider l'éditeur avant toute autre opération pour le mode Modèle
        
        self._ensure_correct_view_for_mode(selected_mode)
        
        if selected_mode == "Modele":
            self._update_lamicoid_editor_params()
        elif selected_mode == "Lamicoid":
            # Si un template est déjà sélectionné dans le combobox, le charger
            current_template = self.template_selection_combo.currentText()
            NON_MODEL_ITEMS = ["Erreur chargement modèles", "Aucun modèle disponible", "Dossier modèles absent"]
            if current_template and current_template not in NON_MODEL_ITEMS:
                logger.debug(f"Mode Lamicoid: Rechargement du template '{current_template}' si déjà sélectionné.")
                self._on_template_selected(current_template) # Appelle _load_template_into_editor
            else:
                # Si aucun template valide n'est sélectionné, s'assurer que l'éditeur est vide
                if self.lamicoid_editor_widget:
                    self.lamicoid_editor_widget.clear()

    def _update_lamicoid_editor_params(self):
        if self.mode_selection_combo.currentText() == "Modele":
            width_mm = self.width_spinbox.value()
            height_mm = self.height_spinbox.value()
            radius_mm = self.radius_spinbox.value()
            margin_mm = self.margin_spinbox.value()
            grid_spacing_mm = self.grid_spacing_spinbox.value()
            
            self.lamicoid_editor_widget.set_lamicoid_properties(
                width_px=mm_to_pixels(width_mm),
                height_px=mm_to_pixels(height_mm),
                corner_radius_px=mm_to_pixels(radius_mm),
                margin_px=mm_to_pixels(margin_mm),
                grid_spacing_px=mm_to_pixels(grid_spacing_mm)
            )
            logger.debug(f"Lamicoid editor params updated: W={width_mm}mm, H={height_mm}mm, R={radius_mm}mm, M={margin_mm}mm, Grid={grid_spacing_mm}mm")
        # Si Lamicoid doit aussi mettre à jour les paramètres, ajouter une condition ici
        # elif self.mode_selection_combo.currentText() == "Lamicoid":
            # self.lamicoid_editor_widget.set_lamicoid_properties(...) # avec les valeurs appropriées
            # logger.debug("Lamicoid editor params updated for Lamicoid mode.")

    def _add_text_item_to_editor(self):
        if self.lamicoid_editor_widget and self.right_display_stack.currentWidget() == self.lamicoid_editor_widget:
            logger.debug("Demande d'ajout d'un item Texte à l'éditeur Lamicoid.")
            self.lamicoid_editor_widget.add_editor_item("texte") # Type "texte" pour l'instant
        else:
            logger.warning("LamicoidEditorWidget n'est pas actif, impossible d'ajouter un item texte.")

    def _add_rect_item_to_editor(self):
        if self.lamicoid_editor_widget and self.right_display_stack.currentWidget() == self.lamicoid_editor_widget:
            logger.debug("Demande d'ajout d'un item Rectangle à l'éditeur Lamicoid.")
            self.lamicoid_editor_widget.add_editor_item("rectangle") 
        else:
            logger.warning("LamicoidEditorWidget n'est pas actif, impossible d'ajouter un item rectangle.")

    def _add_image_item_to_editor(self):
        if not (self.lamicoid_editor_widget and self.right_display_stack.currentWidget() == self.lamicoid_editor_widget):
            logger.warning("LamicoidEditorWidget n'est pas actif, impossible de sélectionner une image.")
            return

        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une image",
            "", # Répertoire initial (vide pour le répertoire courant ou dernier utilisé)
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;Tous les fichiers (*)",
            options=options
        )

        if file_path:
            logger.info(f"Image sélectionnée : {file_path}")
            # Ici, nous appellerons une méthode de lamicoid_editor_widget
            # pour ajouter l'item image avec ce chemin.
            self.lamicoid_editor_widget.add_editor_item("image", image_path=file_path)
        else:
            logger.debug("Sélection d'image annulée.")

    def _open_variables_manager_dialog(self):
        """Ouvre le dialogue de gestion des variables existantes et d'ajout de nouvelles."""
        # Passe une copie de la liste actuelle des variables au dialogue
        manager_dialog = ExistingVariablesDialog(list(self.project_variables), self)
        
        # Connecter le signal du dialogue à une méthode de LamicoidPage
        manager_dialog.variable_clicked_to_add.connect(self._add_variable_item_to_editor_from_dialog)
        
        if manager_dialog.exec_(): # L'utilisateur a cliqué "Fermer" ou a fermé d'une autre manière acceptée
            newly_added_this_session = manager_dialog.get_newly_added_variables_this_session()

            # Mettre à jour la liste principale des variables du projet avec celles nouvellement ajoutées
            if newly_added_this_session:
                for new_var in newly_added_this_session:
                    existing_names = [pv.get('name') for pv in self.project_variables]
                    if new_var.get('name') not in existing_names:
                        self.project_variables.append(new_var)
                    else: 
                        logger.info(f"Variable '{new_var.get('name')}' existe déjà, non ajoutée de nouveau via manager.")
                self._update_variables_display() # Rafraîchir l'affichage dans LamicoidPage
            
            # La logique de "quelle variable a été sélectionnée pour être utilisée" 
            # est maintenant gérée par le slot connecté au signal variable_clicked_to_add.
            # Donc, pas besoin de selected_variable_to_use ici après la fermeture du dialogue.
            logger.debug("Dialogue de gestion des variables fermé.")
        else:
            # Cela pourrait se produire si le dialogue est fermé d'une manière qui cause reject(),
            # ou si exec_() retourne 0 pour une autre raison. 
            # S'il n'y a qu'un bouton "Fermer" qui appelle accept(), cette branche est moins probable.
            logger.debug("Gestionnaire de variables fermé (potentiellement Annuler ou échec exec).")

    def _add_variable_item_to_editor_from_dialog(self, variable_data):
        """Slot pour recevoir les données d'une variable cliquée dans ExistingVariablesDialog et l'ajouter à l'éditeur."""
        logger.info(f"Signal reçu pour ajouter la variable à l'éditeur: {variable_data}")
        
        if self.lamicoid_editor_widget and self.right_display_stack.currentWidget() == self.lamicoid_editor_widget:
            # Ici, nous allons passer le nom de la variable pour qu'il soit affiché
            # et potentiellement d'autres infos si l'item "variable_rectangle" en a besoin.
            item_data = {
                'name': variable_data.get('name', 'N/A'),
                'type': 'variable_rectangle' # Un type spécifique pour cet item
                # Vous pourriez ajouter ici d'autres propriétés de la variable si l'item les utilise
            }
            self.lamicoid_editor_widget.add_editor_item(
                "variable_rectangle", 
                data=item_data
            )
            logger.debug(f"Tentative d'ajout de l'item '{item_data.get('name')}' (type: {item_data.get('type')}) à l'éditeur.")
        else:
            logger.warning("LamicoidEditorWidget n'est pas actif, variable non ajoutée à l'éditeur.")

    def _handle_text_item_selected(self, is_selected: bool, selected_item_object: object):
        """Affiche ou masque les options de texte dans la barre d'outils principale et met à jour son état."""
        # Visibilité des options de texte et du séparateur
        self.text_options_separator.setVisible(is_selected)
        self.bold_button.setVisible(is_selected)
        self.italic_button.setVisible(is_selected)
        self.underline_button.setVisible(is_selected)
        self.font_combo.setVisible(is_selected)
        self.size_spinbox.setVisible(is_selected)
        self.color_button.setVisible(is_selected)
        self.align_combo.setVisible(is_selected)

        self.current_selected_text_item = None # Réinitialiser

        if is_selected and isinstance(selected_item_object, QGraphicsItem):
            # Tenter de caster vers GridRectangleItem si c'est bien un QGraphicsItem
            try:
                selected_item = selected_item_object # On suppose que c'est déjà le bon type ou None
                if selected_item and hasattr(selected_item, 'is_text_item') and selected_item.is_text_item:
                    self.current_selected_text_item = selected_item
                    text_g_item = selected_item.text_item # Accès au QGraphicsTextItem enfant
                    current_font = text_g_item.font()

                    # Mettre à jour les contrôles de la barre d'outils (sans émettre leurs propres signaux)
                    self.bold_button.blockSignals(True)
                    self.italic_button.blockSignals(True)
                    self.underline_button.blockSignals(True)
                    self.font_combo.blockSignals(True)
                    self.size_spinbox.blockSignals(True)
                    self.align_combo.blockSignals(True)

                    self.bold_button.setChecked(current_font.bold())
                    self.italic_button.setChecked(current_font.italic())
                    self.underline_button.setChecked(current_font.underline())
                    
                    font_family_name = current_font.family()
                    font_index = self.font_combo.findText(font_family_name, Qt.MatchFixedString)
                    if font_index >= 0:
                        self.font_combo.setCurrentIndex(font_index)
                    else:
                        self.font_combo.setCurrentIndex(0) # Fallback ou ajouter la police si non listée
                    
                    self.size_spinbox.setValue(current_font.pointSize() if current_font.pointSize() > 0 else 10) # Assurer une valeur > 0
                    
                    # Pour l'alignement, il faut lire depuis le document du QGraphicsTextItem
                    current_alignment_option = text_g_item.document().defaultTextOption()
                    current_alignment_flag = current_alignment_option.alignment()
                    
                    # Mettre à jour le QComboBox avec le modèle
                    align_model = self.align_combo.model()
                    for i in range(align_model.rowCount()):
                        item = align_model.item(i)
                        if item and item.data(Qt.UserRole) == current_alignment_flag:
                            self.align_combo.setCurrentIndex(i)
                            break
                    
                    self.bold_button.blockSignals(False)
                    self.italic_button.blockSignals(False)
                    self.underline_button.blockSignals(False)
                    self.font_combo.blockSignals(False)
                    self.size_spinbox.blockSignals(False)
                    self.align_combo.blockSignals(False)
                    
                    logger.debug(f"Item texte sélectionné: {selected_item}. Barre d'outils contextuelle mise à jour.")
                    return # Sortir tôt si l'item est traité
            except AttributeError as e:
                logger.warning(f"Erreur lors de l'accès aux propriétés de l'item sélectionné: {e}")
        
        # Si pas d'item texte valide sélectionné, les options sont déjà masquées par le bloc ci-dessus
        if not (is_selected and self.current_selected_text_item):
            logger.debug("Aucun item texte valide sélectionné ou déselection. Options de texte masquées.")

    # --- Slots pour appliquer les modifications de texte --- 
    def _get_current_text_g_item(self):
        if hasattr(self, 'current_selected_text_item') and self.current_selected_text_item and \
           hasattr(self.current_selected_text_item, 'text_item'):
            return self.current_selected_text_item.text_item
        return None

    def _apply_text_bold(self, checked):
        text_g_item = self._get_current_text_g_item()
        if text_g_item:
            font = text_g_item.font()
            font.setBold(checked)
            text_g_item.setFont(font)
            text_g_item.update() # Forcer le redessin
            if text_g_item.parentItem(): text_g_item.parentItem().update() # Mettre à jour le parent aussi

    def _apply_text_italic(self, checked):
        text_g_item = self._get_current_text_g_item()
        if text_g_item:
            font = text_g_item.font()
            font.setItalic(checked)
            text_g_item.setFont(font)
            text_g_item.update()
            if text_g_item.parentItem(): text_g_item.parentItem().update()

    def _apply_text_underline(self, checked):
        text_g_item = self._get_current_text_g_item()
        if text_g_item:
            font = text_g_item.font()
            font.setUnderline(checked)
            text_g_item.setFont(font)
            text_g_item.update()
            if text_g_item.parentItem(): text_g_item.parentItem().update()

    def _apply_text_font_family(self, font_family_name):
        text_g_item = self._get_current_text_g_item()
        if text_g_item:
            font = text_g_item.font()
            font.setFamily(font_family_name)
            text_g_item.setFont(font)
            text_g_item.update()
            if text_g_item.parentItem(): text_g_item.parentItem().update()

    def _apply_text_font_size(self, size):
        text_g_item = self._get_current_text_g_item()
        if text_g_item:
            font = text_g_item.font()
            if size > 0:
                font.setPointSize(size)
            text_g_item.setFont(font)
            # Après avoir changé la taille, il est bon d'informer le layout du document
            text_g_item.document().adjustSize()
            text_g_item.update()
            if text_g_item.parentItem(): 
                # Forcer la mise à jour de la géométrie du texte dans l'item parent si elle existe
                if hasattr(text_g_item.parentItem(), 'update_text_item_geometry'):
                    text_g_item.parentItem().update_text_item_geometry()
                text_g_item.parentItem().update()

    def _select_text_color(self):
        text_g_item = self._get_current_text_g_item()
        if text_g_item:
            current_color = text_g_item.defaultTextColor()
            new_color = QColorDialog.getColor(current_color, self, "Choisir la couleur du texte")
            if new_color.isValid():
                text_g_item.setDefaultTextColor(new_color)
    
    def _apply_text_alignment(self, index):
        text_g_item = self._get_current_text_g_item()
        if text_g_item:
            # Obtenir la valeur d'alignement à partir de l'item sélectionné dans le modèle
            align_model = self.align_combo.model()
            item = align_model.item(index)
            if not item: # Vérification si l'item existe à cet index
                logger.warning(f"_apply_text_alignment: Aucun item à l'index {index} du modèle.")
                return

            alignment_from_combo = item.data(Qt.UserRole)
            if alignment_from_combo is None: # Vérification si la donnée utilisateur existe
                logger.warning(f"_apply_text_alignment: Aucune donnée utilisateur pour l'item à l'index {index}.")
                return

            # Convertir la valeur récupérée (qui peut être un int) en Qt.AlignmentFlag
            actual_alignment = Qt.AlignmentFlag(alignment_from_combo)

            doc = text_g_item.document()
            option = doc.defaultTextOption()
            option.setAlignment(actual_alignment) # Utiliser la valeur castée
            doc.setDefaultTextOption(option)
            doc.adjustSize() # Mettre à jour la taille du document
            text_g_item.update() # Redessiner l'item texte
            if text_g_item.parentItem(): 
                # Le parent de text_g_item est text_clipper_item.
                # Le parent de text_clipper_item est self.current_selected_text_item (GridRectangleItem)
                if self.current_selected_text_item and hasattr(self.current_selected_text_item, 'update_text_item_geometry'):
                    self.current_selected_text_item.update_text_item_geometry()
                if self.current_selected_text_item: # S'assurer que le parent existe pour l'update
                    self.current_selected_text_item.update()
            
            # Forcer la mise à jour de la vue
            if self.lamicoid_editor_widget and self.lamicoid_editor_widget.viewport():
                self.lamicoid_editor_widget.viewport().update()

            logger.debug(f"Alignement appliqué: {actual_alignment}")

    def _ensure_correct_view_for_mode(self, mode: str):
        if mode == "Modele":
            self.form_title_label.setText("Paramètres du Modèle")
            self.left_content_stack.setCurrentWidget(self.lamicoid_params_frame)
            self.right_panel_title_label.setText("Éditeur Modèle")
            self.right_display_stack.setCurrentWidget(self.lamicoid_editor_widget)
            self.lamicoid_editor_widget.clear() # Ajout crucial ici
            self.lamicoid_editor_widget.setInteractive(True) # Assurer que l'éditeur est interactif
            self._update_variables_display() 
            
        elif mode == "Lamicoid": 
            self.form_title_label.setText("Charger Lamicoid depuis Modèle") 
            self._populate_template_combobox()
            self.left_content_stack.setCurrentWidget(self.lamicoid_mode_frame) 
            self.right_panel_title_label.setText("Aperçu du Modèle") 
            self.right_display_stack.setCurrentWidget(self.lamicoid_editor_widget) # Afficher l'éditeur pour l'aperçu
            self.lamicoid_editor_widget.setInteractive(False) # Mode aperçu seulement
            # Le contenu sera chargé par _on_template_selected_for_lamicoid
            # On peut clearer ici au cas où on arrive sans sélection de template au préalable
            if self.template_selection_combo.currentIndex() <= 0 : # Si "Sélectionner" ou rien
                 self.lamicoid_editor_widget.clear() 
            else:
                # Si un modèle est déjà sélectionné, le recharger ou s'assurer qu'il est affiché
                self._on_template_selected(self.template_selection_combo.currentText())

        elif mode == "--- Sélectionner ---":
            self.form_title_label.setText("Configuration Modèle")
            self.left_content_stack.setCurrentWidget(self.left_placeholder_widget)
            self.right_panel_title_label.setText("Éditeur Modèle") # Par défaut, montrer l'éditeur
            self.right_display_stack.setCurrentWidget(self.lamicoid_editor_widget) 
            self.lamicoid_editor_widget.clear() # Effacer l'éditeur
            self.lamicoid_editor_widget.setInteractive(True) # Permettre l'édition si on revient à "Sélectionner" puis "Modèle"
            self._update_variables_display()
            
        else: # Cas par défaut ou inconnu
            self.form_title_label.setText("Configuration Modèle")
            self.left_content_stack.setCurrentWidget(self.left_placeholder_widget)
            self.right_panel_title_label.setText("Éditeur Modèle")
            self.right_display_stack.setCurrentWidget(self.lamicoid_editor_widget)
            self.lamicoid_editor_widget.clear() # Effacer l'éditeur
            self.lamicoid_editor_widget.setInteractive(True) # Permettre l'édition si on revient à "Sélectionner" puis "Modèle"
            self._update_variables_display()

    def _clear_layout(self, layout):
        """Utilitaire pour vider un layout de tous ses widgets."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    child_layout = item.layout()
                    if child_layout is not None:
                        self._clear_layout(child_layout) # Appel récursif pour les sous-layouts

    def _update_variables_display(self):
        """Met à jour l'affichage des variables dans self.variables_frame."""
        # Accéder au layout du self.variables_frame. 
        # Il a été créé avec un QVBoxLayout dans _init_ui.
        variables_layout = self.variables_frame.layout() 
        if not variables_layout:
            logger.error("Layout pour variables_frame non trouvé.")
            return

        # Vider les anciens widgets de variables, mais garder le titre
        # On suppose que le titre est le premier widget.
        # Et le placeholder est le deuxième (ou seul autre) widget.
        widgets_to_remove = []
        for i in range(variables_layout.count()):
            item = variables_layout.itemAt(i)
            widget = item.widget()
            # Ne pas supprimer le titre (QLabel avec objectName="VariablesTitle")
            # ni le placeholder (self.variables_placeholder_label)
            if widget and widget.objectName() != "VariablesTitle" and widget != self.variables_placeholder_label:
                widgets_to_remove.append(widget)
        
        for widget in widgets_to_remove:
            variables_layout.removeWidget(widget)
            widget.deleteLater()

        if not self.project_variables:
            self.variables_placeholder_label.setVisible(True)
        else:
            self.variables_placeholder_label.setVisible(False)
            for var_data in self.project_variables:
                var_name_label = QLabel(f"<b>{var_data.get('name', 'N/A')}</b>")
                var_name_label.setWordWrap(True)
                variables_layout.addWidget(var_name_label)

                details = [f"  Type: {var_data.get('type', 'N/A')}"]
                if var_data.get('type') == "Valeur personnalisable" and var_data.get('has_unit'):
                    details.append(f"  Unité: {var_data.get('unit', 'N/A')}")
                elif var_data.get('type') == "Valeur sélectionnable":
                    vals = var_data.get('selectable_values', [])
                    details.append(f"  Valeurs: {', '.join(vals) if vals else 'Aucune'}")
                
                for detail_text in details:
                    detail_label = QLabel(detail_text)
                    detail_label.setWordWrap(True)
                    variables_layout.addWidget(detail_label)
                
                # Ajout d'un petit séparateur ou espace
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                line.setFixedHeight(1)
                line.setStyleSheet("background-color: #555;") # Couleur de la ligne
                variables_layout.addWidget(line)
        
        self.variables_frame.adjustSize()

    def _save_lamicoid_template(self):
        """Sauvegarde la configuration actuelle du Lamicoid en tant que template JSON."""
        import json # Pour la sauvegarde
        from PyQt5.QtWidgets import QInputDialog # Pour demander le nom du template

        # Définir le dossier des templates (par exemple, à la racine du projet)
        # Idéalement, ce chemin pourrait être configuré de manière plus globale.
        # Pour l'instant, nous utilisons un chemin relatif au script principal.
        # Cela suppose que votre script principal est à la racine du projet.
        # Si ce n'est pas le cas, vous devrez ajuster 'Path(__file__).resolve().parent.parent'
        # ou utiliser une méthode plus robuste pour obtenir le répertoire racine de l'application.
        try:
            # Essayer d'obtenir le répertoire du script principal de l'application
            # Cela peut être complexe si le script est packagé ou lancé de différentes manières.
            # Une approche simple est de supposer une structure.
            # Si votre main.py est à la racine:
            # app_root_dir = os.path.dirname(os.path.abspath(sys.argv[0])) # Moins fiable
            # Alternative plus courante si la structure est connue:
            current_script_path = os.path.abspath(__file__)
            # Si lamicoid_page.py est dans pages/templates/, remonter de deux niveaux pour la racine du projet
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
            templates_dir = os.path.join(project_root, "project_templates")
        except Exception:
            # Fallback si la détection du chemin échoue
            logger.warning("Impossible de déterminer le chemin racine du projet dynamiquement, utilisation d'un chemin relatif.")
            templates_dir = "project_templates"

        # Créer le dossier des templates s'il n'existe pas
        if not os.path.exists(templates_dir):
            try:
                os.makedirs(templates_dir)
                logger.info(f"Dossier des templates créé : {templates_dir}")
            except OSError as e:
                logger.error(f"Impossible de créer le dossier des templates '{templates_dir}': {e}")
                QMessageBox.critical(self, "Erreur de Création de Dossier", 
                                     f"Impossible de créer le dossier des templates:\n{templates_dir}\nErreur: {e}")
                return

        # Demander un nom de fichier pour le template
        template_name, ok = QInputDialog.getText(self, "Nom du Template", 
                                                 "Entrez un nom pour le template (sans extension):")
        
        if not (ok and template_name):
            logger.info("Sauvegarde du template annulée par l'utilisateur (pas de nom fourni).")
            return

        # Nettoyer le nom de fichier (éviter les caractères invalides, bien que QInputDialog soit généralement sûr)
        # Pour plus de robustesse, on pourrait utiliser une fonction pour "slugifier" le nom.
        safe_template_name = "".join(c for c in template_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        if not safe_template_name: # Si le nom devient vide après nettoyage
            safe_template_name = "template_sans_nom"
        
        file_name = safe_template_name + ".json"
        file_path = os.path.join(templates_dir, file_name)

        # Vérifier si le fichier existe déjà
        if os.path.exists(file_path):
            reply = QMessageBox.question(self, "Fichier Existant", 
                                         f"Le template '{file_name}' existe déjà.\nVoulez-vous le remplacer ?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                logger.info(f"Sauvegarde du template '{file_name}' annulée (ne pas remplacer).")
                return

        logger.info(f"Début de la sauvegarde du template Lamicoid vers: {file_path}")

        template_data = {}

        # 1. Collecter les paramètres du Lamicoid
        template_data['lamicoid_parameters'] = self._collect_lamicoid_parameters()

        # 2. Collecter les items de l'éditeur
        template_data['editor_items'] = self._collect_editor_items()

        # 3. Collecter les variables du projet
        template_data['project_variables'] = list(self.project_variables) # Créer une copie

        # 4. Écrire dans le fichier JSON
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=4)
            logger.info(f"Template Lamicoid sauvegardé avec succès dans {file_path}")
            QMessageBox.information(self, "Sauvegarde Réussie", f"Le template a été sauvegardé dans:\n{file_path}")
        except IOError as e:
            logger.error(f"Erreur d'écriture lors de la sauvegarde du template: {e}")
            QMessageBox.critical(self, "Erreur de Sauvegarde", f"Impossible de sauvegarder le template.\nErreur: {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la sauvegarde du template: {e}")
            QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur inattendue s'est produite lors de la sauvegarde.\n{e}")

    def _collect_lamicoid_parameters(self) -> dict:
        """Collecte les paramètres dimensionnels et de grille du Lamicoid."""
        params = {
            'width_mm': self.width_spinbox.value(),
            'height_mm': self.height_spinbox.value(),
            'corner_radius_mm': self.radius_spinbox.value(),
            'margin_mm': self.margin_spinbox.value(),
            'grid_spacing_mm': self.grid_spacing_spinbox.value()
        }
        logger.debug(f"Paramètres Lamicoid collectés: {params}")
        return params

    def _collect_editor_items(self) -> list:
        """Collecte les informations de tous les items graphiques pertinents dans l'éditeur."""
        # Supprimer l'importation locale problématique
        # from ui.editors.lamicoid_editor_widget import ExportedGridRectangleItemType

        items_data = []
        if not (self.lamicoid_editor_widget and hasattr(self.lamicoid_editor_widget, '_scene')):
            logger.warning("_collect_editor_items: LamicoidEditorWidget ou sa scène n'est pas disponible.")
            return items_data

        scene_items = self.lamicoid_editor_widget._scene.items()
        for item in scene_items:
            # Vérifier le type par le nom de la classe pour éviter les problèmes d'importation circulaire
            if item.__class__.__name__ == 'GridRectangleItem':
                # Le reste de la logique pour extraire les informations de item...
                # Assurez-vous que les attributs comme item.is_text_item, item.text_item, item.image_path 
                # sont toujours accessibles directement sur l'objet 'item'.
                item_info = {
                    'type': 'grid_rectangle', 
                    'pos_x': item.pos().x(),
                    'pos_y': item.pos().y(),
                    'width': item.rect().width(),
                    'height': item.rect().height(),
                    'z_value': item.zValue()
                }

                if hasattr(item, 'is_text_item') and item.is_text_item:
                    item_info['item_subtype'] = 'text'
                    if hasattr(item, 'text_item') and item.text_item:
                        text_g_item = item.text_item
                        font = text_g_item.font()
                        doc_options = text_g_item.document().defaultTextOption()

                        item_info['text_content'] = text_g_item.toPlainText()
                        item_info['font_family'] = font.family()
                        item_info['font_size_pt'] = font.pointSize()
                        item_info['font_bold'] = font.bold()
                        item_info['font_italic'] = font.italic()
                        item_info['font_underline'] = font.underline()
                        item_info['text_color_rgba'] = text_g_item.defaultTextColor().rgba()
                        item_info['text_alignment'] = int(doc_options.alignment())

                        if hasattr(item, 'is_variable_item') and item.is_variable_item:
                            item_info['item_subtype'] = 'variable_text'
                
                elif hasattr(item, 'image_path') and item.image_path:
                    item_info['item_subtype'] = 'image'
                    item_info['image_path'] = item.image_path
                
                else:
                    item_info['item_subtype'] = 'simple_rectangle'

                items_data.append(item_info)

        logger.debug(f"{len(items_data)} items d'éditeur collectés pour la sauvegarde.")
        return items_data

    # --- Nouvelles méthodes pour la sélection de template ---
    def _populate_template_combobox(self):
        self.template_selection_combo.blockSignals(True)
        self.template_selection_combo.clear()

        initial_item_selected_for_handler = False
        selected_template_name_for_handler = None

        try:
            current_script_path = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
            templates_dir = os.path.join(project_root, "project_templates")

            if not os.path.exists(templates_dir):
                logger.warning(f"Le dossier des modèles '{templates_dir}' n'existe pas.")
                self.template_selection_combo.addItem("Dossier modèles absent")
            else:
                models = [f for f in os.listdir(templates_dir) if f.endswith(".json")]
                if not models:
                    logger.info(f"Aucun modèle trouvé dans '{templates_dir}'.")
                    self.template_selection_combo.addItem("Aucun modèle disponible")
                else:
                    for model_file in sorted(models):
                        self.template_selection_combo.addItem(model_file[:-5]) # Retirer .json
                    
                    if self.template_selection_combo.count() > 0:
                        # Vérifier que l'item à l'index 0 n'est pas un message d'erreur/info
                        first_item_text = self.template_selection_combo.itemText(0)
                        NON_MODEL_ITEMS_FOR_POPULATE = ["Aucun modèle disponible", "Dossier modèles absent", "Erreur chargement modèles"]
                        if first_item_text not in NON_MODEL_ITEMS_FOR_POPULATE:
                            self.template_selection_combo.setCurrentIndex(0)
                            selected_template_name_for_handler = self.template_selection_combo.currentText()
                            initial_item_selected_for_handler = True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles: {e}")
            self.template_selection_combo.addItem("Erreur chargement modèles")
        
        self.template_selection_combo.blockSignals(False)

        if initial_item_selected_for_handler and selected_template_name_for_handler:
            self._on_template_selected(selected_template_name_for_handler)
        elif self.template_selection_combo.count() > 0:
            self._on_template_selected(self.template_selection_combo.currentText())
        else: 
            self._clear_editor_and_params() # Si aucun modèle à sélectionner, effacer l'éditeur

    def _on_template_selected(self, template_name: str):
        NON_MODEL_ITEMS = ["Erreur chargement modèles", "Aucun modèle disponible", "Dossier modèles absent"]
        if template_name and template_name not in NON_MODEL_ITEMS:
            logger.info(f"Modèle sélectionné pour chargement: {template_name}.json")
            self._load_template_into_editor(template_name + ".json")
        else:
            logger.debug(f"Sélection de modèle réinitialisée ou invalide: {template_name}")
            self._clear_editor_and_params()

    def _load_template_into_editor(self, template_file_name_with_ext: str):
        try:
            current_script_path = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
            templates_dir = os.path.join(project_root, "project_templates")
            file_path = os.path.join(templates_dir, template_file_name_with_ext)

            if not os.path.exists(file_path):
                logger.error(f"Fichier modèle non trouvé: {file_path}")
                self._clear_editor_and_params()
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            logger.debug(f"Contenu brut du template JSON ('{template_file_name_with_ext}'): {template_data}")
            
            self._clear_editor_and_params() # Effacer avant de charger

            # 1. Charger les paramètres du Lamicoid
            params = template_data.get('lamicoid_parameters', {})
            logger.debug(f"Paramètres Lamicoid du JSON: {params}")
            
            # Utiliser les méthodes de conversion de LamicoidEditorWidget ou les globales si besoin.
            # Assumons ici que les méthodes mm_to_pixels sont accessibles via self.lamicoid_editor_widget
            # ou que les fonctions globales mm_to_pixels sont utilisées (ce qui est le cas ici).
            width_px_lam = mm_to_pixels(params.get('width_mm', 100.0))
            height_px_lam = mm_to_pixels(params.get('height_mm', 50.0))
            corner_radius_px_lam = mm_to_pixels(params.get('corner_radius_mm', 0.0))
            margin_px_lam = mm_to_pixels(params.get('margin_mm', 0.0))
            grid_spacing_px_lam = mm_to_pixels(params.get('grid_spacing_mm', 5.0))

            logger.debug(f"Conversion des paramètres Lamicoid en pixels: "
                         f"W={width_px_lam}, H={height_px_lam}, R={corner_radius_px_lam}, "
                         f"M={margin_px_lam}, Grid={grid_spacing_px_lam}")

            self.lamicoid_editor_widget.set_lamicoid_properties(
                width_px_lam, height_px_lam, corner_radius_px_lam, margin_px_lam, grid_spacing_px_lam
            )

            # 2. Charger les variables du projet
            self.project_variables = template_data.get('project_variables', [])
            self._update_variables_display()

            # 3. Charger les items de l'éditeur
            editor_items_data = template_data.get('editor_items', [])
            logger.debug(f"Nombre d'items à charger depuis le template: {len(editor_items_data)}")
            if self.lamicoid_editor_widget:
                for i, item_data in enumerate(editor_items_data):
                    logger.debug(f"Chargement item template #{i} - Données JSON brutes: {item_data}")
                    item_subtype = item_data.get('item_subtype', 'simple_rectangle') # rectangle, texte, image, variable_rectangle
                    
                    item_type_for_add = item_subtype # Valeur par défaut
                    if item_subtype == 'variable_text':
                        item_type_for_add = 'variable_rectangle'
                    elif item_subtype == 'simple_rectangle':
                        item_type_for_add = 'rectangle'
                    elif item_subtype == 'text': # Ajout de ce cas
                        item_type_for_add = 'texte'
                    # 'image' est déjà géré car item_type_for_add == item_subtype par défaut.
                    
                    # Les valeurs pos_x, pos_y, width, height du JSON sont déjà en PIXELS
                    pos_x_px = item_data.get('pos_x', 0.0)
                    pos_y_px = item_data.get('pos_y', 0.0)
                    width_px = item_data.get('width', 50.0)  # Valeur par défaut en pixels si absente
                    height_px = item_data.get('height', 30.0) # Valeur par défaut en pixels si absente
                    logger.debug(f"  Item #{i}: pos (px)=({pos_x_px}, {pos_y_px}), size (px)=({width_px}, {height_px})")

                    full_item_data = {
                        'pos': QPointF(pos_x_px, pos_y_px),       # En pixels
                        'size': QSizeF(width_px, height_px),     # En pixels
                        'z_value': item_data.get('z_value', 0)
                    }
                    if item_subtype == 'text' or item_subtype == 'variable_text':
                        full_item_data['text'] = item_data.get('text_content', 'Texte')
                        full_item_data['font_family'] = item_data.get('font_family', 'Arial')
                        full_item_data['font_size_pt'] = item_data.get('font_size_pt', 10)
                        full_item_data['font_bold'] = item_data.get('font_bold', False)
                        full_item_data['font_italic'] = item_data.get('font_italic', False)
                        full_item_data['font_underline'] = item_data.get('font_underline', False)
                        full_item_data['text_color_rgba'] = item_data.get('text_color_rgba') 
                        full_item_data['text_alignment'] = Qt.AlignmentFlag(item_data.get('text_alignment', Qt.AlignLeft))
                        if item_subtype == 'variable_text':
                            full_item_data['variable_name'] = item_data.get('text_content', 'VAR_NAME') 

                    elif item_subtype == 'image':
                        full_item_data['image_path'] = item_data.get('image_path')
                    
                    logger.debug(f"  Item #{i}: full_item_data préparé pour add_editor_item: {full_item_data}")
                    self.lamicoid_editor_widget.add_editor_item(
                        item_type_for_add, 
                        **full_item_data # Déballer full_item_data en arguments mot-clé
                    )

            logger.info(f"Modèle '{template_file_name_with_ext}' chargé dans l'éditeur (ou tentative).")
            # Assurer que l'éditeur est en mode non interactif après chargement si c'est un aperçu
            if self.mode_selection_combo.currentText() == "Lamicoid":
                 self.lamicoid_editor_widget.setInteractive(False)

        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON pour le modèle '{template_file_name_with_ext}': {e}")
            self._clear_editor_and_params()
        except Exception as e:
            logger.error(f"Erreur inattendue lors du chargement du modèle '{template_file_name_with_ext}' dans l'éditeur: {e}")
            self._clear_editor_and_params()

    def _clear_editor_and_params(self):
        if self.lamicoid_editor_widget:
            self.lamicoid_editor_widget.clear()
        
        # Réinitialiser les spinbox à des valeurs par défaut (optionnel)
        # self.width_spinbox.setValue(100.0)
        # self.height_spinbox.setValue(50.0)
        # ... autres spinboxes ...
        # self._update_lamicoid_editor_params() # Mettre à jour l'éditeur avec ces valeurs par défaut

        self.project_variables = []
        self._update_variables_display()
        logger.debug("Éditeur et paramètres réinitialisés.")
        
    def _update_editor_with_current_template(self):
        if self.template_selection_combo.count() > 0:
            current_template_name = self.template_selection_combo.currentText()
            self._on_template_selected(current_template_name)
        else:
            self._clear_editor_and_params()

    def _create_new_lamicoid_from_template(self):
        # ... existing code ...
        pass # Ajout pour corriger l'IndentationError

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    main_window = QWidget()
    layout = QVBoxLayout(main_window)
    lamicoid_page = LamicoidPage()
    layout.addWidget(lamicoid_page)
    main_window.setWindowTitle("Test LamicoidPage - Éditeur Simple")
    main_window.resize(900, 600)
    main_window.show()
    sys.exit(app.exec_()) 