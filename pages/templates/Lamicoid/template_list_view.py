from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QAbstractItemView, QListWidgetItem, QInputDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt
import logging
import uuid

from controllers.documents.lamicoid_2 import TemplateController
from models.documents.lamicoid_2 import TemplateLamicoid

logger = logging.getLogger('GDJ_App')

class TemplateListView(QWidget):
    """
    Widget affichant la liste des templates existants.
    Permet la sélection, l'ajout et la suppression de templates.
    """
    # Signal émis avec l'ID du template sélectionné, ou une chaîne vide si désélectionné
    template_selected = pyqtSignal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TemplateListView")
        self.template_controller = TemplateController.get_instance()
        
        self._setup_ui()
        self.populate_list()
        self._connect_signals()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Nouveau")
        self.delete_button = QPushButton("Supprimer")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)
        
    def _connect_signals(self):
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)
        self.add_button.clicked.connect(self._on_add_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)

    def populate_list(self):
        """Peuple la liste avec les templates du contrôleur."""
        self.list_widget.clear()
        templates = self.template_controller.get_all_templates()
        for template in sorted(templates, key=lambda t: t.nom_template):
            item = QListWidgetItem(template.nom_template)
            item.setData(Qt.UserRole, template.template_id) # Stocker l'ID dans l'item
            self.list_widget.addItem(item)
            
    def _on_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        if current:
            template_id = current.data(Qt.UserRole)
            self.template_selected.emit(template_id)
        else:
            self.template_selected.emit("")

    def _on_add_clicked(self):
        """Affiche un dialogue pour créer un nouveau template."""
        text, ok = QInputDialog.getText(self, 'Nouveau Template', 'Nom du nouveau template:')
        
        if ok and text:
            new_id = str(uuid.uuid4())
            new_template = TemplateLamicoid(template_id=new_id, nom_template=text)
            self.template_controller.add_or_update_template(new_template)
            self.populate_list()

            # Sélectionner le nouvel item dans la liste
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.data(Qt.UserRole) == new_id:
                    self.list_widget.setCurrentItem(item)
                    break
        elif ok and not text:
            QMessageBox.warning(self, "Nom invalide", "Le nom du template ne peut pas être vide.")

    def _on_delete_clicked(self):
        """Affiche une confirmation et supprime le template sélectionné."""
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "Aucune sélection", "Veuillez sélectionner un template à supprimer.")
            return
            
        template_id = current_item.data(Qt.UserRole)
        template_name = current_item.text()
        
        reply = QMessageBox.question(self, 'Confirmation de suppression', 
                                     f"Êtes-vous sûr de vouloir supprimer le template '{template_name}' ?\n"
                                     "Cette action est irréversible.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            deleted = self.template_controller.delete_template(template_id)
            if deleted:
                self.populate_list()
                logger.info(f"Template '{template_name}' (ID: {template_id}) supprimé par l'utilisateur.")
            else:
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue lors de la suppression du template.") 