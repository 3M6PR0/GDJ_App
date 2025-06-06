import logging
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsTextItem, QGraphicsRectItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QPainterPath, QFont

from controllers.documents.lamicoid_2 import TemplateController
from models.documents.lamicoid_2 import (
    TemplateLamicoid, ElementTemplateBase, ElementTexte, ElementImage, ElementVariable
)

logger = logging.getLogger('GDJ_App')

# Constantes de conversion (identiques à l'éditeur existant pour la cohérence)
DEFAULT_DPI = 96.0
INCH_TO_MM = 25.4

class TemplateEditorView(QGraphicsView):
    """
    Vue d'édition visuelle pour un TemplateLamicoid.
    Affiche une prévisualisation du lamicoid et de ses éléments.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TemplateEditorView")
        
        self.current_template: TemplateLamicoid | None = None
        self.template_controller = TemplateController.get_instance()
        
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # L'item qui représente le contour du lamicoid
        self.lamicoid_outline_item: QGraphicsPathItem | None = None
        
        self._setup_view_properties()
        
    def _setup_view_properties(self):
        """Configure les propriétés de la QGraphicsView."""
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setBackgroundBrush(QBrush(QColor("#E0E0E0"))) # Fond légèrement gris
        self.centerOn(0, 0)

    def load_template(self, template_id: str):
        """Charge et dessine le template spécifié."""
        if not template_id:
            self.clear_view()
            return
            
        self.current_template = self.template_controller.get_template_by_id(template_id)
        
        if self.current_template:
            self.clear_view()
            self._draw_template()
        else:
            logger.warning(f"Impossible de charger le template ID {template_id} dans l'éditeur visuel.")
            self.clear_view()

    def clear_view(self):
        """Nettoie la scène de tous les éléments."""
        self._scene.clear()
        self.lamicoid_outline_item = None
        
    def _draw_template(self):
        """Dessine le contour du lamicoid et ses éléments."""
        if not self.current_template:
            return
            
        # 1. Dessiner le contour du Lamicoid
        width_px = self._mm_to_pixels(self.current_template.largeur_mm)
        height_px = self._mm_to_pixels(self.current_template.hauteur_mm)
        radius_px = self._mm_to_pixels(self.current_template.rayon_coin_mm)
        
        # Crée un rectangle centré sur (0,0)
        lamicoid_rect = QRectF(-width_px / 2, -height_px / 2, width_px, height_px)
        
        path = QPainterPath()
        path.addRoundedRect(lamicoid_rect, radius_px, radius_px)
        
        self.lamicoid_outline_item = QGraphicsPathItem(path)
        self.lamicoid_outline_item.setBrush(QBrush(Qt.white))
        self.lamicoid_outline_item.setPen(QPen(Qt.black, 1))
        self.lamicoid_outline_item.setZValue(-10) # En arrière-plan
        self._scene.addItem(self.lamicoid_outline_item)
        
        # 2. Dessiner les éléments
        for element in self.current_template.elements:
            self._draw_element(element)
            
        # Ajuster la vue pour afficher toute la scène
        self.fitInView(self._scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def _draw_element(self, element: ElementTemplateBase):
        """Crée et dessine le QGraphicsItem correspondant à un élément de modèle."""
        
        # Le point (0,0) de la scène correspond au centre du lamicoid.
        # Nos positions d'éléments sont relatives au coin haut-gauche du lamicoid.
        # Il faut donc translater.
        lamicoid_width_px = self._mm_to_pixels(self.current_template.largeur_mm)
        lamicoid_height_px = self._mm_to_pixels(self.current_template.hauteur_mm)
        
        offset_x = -lamicoid_width_px / 2
        offset_y = -lamicoid_height_px / 2
        
        pos_x_px = self._mm_to_pixels(element.position_x_mm) + offset_x
        pos_y_px = self._mm_to_pixels(element.position_y_mm) + offset_y

        if isinstance(element, ElementTexte) or isinstance(element, ElementVariable):
            text_item = QGraphicsTextItem()
            # Pour l'instant, on affiche le nom de la variable ou le texte.
            text_to_display = element.nom_variable if isinstance(element, ElementVariable) else element.contenu_texte
            text_item.setPlainText(text_to_display)
            text_item.setFont(QFont(element.nom_police, element.taille_police))
            text_item.setPos(pos_x_px, pos_y_px)
            self._scene.addItem(text_item)
        
        elif isinstance(element, ElementImage):
            # Sera implémenté plus tard
            # Pour l'instant, on dessine un rectangle placeholder
            width = self._mm_to_pixels(element.largeur_mm)
            height = self._mm_to_pixels(element.hauteur_mm)
            rect_item = QGraphicsRectItem(pos_x_px, pos_y_px, width, height)
            rect_item.setBrush(QBrush(QColor("#CCCCCC")))
            rect_item.setPen(QPen(Qt.black, 1, Qt.DashLine))
            self._scene.addItem(rect_item)
            
            text_label = QGraphicsTextItem("Image", parent=rect_item)
            text_label.setPos(pos_x_px, pos_y_px)

    def resizeEvent(self, event):
        """Ajuste la vue lorsque le widget est redimensionné."""
        super().resizeEvent(event)
        if self.lamicoid_outline_item:
            self.fitInView(self._scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    # --- Fonctions de conversion d'unités ---
    def _mm_to_pixels(self, mm: float) -> float:
        return (mm / INCH_TO_MM) * DEFAULT_DPI

    def _pixels_to_mm(self, pixels: float) -> float:
        return (pixels / DEFAULT_DPI) * INCH_TO_MM 