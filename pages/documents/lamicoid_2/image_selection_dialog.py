from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QFileDialog, QListWidgetItem, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
import os
from utils.image_manager import ImageManager

class ImageSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choisir une image")
        self.setMinimumSize(500, 400)
        self.image_manager = ImageManager.get_instance()
        self.selected_image = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Titre
        title_label = QLabel("Images disponibles :")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Liste des images
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(64, 64))
        self.list_widget.setSpacing(5)
        layout.addWidget(self.list_widget)

        # Boutons
        btn_layout = QHBoxLayout()
        self.add_button = QPushButton("Importer une nouvelle image...")
        self.add_button.setStyleSheet("QPushButton { padding: 8px; }")
        self.select_button = QPushButton("Sélectionner")
        self.select_button.setEnabled(False)
        self.select_button.setStyleSheet("QPushButton { padding: 8px; }")
        self.delete_button = QPushButton("Supprimer")
        self.delete_button.setEnabled(False)
        self.delete_button.setStyleSheet("QPushButton { padding: 8px; }")
        
        btn_layout.addWidget(self.add_button)
        btn_layout.addStretch()
        btn_layout.addWidget(self.delete_button)
        btn_layout.addWidget(self.select_button)
        layout.addLayout(btn_layout)

        # Connexions
        self.add_button.clicked.connect(self._on_add_image)
        self.select_button.clicked.connect(self._on_select)
        self.delete_button.clicked.connect(self._on_delete)
        self.list_widget.currentItemChanged.connect(self._on_item_selected)

        # Charger les images
        self._populate_list()

    def _populate_list(self):
        """Charge la liste des images depuis le gestionnaire d'images."""
        self.list_widget.clear()
        images = self.image_manager.get_all_images()
        
        for img_path in images:
            item = QListWidgetItem()
            
            # Créer l'aperçu de l'image
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                # Redimensionner pour l'aperçu
                scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon = QIcon(scaled_pixmap)
                item.setIcon(icon)
            
            # Nom du fichier
            item.setText(os.path.basename(img_path))
            item.setData(Qt.UserRole, img_path)  # Stocker le chemin complet
            
            self.list_widget.addItem(item)

    def _on_add_image(self):
        """Importe une nouvelle image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Importer une image", 
            "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.svg)"
        )
        
        if file_path:
            # Importer l'image via le gestionnaire
            imported_path = self.image_manager.import_image(file_path)
            if imported_path:
                self._populate_list()
                QMessageBox.information(self, "Succès", "Image importée avec succès !")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible d'importer l'image.")

    def _on_item_selected(self, current, previous):
        """Active/désactive les boutons selon la sélection."""
        has_selection = current is not None
        self.select_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _on_select(self):
        """Sélectionne l'image actuelle."""
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_image = current_item.data(Qt.UserRole)
            self.accept()

    def _on_delete(self):
        """Supprime l'image sélectionnée."""
        current_item = self.list_widget.currentItem()
        if current_item:
            image_path = current_item.data(Qt.UserRole)
            
            # Demander confirmation
            reply = QMessageBox.question(
                self, 
                "Confirmation", 
                f"Voulez-vous vraiment supprimer l'image '{os.path.basename(image_path)}' ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.image_manager.delete_image(image_path):
                    self._populate_list()
                    QMessageBox.information(self, "Succès", "Image supprimée avec succès !")
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible de supprimer l'image.")

    def get_selected_image(self):
        """Retourne le chemin de l'image sélectionnée."""
        return self.selected_image 