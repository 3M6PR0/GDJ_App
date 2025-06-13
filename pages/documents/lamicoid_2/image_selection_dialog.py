from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QFileDialog, QListWidgetItem
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
import os

class ImageSelectionDialog(QDialog):
    def __init__(self, imported_images, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choisir une image")
        self.imported_images = imported_images  # Liste des chemins d'images
        self.selected_image = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self._populate_list()
        layout.addWidget(QLabel("Images importées :"))
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.add_button = QPushButton("Ajouter une image...")
        self.select_button = QPushButton("Sélectionner")
        self.select_button.setEnabled(False)
        btn_layout.addWidget(self.add_button)
        btn_layout.addWidget(self.select_button)
        layout.addLayout(btn_layout)

        self.add_button.clicked.connect(self._on_add_image)
        self.select_button.clicked.connect(self._on_select)
        self.list_widget.currentItemChanged.connect(self._on_item_selected)

    def _populate_list(self):
        self.list_widget.clear()
        for img_path in self.imported_images:
            item = QListWidgetItem(os.path.basename(img_path))
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                icon = QIcon(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                item.setIcon(icon)
            self.list_widget.addItem(item)

    def _on_add_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Importer une image", "", "Images (*.png *.jpg *.jpeg *.bmp *.svg)")
        if file_path:
            self.imported_images.append(file_path)
            self._populate_list()

    def _on_item_selected(self, current, previous):
        self.select_button.setEnabled(current is not None)

    def _on_select(self):
        current = self.list_widget.currentRow()
        if current >= 0:
            self.selected_image = self.imported_images[current]
            self.accept()

    def get_selected_image(self):
        return self.selected_image 