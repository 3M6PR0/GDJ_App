from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtCore import QRectF, Qt
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
            target_rect = self.rect().toRect()
            # Utiliser QImage pour un scaling de meilleure qualité
            image = self.pixmap.toImage()
            if target_rect.width() <= self.pixmap.width() and target_rect.height() <= self.pixmap.height():
                # On réduit seulement (jamais agrandir pour éviter la pixellisation)
                scaled_img = image.scaled(target_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                pixmap_scaled = QPixmap.fromImage(scaled_img)
                x = target_rect.x() + (target_rect.width() - pixmap_scaled.width()) // 2
                y = target_rect.y() + (target_rect.height() - pixmap_scaled.height()) // 2
                painter.drawPixmap(x, y, pixmap_scaled)
            else:
                # Si la bounding box est plus grande, on centre l'image à sa taille réelle
                x = target_rect.x() + (target_rect.width() - self.pixmap.width()) // 2
                y = target_rect.y() + (target_rect.height() - self.pixmap.height()) // 2
                painter.drawPixmap(x, y, self.pixmap)
        else:
            painter.setPen(Qt.red)
            painter.drawRect(self.rect())
            painter.drawText(self.rect(), Qt.AlignCenter, "Image non trouvée")

    def _update_bounding_box(self):
        self.setRect(0, 0, self.model_item.largeur_mm, self.model_item.hauteur_mm) 