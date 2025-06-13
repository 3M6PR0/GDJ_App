from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QPixmap, QPainter
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
            # Dessiner l'image à la taille de l'élément
            painter.drawPixmap(self.rect().toRect(), self.pixmap)
        else:
            painter.setPen(Qt.red)
            painter.drawRect(self.rect())
            painter.drawText(self.rect(), Qt.AlignCenter, "Image non trouvée")

    def _update_bounding_box(self):
        self.setRect(0, 0, self.model_item.largeur_mm, self.model_item.hauteur_mm) 