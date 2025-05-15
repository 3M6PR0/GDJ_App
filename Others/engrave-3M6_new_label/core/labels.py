from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer
from core.static import inch2mm
from core.xml_templates import get_header, get_footer

class Labels:
    def __init__(self):
        self._labels = []
        self._svg_str = ""
        self._width = inch2mm(24)
        self._height = inch2mm(12)

    def add(self, lbl):
        self._labels.append(lbl)

    def remove(self, lbl):
        self._labels.remove(lbl)

    def get_svg(self, final=False):
        self._svg_str = ""
        self._svg_str += get_header(self._width, self._height, final=final).strip()
        for lbl in self._labels:
            self._svg_str += lbl.get_svg(headers=False, final=final)
        self._svg_str += get_footer().strip()
        return self._svg_str

    def get_pixmap(self, width, height):
        svg_data = self.get_svg().encode('utf-8')
        svg_renderer = QSvgRenderer(svg_data)
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(0,0,0,0))
        painter = QPainter(pixmap)
        svg_renderer.render(painter)
        painter.end()
        return pixmap

    def save(self, name):
        with open(name + ".svg", 'w', encoding='utf-8') as f:
            f.write(self.get_svg(final=True))
    def width(self):
        return self._width
    def height(self):
        return self._height
    def __iter__(self):
        return iter(self._labels)