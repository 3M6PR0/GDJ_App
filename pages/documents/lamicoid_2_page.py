# pages/documents/lamicoid_2_page.py
"""Définit la page principale pour la gestion des documents Lamicoid v2."""

import logging
import uuid
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, 
                             QFrame, QStackedWidget, QComboBox, QSizePolicy, QAction, QToolBar)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QColor, QPixmap
from typing import Dict, Optional

from utils.icon_loader import get_icon_path
from ui.components.frame import Frame
from ui.delegates.icon_only_delegate import IconOnlyDelegate
from models.documents.lamicoid_2.feuille_lamicoid import FeuilleLamicoid
from .lamicoid_2.editor_page import EditorPage
from .lamicoid_2.feuille_lamicoid_view import FeuilleLamicoidView
from models.documents.lamicoid_2.template_lamicoid import TemplateLamicoid

logger = logging.getLogger('GDJ_App')

class Lamicoid2Page(QWidget):
    """
    Page conteneur qui utilise un QStackedWidget pour basculer entre la vue 
    de la feuille et la vue de l'éditeur de lamicoid.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Lamicoid2PageContainer")
        
        self.feuille_lamicoid = FeuilleLamicoid(largeur_feuille_mm=600, hauteur_feuille_mm=300)
        self._is_first_show = True

        self.stack = QStackedWidget()
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)

        # Création et configuration de la vue "Feuille"
        self.sheet_view_widget = QWidget()
        self._setup_sheet_view(self.sheet_view_widget)
        
        # Création de la vue "Éditeur"
        self.editor_page = EditorPage()

        self.stack.addWidget(self.sheet_view_widget)
        self.stack.addWidget(self.editor_page)

        self._connect_signals()

        self.feuille_view.display_feuille(self.feuille_lamicoid)
        
        # Réactivation de la création du template
        self._create_default_template()

    def showEvent(self, event):
        """Appelé lorsque le widget est affiché."""
        super().showEvent(event)
        if self._is_first_show:
            # Zoom pour la vue de la feuille
            QTimer.singleShot(0, self.feuille_view.zoom_to_fit)
            # Le zoom de l'éditeur est maintenant géré par l'EditorPage elle-même
            self._is_first_show = False

    def _setup_sheet_view(self, container_widget):
        """Construit l'interface de la vue principale (feuille)."""
        layout = QHBoxLayout(container_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Panneau de gauche...
        left_header_widget = QLabel("Configuration Lamicoid v2")
        left_header_widget.setObjectName("CustomFrameTitle")
        left_panel = Frame(header_widget=left_header_widget, parent=container_widget)
        left_panel.setFixedWidth(350)
        left_panel_content_layout = left_panel.get_content_layout()

        left_content_widget = QWidget()
        left_layout = QVBoxLayout(left_content_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("Inserer un lamicoid"))
        self.new_lamicoid_button = QPushButton("Nouveau Lamicoid")
        left_layout.addWidget(self.new_lamicoid_button)
        left_layout.addStretch(1)
        left_panel_content_layout.addWidget(left_content_widget)

        # Panneau de droite...
        right_header_widget = QLabel("Feuille de Lamicoids")
        right_header_widget.setObjectName("CustomFrameTitle")
        right_panel = Frame(header_widget=right_header_widget, parent=container_widget)
        right_panel_content_layout = right_panel.get_content_layout()

        self._create_right_panel_toolbar(right_panel_content_layout)

        self.feuille_view = FeuilleLamicoidView(self)
        right_panel_content_layout.addWidget(self.feuille_view)
        
        layout.addWidget(left_panel)
        layout.addWidget(right_panel, 1)

    def _create_right_panel_toolbar(self, layout):
        """Crée la barre d'outils pour le panneau de droite."""
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

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        toolbar_layout.addWidget(separator)

        toolbar_layout.addWidget(QLabel("Couleur feuille:"))
        self.color_combo = QComboBox()
        self.color_combo.setObjectName("ColorComboBox")
        self.color_combo.setItemDelegate(IconOnlyDelegate(self.color_combo, actual_icon_size=QSize(20, 20)))
        self.color_combo.setIconSize(QSize(20, 20))
        self.color_combo.setFixedWidth(35)
        self.color_combo.setStyleSheet("""
            QComboBox#ColorComboBox { border: 1px solid #8f8f91; border-radius: 4px; padding: 6px; }
            QComboBox#ColorComboBox::drop-down { border: 0px; width: 0px; }
            QComboBox#ColorComboBox::down-arrow { image: none; border: 0px; width: 0px; height: 0px; }
        """)
        
        colors = {
            "Gris": QColor("#B0B0B0"), "Rouge": QColor("#B82B2B"), "Bleu": QColor("#3B5998"),
            "Vert": QColor("#5A8A3E"), "Jaune": QColor(Qt.yellow), "Blanc": QColor(Qt.white), "Noir": QColor(Qt.black)
        }
        for name, color in colors.items():
            pixmap = QPixmap(20, 20)
            pixmap.fill(color)
            self.color_combo.addItem(QIcon(pixmap), "")
            self.color_combo.setItemData(self.color_combo.count() - 1, name, Qt.UserRole)
            
        toolbar_layout.addWidget(self.color_combo)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

    def _create_default_template(self):
        """Crée un template par défaut et l'affiche dans l'éditeur."""
        default_template = TemplateLamicoid(
            template_id=str(uuid.uuid4()),
            nom_template="Nouveau Template",
            largeur_mm=100,
            hauteur_mm=50
        )
        self.editor_page.set_template(default_template)

    def _connect_signals(self):
        """Connecte les signaux pour la navigation et les actions."""
        self.new_lamicoid_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.editor_page.cancel_button.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.zoom_in_button.clicked.connect(self.feuille_view.zoom_in)
        self.zoom_out_button.clicked.connect(self.feuille_view.zoom_out)
        self.zoom_to_fit_button.clicked.connect(self.feuille_view.zoom_to_fit)
        self.color_combo.currentIndexChanged.connect(self._on_color_selected)

    def _on_color_selected(self, index):
        """Appelé lorsque l'utilisateur sélectionne une couleur."""
        color_name = self.color_combo.itemData(index, Qt.UserRole)
        if color_name:
            self.feuille_view.set_sheet_color(color_name)

    def get_document_data(self):
        """Méthode pour que la fenêtre parente puisse récupérer les données."""
        return {"type": "Lamicoid 2", "content": "Données à définir"} 