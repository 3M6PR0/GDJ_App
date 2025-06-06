import logging
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QBrush, QColor

from models.documents.lamicoid_2.elements import ElementTemplateBase

logger = logging.getLogger('GDJ_App')

class EditableItemBase(QGraphicsRectItem):
    """
    Classe de base pour tous les éléments graphiques éditables sur la scène.
    Fournit une bordure de sélection et la gestion de la sélection.
    """
    def __init__(self, model_item: ElementTemplateBase, parent: QGraphicsItem = None):
        super().__init__(parent)
        self.model_item = model_item
        
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        """Appelé lorsque l'état de l'item change, notamment la sélection."""
        if change == QGraphicsItem.ItemSelectedChange:
            self.update_selection_visuals(bool(value))
        return super().itemChange(change, value)

    def update_selection_visuals(self, is_selected: bool):
        """Met à jour l'apparence de l'item en fonction de son état de sélection."""
        if is_selected:
            selection_pen = QPen(QColor("#007ACC"), 1.5)
            selection_pen.setStyle(Qt.DashLine)
            self.setPen(selection_pen)
        else:
            # Rétablir l'apparence par défaut (aucune bordure pour la base)
            self.setPen(QPen(Qt.NoPen))
        self.update()

    def get_model_id(self) -> str:
        """Retourne l'ID du modèle de données associé."""
        return self.model_item.element_id 