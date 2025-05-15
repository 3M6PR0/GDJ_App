from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPainter
from core.static import pix2mm, mm2pix

class LabelDisplay(QLabel):
    def __init__(self, root, label_manager):
        super().__init__(root)
        self._root = root
        self._label_manager = label_manager
        self.setAlignment(Qt.AlignTop)
        self.pixmap = None
        self._margin = 200  # Margin in pixels
        # MOVEMENTS
        self.offset = QPoint(0, 0)
        self.last_mouse_position = QPoint()
        self.position_before_update = QPoint(0, 0)
        self.zoom_factor = 1.0
        self.min_zoom = 0.2
        self.max_zoom = 2.0
        self.dragging = False
        self.moving = False
        self._move_delta = None
        self._pressed_ctrl = False
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.update_pixmap()

    def update_pixmap(self):
        labels = self._label_manager.get_labels()
        w = int(mm2pix(labels.width()) * self.zoom_factor)
        h = int(mm2pix(labels.height()) * self.zoom_factor)
        self.pixmap = labels.get_pixmap(w, h)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.pixmap:
            painter = QPainter(self)
            painter.drawPixmap(self.offset, self.pixmap)

    def update(self):
        # Update offset
        d_width = self.width() - self.pixmap.width()
        d_height = self.height() - self.pixmap.height()
        min_x = d_width//2 if d_width >= 0 else d_width - self._margin
        max_x = d_width//2 if d_width >= 0 else self._margin
        min_y = d_height//2 if d_height >= 0 else d_height - self._margin
        max_y = d_height//2 if d_height >= 0 else self._margin
        offset_x = max(min_x, min(self.offset.x(), max_x))
        offset_y = max(min_y, min(self.offset.y(), max_y))
        self.offset = QPoint(offset_x, offset_y)
        super().update()

    ### EVENTS
    def wheelEvent(self, event):
        zoom_change = 0.2 if event.angleDelta().y() > 0 else -0.2
        new_zoom = max(self.min_zoom, min(self.zoom_factor + zoom_change, self.max_zoom))
        if new_zoom != self.zoom_factor:
            pos = event.pos()
            x_rel = (pos.x() - self.offset.x()) / self.zoom_factor
            y_rel = (pos.y() - self.offset.y()) / self.zoom_factor
            self.zoom_factor = new_zoom
            self.update_pixmap()
            new_x = pos.x() - x_rel * self.zoom_factor
            new_y = pos.y() - y_rel * self.zoom_factor
            self.offset = QPoint(int(new_x), int(new_y))
            self.update()
            event.accept()
        else:
            super().wheelEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.globalPos() - self.last_mouse_position
            self.offset = self.position_before_update + delta
            self.update()
            event.accept()
        elif self.moving:
            dt = event.globalPos() - self._move_delta
            self._move_delta = event.globalPos()
            new_x = dt.x() / (self.zoom_factor * 5)
            new_y = dt.y() / (self.zoom_factor * 5)
            self._label_manager.current_move(new_x, new_y)
            self.update_pixmap()
        else:
            super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.dragging = True
            self.last_mouse_position = event.globalPos()
            self.position_before_update = self.offset
            event.accept()
        elif event.button() == Qt.LeftButton:
            self.moving = True
            self._move_delta = event.globalPos()
            x_in_space = (event.x() - self.offset.x()) / self.zoom_factor
            y_in_space = (event.y() - self.offset.y()) / self.zoom_factor
            lbl = self._label_manager.label_at_pos(pix2mm(x_in_space), pix2mm(y_in_space))
            self._label_manager.select_label(lbl)
            self.update_pixmap()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.dragging = False
            event.accept()
        elif event.button() == Qt.LeftButton:
            self.moving = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self._label_manager.selected_delete()
            self.update_pixmap()
            event.accept()
        if event.key() == Qt.Key_Control:
            self._pressed_ctrl = True
        if event.key() == Qt.Key_C and self._pressed_ctrl:
            self._label_manager.copy()
        elif event.key() == Qt.Key_V and self._pressed_ctrl:
            self._label_manager.paste()
            self.update_pixmap()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self._pressed_ctrl = False