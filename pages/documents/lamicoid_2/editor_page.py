"""Définit la page complète pour l'édition d'un lamicoid (template)."""

import logging
import uuid
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, QDoubleSpinBox, QLineEdit, QFormLayout, QGroupBox, QFontComboBox, QSpinBox, QButtonGroup
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QIcon, QFont
from ui.components.frame import Frame # Importer le Frame personnalisé
from utils.icon_loader import get_icon_path
from .template_editor_view import TemplateEditorView
from models.documents.lamicoid_2.template_lamicoid import TemplateLamicoid
from models.documents.lamicoid_2.elements import ElementTexte
from .items.texte_item import TexteItem

logger = logging.getLogger('GDJ_App')

class EditorPage(QWidget):
    """
    Page contenant un panneau de configuration à gauche et
    l'éditeur de template à droite, utilisant des Frames personnalisées.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        print("[DEBUG] CONSTRUCTEUR EditorPage appelé !")
        self.setObjectName("LamicoidEditorPage")
        self.current_template = None
        self._is_first_show = True
        self.selected_text_item = None  # Pour garder l'élément texte sélectionné
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Barre de boutons supérieure
        button_bar = QHBoxLayout()
        self.save_button = QPushButton("Enregistrer")
        self.cancel_button = QPushButton("Annuler")
        button_bar.addStretch(1)
        button_bar.addWidget(self.cancel_button)
        button_bar.addWidget(self.save_button)
        main_layout.addLayout(button_bar)
        
        # Zone de contenu principale (avec les deux panneaux)
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout, 1)

        # PANNEAU DE GAUCHE
        left_header = QLabel("Nouveau Modèle")
        left_header.setObjectName("CustomFrameTitle")
        left_panel = Frame(header_widget=left_header, parent=self)
        left_panel.setFixedWidth(350)
        left_panel_layout = left_panel.get_content_layout()

        # -- Groupe 1: Paramètres du Modèle --
        params_groupbox = QGroupBox("Paramètres du Modèle")
        form_layout = QFormLayout()
        self.name_input = QLineEdit("Nouveau Modèle")
        self.width_spinbox = QDoubleSpinBox()
        self.width_spinbox.setRange(1, 2000)
        self.width_spinbox.setSuffix(" mm")
        self.width_spinbox.setValue(100.0)
        self.height_spinbox = QDoubleSpinBox()
        self.height_spinbox.setRange(1, 2000)
        self.height_spinbox.setSuffix(" mm")
        self.height_spinbox.setValue(50.0)
        self.radius_spinbox = QDoubleSpinBox()
        self.radius_spinbox.setRange(0, 100)
        self.radius_spinbox.setSuffix(" mm")
        self.radius_spinbox.setValue(2.0)
        self.margin_spinbox = QDoubleSpinBox()
        self.margin_spinbox.setRange(0, 100)
        self.margin_spinbox.setSuffix(" mm")
        self.margin_spinbox.setValue(2.0)
        self.grid_spacing_spinbox = QDoubleSpinBox()
        self.grid_spacing_spinbox.setRange(0.1, 10)
        self.grid_spacing_spinbox.setSuffix(" mm")
        self.grid_spacing_spinbox.setValue(1.0)
        form_layout.addRow("Nom:", self.name_input)
        form_layout.addRow("Largeur:", self.width_spinbox)
        form_layout.addRow("Hauteur:", self.height_spinbox)
        form_layout.addRow("Rayon Coins:", self.radius_spinbox)
        form_layout.addRow("Marge:", self.margin_spinbox)
        form_layout.addRow("Espacement Grille:", self.grid_spacing_spinbox)
        params_groupbox.setLayout(form_layout)

        # -- Groupe 2: Variables --
        variables_groupbox = QGroupBox("Variables")
        variables_layout = QVBoxLayout()
        variables_layout.addWidget(QLabel("test: Valeur personnalisable"))
        variables_groupbox.setLayout(variables_layout)

        # -- Groupe 3: Propriétés du Texte (initialement caché) --
        self.text_properties_groupbox = QGroupBox("Propriétés du Texte")
        text_props_layout = QVBoxLayout()
        self.font_combo = QFontComboBox()
        self.font_size_spinbox = QSpinBox()
        self.text_properties_groupbox.setLayout(text_props_layout)
        self.text_properties_groupbox.setVisible(False) # Caché par défaut

        # -- Boutons d'action en bas --
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addWidget(QPushButton("Effacer"))
        bottom_buttons_layout.addWidget(QPushButton("Insérer Img"))
        bottom_buttons_layout.addWidget(QPushButton("Test Epilog"))
        bottom_buttons_layout.addWidget(QPushButton("Enr. Lam."))
        bottom_buttons_layout.addWidget(QPushButton("OK/Texte"))

        left_panel_layout.addWidget(params_groupbox)
        left_panel_layout.addWidget(variables_groupbox)
        left_panel_layout.addWidget(self.text_properties_groupbox)
        left_panel_layout.addStretch(1)
        left_panel_layout.addLayout(bottom_buttons_layout)

        # Panneau de droite avec Frame personnalisé
        right_header = QLabel("Éditeur Modèle")
        right_header.setObjectName("CustomFrameTitle")
        right_panel = Frame(header_widget=right_header, parent=self)
        right_panel_layout = right_panel.get_content_layout()
        
        # -- Barre d'outils de l'éditeur --
        self.editor_toolbar = QFrame()
        self.editor_toolbar.setObjectName("EditorToolbar")
        self.editor_toolbar.setFixedHeight(60)  # Force une hauteur visible
        editor_toolbar_layout = QHBoxLayout(self.editor_toolbar)
        editor_toolbar_layout.setContentsMargins(5, 5, 5, 5)
        editor_toolbar_layout.setSpacing(5)

        # Boutons d'ajout
        self.add_text_button = QPushButton(QIcon(get_icon_path("round_abc.png")), "")
        self.add_image_button = QPushButton(QIcon(get_icon_path("round_image.png")), "")
        editor_toolbar_layout.addWidget(self.add_text_button)
        editor_toolbar_layout.addWidget(self.add_image_button)

        # Conteneur pour les boutons de style texte
        self.text_style_container = QWidget(self.editor_toolbar)
        text_style_layout = QHBoxLayout(self.text_style_container)
        text_style_layout.setContentsMargins(0, 0, 0, 0)
        text_style_layout.setSpacing(2)

        self.bold_button = QPushButton(QIcon(get_icon_path("round_format_bold.png")), "", self.text_style_container)
        self.bold_button.setToolTip("Gras")
        self.bold_button.setCheckable(True)
        text_style_layout.addWidget(self.bold_button)

        self.italic_button = QPushButton(QIcon(get_icon_path("round_format_italic.png")), "", self.text_style_container)
        self.italic_button.setToolTip("Italique")
        self.italic_button.setCheckable(True)
        text_style_layout.addWidget(self.italic_button)

        self.underline_button = QPushButton(QIcon(get_icon_path("round_format_underlined.png")), "", self.text_style_container)
        self.underline_button.setToolTip("Souligné")
        self.underline_button.setCheckable(True)
        text_style_layout.addWidget(self.underline_button)

        self.text_style_container.setVisible(False)  # Masqué par défaut
        editor_toolbar_layout.addWidget(self.text_style_container)
        editor_toolbar_layout.addStretch()

        right_panel_layout.addWidget(self.editor_toolbar)

        self.editor_view = TemplateEditorView()
        right_panel_layout.addWidget(self.editor_view)

        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel, 1)

        self._connect_signals()

        # Appliquer le style QSS directement
        button_size = 28
        qss = f"""
            QFrame#EditorToolbar QPushButton {{
                min-width: {button_size}px;
                max-width: {button_size}px;
                min-height: {button_size}px;
                max-height: {button_size}px;
                background-color: #4a4d4e;
                border: 1px solid #555;
                border-radius: 8px;
                color: #ddeeff;
            }}
            QFrame#EditorToolbar QPushButton:hover {{
                background-color: #5a5d5e;
                border: 1px solid #666;
            }}
            QFrame#EditorToolbar QPushButton:pressed {{
                background-color: #3a3d3e;
            }}
            QFrame#EditorToolbar QPushButton:checked {{
                background-color: #007ACC;
                border: 1px solid #005C9C;
            }}
        """
        self.editor_toolbar.setStyleSheet(qss)

    def _add_new_text_element(self):
        """Ajoute un nouvel élément de texte au template et met à jour la vue."""
        if not self.current_template:
            return

        # 1. Créer le modèle de données
        new_element = ElementTexte(
            element_id=str(uuid.uuid4()),
            x_mm=self.current_template.largeur_mm / 2,
            y_mm=self.current_template.hauteur_mm / 2,
            contenu="Texte",
            nom_police="Arial",
            taille_police_pt=12
        )

        # 2. L'ajouter à la liste d'éléments du template
        self.current_template.elements.append(new_element)

        # 3. Demander à la vue de se redessiner complètement
        self.editor_view.load_template_object(self.current_template)

    def set_template(self, template: TemplateLamicoid):
        """Reçoit le template à éditer et met à jour l'UI."""
        self.current_template = template
        self.editor_view.load_template_object(template)
        
        # Mettre à jour les champs du panneau de gauche
        self.name_input.setText(template.nom_template)
        self.width_spinbox.setValue(template.largeur_mm)
        self.height_spinbox.setValue(template.hauteur_mm)
        self.radius_spinbox.setValue(template.rayon_coin_mm)
        self.margin_spinbox.setValue(template.marge_mm)
        self.grid_spacing_spinbox.setValue(template.espacement_grille_mm)

    def _update_template_properties(self):
        """Met à jour les propriétés du template à partir des champs de l'UI."""
        if not self.current_template:
            return

        self.current_template.nom_template = self.name_input.text()
        self.current_template.largeur_mm = self.width_spinbox.value()
        self.current_template.hauteur_mm = self.height_spinbox.value()
        self.current_template.rayon_coin_mm = self.radius_spinbox.value()
        self.current_template.marge_mm = self.margin_spinbox.value()
        self.current_template.espacement_grille_mm = self.grid_spacing_spinbox.value()
        
        self.editor_view.load_template_object(self.current_template)

    def _connect_signals(self):
        """Connecte les signaux des boutons."""
        # -- Signaux du formulaire de paramètres --
        self.name_input.textChanged.connect(self._update_template_properties)
        self.width_spinbox.valueChanged.connect(self._update_template_properties)
        self.height_spinbox.valueChanged.connect(self._update_template_properties)
        self.radius_spinbox.valueChanged.connect(self._update_template_properties)
        self.margin_spinbox.valueChanged.connect(self._update_template_properties)
        self.grid_spacing_spinbox.valueChanged.connect(self._update_template_properties)
        
        # -- Signaux de la barre d'outils --
        self.add_text_button.clicked.connect(self._add_new_text_element)

        # Connexion du signal de sélection d'un texte
        self.editor_view.text_item_selected.connect(self._on_text_item_selected)

        self.bold_button.clicked.connect(self._on_bold_clicked)
        self.italic_button.clicked.connect(self._on_italic_clicked)
        self.underline_button.clicked.connect(self._on_underline_clicked)

    def showEvent(self, event):
        """Appelé lorsque le widget est affiché pour la première fois."""
        super().showEvent(event)
        if self._is_first_show:
            # La logique de zoom initial est maintenant gérée directement
            # par la TemplateEditorView elle-même. Cet appel n'est plus nécessaire.
            # QTimer.singleShot(0, self.editor_view.initial_view_setup)
            self._is_first_show = False 

    def _on_text_item_selected(self, is_selected, item):
        self.text_style_container.setVisible(bool(is_selected))
        self.selected_text_item = item if is_selected else None

    def _on_bold_clicked(self):
        if self.selected_text_item:
            font = self.selected_text_item.model_item.nom_police
            size = self.selected_text_item.model_item.taille_police_pt
            qfont = QFont(font, size)
            qfont.setBold(self.bold_button.isChecked())
            qfont.setItalic(self.italic_button.isChecked())
            qfont.setUnderline(self.underline_button.isChecked())
            self.selected_text_item.model_item.nom_police = qfont.family()
            self.selected_text_item.model_item.taille_police_pt = qfont.pointSize()
            self.selected_text_item.model_item.bold = self.bold_button.isChecked()
            self.selected_text_item.model_item.italic = self.italic_button.isChecked()
            self.selected_text_item.model_item.underline = self.underline_button.isChecked()
            self.selected_text_item.update()

    def _on_italic_clicked(self):
        self._on_bold_clicked()

    def _on_underline_clicked(self):
        self._on_bold_clicked() 