"""
Vue pour l'édition d'un template de lamicoid.
"""

import logging
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsTextItem, QGraphicsRectItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QPainterPath, QFont

from controllers.documents.lamicoid_2 import TemplateController
from models.documents.lamicoid_2 import (
    TemplateLamicoid, ElementTemplateBase, ElementTexte, ElementImage, ElementVariable
)

logger = logging.getLogger('GDJ_App')

# --- Fonctions de conversion d'unités ---
DEFAULT_DPI = 96.0
INCH_TO_MM = 25.4

def _mm_to_pixels(mm: float) -> float:
    return (mm / INCH_TO_MM) * DEFAULT_DPI

def _pixels_to_mm(pixels: float) -> float:
    return (pixels / DEFAULT_DPI) * INCH_TO_MM

class LamicoidCanvasItem(QGraphicsPathItem):
    """
    Item représentant le canevas du lamicoid (fond, marge, grille).
    """
    def __init__(self, template: TemplateLamicoid, parent=None):
        super().__init__(parent)
        self.template = template
        self.setPath(self._create_path())
        self.setBrush(Qt.white)
        self.setPen(QPen(Qt.black, 0.5))

    def _create_path(self):
        width_px = _mm_to_pixels(self.template.largeur_mm)
        height_px = _mm_to_pixels(self.template.hauteur_mm)
        radius_px = _mm_to_pixels(self.template.rayon_coin_mm)
        rect = QRectF(-width_px / 2, -height_px / 2, width_px, height_px)
        path = QPainterPath()
        path.addRoundedRect(rect, radius_px, radius_px)
        return path

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget) # Dessine le fond et la bordure
        
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipPath(self.path())

        self._draw_grid(painter)
        self._draw_margin(painter)

        painter.restore()

    def _draw_grid(self, painter: QPainter):
        grid_spacing_px = _mm_to_pixels(self.template.espacement_grille_mm)
        if grid_spacing_px <= 0: return

        width_px = _mm_to_pixels(self.template.largeur_mm)
        height_px = _mm_to_pixels(self.template.hauteur_mm)
        
        grid_pen = QPen(QColor("#E0E0E0"), 0.5)
        painter.setPen(grid_pen)
        
        # Lignes verticales depuis le centre
        x = 0
        while x < width_px / 2:
            painter.drawLine(int(x), int(-height_px / 2), int(x), int(height_px / 2))
            painter.drawLine(int(-x), int(-height_px / 2), int(-x), int(height_px / 2))
            x += grid_spacing_px
        
        # Lignes horizontales depuis le centre
        y = 0
        while y < height_px / 2:
            painter.drawLine(int(-width_px / 2), int(y), int(width_px / 2), int(y))
            painter.drawLine(int(-width_px / 2), int(-y), int(width_px / 2), int(-y))
            y += grid_spacing_px

    def _draw_margin(self, painter: QPainter):
        margin_px = _mm_to_pixels(self.template.marge_mm)
        if margin_px <= 0: return

        width_px = _mm_to_pixels(self.template.largeur_mm)
        height_px = _mm_to_pixels(self.template.hauteur_mm)

        margin_rect = QRectF(
            -width_px / 2 + margin_px, -height_px / 2 + margin_px,
            width_px - 2 * margin_px, height_px - 2 * margin_px
        )
        margin_pen = QPen(Qt.gray, 1, Qt.DashLine)
        painter.setPen(margin_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(margin_rect)


class TemplateEditorView(QGraphicsView):
    """
    Vue d'édition visuelle pour un TemplateLamicoid.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TemplateEditorView")
        
        self.current_template: TemplateLamicoid | None = None
        self.template_controller = TemplateController.get_instance()
        
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        self.lamicoid_canvas_item: LamicoidCanvasItem | None = None
        
        self._setup_view_properties()
        
    def _setup_view_properties(self):
        """Configure les propriétés de la QGraphicsView."""
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setBackgroundBrush(QBrush(QColor("#E0E0E0")))
        self.centerOn(0, 0)

    def load_template_object(self, template: TemplateLamicoid | None):
        """Charge et dessine un objet TemplateLamicoid."""
        self.current_template = template
        self.update_template_view()

    def update_template_view(self):
        """Met à jour la vue pour refléter les changements du template actuel."""
        self.clear_view()
        if self.current_template:
            self._draw_template()

    def clear_view(self):
        """Nettoie la scène de tous les éléments."""
        self._scene.clear()
        self.lamicoid_canvas_item = None
        
    def _draw_template(self):
        """Dessine le canevas du lamicoid et ses éléments."""
        if not self.current_template: return
            
        self.lamicoid_canvas_item = LamicoidCanvasItem(self.current_template)
        self.lamicoid_canvas_item.setZValue(-10)
        self._scene.addItem(self.lamicoid_canvas_item)
        
        for element in self.current_template.elements:
            self._draw_element(element)
            
        self.fitInView(self.get_scene_items_rect(), Qt.KeepAspectRatio)

    def _draw_element(self, element: ElementTemplateBase):
        lamicoid_width_px = _mm_to_pixels(self.current_template.largeur_mm)
        lamicoid_height_px = _mm_to_pixels(self.current_template.hauteur_mm)
        offset_x = -lamicoid_width_px / 2
        offset_y = -lamicoid_height_px / 2
        
        pos_x_px = _mm_to_pixels(element.x_mm) + offset_x
        pos_y_px = _mm_to_pixels(element.y_mm) + offset_y

        if isinstance(element, (ElementTexte, ElementVariable)):
            font = QFont(element.nom_police, element.taille_police_pt)
            
            text_item = QGraphicsTextItem()
            text_to_display = element.nom_variable if isinstance(element, ElementVariable) else element.contenu
            text_item.setPlainText(text_to_display)
            text_item.setFont(font)
            text_item.setDefaultTextColor(QColor("#000000")) # À dynamiser plus tard
            text_item.setPos(pos_x_px, pos_y_px)
            self._scene.addItem(text_item)
        
        elif isinstance(element, ElementImage):
            width = _mm_to_pixels(element.largeur_mm)
            height = _mm_to_pixels(element.hauteur_mm)
            rect_item = QGraphicsRectItem(pos_x_px, pos_y_px, width, height)
            rect_item.setBrush(QBrush(QColor("#CCCCCC")))
            rect_item.setPen(QPen(Qt.black, 1, Qt.DashLine))
            self._scene.addItem(rect_item)
            
            text_label = QGraphicsTextItem("Image", parent=rect_item)
            text_label.setPos(pos_x_px, pos_y_px)

    def get_scene_items_rect(self):
        """Calcule le rectangle englobant de tous les items, avec une marge."""
        rect = self._scene.itemsBoundingRect()
        if not rect.isNull():
            margin = 20 # Marge en pixels
            rect.adjust(-margin, -margin, margin, margin)
        return rect

    def resizeEvent(self, event):
        """Ajuste la vue lorsque le widget est redimensionné."""
        super().resizeEvent(event)
        if self._scene.items():
            self.fitInView(self.get_scene_items_rect(), Qt.KeepAspectRatio)