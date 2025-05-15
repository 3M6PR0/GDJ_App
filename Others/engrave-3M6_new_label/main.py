import os.path
import subprocess
import sys
import time
import cairosvg
import tempfile
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QStackedWidget, QPushButton, QMessageBox)
from PyQt5.QtGui import QPalette, QColor, QIcon
from core.editors.editor_csa import EditorCSA
from core.editors.editor_current import EditorCurrent
from core.editors.editor_fuse import EditorFuse
from core.editors.editor_jacmar import EditorJacmar
from core.label.label_csa import LabelCSA
from core.label.label_current import LabelCurrent
from core.label.label_fuse import LabelFuse
from core.label.label_jacmar import LabelJacmar
from core.label_manager import LabelManager
from core.labels import Labels
from core.label_display import LabelDisplay
from core.static import find_chrome_path, get_res_item, solve_rect_position
from core.template import LabelCode


class LabelCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1000, 600)
        self.setWindowTitle("Jacmar Label Creator")
        self.setWindowIcon(QIcon(get_res_item("app_icon.png")))
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.stacked_widget = QStackedWidget()
        self.create_left_section()
        editors = {
            LabelCode.CSA : EditorCSA(self, LabelCSA),
            LabelCode.FUSE : EditorFuse(self, LabelFuse),
            LabelCode.CURRENT : EditorCurrent(self, LabelCurrent),
            LabelCode.JACMAR : EditorJacmar(self, LabelJacmar)
        }
        self._labels = Labels()
        self.label_manager = LabelManager(self._labels, editors)
        self.create_display_section()
        self.update_display()

    def create_left_section(self):
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        # ComboBox and Add button layout
        combo_layout = QHBoxLayout()
        self.editor_selector = QComboBox()
        self.editor_selector.addItems(["Label CSA", "Label Fuses", "Label Current", "Label Jacmar"])
        self.editor_selector.currentIndexChanged.connect(self.cb_select_editor)
        combo_layout.addWidget(self.editor_selector)
        button_add = QPushButton("Add Label")
        button_add.clicked.connect(self.on_lbl_add)
        combo_layout.addWidget(button_add)
        left_layout.addLayout(combo_layout)
        self.stacked_widget = QStackedWidget()
        left_layout.addWidget(self.stacked_widget)
        # Print
        button_layout = QHBoxLayout()
        button_export = QPushButton("Export")
        button_export.clicked.connect(self.on_export_pdf)
        button_layout.addWidget(button_export)
        left_layout.addLayout(button_layout)
        self.main_layout.addWidget(self.left_panel, 1)

    def create_display_section(self):
        widget_display = QWidget()
        widget_display.setPalette(QPalette(QColor("#e0e0e0")))
        widget_display.setAutoFillBackground(True)
        layout_display = QVBoxLayout(widget_display)
        # DISPLAY CURRENT
        self._display = LabelDisplay(self, self.label_manager)
        self._display.setStyleSheet("border: 1px solid black;")
        self.update_display()
        layout_display.addWidget(self._display)
        self.main_layout.addWidget(widget_display, 2)

    def cb_select_editor(self, index):
        self.label_manager.set_editor_idx(index)
        self.stacked_widget.setCurrentIndex(index)
        self.editor_selector.setCurrentIndex(index)
        self.update_display()

    def update_display(self):
        solve_rect_position(self.label_manager.current_label(), self._labels, self._labels.width(), self._labels.height(), margin=2.0)
        self._display.update_pixmap()

    def on_export_pdf(self):
        temp_dir = tempfile.gettempdir()
        temp_pdf_path = os.path.join(temp_dir, f"tmp_{time.strftime('%Y_%m_%d_%H_%M_%S')}.pdf")
        cairosvg.svg2pdf(bytestring=self._labels.get_svg(final=True).encode('utf-8'), write_to=temp_pdf_path)

        chrome_path = find_chrome_path()
        if chrome_path:
            subprocess.Popen([chrome_path, temp_pdf_path], start_new_session=True)
        else:
            QMessageBox.warning(self, "Browser Not Found", "Google Chrome is not installed. Please install it to open result.\nIf it's installed, add Chrome to PATH.", QMessageBox.Ok)

    def on_export_svg(self):
        temp_dir = tempfile.gettempdir()
        temp_svg_path = os.path.join(temp_dir, f"tmp_{time.strftime('%Y_%m_%d_%H_%M_%S')}.svg")
        with open(temp_svg_path, "wb") as f:
            f.write(self._labels.get_svg(final=True).encode('utf-8'))
        chrome_path = find_chrome_path()
        if chrome_path:
            subprocess.Popen([chrome_path, temp_svg_path], start_new_session=True)
            print("SUB RUN")
        else:
            QMessageBox.warning(self, "Browser Not Found", "Google Chrome is not installed. Please install it to open result.\nIf it's installed, add Chrome to PATH.", QMessageBox.Ok)

    def on_lbl_add(self):
        self.label_manager.add()
        self.update_display()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LabelCreator()
    window.show()
    sys.exit(app.exec_())
