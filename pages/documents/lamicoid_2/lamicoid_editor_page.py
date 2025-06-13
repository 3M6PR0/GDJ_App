from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QFormLayout, QSizePolicy, QStackedWidget, QDialog, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QFontMetrics

from ui.components.frame import Frame
from .template_editor_view import TemplateEditorView # La nouvelle vue d'édition
from .feuille_lamicoid_view import FeuilleLamicoidView # La vue en feuille
from widgets.numeric_input_with_unit import NumericInputWithUnit
from utils.icon_loader import get_icon_path
from models.documents.lamicoid_2 import TemplateLamicoid
from models.documents.lamicoid_2.elements import ElementTexte, ElementVariable, ElementImage
from dialogs.existing_variables_dialog import ExistingVariablesDialog
from dialogs.variable_config_dialog import VariableConfigDialog
from utils.signals import signals
from .image_selection_dialog import ImageSelectionDialog

class LamicoidEditorPage(QWidget):
    """
    Page principale pour l'édition de documents Lamicoid v2.
    Combine les contrôles, la feuille d'items et l'éditeur visuel.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LamicoidEditorPage")
        
        self.project_variables = [] # Initialiser la liste
        self.current_template = TemplateLamicoid(template_id="virtual", nom_template="Édition en cours")
        self.imported_images = []  # Liste des chemins d'images importées
        
        self._init_ui()
        self._connect_signals()
        
        print("[DEBUG] État initial de la barre d'outils:")
        print(f"[DEBUG] editor_toolbar visible: {self.editor_toolbar.isVisible()}")
        print(f"[DEBUG] add_image_button visible: {self.add_image_button.isVisible()}")
        print(f"[DEBUG] add_image_button enabled: {self.add_image_button.isEnabled()}")
        print(f"[DEBUG] add_image_button isWidgetType: {self.add_image_button.isWidgetType()}")
        print(f"[DEBUG] add_image_button parent: {self.add_image_button.parent()}")
        
        self.left_content_stack.setCurrentWidget(self.lamicoid_params_frame)
        self.editor_toolbar.show() # Rendre visible par défaut
        self.editor_view.load_template_object(self.current_template) # Charger le template initial
        
    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # === PANNEAU DE GAUCHE ===
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel)

        # === PANNEAU CENTRAL (CONTENU PRINCIPAL) ===
        right_panel_container = self._create_right_panel()
        main_layout.addWidget(right_panel_container, 1) # Le 1 permet à ce panneau de s'étendre

    def _create_left_panel(self):
        """Crée et retourne le widget du panneau de gauche."""
        
        # Le header personnalisé pour le Frame
        left_header_widget = QWidget()
        left_header_widget.setObjectName("FrameHeaderContainer")
        left_header_layout = QVBoxLayout(left_header_widget)
        left_header_layout.setContentsMargins(0,0,0,0)
        
        title_label = QLabel("Configuration")
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setObjectName("CustomFrameTitle")
        left_header_layout.addWidget(title_label)
        
        # Le Frame principal pour le panneau de gauche
        left_panel = Frame(header_widget=left_header_widget, parent=self)
        left_panel.setFixedWidth(350)
        
        content_layout = left_panel.get_content_layout()
        content_layout.setSpacing(10)
        
        # --- Stack pour basculer entre les paramètres ---
        self.left_content_stack = QStackedWidget()
        
        # --- Panneau 1: Paramètres du Lamicoid ---
        self.lamicoid_params_frame = self._create_lamicoid_params_panel()
        self.left_content_stack.addWidget(self.lamicoid_params_frame)
        
        # --- Panneau 2: Paramètres de l'élément sélectionné ---
        self.element_params_frame = self._create_element_params_panel()
        self.left_content_stack.addWidget(self.element_params_frame)

        content_layout.addWidget(self.left_content_stack)
        
        return left_panel

    def _create_lamicoid_params_panel(self):
        """Crée le panneau de configuration des dimensions du lamicoid."""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5,5,5,5)
        layout.setSpacing(8)
        
        params_form_layout = QFormLayout()
        params_form_layout.setSpacing(8)
        params_form_layout.setLabelAlignment(Qt.AlignLeft)

        self.width_spinbox = NumericInputWithUnit(unit_text="mm", initial_value=self.current_template.largeur_mm, max_decimals=0)
        params_form_layout.addRow("Largeur:", self.width_spinbox)

        self.height_spinbox = NumericInputWithUnit(unit_text="mm", initial_value=self.current_template.hauteur_mm, max_decimals=0)
        params_form_layout.addRow("Hauteur:", self.height_spinbox)

        self.radius_spinbox = NumericInputWithUnit(unit_text="mm", initial_value=self.current_template.rayon_coin_mm, max_decimals=0)
        params_form_layout.addRow("Rayon Coins:", self.radius_spinbox)
        
        self.margin_spinbox = NumericInputWithUnit(unit_text="mm", initial_value=self.current_template.marge_mm, max_decimals=1)
        params_form_layout.addRow("Marge:", self.margin_spinbox)
        
        layout.addLayout(params_form_layout)
        layout.addStretch()
        return panel

    def _create_element_params_panel(self):
        """Crée le panneau (pour l'instant vide) pour les options de l'élément."""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        label = QLabel("Aucun élément sélectionné")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return panel

    def _create_right_panel(self):
        """Crée le conteneur du panneau de droite avec les barres d'outils et le QStackedWidget."""
        
        right_panel_container = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_container)
        right_panel_layout.setContentsMargins(0,0,0,0)
        right_panel_layout.setSpacing(10)
        
        # Barre d'outils du haut (Feuille / Éditeur)
        top_toolbar = self._create_right_top_toolbar()
        right_panel_layout.addWidget(top_toolbar)
        
        # Barre d'outils d'édition (Ajouter Texte, etc.)
        self.editor_toolbar = self._create_editor_toolbar()
        right_panel_layout.addWidget(self.editor_toolbar)
        
        self.view_stack = QStackedWidget()
        self.feuille_view = FeuilleLamicoidView()
        self.editor_view = TemplateEditorView()
        self.view_stack.addWidget(self.feuille_view)
        self.view_stack.addWidget(self.editor_view)
        
        right_panel_layout.addWidget(self.view_stack, 1)
        
        return right_panel_container

    def _create_right_top_toolbar(self):
        """Crée la barre d'outils pour basculer entre les vues."""
        toolbar = QFrame()
        toolbar.setObjectName("RightTopToolbar")
        toolbar.setFixedHeight(40)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5,5,5,5)
        toolbar_layout.setSpacing(10)
        
        self.switch_to_feuille_btn = QPushButton("Feuille")
        self.switch_to_feuille_btn.setCheckable(True)
        self.switch_to_feuille_btn.setChecked(True)
        
        self.switch_to_editor_btn = QPushButton("Éditeur")
        self.switch_to_editor_btn.setCheckable(True)
        
        toolbar_layout.addWidget(self.switch_to_feuille_btn)
        toolbar_layout.addWidget(self.switch_to_editor_btn)
        toolbar_layout.addStretch()
        
        return toolbar

    def _create_editor_toolbar(self):
        """Crée la barre d'outils d'édition (Ajouter Texte, etc.)."""
        print("[DEBUG] Création de la barre d'outils d'édition...")
        toolbar = QFrame()
        toolbar.setObjectName("EditorToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(8)

        print("[DEBUG] Création du bouton texte...")
        self.add_text_button = QPushButton(QIcon(get_icon_path("type.svg")), "")
        self.add_text_button.setToolTip("Ajouter un Texte")
        toolbar_layout.addWidget(self.add_text_button)

        print("[DEBUG] Suppression et recréation du bouton image...")
        try:
            del self.add_image_button
        except AttributeError:
            pass
        self.add_image_button = QPushButton()
        self.add_image_button.setIcon(QIcon(get_icon_path("image.svg")))
        self.add_image_button.setToolTip("Ajouter une Image")
        self.add_image_button.clicked.connect(lambda: print("[DEBUG] BOUTON IMAGE RECRÉÉ ET CLIQUÉ !!!!!!!!!!!"))
        toolbar_layout.addWidget(self.add_image_button)
        
        # Ajout des boutons d'édition de texte dans un conteneur à droite
        self.text_style_container = QWidget(toolbar)
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

        # Le conteneur est visible par défaut pour le test
        self.text_style_container.setVisible(True)

        # Ajout d'un bouton TEST pour vérifier le layout
        toolbar_layout.addWidget(self.text_style_container)
        toolbar_layout.addWidget(QPushButton("TEST"))
        toolbar_layout.addStretch(1)

        return toolbar

    def _connect_signals(self):
        """Connecte tous les signaux de la page."""
        # Connexions pour les paramètres du lamicoid
        self.width_spinbox.valueChanged.connect(self._on_lamicoid_params_changed)
        self.height_spinbox.valueChanged.connect(self._on_lamicoid_params_changed)
        self.radius_spinbox.valueChanged.connect(self._on_lamicoid_params_changed)
        self.margin_spinbox.valueChanged.connect(self._on_lamicoid_params_changed)
        
        # Connexions pour les boutons de la barre d'outils
        self.switch_to_feuille_btn.clicked.connect(lambda: self._on_switch_view("feuille"))
        self.switch_to_editor_btn.clicked.connect(lambda: self._on_switch_view("editor"))
        
        # Connexions pour les boutons d'ajout
        self.add_text_button.clicked.connect(self._add_text_item_to_editor)
        self.add_variable_button.clicked.connect(self._open_add_variable_dialog)
        self.add_image_button.clicked.connect(self._add_image_item_to_editor)
        
        # Connexions pour les options de texte
        self.bold_button.toggled.connect(self._apply_text_bold)
        self.italic_button.toggled.connect(self._apply_text_italic)
        self.underline_button.toggled.connect(self._apply_text_underline)
        
        # Se connecter au signal global qui met à jour les variables
        signals.variables_updated.connect(self.update_project_variables)
        self.editor_view.text_item_selected.connect(self._on_text_item_selected)

    def _on_lamicoid_params_changed(self):
        """Met à jour le template en mémoire et redessine l'éditeur."""
        if not self.current_template:
            return
            
        self.current_template.largeur_mm = self.width_spinbox.value()
        self.current_template.hauteur_mm = self.height_spinbox.value()
        self.current_template.rayon_coin_mm = self.radius_spinbox.value()
        self.current_template.marge_mm = self.margin_spinbox.value()
        
        # Demander à la vue de se redessiner avec le template mis à jour
        self.editor_view.update_template_view()

    def _on_switch_view(self, view_type):
        """Bascule entre la vue "Feuille" et la vue "Éditeur"."""
        self.view_stack.setCurrentWidget(self.editor_view if view_type == "editor" else self.feuille_view)
        self.editor_toolbar.setVisible(view_type == "editor")
        
        self.switch_to_editor_btn.setChecked(view_type == "editor")
        self.switch_to_feuille_btn.setChecked(view_type == "feuille")

    def update_project_variables(self, variables: list):
        """Met à jour la liste des variables du projet."""
        self.project_variables = variables
        # On pourrait aussi mettre à jour un affichage des variables ici si nécessaire

    def _open_add_variable_dialog(self):
        """Ouvre la boîte de dialogue pour choisir ou créer une variable."""
        # 'self.project_variables' est maintenant mis à jour par le signal
        dialog = ExistingVariablesDialog(self.project_variables, self)
        if dialog.exec_() == QDialog.Accepted:
            variable_data = dialog.getSelectedVariable()
            if variable_data:
                self._add_variable_item_to_editor(variable_data)

    def _add_variable_item_to_editor(self, variable_data: dict):
        """Ajoute un élément variable centré selon sa taille réelle."""
        if not self.current_template:
            return
        contenu = variable_data.get('name', 'N/A')
        police = "Arial"
        taille_pt = 12
        font = QFont(police, taille_pt)
        metrics = QFontMetrics(font)
        largeur_texte_px = metrics.horizontalAdvance(contenu)
        hauteur_texte_px = metrics.height()
        from pages.documents.lamicoid_2.template_editor_view import _pixels_to_mm
        largeur_texte_mm = _pixels_to_mm(largeur_texte_px)
        hauteur_texte_mm = _pixels_to_mm(hauteur_texte_px)
        x = self.current_template.largeur_mm / 2 - largeur_texte_mm / 2
        y = self.current_template.hauteur_mm / 2 - hauteur_texte_mm / 2
        new_variable_element = ElementTexte(
            contenu=contenu,
            nom_police=police,
            taille_police_pt=taille_pt,
            x_mm=x,
            y_mm=y
        )
        new_variable_element._just_added = True
        self.current_template.elements.append(new_variable_element)
        self.editor_view.update_template_view()

    def _add_text_item_to_editor(self):
        """Ajoute un nouvel élément texte centré selon sa taille réelle."""
        if not self.current_template:
            return
        # Définir les propriétés du texte
        contenu = "Nouveau Texte"
        police = "Arial"
        taille_pt = 12
        font = QFont(police, taille_pt)
        metrics = QFontMetrics(font)
        largeur_texte_px = metrics.horizontalAdvance(contenu)
        hauteur_texte_px = metrics.height()
        from pages.documents.lamicoid_2.template_editor_view import _pixels_to_mm
        largeur_texte_mm = _pixels_to_mm(largeur_texte_px)
        hauteur_texte_mm = _pixels_to_mm(hauteur_texte_px)
        x = self.current_template.largeur_mm / 2 - largeur_texte_mm / 2
        y = self.current_template.hauteur_mm / 2 - hauteur_texte_mm / 2
        new_text_element = ElementTexte(
            contenu=contenu,
            nom_police=police,
            taille_police_pt=taille_pt,
            x_mm=x,
            y_mm=y
        )
        new_text_element._just_added = True
        self.current_template.elements.append(new_text_element)
        self.editor_view.update_template_view()

    def _add_image_item_to_editor(self):
        print("[DEBUG] _add_image_item_to_editor appelée")
        if not self.current_template:
            print("[DEBUG] Pas de template courant")
            return
        print("[DEBUG] Ouverture du dialog ImageSelectionDialog...")
        dialog = ImageSelectionDialog(self.imported_images, self)
        if dialog.exec_() == QDialog.Accepted:
            img_path = dialog.get_selected_image()
            print(f"[DEBUG] Image sélectionnée : {img_path}")
            if img_path:
                largeur_image = 20
                hauteur_image = 20
                x = self.current_template.largeur_mm / 2 - largeur_image / 2
                y = self.current_template.hauteur_mm / 2 - hauteur_image / 2
                from models.documents.lamicoid_2.elements import ElementImage
                new_image_element = ElementImage(
                    chemin_fichier=img_path,
                    largeur_mm=largeur_image,
                    hauteur_mm=hauteur_image,
                    x_mm=x,
                    y_mm=y
                )
                new_image_element._just_added = True
                self.current_template.elements.append(new_image_element)
                self.editor_view.update_template_view()
        else:
            print("[DEBUG] Dialog annulé ou fermé sans sélection")

    def load_document(self, document_id: str):
        """Charge un document Lamicoid existant dans les vues."""
        self.feuille_view.load_document(document_id)
        pass
        
    def create_new_document(self):
        """Initialise la page pour un nouveau document vierge."""
        self.feuille_view.clear_view()
        self.editor_view.clear_view()
        pass

    def _on_text_item_selected(self, is_selected, item):
        print("SELECTION TEXTE", is_selected)
        self.editor_toolbar.show()
        self.text_style_container.setVisible(bool(is_selected))

    def _apply_text_bold(self, is_checked):
        self.editor_view.apply_text_bold(is_checked)

    def _apply_text_italic(self, is_checked):
        self.editor_view.apply_text_italic(is_checked)

    def _apply_text_underline(self, is_checked):
        self.editor_view.apply_text_underline(is_checked) 