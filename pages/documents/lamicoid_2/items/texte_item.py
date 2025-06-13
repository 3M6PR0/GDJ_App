"""Définit l'item graphique pour un élément de texte."""

from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QObject, pyqtSignal

from models.documents.lamicoid_2.elements import ElementTexte
from .base_item import EditableItemBase

class SelectionSignalHelper(QObject):
    element_selected = pyqtSignal(object)

class TexteItem(EditableItemBase):
    """
    Un item éditable qui affiche un élément de texte.
    La boîte englobante est gérée par EditableItemBase.
    """
    def __init__(self, element_texte: ElementTexte, parent: QGraphicsItem = None):
        super().__init__(model_item=element_texte, parent=parent)
        self.signal_helper = SelectionSignalHelper()
        self.setPos(self.model_item.x_mm, self.model_item.y_mm)
        
        # Mettre à jour la géométrie de la boîte en fonction du texte
        self._update_bounding_box()

    def _update_bounding_box(self):
        """Ajuste le rectangle de l'item à la taille du texte."""
        font = QFont(self.model_item.nom_police, self.model_item.taille_police_pt)
        # Utiliser un QGraphicsTextItem temporaire pour calculer la taille
        temp_text_item = QGraphicsTextItem(self.model_item.contenu)
        temp_text_item.setFont(font)
        text_rect = temp_text_item.boundingRect()
        self.setRect(0, 0, text_rect.width(), text_rect.height())

    def paint(self, painter, option, widget=None):
        # 1. Laisser la classe de base dessiner le cadre de sélection si nécessaire
        super().paint(painter, option, widget)

        # 2. Dessiner le texte
        painter.setPen(QColor(Qt.black))
        font = QFont(self.model_item.nom_police, self.model_item.taille_police_pt)
        font.setBold(getattr(self.model_item, 'bold', False))
        font.setItalic(getattr(self.model_item, 'italic', False))
        font.setUnderline(getattr(self.model_item, 'underline', False))
        painter.setFont(font)
        # Utiliser l'alignement du modèle
        align = getattr(self.model_item, 'align', Qt.AlignHCenter)
        painter.drawText(self.rect(), align | Qt.AlignVCenter, self.model_item.contenu)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Surcharge pour mettre à jour le modèle après un déplacement."""
        if change == QGraphicsItem.ItemSelectedChange:
            print(f"[DEBUG] TexteItem sélection changée : {value}")
            self.signal_helper.element_selected.emit(self if value else None)
        if change == QGraphicsItem.ItemPositionHasChanged:
            # La nouvelle position est 'value' (un QPointF)
            # NOTE: Pour l'instant, on met à jour avec les coordonnées de la scène (pixels)
            # La conversion en mm se fera plus tard.
            self.model_item.x_mm = value.x()
            self.model_item.y_mm = value.y()
        
        # Appeler l'implémentation de la classe de base pour gérer la sélection, etc.
        return super().itemChange(change, value)

    def set_alignment(self, alignment):
        """Définit l'alignement du texte."""
        self.model_item.align = alignment
        self.update()  # Force le redessinage de l'item 