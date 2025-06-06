# pages/documents/lamicoid_2_page.py
"""Définit la page principale pour la gestion des documents Lamicoid v2."""

import logging
import uuid
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QPushButton, QFrame, QLineEdit, QListWidget)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QColor, QPixmap
from typing import Dict, Optional

from ui.components.frame import Frame
from controllers.documents.lamicoid_2.template_controller import TemplateController
from models.documents.lamicoid_2.template_lamicoid import TemplateLamicoid
from models.documents.lamicoid_2.lamicoid import Lamicoid
from models.documents.lamicoid_2.feuille_lamicoid import FeuilleLamicoid, LamicoidPositionne
from models.documents.lamicoid_2.elements import ElementVariable

from .lamicoid_2.feuille_lamicoid_view import FeuilleLamicoidView
from utils.icon_loader import get_icon_path
from ui.delegates.icon_only_delegate import IconOnlyDelegate

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
        
        self.feuille_lamicoid = FeuilleLamicoid(largeur_feuille_mm=600, hauteur_feuille_mm=300)
        self._is_first_show = True
        
        self._init_ui()
        self._connect_signals()
        
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

        # Label "Inserer un lamicoid"
        inserer_label = QLabel("Inserer un lamicoid")
        inserer_label.setObjectName("insererLabel")
        inserer_label.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        left_panel_content_layout.addWidget(inserer_label)

        # Cadre avec bordure et fond transparent
        inserer_frame = QFrame()
        inserer_frame.setObjectName("insererFrame")
        inserer_frame.setStyleSheet("""
            QFrame#insererFrame {
                background-color: transparent;
                border: 1px solid #4A4D4E;
                border-radius: 6px;
            }
        """)
        inserer_layout = QVBoxLayout(inserer_frame)
        inserer_layout.setContentsMargins(8, 8, 8, 8)
        # Le cadre est vide pour l'instant
        inserer_layout.addStretch(1)
        left_panel_content_layout.addWidget(inserer_frame)

        left_panel_content_layout.addStretch(1)
        
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
        self.color_combo.setObjectName("ColorComboBox")
        self.color_combo.setItemDelegate(IconOnlyDelegate(self.color_combo, actual_icon_size=QSize(20, 20)))
        self.color_combo.setIconSize(QSize(20, 20))
        self.color_combo.setFixedWidth(35)
        self.color_combo.setStyleSheet("""
            QComboBox#ColorComboBox {
                border: 1px solid #8f8f91;
                border-radius: 4px;
                padding: 6px; /* (35px width - 2px border - 20px icon) / 2 = 6.5px */
            }
            QComboBox#ColorComboBox::drop-down {
                border: 0px;
                width: 0px;
            }
            QComboBox#ColorComboBox::down-arrow {
                image: none;
                border: 0px;
                width: 0px;
                height: 0px;
            }
        """)
        
        colors = {
            "Gris": QColor("#B0B0B0"),
            "Rouge": QColor("#B82B2B"),
            "Bleu": QColor("#3B5998"),
            "Vert": QColor("#5A8A3E"),
            "Jaune": QColor(Qt.yellow),
            "Blanc": QColor(Qt.white),
            "Noir": QColor(Qt.black)
        }

        for name, color in colors.items():
            pixmap = QPixmap(20, 20)
            pixmap.fill(color)
            self.color_combo.addItem(QIcon(pixmap), "") # Texte vide
            # L'index 0 est le rôle d'affichage (texte), on stocke le nom de la couleur dans un autre rôle
            self.color_combo.setItemData(self.color_combo.count() - 1, name, Qt.UserRole)
            
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