"""
Vue pour l'édition d'un template de lamicoid.
"""

import logging
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPathItem, 
                             QGraphicsTextItem, QGraphicsRectItem, QGraphicsDropShadowEffect, QGraphicsItem)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QPainterPath, QFont

from controllers.documents.lamicoid_2 import TemplateController
from models.documents.lamicoid_2 import (
    TemplateLamicoid, ElementTemplateBase, ElementTexte #, ElementImage, ElementVariable
)
from .items.texte_item import TexteItem

logger = logging.getLogger('GDJ_App')

# --- Fonctions de conversion d'unités ---
DEFAULT_DPI = 96.0
INCH_TO_MM = 25.4

def _mm_to_pixels(mm: float) -> float:
    return (mm / INCH_TO_MM) * DEFAULT_DPI

def _pixels_to_mm(pixels: float) -> float:
    return (pixels / DEFAULT_DPI) * INCH_TO_MM

class MarginAndGridItem(QGraphicsItem):
    """
    Un item graphique qui dessine à la fois la marge (bleue, arrondie, en pointillés)
    et la grille (cosmétique, contenue à l'intérieur de la marge).
    """
    def __init__(self, template: TemplateLamicoid, parent=None):
        super().__init__(parent)
        self.template = template
        self.width_px = _mm_to_pixels(self.template.largeur_mm)
        self.height_px = _mm_to_pixels(self.template.hauteur_mm)
        self.setZValue(-9)

    def boundingRect(self) -> QRectF:
        return QRectF(-self.width_px / 2, -self.height_px / 2, self.width_px, self.height_px)

    def paint(self, painter: QPainter, option, widget=None):
        margin_px = _mm_to_pixels(self.template.marge_mm)
        radius_px = _mm_to_pixels(self.template.rayon_coin_mm)
        grid_spacing_px = _mm_to_pixels(self.template.espacement_grille_mm)

        # 1. Définir le chemin de la marge arrondie
        margin_rect = QRectF(
            -self.width_px / 2 + margin_px, -self.height_px / 2 + margin_px,
            self.width_px - 2 * margin_px, self.height_px - 2 * margin_px
        )
        margin_path = QPainterPath()
        margin_corner_radius = max(0, radius_px - margin_px)
        margin_path.addRoundedRect(margin_rect, margin_corner_radius, margin_corner_radius)

        # 2. Dessiner la marge bleue
        if margin_px > 0:
            margin_pen = QPen(QColor("#3B5998"), 1, Qt.DashLine)
            margin_pen.setDashPattern([3, 2])
            painter.setPen(margin_pen)
            painter.drawPath(margin_path)

        # 3. Dessiner la grille découpée par le chemin de la marge
        if grid_spacing_px > 0:
            painter.save()
            painter.setClipPath(margin_path)

            grid_pen = QPen(QColor("#E0E0E0"), 0.5)
            grid_pen.setCosmetic(True)
            painter.setPen(grid_pen)

            x = grid_spacing_px
            while x < margin_rect.width() / 2:
                painter.drawLine(int(x), int(margin_rect.top()), int(x), int(margin_rect.bottom()))
                painter.drawLine(int(-x), int(margin_rect.top()), int(-x), int(margin_rect.bottom()))
                x += grid_spacing_px
            
            y = grid_spacing_px
            while y < margin_rect.height() / 2:
                painter.drawLine(int(margin_rect.left()), int(y), int(margin_rect.right()), int(y))
                painter.drawLine(int(margin_rect.left()), int(-y), int(margin_rect.right()), int(-y))
                y += grid_spacing_px
            
            center_line_pen = QPen(QColor("#CCCCCC"), 0.5)
            center_line_pen.setCosmetic(True)
            painter.setPen(center_line_pen)
            painter.drawLine(0, int(margin_rect.top()), 0, int(margin_rect.bottom()))
            painter.drawLine(int(margin_rect.left()), 0, int(margin_rect.right()), 0)
            
            painter.restore()

class TemplateEditorView(QGraphicsView):
    """
    Vue d'édition visuelle pour un TemplateLamicoid.
    """
    text_item_selected = pyqtSignal(bool, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TemplateEditorView")
        
        self.current_template: TemplateLamicoid | None = None
        self.template_controller = TemplateController.get_instance()
        
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        self.lamicoid_item: QGraphicsPathItem | None = None
        self.margin_grid_item: MarginAndGridItem | None = None
        
        self._setup_view_properties()
        
    def _setup_view_properties(self):
        """Configure les propriétés de la QGraphicsView."""
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.viewport().setAutoFillBackground(False)
        self.centerOn(0, 0)

    @property
    def content_rect_px(self) -> QRectF:
        """Retourne le rectangle de contenu (intérieur des marges) en coordonnées de scène."""
        if self.current_template:
            width_px = _mm_to_pixels(self.current_template.largeur_mm)
            height_px = _mm_to_pixels(self.current_template.hauteur_mm)
            margin_px = _mm_to_pixels(self.current_template.marge_mm)
            
            left = -width_px / 2 + margin_px
            top = -height_px / 2 + margin_px
            content_width = width_px - 2 * margin_px
            content_height = height_px - 2 * margin_px
            
            return QRectF(left, top, content_width, content_height)
        return QRectF()

    @property
    def grid_spacing(self) -> float:
        """Retourne l'espacement de la grille en pixels. Retourne 0 si non applicable."""
        if self.current_template and self.current_template.espacement_grille_mm > 0:
            return _mm_to_pixels(self.current_template.espacement_grille_mm)
        return 0.0

    @property
    def grid_offset(self) -> QPointF:
        """Retourne le décalage (coin supérieur gauche) de la zone de la grille."""
        if self.current_template:
            width_px = _mm_to_pixels(self.current_template.largeur_mm)
            height_px = _mm_to_pixels(self.current_template.hauteur_mm)
            margin_px = _mm_to_pixels(self.current_template.marge_mm)
            
            offset_x = -width_px / 2 + margin_px
            offset_y = -height_px / 2 + margin_px
            return QPointF(offset_x, offset_y)
        return QPointF(0, 0)

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
        self.lamicoid_item = None
        self.margin_grid_item = None
        
    def _draw_template(self):
        """Dessine le canevas du lamicoid et ses éléments."""
        if not self.current_template: return
            
        # 1. Dessiner le Lamicoid avec son ombre
        self._draw_lamicoid_base()

        # 2. Dessiner la marge et la grille
        self._draw_grid_and_margin()
        
        # 3. Dessiner les éléments
        for element in self.current_template.elements:
            self._draw_element(element)
            
        self._scene.setSceneRect(self.get_scene_items_rect())
        self.fitInView(self.get_scene_items_rect(), Qt.KeepAspectRatio)

    def _draw_lamicoid_base(self):
        """Prépare le fond blanc du lamicoid avec son ombre."""
        width_px = _mm_to_pixels(self.current_template.largeur_mm)
        height_px = _mm_to_pixels(self.current_template.hauteur_mm)
        radius_px = _mm_to_pixels(self.current_template.rayon_coin_mm)
        
        path = QPainterPath()
        rect = QRectF(-width_px / 2, -height_px / 2, width_px, height_px)
        path.addRoundedRect(rect, radius_px, radius_px)
        
        self.lamicoid_item = QGraphicsPathItem(path)
        self.lamicoid_item.setBrush(Qt.white)
        self.lamicoid_item.setPen(QPen(QColor("#BDBDBD"), 1))
        self.lamicoid_item.setZValue(-10)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(2, 2)
        self.lamicoid_item.setGraphicsEffect(shadow)
        
        self._scene.addItem(self.lamicoid_item)

    def _draw_grid_and_margin(self):
        """Crée un seul item pour la marge et la grille."""
        self.margin_grid_item = MarginAndGridItem(self.current_template)
        self._scene.addItem(self.margin_grid_item)

    def _draw_element(self, element: ElementTemplateBase):
        """Crée et ajoute l'item graphique approprié à la scène, centré sur le lamicoid uniquement à la création."""
        lamicoid_width_px = _mm_to_pixels(self.current_template.largeur_mm)
        lamicoid_height_px = _mm_to_pixels(self.current_template.hauteur_mm)

        if isinstance(element, ElementTexte):
            item = TexteItem(element)
            if hasattr(element, '_just_added') and element._just_added:
                # Centrer uniquement à la création
                if hasattr(item, '_update_bounding_box'):
                    item._update_bounding_box()
                bounding = item.boundingRect()
                pos_x_px = _mm_to_pixels(element.x_mm) - lamicoid_width_px / 2
                pos_y_px = _mm_to_pixels(element.y_mm) - lamicoid_height_px / 2
                item.setPos(pos_x_px - bounding.width() / 2, pos_y_px - bounding.height() / 2)
                delattr(element, '_just_added')
            else:
                # Utiliser la position du modèle sans recentrage
                pos_x_px = _mm_to_pixels(element.x_mm) - lamicoid_width_px / 2
                pos_y_px = _mm_to_pixels(element.y_mm) - lamicoid_height_px / 2
                item.setPos(pos_x_px, pos_y_px)
            item.setFlag(QGraphicsItem.ItemIsSelectable, True)
            item.setFlag(QGraphicsItem.ItemIsMovable, True)
            item.signal_helper.element_selected.connect(
                lambda selected_item: self.text_item_selected.emit(bool(selected_item), selected_item)
            )
            self._scene.addItem(item)
        # Le code pour d'autres types d'éléments (Image, etc.) viendra ici
        # elif isinstance(element, ElementImage):
        #     pass

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