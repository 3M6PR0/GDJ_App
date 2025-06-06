"""Définit la page complète pour l'édition d'un lamicoid (template)."""

import logging
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
from ui.components.frame import Frame # Importer le Frame personnalisé
from .template_editor_view import TemplateEditorView

logger = logging.getLogger('GDJ_App')

class EditorPage(QWidget):
    """
    Page contenant un panneau de configuration à gauche et
    l'éditeur de template à droite, utilisant des Frames personnalisées.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LamicoidEditorPage")
        
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

        # Panneau de gauche avec Frame personnalisé
        left_header = QLabel("Outils de l'éditeur")
        left_header.setObjectName("CustomFrameTitle")
        left_panel = Frame(header_widget=left_header, parent=self)
        left_panel.setFixedWidth(350)
        left_panel_layout = left_panel.get_content_layout()

        # ... (les outils viendront ici)
        left_panel_layout.addStretch(1)

        # Panneau de droite avec Frame personnalisé
        right_header = QLabel("Éditeur de Template")
        right_header.setObjectName("CustomFrameTitle")
        right_panel = Frame(header_widget=right_header, parent=self)
        right_panel_layout = right_panel.get_content_layout()
        
        self.editor_view = TemplateEditorView()
        right_panel_layout.addWidget(self.editor_view)

        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel, 1) 