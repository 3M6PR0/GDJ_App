from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon

class IconOnlyDelegate(QStyledItemDelegate):
    """
    Un délégué pour QComboBox qui dessine uniquement une icône,
    centrée, sans afficher de texte.
    """
    def __init__(self, parent=None, render_size=QSize(28, 28), actual_icon_size=QSize(24, 24)):
        super().__init__(parent)
        self.render_size = render_size
        self.actual_icon_size = actual_icon_size

    def paint(self, painter, option, index):
        """Dessine l'icône de l'item."""
        icon = index.data(Qt.DecorationRole)
        if not isinstance(icon, QIcon):
            return

        painter.save()
        rect = option.rect

        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, option.palette.highlight())

        # Dessiner l'icône à sa taille réelle, centrée dans le rectangle de l'item.
        pixmap = icon.pixmap(self.actual_icon_size) 
        x = rect.x() + (rect.width() - pixmap.width()) // 2
        y = rect.y() + (rect.height() - pixmap.height()) // 2
        
        painter.drawPixmap(x, y, pixmap)
        painter.restore()

    def sizeHint(self, option, index):
        """Retourne la taille pour chaque item, assurant une taille uniforme."""
        return self.render_size 