import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDoubleSpinBox, QMessageBox
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from ui.components.frame import Frame
from controllers.documents.lamicoid_2 import TemplateController
from models.documents.lamicoid_2 import TemplateLamicoid

logger = logging.getLogger('GDJ_App')

class TemplatePropertiesView(QWidget):
    """
    Vue pour éditer les propriétés de base d'un TemplateLamicoid.
    """
    # Signal émis lorsque le template a été sauvegardé avec succès
    template_saved = pyqtSignal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TemplatePropertiesView")
        self.template_controller = TemplateController.get_instance()
        self.current_template: TemplateLamicoid | None = None
        
        self._setup_ui()
        self._connect_signals()
        self.set_enabled_state(False) # Désactivé par défaut
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Utilisation du Frame personnalisé pour la cohérence visuelle
        properties_frame = Frame(title="Propriétés du Template")
        form_layout = QFormLayout(properties_frame.get_content_widget())
        form_layout.setSpacing(10)
        
        # --- Création des champs du formulaire ---
        self.name_edit = QLineEdit()
        self.width_spinbox = QDoubleSpinBox()
        self.height_spinbox = QDoubleSpinBox()
        self.margin_spinbox = QDoubleSpinBox()
        self.radius_spinbox = QDoubleSpinBox()

        for spinbox in [self.width_spinbox, self.height_spinbox, self.margin_spinbox, self.radius_spinbox]:
            spinbox.setSuffix(" mm")
            spinbox.setDecimals(2)
            spinbox.setRange(0.0, 5000.0)
            spinbox.setSingleStep(0.5)

        # Ajout des champs au formulaire avec des labels stylés
        form_layout.addRow(self._create_form_label("Nom du template:"), self.name_edit)
        form_layout.addRow(self._create_form_label("Largeur:"), self.width_spinbox)
        form_layout.addRow(self._create_form_label("Hauteur:"), self.height_spinbox)
        form_layout.addRow(self._create_form_label("Marge:"), self.margin_spinbox)
        form_layout.addRow(self._create_form_label("Rayon des coins:"), self.radius_spinbox)
        
        main_layout.addWidget(properties_frame)
        
        # --- Bouton de sauvegarde ---
        self.save_button = QPushButton("Sauvegarder les modifications")
        # Utilisation du même style que les autres boutons importants
        self.save_button.setObjectName("TopNavButton") 
        main_layout.addWidget(self.save_button)
        main_layout.addStretch()

    def _create_form_label(self, text):
        """Helper pour créer un QLabel avec le bon style."""
        label = self.name_label = QLineEdit()
        label.setObjectName("FormLabel") # Respecte le style QSS
        return label

    def _connect_signals(self):
        self.save_button.clicked.connect(self._on_save_clicked)

    @pyqtSlot(str)
    def load_template(self, template_id: str):
        """Charge un template dans la vue pour l'édition."""
        if not template_id:
            self.current_template = None
            self.clear_fields()
            self.set_enabled_state(False)
            return

        self.current_template = self.template_controller.get_template_by_id(template_id)
        
        if self.current_template:
            self.name_edit.setText(self.current_template.nom_template)
            self.width_spinbox.setValue(self.current_template.largeur_mm)
            self.height_spinbox.setValue(self.current_template.hauteur_mm)
            self.margin_spinbox.setValue(self.current_template.marge_mm)
            self.radius_spinbox.setValue(self.current_template.rayon_coin_mm)
            self.set_enabled_state(True)
        else:
            logger.warning(f"Impossible de charger le template avec l'ID {template_id} dans la vue des propriétés.")
            self.clear_fields()
            self.set_enabled_state(False)

    def clear_fields(self):
        """Vide tous les champs du formulaire."""
        self.name_edit.clear()
        self.width_spinbox.setValue(0)
        self.height_spinbox.setValue(0)
        self.margin_spinbox.setValue(0)
        self.radius_spinbox.setValue(0)
        
    def set_enabled_state(self, enabled: bool):
        """Active ou désactive tous les contrôles de la vue."""
        self.name_edit.setEnabled(enabled)
        self.width_spinbox.setEnabled(enabled)
        self.height_spinbox.setEnabled(enabled)
        self.margin_spinbox.setEnabled(enabled)
        self.radius_spinbox.setEnabled(enabled)
        self.save_button.setEnabled(enabled)

    def _on_save_clicked(self):
        """Sauvegarde les modifications apportées au template."""
        if not self.current_template:
            return
            
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Nom invalide", "Le nom du template ne peut pas être vide.")
            return

        # Mettre à jour l'objet modèle avec les valeurs de l'interface
        self.current_template.nom_template = self.name_edit.text().strip()
        self.current_template.largeur_mm = self.width_spinbox.value()
        self.current_template.hauteur_mm = self.height_spinbox.value()
        self.current_template.marge_mm = self.margin_spinbox.value()
        self.current_template.rayon_coin_mm = self.radius_spinbox.value()
        
        # Utiliser le contrôleur pour sauvegarder
        self.template_controller.add_or_update_template(self.current_template)
        
        logger.info(f"Template '{self.current_template.nom_template}' sauvegardé.")
        QMessageBox.information(self, "Sauvegardé", f"Le template '{self.current_template.nom_template}' a été sauvegardé avec succès.")
        
        # Émettre un signal pour que d'autres parties de l'UI puissent se mettre à jour
        self.template_saved.emit(self.current_template.template_id) 