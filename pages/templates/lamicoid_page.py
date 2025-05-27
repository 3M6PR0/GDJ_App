from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QScrollArea, QFormLayout, QDateEdit, 
                             QLineEdit, QSpinBox, QComboBox, QSizePolicy, QMessageBox,
                             QStackedWidget, QDialog, QDoubleSpinBox, QFileDialog)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont
import logging

from ui.components.frame import Frame
from utils.signals import signals
from ui.editors.lamicoid_editor_widget import LamicoidEditorWidget

logger = logging.getLogger('GDJ_App')

# Conversion (peut être déplacé dans un fichier utils plus tard)
DEFAULT_DPI = 96.0
INCH_TO_MM = 25.4

def mm_to_pixels(mm: float, dpi: float = DEFAULT_DPI) -> float:
    return (mm / INCH_TO_MM) * dpi

def pixels_to_mm(pixels: float, dpi: float = DEFAULT_DPI) -> float:
    return (pixels / dpi) * INCH_TO_MM

class LamicoidPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LamicoidPage")
        
        self._init_ui()
        self._connect_signals()
        self._on_mode_selected(self.mode_selection_combo.currentText()) 
        logger.debug(f"LamicoidPage initialisée.")

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
        self.radius_spinbox.setMinimum(0.0); self.radius_spinbox.setMaximum(50.0); self.radius_spinbox.setValue(5.0)
        params_form_layout.addRow("Rayon Coins:", self.radius_spinbox)

        self.margin_spinbox = QDoubleSpinBox()
        self.margin_spinbox.setSuffix(" mm")
        self.margin_spinbox.setMinimum(0.0); self.margin_spinbox.setMaximum(50.0); self.margin_spinbox.setValue(5.0)
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

        self.add_text_button = QPushButton("Texte")
        # add_icon = self.style().standardIcon(QStyle.SP_FileIcon) # Exemple d'icône
        # self.add_text_button.setIcon(add_icon)
        editor_toolbar_layout.addWidget(self.add_text_button)

        self.add_rect_button = QPushButton("Rectangle")
        editor_toolbar_layout.addWidget(self.add_rect_button)

        self.add_image_button = QPushButton("Image")
        editor_toolbar_layout.addWidget(self.add_image_button)

        editor_toolbar_layout.addStretch() # Pousse les boutons à gauche
        
        right_panel_content_layout.addWidget(self.editor_toolbar) # AJOUTÉ AVANT LE STACK
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