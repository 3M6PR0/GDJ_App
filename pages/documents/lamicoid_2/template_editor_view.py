"""
Vue pour l'édition d'un template de lamicoid.
"""

from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen

from models.documents.lamicoid_2.template_lamicoid import TemplateLamicoid

class TemplateEditorView(QGraphicsView):
    """
    Vue QGraphicsView spécialisée pour la création et l'édition de templates.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self._template_item = None
        self.scene.setBackgroundBrush(QBrush(QColor("#E0E0E0")))

    def display_template(self, template: TemplateLamicoid):
        """
        Affiche le contour du template dans la scène.
        """
        self.scene.clear()
        
        # Dessine le rectangle du template
        self._template_item = self.scene.addRect(
            0, 0, template.largeur_mm, template.hauteur_mm,
            QPen(Qt.black), QBrush(Qt.white)
        )
        
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def clear(self):
        """Vide la scène."""
        self.scene.clear()
        self._template_item = None 