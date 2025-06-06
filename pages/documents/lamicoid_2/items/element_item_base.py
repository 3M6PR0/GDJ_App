# pages/documents/lamicoid_2/items/element_item_base.py
import logging
from PyQt5.QtWidgets import QGraphicsObject, QGraphicsItem, QGraphicsEllipseItem
from PyQt5.QtGui import QPen, QColor, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal

from utils.conversions import mm_to_pixels, pixels_to_mm

class ElementItemBase(QGraphicsObject):
    """
    Classe de base pour tous les éléments graphiques dans l'éditeur.
    Gère la sélection, le déplacement, le redimensionnement et le magnétisme.
    """
    
    element_changed = pyqtSignal('QGraphicsObject')
    
    HANDLE_SIZE = 10
    
    def __init__(self, element_data, view, parent=None):
        super().__init__(parent)
        
        self.element = element_data
        self.view = view # Référence à la vue pour le magnétisme
        self._handles = []
        self._handle_positions = [
            QPointF(0, 0), QPointF(0.5, 0), QPointF(1, 0), QPointF(0, 0.5),
            QPointF(1, 0.5), QPointF(0, 1), QPointF(0.5, 1), QPointF(1, 1)
        ]
        self.current_handle = None
        self.mouse_press_pos = None
        self.mouse_press_rect = None

        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self._create_handles()

    def setRect(self, rect):
        self.prepareGeometryChange()
        self.setPos(rect.topLeft())
        # La géométrie de l'item lui-même est relative à sa position, donc (0,0)
        self.element.x_mm = pixels_to_mm(rect.x())
        self.element.y_mm = pixels_to_mm(rect.y())
        self.element.largeur_mm = pixels_to_mm(rect.width())
        self.element.hauteur_mm = pixels_to_mm(rect.height())
        self.update_handles()
        self.update()

    def rect(self):
        return QRectF(0, 0, mm_to_pixels(self.element.largeur_mm), mm_to_pixels(self.element.hauteur_mm))

    def boundingRect(self):
        # Ajouter une marge pour inclure les poignées
        handle_margin = self.HANDLE_SIZE
        return self.rect().adjusted(-handle_margin, -handle_margin, handle_margin, handle_margin)

    def paint(self, painter, option, widget=None):
        if self.isSelected():
            pen = QPen(QColor("#007ACC"), 2, Qt.DashLine)
            painter.setPen(pen)
            
            # Dessin d'un fond très léger pour indiquer la zone
            background_rect = self.rect()
            painter.setBrush(QColor(0, 122, 204, 20)) 
            painter.drawRect(background_rect)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.view:
            # Magnétisme lors du déplacement
            return self.view.snap_point_to_grid(value)
        
        if change == QGraphicsItem.ItemSelectedChange and value:
            self.element_changed.emit(self)
            
        return super().itemChange(change, value)
        
    def hoverEnterEvent(self, event):
        self._show_handles(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._show_handles(False)
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event):
        self.mouse_press_pos = event.pos()
        self.mouse_press_rect = self.rect()
        
        # Déterminer si un handle est cliqué
        for i, h in enumerate(self._handles):
            if h.isUnderMouse():
                self.current_handle = i
                break
        else:
            self.current_handle = None
        
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.current_handle is not None:
            self.setCursor(Qt.BlankCursor) # Cacher le curseur pendant le redimensionnement
            self._resize(event.pos())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        self.current_handle = None
        self.mouse_press_pos = None
        self.mouse_press_rect = None
        
        # Émettre le signal que l'élément a changé
        self.element_changed.emit(self)
        super().mouseReleaseEvent(event)

    def _create_handles(self):
        """Crée les 8 poignées de redimensionnement."""
        for _ in self._handle_positions:
            handle = QGraphicsEllipseItem(self)
            handle.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            handle.setPen(QPen(QColor("red"), 2))
            handle.setBrush(QBrush(QColor("red")))
            self._handles.append(handle)
        self.update_handles()
        self._show_handles(False)
        
    def _show_handles(self, show):
        for handle in self._handles:
            handle.setVisible(show)

    def update_handles(self):
        """Met à jour la position des poignées."""
        rect = self.rect()
        for i, pos_factor in enumerate(self._handle_positions):
            x = rect.left() + rect.width() * pos_factor.x()
            y = rect.top() + rect.height() * pos_factor.y()
            handle_rect = QRectF(x - self.HANDLE_SIZE / 2, y - self.HANDLE_SIZE / 2, self.HANDLE_SIZE, self.HANDLE_SIZE)
            self._handles[i].setRect(handle_rect)
            
    def _resize(self, new_pos):
        rect = self.rect()
        new_rect = QRectF(self.mouse_press_rect)
        delta = new_pos - self.mouse_press_pos

        if self.current_handle in [0, 3, 5]: # Left handles
            new_rect.setLeft(self.mouse_press_rect.left() + delta.x())
        if self.current_handle in [0, 1, 2]: # Top handles
            new_rect.setTop(self.mouse_press_rect.top() + delta.y())
        if self.current_handle in [2, 4, 7]: # Right handles
            new_rect.setRight(self.mouse_press_rect.right() + delta.x())
        if self.current_handle in [5, 6, 7]: # Bottom handles
            new_rect.setBottom(self.mouse_press_rect.bottom() + delta.y())
        
        # S'assurer que le rectangle ne s'inverse pas
        if new_rect.width() < self.HANDLE_SIZE:
            if self.current_handle in [0, 3, 5]: new_rect.setLeft(new_rect.right() - self.HANDLE_SIZE)
            else: new_rect.setRight(new_rect.left() + self.HANDLE_SIZE)
        if new_rect.height() < self.HANDLE_SIZE:
            if self.current_handle in [0, 1, 2]: new_rect.setTop(new_rect.bottom() - self.HANDLE_SIZE)
            else: new_rect.setBottom(new_rect.top() + self.HANDLE_SIZE)

        # Magnétisme sur le point en cours de redimensionnement
        new_pos_scene = self.mapToScene(new_rect.topLeft() if self.current_handle == 0 else \
                                        new_rect.topRight() if self.current_handle == 2 else \
                                        new_rect.bottomLeft() if self.current_handle == 5 else \
                                        new_rect.bottomRight() if self.current_handle == 7 else \
                                        new_pos)
        snapped_pos_scene = self.view.snap_point_to_grid(new_pos_scene)
        snapped_delta = self.mapFromScene(snapped_pos_scene) - self.mapFromScene(new_pos_scene)
        new_rect.translate(snapped_delta)

        # Appliquer la nouvelle géométrie
        self.prepareGeometryChange()
        self.setPos(self.pos() + new_rect.topLeft())
        self.element.x_mm = pixels_to_mm(self.pos().x())
        self.element.y_mm = pixels_to_mm(self.pos().y())
        self.element.largeur_mm = pixels_to_mm(new_rect.width())
        self.element.hauteur_mm = pixels_to_mm(new_rect.height())
        self.update_handles()
        self.update() 