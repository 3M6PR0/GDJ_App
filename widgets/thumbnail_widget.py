import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy, QApplication
)
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QBitmap, QColor, QPainterPath, QMouseEvent
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QRectF
import logging # Ajout pour le logger

# Initialisation du logger
logger = logging.getLogger('GDJ_App')

# --- Try importing icon loader, fallback to text if unavailable ---
try:
    from utils.icon_loader import get_icon_path
    ICON_LOADER_AVAILABLE = True
except ImportError:
    ICON_LOADER_AVAILABLE = False
    logger.warning("WARN: utils.icon_loader not found, using text 'X' for delete button.") # Remplacement de print
# -------------------------------------------------------------

# --- NOUVELLE CLASSE INTERNE --- 
class RoundedImageWidget(QWidget):
    clicked = pyqtSignal()
    def __init__(self, pixmap: QPixmap, size: QSize, border_radius: int = 8, parent=None):
        super().__init__(parent)
        self._pixmap = pixmap
        self._border_radius = border_radius
        self.setFixedSize(size)

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update() # Redemander un dessin

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self._border_radius, self._border_radius)
        
        # Définir le chemin de découpe
        painter.setClipPath(path)

        # Dessiner le pixmap dans le rectangle du widget
        # Le pixmap a déjà été mis à l'échelle avec KeepAspectRatioByExpanding
        painter.drawPixmap(self.rect(), self._pixmap)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        # Laisser le parent gérer d'autres événements souris si besoin
        # super().mousePressEvent(event) # Décommenter si nécessaire
# ----------------------------- 

class ThumbnailWidget(QWidget):
    """ 
    Widget pour afficher une miniature d'image/PDF avec un bouton de suppression.
    Émet un signal `delete_requested(file_path)` lors du clic sur le bouton 'X'.
    """
    delete_requested = pyqtSignal(str) # Signal émis avec le chemin du fichier
    clicked = pyqtSignal(str)

    THUMBNAIL_SIZE = 100 # Taille cible (largeur/hauteur) pour la miniature

    def __init__(self, file_path: str, pixmap: QPixmap, show_delete_button: bool = True, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._border_radius = 8 # Stocker le radius ici aussi

        # Layout principal vertical (Image + Nom de fichier)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(4)
        self.setLayout(main_layout)

        # --- Mise à l'échelle du Pixmap (fait ici une seule fois) --- 
        scaled_pixmap = pixmap.scaled(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE,
                                      Qt.KeepAspectRatioByExpanding,
                                      Qt.SmoothTransformation)
        # -----------------------------------------------------------

        # --- MODIFICATION: Utiliser RoundedImageWidget --- 
        # image_container = QWidget()
        # image_container.setFixedSize(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE)
        # image_container.setStyleSheet("background-color: transparent;") 
        self.image_container = RoundedImageWidget(scaled_pixmap, 
                                                QSize(self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE), 
                                                self._border_radius)
        self.image_container.clicked.connect(self._emit_thumbnail_clicked)
        # --------------------------------------------------

        # --- Création conditionnelle du bouton de suppression --- 
        self.delete_button = None
        if show_delete_button:
            self.delete_button = QPushButton(self.image_container) # Parent = image_container (le RoundedImageWidget)
            self.delete_button.setFixedSize(18, 18)
            self.delete_button.setToolTip("Supprimer cette facture")
            self.delete_button.setCursor(Qt.PointingHandCursor)
            self.delete_button.clicked.connect(self._emit_delete_signal)

            # Style du bouton 'X'
            delete_icon_path = None
            if ICON_LOADER_AVAILABLE:
                delete_icon_path = get_icon_path("round_cancel.png") # Utiliser une icône si possible

            if delete_icon_path:
                self.delete_button.setIcon(QIcon(delete_icon_path))
                self.delete_button.setIconSize(QSize(12, 12)) # Ajuster taille icône
                self.delete_button.setText("") # Pas de texte si icône
                # Style pour bouton icône rond rouge
                self.delete_button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(200, 50, 50, 0.85);
                        border-radius: 9px; /* Cercle */
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: rgba(230, 50, 50, 1.0);
                    }
                    QPushButton:pressed {
                        background-color: rgba(180, 40, 40, 1.0);
                    }
                """)
            else:
                # Style pour bouton texte 'X' si icône indisponible
                self.delete_button.setText("✕")
                self.delete_button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(200, 50, 50, 0.8);
                        color: white;
                        border: none;
                        border-radius: 9px;
                        font-weight: bold;
                        font-size: 10px;
                        padding-bottom: 1px; /* Ajustement vertical du texte */
                    }
                    QPushButton:hover {
                        background-color: rgba(230, 50, 50, 1.0);
                    }
                    QPushButton:pressed {
                        background-color: rgba(180, 40, 40, 1.0);
                    }
                """)

            # Positionner le bouton dans le coin supérieur droit du conteneur arrondi
            # S'assurer que image_container a déjà une taille définie avant move()
            # Note: move peut être appelé plus tard si la taille n'est pas garantie ici
            self.delete_button.move(self.image_container.width() - self.delete_button.width() - 2, 2)
        # --------------------------------------------------------

        # Ajouter le conteneur d'image arrondi au layout principal
        main_layout.addWidget(self.image_container)

        # Label pour le nom de fichier (tronqué)
        file_name = os.path.basename(file_path)
        # Simple troncature si trop long (pourrait être amélioré avec QFontMetrics)
        max_len = 20
        display_name = (file_name[:max_len] + '...') if len(file_name) > max_len else file_name
        file_name_label = QLabel(display_name)
        file_name_label.setAlignment(Qt.AlignCenter)
        file_name_label.setToolTip(file_path) # Tooltip montre le chemin complet
        file_name_label.setMaximumWidth(self.THUMBNAIL_SIZE + 10) # Un peu plus large que l'image
        file_name_label.setStyleSheet("font-size: 9px; color: #BBB;") # Police plus petite/grise
        main_layout.addWidget(file_name_label)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) # Le widget prend sa taille naturelle

    def _emit_delete_signal(self):
        self.delete_requested.emit(self.file_path)

    def _emit_thumbnail_clicked(self):
        self.clicked.emit(self.file_path)

# --- Bloc de test ---
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Créer un QWidget pour contenir plusieurs thumbnails
    container = QWidget()
    layout = QHBoxLayout(container)

    # Créer quelques pixmaps de test
    pixmap1 = QPixmap(150, 100); pixmap1.fill(Qt.blue)
    pixmap2 = QPixmap(80, 120); pixmap2.fill(Qt.green)
    pixmap3 = QPixmap(100, 100); pixmap3.fill(Qt.red)

    thumb1 = ThumbnailWidget("/dossier/facture_A.pdf", pixmap1)
    thumb2 = ThumbnailWidget("/autre/image_looooongue.jpg", pixmap2)
    thumb3 = ThumbnailWidget("C:/test.png", pixmap3)

    layout.addWidget(thumb1)
    layout.addWidget(thumb2)
    layout.addWidget(thumb3)

    def on_delete(path):
        logger.info(f"--- Signal reçu: Supprimer {path} ---") # Remplacement de print par logger.info
        # Trouver le widget correspondant et le supprimer (simulation)
        # sender_widget = app.sender().parent() # Le bouton est enfant du container, qui est enfant du ThumbnailWidget? Non.
                                             # Plus fiable de chercher dans le layout
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, ThumbnailWidget) and widget.file_path == path:
                logger.info(f"Widget trouvé pour {path}, suppression...") # Remplacement de print par logger.info
                widget.deleteLater()
                break

    thumb1.delete_requested.connect(on_delete)
    thumb2.delete_requested.connect(on_delete)
    thumb3.delete_requested.connect(on_delete)

    container.setWindowTitle("Test ThumbnailWidget")
    container.show()
    sys.exit(app.exec_()) 