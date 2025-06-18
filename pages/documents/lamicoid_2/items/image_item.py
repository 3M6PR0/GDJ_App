from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtCore import QRectF, Qt, QSizeF, QPointF
from .base_item import EditableItemBase
from models.documents.lamicoid_2.elements import ElementImage

class ImageItem(EditableItemBase):
    def __init__(self, element_image: ElementImage, parent: QGraphicsItem = None):
        super().__init__(model_item=element_image, parent=parent)
        self.pixmap = QPixmap(element_image.chemin_fichier)
        self.setRect(0, 0, element_image.largeur_mm, element_image.hauteur_mm)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        if not self.pixmap.isNull():
            # Le rectangle englobant de l'item, qui peut être déformé.
            bounding_rect = self.rect()

            # La taille originale du pixmap.
            pixmap_size = QSizeF(self.pixmap.size())

            # On calcule la taille de l'image qui remplit le bounding_rect
            # tout en conservant le ratio.
            scaled_size = pixmap_size.scaled(bounding_rect.size(), Qt.KeepAspectRatio)

            # On calcule la position pour centrer l'image dans le bounding_rect.
            x = bounding_rect.x() + (bounding_rect.width() - scaled_size.width()) / 2
            y = bounding_rect.y() + (bounding_rect.height() - scaled_size.height()) / 2
            
            # Le rectangle final où dessiner, centré et avec le bon ratio.
            final_draw_rect = QRectF(x, y, scaled_size.width(), scaled_size.height())
            
            # On s'assure que le painter utilise un rendu de haute qualité
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # On dessine le pixmap dans le rectangle calculé.
            painter.drawPixmap(final_draw_rect, self.pixmap, QRectF(self.pixmap.rect()))
        else:
            painter.setPen(Qt.red)
            painter.drawRect(self.rect())
            painter.drawText(self.rect(), Qt.AlignCenter, "Image non trouvée")

    def interactive_resize(self, mouse_pos: QPointF):
        """Surcharge pour forcer le maintien du ratio de l'image."""
        if self.pixmap.isNull() or self.pixmap.height() == 0:
            super().interactive_resize(mouse_pos)
            return

        aspect_ratio = self.pixmap.width() / self.pixmap.height()

        self.prepareGeometryChange()
        
        new_rect = QRectF(self.rect())
        original_rect = self.mouse_press_rect

        diff = mouse_pos - self.mouse_press_pos
        
        if self.current_handle == 'bottom_right':
            new_width = original_rect.width() + diff.x()
            new_height = new_width / aspect_ratio
            new_rect.setWidth(new_width)
            new_rect.setHeight(new_height)
            
        elif self.current_handle == 'top_left':
            new_width = original_rect.width() - diff.x()
            new_height = new_width / aspect_ratio
            new_top_left = QPointF(original_rect.right() - new_width, original_rect.bottom() - new_height)
            new_rect.setTopLeft(new_top_left)

        elif self.current_handle == 'top_right':
            new_width = original_rect.width() + diff.x()
            new_height = new_width / aspect_ratio
            new_top_right = QPointF(original_rect.left() + new_width, original_rect.bottom() - new_height)
            new_rect.setTopRight(new_top_right)

        elif self.current_handle == 'bottom_left':
            new_width = original_rect.width() - diff.x()
            new_height = new_width / aspect_ratio
            new_bottom_left = QPointF(original_rect.right() - new_width, original_rect.top() + new_height)
            new_rect.setBottomLeft(new_bottom_left)

        min_size = self.handle_size * 2
        if new_rect.width() < min_size or new_rect.height() < min_size:
             return

        self.setRect(new_rect)
        self.update_handles_pos()

    def _update_bounding_box(self):
        self.setRect(0, 0, self.model_item.largeur_mm, self.model_item.hauteur_mm) 