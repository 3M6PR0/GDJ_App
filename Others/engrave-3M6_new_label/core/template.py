import time
import cairosvg
from copy import deepcopy
from enum import IntEnum
from io import BytesIO
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPalette, QColor
from PyQt5.QtWidgets import QPushButton, QLabel, QCheckBox, QSizePolicy, QSpacerItem, QGridLayout, QWidget, QFrame
from core.widgets import Entry

class LabelCode(IntEnum):
    CSA = 0
    FUSE = 1
    CURRENT = 2
    JACMAR = 3

class DataLabel:
    def __init__(self):
        self.x = 5
        self.y = 5
        self.w = 110
        self.h = 40

class Label:
    margin = 2
    code = -1
    def __init__(self):
        self.data = None
        self._text_spacing = 2.5
        self._lbl_base_height = 41
        self._highlight = True
        self._svg_str = ""
        self._changed = True

    def updated(self):
        self._changed = True

    def copy(self):
        return deepcopy(self)

    @property
    def x(self):
        return self.data.x
    @property
    def y(self):
        return self.data.y
    @x.setter
    def x(self, val):
        self._changed = True
        self.data.x = val
    @y.setter
    def y(self, val):
        self._changed = True
        self.data.y = val
    @property
    def width(self):
        return self.data.w
    @property
    def height(self):
        return self.data.h
    @property
    def highlight(self):
        return self._highlight
    @highlight.setter
    def highlight(self, state):
        self._changed = True
        self._highlight = state

    def within_bbox(self, x, y, margin=0.0):
        x_range = (self.x - margin) < x < (self.x + self.width + margin)
        y_range = (self.y - margin) < y < (self.y + self.height + margin)
        return x_range and y_range

    def overlaps(self, l: 'Label', margin=0.0) -> bool:
        x_overlap = (self.x - margin < l.x + l.width and self.x + self.width + margin > l.x)
        y_overlap = (self.y - margin < l.y + l.height and self.y + self.height + margin > l.y)
        return x_overlap and y_overlap

    def center(self) -> tuple:
        return self.x + self.width / 2, self.y + self.height / 2

    def changed(self):
        return self._changed

    def get_svg(self, headers=True, final=False):
        raise NotImplementedError

    def get_pixmap(self, width, height):
        png_output = BytesIO()
        try:
            cairosvg.svg2png(bytestring=self.get_svg().encode('utf-8'),
                            write_to=png_output,
                            output_width=width,
                            output_height=height)
        except Exception as e:
             print("Error generating PNG from SVG:", e)
             return
        png_output.seek(0)
        pixmap = QPixmap()
        if not pixmap.loadFromData(png_output.read()):
            print("Failed to load pixmap from SVG.")
            return
        return pixmap

    def save(self, path_out):
        path_out += "gencsa_" + str(time.time()) + ".svg"
        with open(path_out, 'w', encoding='utf-8') as f:
            f.write(self.get_svg(final=True))


class EditorTemplate(QWidget):
    def __init__(self, root, label_type):
        super().__init__()
        self._root = root
        self._label_type = label_type
        self._label_callback = None
        self._row_counter = 0

        layout_widget = QWidget()
        layout_widget.setPalette(QPalette(QColor("#e0e0e0")))
        layout_widget.setAutoFillBackground(True)
        layout_widget.setFixedWidth(400)
        self._layout = QGridLayout(layout_widget)
        self.create_layout()

        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self._layout.addItem(spacer, self._row_counter, 0, 1, 3)
        self._root.stacked_widget.addWidget(layout_widget)

    def _increment_row(self, step=1):
        """ Helper function to increment the row counter by a given number of rows. """
        current_row = self._row_counter
        self._row_counter += step
        return current_row

    def _create_separator(self):
        """ Adds a separator to the layout, spanning across all columns. """
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setContentsMargins(5, 20, 5, 20)
        row = self._increment_row()
        self._layout.addWidget(separator, row, 0, 1, self._layout.columnCount())

    def _create_entry(self, text, value, on_change, presets=None):
        """ Adds an entry with a label. """
        row = self._increment_row()
        text_entry = Entry(presets)
        text_entry.setText(str(value))
        text_entry.textChanged.connect(on_change)
        self._layout.addWidget(QLabel(text), row, 0)
        self._layout.addWidget(text_entry, row, 1, 1, 2)
        return text_entry

    def _create_checkbox(self, text, on_change, state=0):
        """ Adds a checkbox with a label. """
        row = self._increment_row()
        checkbox = QCheckBox()
        checkbox.setCheckState(state)
        checkbox.stateChanged.connect(on_change)
        self._layout.addWidget(QLabel(text), row, 0)
        self._layout.addWidget(checkbox, row, 1, 1, 2)
        return checkbox

    def _create_line_entry(self, heads, on_add, on_rm, presets=None):
        """ Adds multiple entries in a row with an 'Add' and 'Remove' button. """
        row = self._increment_row()
        _items = []
        presets = [None for _ in heads] if presets is None else presets
        assert len(heads) == len(presets)

        for j, h in enumerate(heads):
            self._layout.addWidget(QLabel(h), row, j, Qt.AlignTop)
            e = Entry(presets=presets[j])
            self._layout.addWidget(e, row + 1, j, Qt.AlignTop)
            _items.append(e)

        add_button = QPushButton("Add")
        rm_button = QPushButton("Remove")
        add_button.clicked.connect(on_add)
        rm_button.clicked.connect(on_rm)

        self._layout.addWidget(add_button, row + 2, 0, Qt.AlignTop)
        self._layout.addWidget(rm_button, row + 2, 2, Qt.AlignTop)
        self._increment_row(3)
        return _items

    def _create_text(self, text):
        """ Adds a label that spans across all columns. """
        row = self._increment_row()
        column_count = self._layout.columnCount()
        label = QLabel(text)
        self._layout.addWidget(label, row, 0, 1, column_count)

    def attach(self, lbl):
        self._label_callback = None
        if lbl:
            self.set_data(lbl)
            lbl.highlight = True
            self._label_callback = lbl
        self._root.update_display()

    def detach(self):
        if self._label_callback:
            self._label_callback.highlight = False
        self._label_callback = None

    def callback_label(self):
        return self._label_callback

    def set_data(self, label):
        pass

    def update_data(self):
        pass

    def bring_up(self):
        self._root.cb_select_editor(self._label_type.code)

    def create_label(self):
        lbl = self._label_type()
        lbl.x += 10
        lbl.y += 10
        return lbl