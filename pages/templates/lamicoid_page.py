from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QScrollArea, QFormLayout, QDateEdit, 
                             QLineEdit, QSpinBox, QComboBox, QSizePolicy, QMessageBox,
                             QStackedWidget, QDialog, QDoubleSpinBox, QFileDialog, QGraphicsItem,
                             QColorDialog, QStyledItemDelegate, QStyle)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QStandardItemModel, QStandardItem
import logging

from ui.components.frame import Frame
from utils.signals import signals
from ui.editors.lamicoid_editor_widget import LamicoidEditorWidget
from utils.icon_loader import get_icon_path

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
        
        self._init_ui()
        self._connect_signals()
        self._apply_toolbar_styles()
        self._on_mode_selected(self.mode_selection_combo.currentText()) 
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
        type_lamicoid_label = QLabel("Action:")
        self.mode_selection_combo = QComboBox()
        self.mode_selection_combo.addItem("--- Sélectionner ---")
        self.mode_selection_combo.addItem("Nouveau Lamicoid")
        self.mode_selection_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        type_lamicoid_combo_layout.addWidget(type_lamicoid_label)
        type_lamicoid_combo_layout.addWidget(self.mode_selection_combo, 1)
        left_header_layout.addWidget(type_lamicoid_combo_container)
        
        left_panel = Frame(header_widget=left_header_widget, parent=self)
        left_panel.setFixedWidth(350)
        left_panel_content_layout = left_panel.get_content_layout()

        self.left_content_stack = QStackedWidget(self)

        self.lamicoid_params_frame = QFrame(self)
        self.lamicoid_params_frame.setObjectName("LamicoidParamsFrame")
        params_layout = QVBoxLayout(self.lamicoid_params_frame)
        params_layout.setContentsMargins(5,5,5,5)
        params_layout.setSpacing(8)

        params_form_layout = QFormLayout()
        params_form_layout.setSpacing(8)
        params_form_layout.setLabelAlignment(Qt.AlignLeft)

        self.width_spinbox = QDoubleSpinBox()
        self.width_spinbox.setSuffix(" mm")
        self.width_spinbox.setMinimum(10.0); self.width_spinbox.setMaximum(1000.0); self.width_spinbox.setValue(100.0)
        params_form_layout.addRow("Largeur:", self.width_spinbox)

        self.height_spinbox = QDoubleSpinBox()
        self.height_spinbox.setSuffix(" mm")
        self.height_spinbox.setMinimum(10.0); self.height_spinbox.setMaximum(1000.0); self.height_spinbox.setValue(50.0)
        params_form_layout.addRow("Hauteur:", self.height_spinbox)

        self.radius_spinbox = QDoubleSpinBox()
        self.radius_spinbox.setSuffix(" mm")
        self.radius_spinbox.setMinimum(0.0); self.radius_spinbox.setMaximum(50.0); self.radius_spinbox.setValue(2.0)
        params_form_layout.addRow("Rayon Coins:", self.radius_spinbox)

        self.margin_spinbox = QDoubleSpinBox()
        self.margin_spinbox.setSuffix(" mm")
        self.margin_spinbox.setMinimum(0.0); self.margin_spinbox.setMaximum(50.0); self.margin_spinbox.setValue(2.0)
        params_form_layout.addRow("Marge Intérieure:", self.margin_spinbox)

        self.grid_spacing_spinbox = QDoubleSpinBox()
        self.grid_spacing_spinbox.setSuffix(" mm")
        self.grid_spacing_spinbox.setMinimum(0.1); self.grid_spacing_spinbox.setMaximum(50.0); self.grid_spacing_spinbox.setValue(1.0)
        self.grid_spacing_spinbox.setSingleStep(0.1)
        self.grid_spacing_spinbox.setDecimals(1)
        params_form_layout.addRow("Espacement Grille:", self.grid_spacing_spinbox)

        params_layout.addLayout(params_form_layout)
        params_layout.addStretch(1)
        
        self.left_content_stack.addWidget(self.lamicoid_params_frame)

        self.left_placeholder_widget = QLabel("Sélectionnez une action.")
        self.left_placeholder_widget.setAlignment(Qt.AlignCenter)
        self.left_content_stack.addWidget(self.left_placeholder_widget)

        left_panel_content_layout.addWidget(self.left_content_stack)
        page_layout.addWidget(left_panel)

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
        self.mode_selection_combo.setCurrentIndex(0)
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

    def _on_mode_selected(self, selected_mode: str):
        logger.debug(f"Mode sélectionné: {selected_mode}")
        self._ensure_correct_view_for_mode(selected_mode)
        if selected_mode == "Nouveau Lamicoid":
            self._update_lamicoid_editor_params() 

    def _update_lamicoid_editor_params(self):
        if self.mode_selection_combo.currentText() == "Nouveau Lamicoid":
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
        if mode == "Nouveau Lamicoid":
            self.form_title_label.setText("Paramètres du Lamicoid")
            self.left_content_stack.setCurrentWidget(self.lamicoid_params_frame)
            self.right_panel_title_label.setText("Éditeur Visuel Lamicoid")
            self.right_display_stack.setCurrentWidget(self.lamicoid_editor_widget)
            
        elif mode == "--- Sélectionner ---":
            self.form_title_label.setText("Configuration Lamicoid")
            self.left_content_stack.setCurrentWidget(self.left_placeholder_widget)
            self.right_panel_title_label.setText("Éditeur Lamicoid")
            self.right_display_stack.setCurrentWidget(self.lamicoid_editor_widget) 
            
        else:
            self.form_title_label.setText("Configuration Lamicoid")
            self.left_content_stack.setCurrentWidget(self.left_placeholder_widget)
            self.right_panel_title_label.setText("Éditeur Lamicoid")
            self.right_display_stack.setCurrentWidget(self.lamicoid_editor_widget)

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