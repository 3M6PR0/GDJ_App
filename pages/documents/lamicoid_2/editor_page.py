"""Définit la page complète pour l'édition d'un lamicoid (template)."""

import logging
import uuid
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, QDoubleSpinBox, QLineEdit, QFormLayout, QGroupBox, QFontComboBox, QSpinBox, QButtonGroup, QComboBox, QStyledItemDelegate, QStyle, QStyleOptionComboBox, QFileDialog, QDialog
from PyQt5.QtCore import QSize, QTimer, Qt
from PyQt5.QtGui import QIcon, QFont, QPainter
from ui.components.frame import Frame # Importer le Frame personnalisé
from utils.icon_loader import get_icon_path
from .template_editor_view import TemplateEditorView
from models.documents.lamicoid_2.template_lamicoid import TemplateLamicoid
from models.documents.lamicoid_2.elements import ElementTexte, ElementImage
from .items.texte_item import TexteItem
from .image_selection_dialog import ImageSelectionDialog

logger = logging.getLogger('GDJ_App')

class CenteredIconDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        icon = index.data(Qt.DecorationRole)
        if isinstance(icon, QIcon):
            icon_size = QSize(24, 24)
            x = option.rect.x() + (option.rect.width() - icon_size.width()) // 2
            y = option.rect.y() + (option.rect.height() - icon_size.height()) // 2
            icon.paint(painter, option.rect.adjusted(x - option.rect.x(), y - option.rect.y(), -(option.rect.right() - (x + icon_size.width())), -(option.rect.bottom() - (y + icon_size.height()))))
        else:
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        return QSize(28, 28)

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
        self.selected_item = None  # Pour garder l'élément sélectionné (texte ou image)
        self.editor_toolbar = None
        self.text_style_container = None
        
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
        text_props_layout.addWidget(self.font_combo)

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

        # Boutons de rotation
        self.rotate_left_button = QPushButton(QIcon(get_icon_path("round_rotate_left.png")), "")
        self.rotate_left_button.setToolTip("Tourner à gauche")
        self.rotate_left_button.setVisible(False)
        editor_toolbar_layout.addWidget(self.rotate_left_button)

        self.rotate_right_button = QPushButton(QIcon(get_icon_path("round_rotate_right.png")), "")
        self.rotate_right_button.setToolTip("Tourner à droite")
        self.rotate_right_button.setVisible(False)
        editor_toolbar_layout.addWidget(self.rotate_right_button)

        # Conteneur pour les boutons de style texte
        self.text_style_container = QWidget(self.editor_toolbar)
        text_style_layout = QHBoxLayout(self.text_style_container)
        text_style_layout.setContentsMargins(0, 0, 0, 0)
        text_style_layout.setSpacing(2)

        # Bouton diminuer taille texte
        self.decrease_font_button = QPushButton(QIcon(get_icon_path("round_text_decrease.png")), "")
        self.decrease_font_button.setToolTip("Rétrécir le texte")
        text_style_layout.addWidget(self.decrease_font_button)

        # QSpinBox pour la taille du texte (bien placé dans text_style_layout)
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setObjectName("FontSizeSpinBox")
        self.font_size_spinbox.setRange(6, 200)
        self.font_size_spinbox.setFixedWidth(48)
        self.font_size_spinbox.setToolTip("Taille du texte")
        self.font_size_spinbox.setStyleSheet("""
            QSpinBox#FontSizeSpinBox::up-button,
            QSpinBox#FontSizeSpinBox::down-button {
                width: 0px;
                height: 0px;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        text_style_layout.addWidget(self.font_size_spinbox)

        # Bouton augmenter taille texte
        self.increase_font_button = QPushButton(QIcon(get_icon_path("round_text_increase.png")), "")
        self.increase_font_button.setToolTip("Agrandir le texte")
        text_style_layout.addWidget(self.increase_font_button)

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

        # Ajout du QComboBox pour l'alignement
        self.align_combo = QComboBox(self.text_style_container)
        self.align_combo.setObjectName("AlignCombo")
        self.align_combo.setFixedSize(QSize(28, 28))
        # Appliquer le délégué personnalisé à l'affichage principal
        self.align_combo.setItemDelegate(CenteredIconDelegate(self.align_combo))
        # Appliquer un délégué standard à la popup (liste déroulante)
        self.align_combo.view().setItemDelegate(QStyledItemDelegate(self.align_combo.view()))
        # Ajouter les options d'alignement avec leurs icônes
        align_options = [
            ("round_format_align_left.png", "Aligner à Gauche", Qt.AlignLeft),
            ("round_format_align_center.png", "Aligner au Centre", Qt.AlignCenter),
            ("round_format_align_right.png", "Aligner à Droite", Qt.AlignRight)
        ]
        for icon_file, tooltip, align_flag in align_options:
            icon_path = get_icon_path(icon_file)
            if icon_path:
                self.align_combo.addItem(QIcon(icon_path), "", align_flag)
                self.align_combo.setItemData(self.align_combo.count() - 1, tooltip, Qt.ToolTipRole)
        # Style du QComboBox (restaurer le style de la liste déroulante)
        self.align_combo.setStyleSheet("""
            QComboBox#AlignCombo {
                background-color: #4a4d4e;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 0px;
                text-align: center;
            }
            QComboBox#AlignCombo::drop-down {
                width: 0px;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QComboBox#AlignCombo::down-arrow {
                width: 0px;
                height: 0px;
                image: none;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QComboBox#AlignCombo QAbstractItemView {
                background-color: #4a4d4e;
                border: 1px solid #555;
                border-radius: 8px;
                selection-background-color: #007ACC;
                color: #ddeeff;
            }
            QComboBox#AlignCombo QAbstractItemView::item {
                padding: 0px;
                min-height: 28px;
                min-width: 28px;
            }
            QComboBox#AlignCombo QAbstractItemView::item:selected {
                background-color: #007ACC;
                color: #fff;
            }
        """)
        
        text_style_layout.addWidget(self.align_combo)

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

        # 3. Ajouter directement l'élément à la scène sans recréer complètement la vue
        self.editor_view.add_element_to_scene(new_element)

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
        
        # Mettre à jour la vue en recréant seulement le fond et la grille, pas les éléments
        self.editor_view.update_template_background()

    def _connect_signals(self):
        """Connecte les signaux des boutons."""
        # -- Signaux du formulaire de paramètres --
        self.name_input.textChanged.connect(self._update_template_properties)
        self.width_spinbox.valueChanged.connect(self._update_template_properties)
        self.height_spinbox.valueChanged.connect(self._update_template_properties)
        self.radius_spinbox.valueChanged.connect(self._update_template_properties)
        self.margin_spinbox.valueChanged.connect(self._update_template_properties)
        self.grid_spacing_spinbox.valueChanged.connect(self._update_template_properties)
        
        # -- Signaux des boutons de style texte --
        self.bold_button.clicked.connect(self._on_bold_clicked)
        self.italic_button.clicked.connect(self._on_italic_clicked)
        self.underline_button.clicked.connect(self._on_underline_clicked)
        self.align_combo.currentIndexChanged.connect(self._on_align_changed)
        self.decrease_font_button.clicked.connect(lambda: self._change_selected_text_size(-1))
        self.increase_font_button.clicked.connect(lambda: self._change_selected_text_size(1))
        self.font_size_spinbox.valueChanged.connect(self._set_selected_text_size)

        # -- Signaux des boutons d'ajout --
        self.add_text_button.clicked.connect(self._add_new_text_element)
        self.add_image_button.clicked.connect(self._on_add_image_clicked)

        # Connexion du signal de sélection de la scène
        self.editor_view.scene().selectionChanged.connect(self._update_ui_for_selection)

        # -- Signaux des boutons de rotation --
        self.rotate_left_button.clicked.connect(lambda: self._rotate_selected_item(-90))
        self.rotate_right_button.clicked.connect(lambda: self._rotate_selected_item(90))

    def showEvent(self, event):
        """Appelé lorsque le widget est affiché pour la première fois."""
        super().showEvent(event)
        if self._is_first_show:
            # La logique de zoom initial est maintenant gérée directement
            # par la TemplateEditorView elle-même. Cet appel n'est plus nécessaire.
            # QTimer.singleShot(0, self.editor_view.initial_view_setup)
            self._is_first_show = False 

    def _update_ui_for_selection(self):
        """Met à jour l'état de l'interface en fonction de la sélection actuelle."""
        selected_items = self.editor_view.scene().selectedItems()
        self.selected_item = selected_items[0] if selected_items else None

        has_selection = bool(selected_items)
        self.rotate_left_button.setVisible(has_selection)
        self.rotate_right_button.setVisible(has_selection)

        # Si rien n'est sélectionné, on s'assure que le panneau de texte est caché.
        if not has_selection:
            self.text_style_container.setVisible(False)
            return

        # Le panneau de texte n'est visible que si TOUS les éléments sélectionnés sont des textes.
        all_items_are_text = all(isinstance(item, TexteItem) for item in selected_items)
        self.text_style_container.setVisible(all_items_are_text)

        if all_items_are_text:
            # Baser l'état de l'UI sur le premier élément de texte
            first_text_item = selected_items[0]
            model = first_text_item.model_item

            self.bold_button.blockSignals(True)
            self.italic_button.blockSignals(True)
            self.underline_button.blockSignals(True)
            self.font_size_spinbox.blockSignals(True)
            self.align_combo.blockSignals(True)

            self.bold_button.setChecked(getattr(model, 'bold', False))
            self.italic_button.setChecked(getattr(model, 'italic', False))
            self.underline_button.setChecked(getattr(model, 'underline', False))
            self.font_size_spinbox.setValue(model.taille_police_pt)
            
            alignment = getattr(model, 'align', Qt.AlignLeft)
            for i in range(self.align_combo.count()):
                if self.align_combo.itemData(i) == alignment:
                    self.align_combo.setCurrentIndex(i)
                    break
            
            self.bold_button.blockSignals(False)
            self.italic_button.blockSignals(False)
            self.underline_button.blockSignals(False)
            self.font_size_spinbox.blockSignals(False)
            self.align_combo.blockSignals(False)

    def _on_bold_clicked(self):
        """Met en gras tous les éléments de texte sélectionnés."""
        is_checked = self.bold_button.isChecked()
        selected_items = self.editor_view.scene().selectedItems()
        for item in selected_items:
            if isinstance(item, TexteItem):
                item.model_item.bold = is_checked
                item.update()

    def _on_italic_clicked(self):
        """Met en italique tous les éléments de texte sélectionnés."""
        is_checked = self.italic_button.isChecked()
        selected_items = self.editor_view.scene().selectedItems()
        for item in selected_items:
            if isinstance(item, TexteItem):
                item.model_item.italic = is_checked
                item.update()

    def _on_underline_clicked(self):
        """Souligne tous les éléments de texte sélectionnés."""
        is_checked = self.underline_button.isChecked()
        selected_items = self.editor_view.scene().selectedItems()
        for item in selected_items:
            if isinstance(item, TexteItem):
                item.model_item.underline = is_checked
                item.update()

    def _on_align_changed(self, index):
        """Change l'alignement de tous les éléments de texte sélectionnés."""
        alignment = self.align_combo.itemData(index)
        selected_items = self.editor_view.scene().selectedItems()
        for item in selected_items:
            if isinstance(item, TexteItem):
                item.set_alignment(alignment)

    def _rotate_selected_item(self, angle):
        """Applique une rotation à tous les éléments sélectionnés."""
        selected_items = self.editor_view.scene().selectedItems()
        for item in selected_items:
            current_angle = item.rotation() if hasattr(item, 'rotation') else 0
            item.setRotation(current_angle + angle)

    def _change_selected_text_size(self, delta):
        """Change la taille de la police de tous les éléments de texte sélectionnés."""
        selected_items = self.editor_view.scene().selectedItems()
        # Si on ne change qu'un item, on peut se baser sur sa taille.
        # Sinon, on ne fait qu'incrémenter/décrémenter.
        new_size = None
        for item in selected_items:
            if isinstance(item, TexteItem):
                current_size = item.model_item.taille_police_pt
                new_size = max(6, min(200, current_size + delta))
                item.model_item.taille_police_pt = new_size
                item.update()
        
        # Mettre à jour le spinbox si une taille a été calculée
        if new_size is not None:
            self.font_size_spinbox.blockSignals(True)
            self.font_size_spinbox.setValue(new_size)
            self.font_size_spinbox.blockSignals(False)

    def _set_selected_text_size(self, value):
        """Définit la taille de la police pour tous les éléments de texte sélectionnés."""
        selected_items = self.editor_view.scene().selectedItems()
        for item in selected_items:
            if isinstance(item, TexteItem):
                item.model_item.taille_police_pt = value
                item.update()

    def _on_add_image_clicked(self):
        dialog = ImageSelectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            img_path = dialog.get_selected_image()
            print(f"[DEBUG] Image sélectionnée : {img_path}")
            if not self.current_template:
                print("[DEBUG] Aucun template courant, impossible d'ajouter l'image.")
                return
            # Taille par défaut de l'image (en mm)
            largeur_image = 20
            hauteur_image = 20
            x = self.current_template.largeur_mm / 2 - largeur_image / 2
            y = self.current_template.hauteur_mm / 2 - hauteur_image / 2
            new_image_element = ElementImage(
                element_id=str(uuid.uuid4()),
                chemin_fichier=img_path,
                largeur_mm=largeur_image,
                hauteur_mm=hauteur_image,
                x_mm=x,
                y_mm=y
            )
            new_image_element._just_added = True
            self.current_template.elements.append(new_image_element)
            
            # Ajouter directement l'élément à la scène sans recréer complètement la vue
            self.editor_view.add_element_to_scene(new_image_element)
            print("[DEBUG] Image ajoutée au template et vue rafraîchie.")
        else:
            print("[DEBUG] Dialog annulé ou fermé sans sélection") 