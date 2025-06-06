from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSplitter, QVBoxLayout
from PyQt5.QtCore import Qt
import logging

from .template_list_view import TemplateListView
from .template_properties_view import TemplatePropertiesView
from .template_editor_view import TemplateEditorView

logger = logging.getLogger('GDJ_App')

class TemplateManagementPage(QWidget):
    """
    Page principale pour la gestion des templates de Lamicoid.
    Combine la liste des templates, l'édition de propriétés et l'éditeur visuel.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TemplateManagementPage")
        
        # Le template actuellement sélectionné pour l'édition
        self.current_template_id: str | None = None
        
        self._setup_ui()
        self._connect_signals()
        logger.debug("TemplateManagementPage initialisée.")

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Splitter principal (vertical) pour séparer les propriétés de l'éditeur visuel ---
        editor_splitter = QSplitter(Qt.Vertical)
        
        # --- Zone des propriétés (en haut) ---
        self.properties_view = TemplatePropertiesView(editor_splitter)
        editor_splitter.addWidget(self.properties_view)
        
        # --- Éditeur visuel (en bas) ---
        self.visual_editor_view = TemplateEditorView(editor_splitter)
        editor_splitter.addWidget(self.visual_editor_view)

        editor_splitter.setSizes([250, 600]) # Donne plus de place à l'éditeur visuel
        
        # --- Splitter horizontal (principal) ---
        main_splitter = QSplitter(Qt.Horizontal, self)
        
        # --- Zone de gauche : La liste ---
        self.list_view = TemplateListView(self)
        main_splitter.addWidget(self.list_view)
        
        # --- Zone de droite : Le splitter vertical avec propriétés + éditeur ---
        main_splitter.addWidget(editor_splitter)

        main_splitter.setSizes([250, 750]) # Configuration des tailles initiales
        
        main_layout.addWidget(main_splitter)
        
    def _connect_signals(self):
        """Connecte les signaux entre les composants de la page."""
        # Sélection d'un item dans la liste
        self.list_view.template_selected.connect(self.handle_template_selection)
        
        # Sauvegarde depuis la vue des propriétés
        self.properties_view.template_saved.connect(self.list_view.populate_list)
        self.properties_view.template_saved.connect(self.visual_editor_view.load_template)

    def handle_template_selection(self, template_id: str):
        """Met à jour les vues d'édition lorsqu'un template est sélectionné."""
        self.current_template_id = template_id
        
        # Charge le template dans les deux vues de droite
        self.properties_view.load_template(template_id)
        self.visual_editor_view.load_template(template_id)
            
        logger.debug(f"Template sélectionné dans la page principale : {template_id}") 