from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QFileDialog, QListWidgetItem, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtCore import Qt, QSize
import os
from utils.image_manager import ImageManager

class ImageSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choisir une image")
        self.resize(800, 600)  # Fenêtre plus grande
        self.image_manager = ImageManager.get_instance()
        self.selected_image = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Titre
        title_label = QLabel("Images disponibles :")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Liste des images en mode icônes
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(QSize(128, 128))
        self.list_widget.setSpacing(15)
        self.list_widget.setResizeMode(QListWidget.Adjust) # Ajustement dynamique
        self.list_widget.setMovement(QListWidget.Static) # Empêche le drag-drop
        layout.addWidget(self.list_widget)

        # Label pour le nom du fichier sélectionné
        self.selected_file_label = QLabel("Aucune image sélectionnée")
        self.selected_file_label.setAlignment(Qt.AlignCenter)
        self.selected_file_label.setStyleSheet("margin-top: 10px; font-style: italic;")
        layout.addWidget(self.selected_file_label)

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
            
            # Créer une vignette carrée avec l'image centrée
            original_pixmap = QPixmap(img_path)
            if not original_pixmap.isNull():
                icon_size = QSize(128, 128)
                
                # Créer un pixmap de fond carré et transparent
                final_pixmap = QPixmap(icon_size)
                final_pixmap.fill(Qt.transparent)

                # Redimensionner l'image originale pour qu'elle tienne dans le carré
                scaled_pixmap = original_pixmap.scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # Dessiner l'image redimensionnée au centre du fond
                painter = QPainter(final_pixmap)
                x = (icon_size.width() - scaled_pixmap.width()) / 2
                y = (icon_size.height() - scaled_pixmap.height()) / 2
                painter.drawPixmap(int(x), int(y), scaled_pixmap)
                painter.end()

                icon = QIcon(final_pixmap)
                item.setIcon(icon)
            
            # Ne pas afficher le texte ici, on l'affichera en bas
            # item.setText(os.path.basename(img_path))
            item.setData(Qt.UserRole, img_path)  # Stocker le chemin complet
            item.setToolTip(os.path.basename(img_path)) # Afficher au survol
            
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
        
        # Mettre à jour le label du nom de fichier
        if has_selection:
            file_path = current.data(Qt.UserRole)
            self.selected_file_label.setText(os.path.basename(file_path))
        else:
            self.selected_file_label.setText("Aucune image sélectionnée")

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