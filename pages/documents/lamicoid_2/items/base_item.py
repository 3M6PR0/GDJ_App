import logging
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem, QStyle
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter

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
        self.handle_size = 8.0
        self.handles = {}
        self.current_handle = None
        self.mouse_press_pos = None
        self.mouse_press_rect = None

        self.setAcceptHoverEvents(True)
        
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        # Définir le style par défaut (bordure solide)
        self._default_pen = QPen(QColor(Qt.black), 1, Qt.SolidLine)
        self.setPen(self._default_pen)

    def boundingRect(self) -> QRectF:
        """
        Retourne le rectangle englobant.
        Cette zone doit inclure le rectangle de base, la largeur du stylo,
        et la taille des poignées de redimensionnement si l'objet est sélectionné.
        """
        pen_width = self.pen().widthF()
        half_pen_width = pen_width / 2.0

        # Marge pour les poignées, uniquement si sélectionné
        handle_margin = self.handle_size / 2.0 if self.isSelected() else 0.0

        # La marge totale est la somme de la marge du stylo et des poignées
        margin = half_pen_width + handle_margin
        
        # On part du rectangle de base de l'item
        base_rect = self.rect()

        # Et on l'ajuste pour inclure les marges
        return base_rect.adjusted(-margin, -margin, margin, margin)

    def paint(self, painter: QPainter, option, widget=None):
        """Dessine l'item et ses poignées de redimensionnement si sélectionné."""
        super().paint(painter, option, widget)

        if self.isSelected():
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor("#007ACC")))
            painter.setPen(QPen(QColor(Qt.white), 1))

            for handle, rect in self.handles.items():
                painter.drawRect(rect)

    def itemChange(self, change, value):
        """Appelé lorsque l'état de l'item change, notamment la sélection."""
        if change == QGraphicsItem.ItemSelectedChange:
            self.update_selection_visuals(bool(value))
        elif change == QGraphicsItem.ItemPositionChange and self.isSelected():
            # Mettre à jour la position des poignées lors du déplacement
            self.update_handles_pos()
        return super().itemChange(change, value)

    def update_selection_visuals(self, is_selected: bool):
        """Met à jour l'apparence de l'item en fonction de son état de sélection."""
        if is_selected:
            selection_pen = QPen(QColor("#007ACC"), 1.5)
            selection_pen.setStyle(Qt.DashLine)
            self.setPen(selection_pen)
        else:
            # Rétablir l'apparence par défaut
            self.setPen(self._default_pen)
        
        # Mettre à jour la position des poignées
        if is_selected:
            self.update_handles_pos()
        
        self.update()

    def update_handles_pos(self):
        """Met à jour la position des poignées de redimensionnement."""
        s = self.handle_size
        r = self.rect()
        self.handles['top_left'] = QRectF(r.left() - s/2, r.top() - s/2, s, s)
        self.handles['top_right'] = QRectF(r.right() - s/2, r.top() - s/2, s, s)
        self.handles['bottom_left'] = QRectF(r.left() - s/2, r.bottom() - s/2, s, s)
        self.handles['bottom_right'] = QRectF(r.right() - s/2, r.bottom() - s/2, s, s)

    def hoverMoveEvent(self, event):
        """Change le curseur si la souris est sur une poignée."""
        handle = self.handle_at(event.pos())
        if handle:
            if handle in ['top_left', 'bottom_right']:
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)
    
    def mousePressEvent(self, event):
        """Initialise le redimensionnement si on clique sur une poignée."""
        self.current_handle = self.handle_at(event.pos())
        if self.current_handle:
            self.mouse_press_pos = event.pos()
            self.mouse_press_rect = self.rect()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Effectue le redimensionnement si une poignée est sélectionnée."""
        if self.current_handle:
            self.interactive_resize(event.pos())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Finalise le redimensionnement."""
        super().mouseReleaseEvent(event)
        self.current_handle = None
        self.mouse_press_pos = None
        self.mouse_press_rect = None
        self.update()

    def handle_at(self, pos: QPointF):
        """Retourne la poignée à une position donnée, ou None."""
        for handle, rect in self.handles.items():
            if rect.contains(pos):
                return handle
        return None

    def interactive_resize(self, mouse_pos: QPointF):
        """Met à jour le rectangle de l'item pendant un redimensionnement interactif."""
        rect = self.rect()
        diff = mouse_pos - self.mouse_press_pos

        self.prepareGeometryChange()

        if self.current_handle == 'top_left':
            rect.setTopLeft(self.mouse_press_rect.topLeft() + diff)
        elif self.current_handle == 'top_right':
            rect.setTopRight(self.mouse_press_rect.topRight() + diff)
        elif self.current_handle == 'bottom_left':
            rect.setBottomLeft(self.mouse_press_rect.bottomLeft() + diff)
        elif self.current_handle == 'bottom_right':
            rect.setBottomRight(self.mouse_press_rect.bottomRight() + diff)

        self.setRect(rect)
        self.update_handles_pos()
        self.update()

    def get_model_id(self) -> str:
        """Retourne l'ID du modèle de données associé."""
        return self.model_item.element_id 