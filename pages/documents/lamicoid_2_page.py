# pages/documents/lamicoid_2_page.py
"""Définit la page principale pour la gestion des documents Lamicoid v2."""

import logging
import uuid
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QPushButton, QFrame, QLineEdit, QListWidget)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon
from typing import Dict, Optional

from ui.components.frame import Frame
from controllers.documents.lamicoid_2.template_controller import TemplateController
from models.documents.lamicoid_2.template_lamicoid import TemplateLamicoid
from models.documents.lamicoid_2.lamicoid import Lamicoid
from models.documents.lamicoid_2.feuille_lamicoid import FeuilleLamicoid, LamicoidPositionne
from models.documents.lamicoid_2.elements import ElementVariable

from .lamicoid_2.feuille_lamicoid_view import FeuilleLamicoidView
from utils.icon_loader import get_icon_path

logger = logging.getLogger('GDJ_App')

class Lamicoid2Page(QWidget):
    """
    Page principale pour la création et la gestion d'un document Lamicoid v2.
    Dispose d'un panneau de configuration à gauche et d'un éditeur de feuille à droite.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Lamicoid2Page")
        logger.info("Initialisation de Lamicoid2Page.")
        
        self.template_controller = TemplateController.get_instance()
        self.variable_inputs: Dict[str, QLineEdit] = {}
        self.selected_template: Optional[TemplateLamicoid] = None
        self.feuille_lamicoid = FeuilleLamicoid(largeur_feuille_mm=600, hauteur_feuille_mm=300)
        self._is_first_show = True
        
        self._init_ui()
        self._connect_signals()
        
        self._populate_template_combobox()
        self.feuille_view.display_feuille(self.feuille_lamicoid)

    def showEvent(self, event):
        """Appelé lorsque le widget est affiché."""
        super().showEvent(event)
        if self._is_first_show:
            QTimer.singleShot(0, self.feuille_view.zoom_to_fit)
            self._is_first_show = False

    def _init_ui(self):
        """Initialise l'interface utilisateur principale avec deux panneaux personnalisés."""
        page_layout = QHBoxLayout(self)
        page_layout.setContentsMargins(10, 10, 10, 10)
        page_layout.setSpacing(10)

        # 1. Panneau de gauche pour la configuration
        left_header_widget = QLabel("Configuration Lamicoid v2")
        left_header_widget.setObjectName("CustomFrameTitle")
        left_panel = Frame(header_widget=left_header_widget, parent=self)
        left_panel.setFixedWidth(350)
        left_panel_content_layout = left_panel.get_content_layout()

        # ComboBox pour la sélection de modèle
        template_selection_label = QLabel("Sélectionner un modèle:")
        self.template_combobox = QComboBox()
        left_panel_content_layout.addWidget(template_selection_label)
        left_panel_content_layout.addWidget(self.template_combobox)
        
        # Zone pour les champs de variables dynamiques
        self.variables_frame = QFrame(self) # C'est un sous-cadre, QFrame est ok ici
        self.variables_frame.setObjectName("VariablesFrame")
        self.variables_frame.setFrameShape(QFrame.StyledPanel)
        self.variables_layout = QVBoxLayout(self.variables_frame)
        self.variables_layout.setContentsMargins(5, 5, 5, 5)
        
        self.variables_placeholder = QLabel("Sélectionnez un modèle pour voir ses variables.")
        self.variables_layout.addWidget(self.variables_placeholder)
        
        left_panel_content_layout.addWidget(self.variables_frame)
        
        # Bouton pour créer l'instance du lamicoid
        self.add_lamicoid_button = QPushButton("Ajouter à la feuille")
        left_panel_content_layout.addWidget(self.add_lamicoid_button)

        left_panel_content_layout.addStretch(1)

        # Bouton pour gérer les templates
        self.manage_templates_button = QPushButton("Gérer les modèles")
        left_panel_content_layout.addWidget(self.manage_templates_button)
        
        # 2. Panneau de droite pour l'éditeur de la feuille
        right_header_widget = QLabel("Feuille de Lamicoids")
        right_header_widget.setObjectName("CustomFrameTitle")
        right_panel = Frame(header_widget=right_header_widget, parent=self)
        right_panel_content_layout = right_panel.get_content_layout()

        # Barre d'outils pour le zoom
        toolbar_layout = QHBoxLayout()
        self.zoom_in_button = QPushButton()
        self.zoom_in_button.setIcon(QIcon(get_icon_path("round_zoom_in.png")))
        self.zoom_in_button.setIconSize(QSize(24, 24))
        
        self.zoom_out_button = QPushButton()
        self.zoom_out_button.setIcon(QIcon(get_icon_path("round_zoom_out.png")))
        self.zoom_out_button.setIconSize(QSize(24, 24))

        self.zoom_to_fit_button = QPushButton()
        self.zoom_to_fit_button.setIcon(QIcon(get_icon_path("round_fit_screen.png")))
        self.zoom_to_fit_button.setIconSize(QSize(24, 24))

        toolbar_layout.addWidget(self.zoom_in_button)
        toolbar_layout.addWidget(self.zoom_out_button)
        toolbar_layout.addWidget(self.zoom_to_fit_button)

        # Séparateur vertical
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        toolbar_layout.addWidget(separator)

        # ComboBox pour la couleur de la feuille
        toolbar_layout.addWidget(QLabel("Couleur feuille:"))
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Gris", "Rouge", "Bleu", "Vert", "Jaune", "Blanc", "Noir"])
        toolbar_layout.addWidget(self.color_combo)
        
        toolbar_layout.addStretch()
        right_panel_content_layout.addLayout(toolbar_layout)

        self.feuille_view = FeuilleLamicoidView(self)
        right_panel_content_layout.addWidget(self.feuille_view)

        # Ajout des panneaux au layout principal
        page_layout.addWidget(left_panel)
        page_layout.addWidget(right_panel, 1) # Le panneau de droite prend l'espace restant

    def _connect_signals(self):
        """Connecte les signaux des widgets de la page."""
        self.manage_templates_button.clicked.connect(self._open_template_manager)
        self.template_combobox.currentTextChanged.connect(self._on_template_selected)
        self.add_lamicoid_button.clicked.connect(self._create_lamicoid_instance)
        self.zoom_in_button.clicked.connect(self.feuille_view.zoom_in)
        self.zoom_out_button.clicked.connect(self.feuille_view.zoom_out)
        self.zoom_to_fit_button.clicked.connect(self.feuille_view.zoom_to_fit)
        self.color_combo.currentTextChanged.connect(self.feuille_view.set_sheet_color)

    def _populate_template_combobox(self):
        """Peuple le ComboBox avec les noms des modèles disponibles."""
        try:
            self.template_combobox.clear()
            templates = self.template_controller.get_all_templates()
            template_names = [t.nom_template for t in templates]

            if not template_names:
                self.template_combobox.addItem("Aucun modèle trouvé")
                self.template_combobox.setEnabled(False)
            else:
                self.template_combobox.addItem("-- Choisissez un modèle --")
                self.template_combobox.addItems(template_names)
                self.template_combobox.setEnabled(True)
            logger.info(f"{len(template_names)} modèles de lamicoid chargés dans le ComboBox.")
        except Exception as e:
            logger.error(f"Erreur lors du peuplement du ComboBox des modèles: {e}", exc_info=True)
            self.template_combobox.clear()
            self.template_combobox.addItem("Erreur de chargement")
            self.template_combobox.setEnabled(False)

    def _on_template_selected(self, template_name: str):
        """Appelé lorsqu'un utilisateur sélectionne un modèle dans le ComboBox."""
        self._clear_variables_frame()
        self.selected_template = None

        if template_name == "-- Choisissez un modèle --" or not template_name:
            self.variables_placeholder.setVisible(True)
            logger.debug("Aucun modèle sélectionné.")
            return

        try:
            # Note: `get_template_by_name` n'existe pas, nous devons itérer
            templates = self.template_controller.get_all_templates()
            template = next((t for t in templates if t.nom_template == template_name), None)
            
            if template:
                self.selected_template = template
                logger.info(f"Modèle '{template.nom_template}' sélectionné.")
                self._display_variables_for_template(template)
            else:
                logger.warning(f"Le modèle nommé '{template_name}' n'a pas pu être trouvé.")
                self.variables_placeholder.setVisible(True)
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du modèle '{template_name}': {e}", exc_info=True)
            self.variables_placeholder.setVisible(True)

    def _display_variables_for_template(self, template):
        """Peuple le frame de gauche avec les champs des variables du template."""
        self._clear_variables_frame()
        
        variable_elements = [elem for elem in template.elements if isinstance(elem, ElementVariable)]
        
        if not variable_elements:
            self.variables_placeholder.setText("Ce modèle n'a pas de variables.")
            self.variables_placeholder.setVisible(True)
            return

        self.variables_placeholder.setVisible(False)
        for var_element in variable_elements:
            label = QLabel(f"{var_element.label_descriptif}:")
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(var_element.valeur_par_defaut)
            self.variable_inputs[var_element.nom_variable] = line_edit
            self.variables_layout.addWidget(label)
            self.variables_layout.addWidget(line_edit)

    def _clear_variables_frame(self):
        """Vide tous les widgets du layout des variables."""
        self.variable_inputs.clear()
        # Vider le layout en supprimant les widgets
        while self.variables_layout.count():
            child = self.variables_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Recréer et ajouter le placeholder
        self.variables_placeholder = QLabel("Sélectionnez un modèle pour voir ses variables.")
        self.variables_layout.addWidget(self.variables_placeholder)
        self.variables_placeholder.setVisible(True)

    def _create_lamicoid_instance(self):
        """Crée une instance de Lamicoid et l'ajoute à la feuille."""
        if not self.selected_template:
            logger.warning("Tentative de création d'un lamicoid sans modèle sélectionné.")
            return
            
        variable_values = {
            var_name: line_edit.text() or line_edit.placeholderText()
            for var_name, line_edit in self.variable_inputs.items()
        }
            
        new_lamicoid = Lamicoid(
            instance_id=str(uuid.uuid4()),
            template_id=self.selected_template.template_id,
            valeurs_variables=variable_values
        )

        # Pour l'instant, on l'ajoute en (0,0)
        lamicoid_positionne = LamicoidPositionne(
            lamicoid=new_lamicoid,
            position_x_mm=0,
            position_y_mm=0
        )
        
        self.feuille_lamicoid.lamicoids_sur_feuille.append(lamicoid_positionne)
        logger.info(f"Nouveau lamicoid (ID: {new_lamicoid.instance_id}) ajouté à la feuille. Total: {len(self.feuille_lamicoid.lamicoids_sur_feuille)}")
        
        # Redessiner la feuille pour afficher le nouvel item
        self.feuille_view.display_feuille(self.feuille_lamicoid)

    def _open_template_manager(self):
        """Ouvre la fenêtre de gestion des templates."""
        # Pour l'instant, on ne fait rien ici pour éviter les dépendances circulaires
        # ou des importations complexes. Cela sera géré plus tard.
        logger.info("Ouverture du gestionnaire de templates demandée (non implémenté).")
        # --- CODE DE DIALOGUE TEMPORAIREMENT DESACTIVE ---
        # try:
        #     from pages.templates.Lamicoid.template_management_page import TemplateManagementPage
        #     dialog = QDialog(self)
        #     dialog.setWindowTitle("Gestion des Modèles de Lamicoid")
        #     dialog.setMinimumSize(1000, 700)
            
        #     layout = QVBoxLayout(dialog)
        #     template_page = TemplateManagementPage()
        #     layout.addWidget(template_page)
            
        #     dialog.exec_()
        #     logger.info("Fenêtre de gestion des templates fermée.")
            
        #     self._populate_template_combobox()
        # except Exception as e:
        #     logger.error(f"Erreur lors de l'ouverture du gestionnaire de templates: {e}", exc_info=True)

    def get_document_data(self):
        """Méthode pour que la fenêtre parente puisse récupérer les données."""
        return {"type": "Lamicoid 2", "content": "Données à définir"} 