"""
Vue pour l'édition d'un template de lamicoid.
"""

import logging
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPathItem, 
                             QGraphicsTextItem, QGraphicsRectItem, QGraphicsDropShadowEffect)
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
        
        self.lamicoid_item: QGraphicsPathItem | None = None
        self.margin_item: QGraphicsPathItem | None = None
        self.grid_lines: list = []
        
        self._setup_view_properties()
        
    def _setup_view_properties(self):
        """Configure les propriétés de la QGraphicsView."""
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setBackgroundBrush(QBrush(QColor("#F0F0F0"))) # Couleur exacte de l'ancienne version
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
        self.lamicoid_item = None
        self.margin_item = None
        self.grid_lines = []
        
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
        """Dessine la grille et la marge en respectant les spécificités de l'ancienne version."""
        width_px = _mm_to_pixels(self.current_template.largeur_mm)
        height_px = _mm_to_pixels(self.current_template.hauteur_mm)
        margin_px = _mm_to_pixels(self.current_template.marge_mm)
        radius_px = _mm_to_pixels(self.current_template.rayon_coin_mm)
        grid_spacing_px = _mm_to_pixels(self.current_template.espacement_grille_mm)

        margin_rect = QRectF(-width_px/2 + margin_px, -height_px/2 + margin_px, width_px - 2*margin_px, height_px - 2*margin_px)

        # Marge bleue avec coins arrondis
        if margin_px > 0:
            margin_path = QPainterPath()
            margin_corner_radius = max(0, radius_px - margin_px)
            margin_path.addRoundedRect(margin_rect, margin_corner_radius, margin_corner_radius)
            
            margin_pen = QPen(QColor("#3B5998"), 1, Qt.DashLine)
            margin_pen.setDashPattern([3, 2])
            self.margin_item = self._scene.addPath(margin_path, margin_pen)
            self.margin_item.setZValue(-9)

        # Grille cosmétique à l'intérieur de la marge
        if grid_spacing_px > 0:
            grid_pen = QPen(QColor("#E0E0E0"), 0.5)
            grid_pen.setCosmetic(True)

            # Lignes verticales centrées
            x = grid_spacing_px
            while x < margin_rect.width() / 2:
                line = self._scene.addLine(x, margin_rect.top(), x, margin_rect.bottom(), grid_pen)
                line.setZValue(-9); self.grid_lines.append(line)
                line = self._scene.addLine(-x, margin_rect.top(), -x, margin_rect.bottom(), grid_pen)
                line.setZValue(-9); self.grid_lines.append(line)
                x += grid_spacing_px
            
            # Lignes horizontales centrées
            y = grid_spacing_px
            while y < margin_rect.height() / 2:
                line = self._scene.addLine(margin_rect.left(), y, margin_rect.right(), y, grid_pen)
                line.setZValue(-9); self.grid_lines.append(line)
                line = self._scene.addLine(margin_rect.left(), -y, margin_rect.right(), -y, grid_pen)
                line.setZValue(-9); self.grid_lines.append(line)
                y += grid_spacing_px

            # Ligne centrale (si l'espacement n'est pas parfaitement divisible)
            center_line_pen = QPen(QColor("#CCCCCC"), 0.5) # Un peu plus sombre
            center_line_pen.setCosmetic(True)
            line = self._scene.addLine(0, margin_rect.top(), 0, margin_rect.bottom(), center_line_pen)
            line.setZValue(-9); self.grid_lines.append(line)
            line = self._scene.addLine(margin_rect.left(), 0, margin_rect.right(), 0, center_line_pen)
            line.setZValue(-9); self.grid_lines.append(line)

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