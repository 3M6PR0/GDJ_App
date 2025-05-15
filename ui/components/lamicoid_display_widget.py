from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

from models.documents.lamicoid.lamicoid import LamicoidDocument
from models.documents.lamicoid.lamicoid_item import LamicoidItem
import logging

logger = logging.getLogger('GDJ_App')

class LamicoidDisplayWidget(QLabel):
    """
    Widget destiné à afficher une représentation visuelle (potentiellement SVG rendue en QPixmap)
    d'un ensemble d'items Lamicoid contenus dans un LamicoidDocument.
    Inspiré par LabelDisplay du projet de référence 'engrave'.
    """
    def __init__(self, document: LamicoidDocument, parent=None):
        super().__init__(parent)
        self.document = document
        self.setObjectName("LamicoidDisplayWidget")
        
        # Configuration de base
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft) # Ou Qt.AlignCenter si on veut centrer le contenu
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(200, 200) # Taille minimale pour être visible

        # Appliquer un fond distinctif pour le moment
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#555555")) # Gris foncé pour le fond
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        self.setText("Zone d'affichage Lamicoid (Placeholder)") # Placeholder text
        self.setStyleSheet("QLabel { color: white; border: 1px solid #666666; padding: 10px; }")

        logger.debug(f"LamicoidDisplayWidget initialisé pour le document: {self.document.file_name if self.document else 'None'}")

    def update_display(self):
        """
        Cette méthode sera appelée pour rafraîchir l'affichage.
        Pour l'instant, elle ne fait rien de plus, mais elle sera cruciale
        quand nous implémenterons le rendu SVG.
        """
        # Exemple futur:
        # pixmap = self.document.get_pixmap_representation(self.width(), self.height())
        # if pixmap:
        #     self.setPixmap(pixmap)
        # else:
        #     self.setText("Erreur de rendu ou document vide.")
        logger.debug("LamicoidDisplayWidget.update_display() appelée (actuellement un no-op).")
        # Pour l'instant, s'assurer que le texte placeholder reste si pas de pixmap
        if not self.pixmap(): # Vérifie si un pixmap est déjà défini
             self.setText(f"Zone d'affichage Lamicoid\nDocument: {self.document.title or self.document.file_name}\n{len(self.document.items)} items")


    # Des méthodes pour le zoom et le panoramique pourraient être ajoutées ici plus tard,
    # similaires à celles dans LabelDisplay du projet de référence.
    # def wheelEvent(self, event): ...
    # def mousePressEvent(self, event): ...
    # def mouseMoveEvent(self, event): ...
    # def mouseReleaseEvent(self, event): ...

    def paintEvent(self, event):
        # Surcharger paintEvent si on a besoin d'un dessin plus complexe que juste setPixmap.
        # Pour l'instant, le comportement par défaut de QLabel (qui dessine son pixmap ou texte) est suffisant.
        super().paintEvent(event)
        # Exemple si on voulait dessiner des choses en plus du pixmap :
        # painter = QPainter(self)
        # if self.pixmap():
        #     painter.drawPixmap(0, 0, self.pixmap()) # Ou avec un offset
        # painter.setPen(QColor("red"))
        # painter.drawText(self.rect(), Qt.AlignCenter, "Overlay Text")


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    import sys
    from datetime import date

    app = QApplication(sys.argv)

    # Créer un LamicoidDocument de test
    test_doc = LamicoidDocument(file_name="TestLamicoidDoc.json", profile_name="TestProfile")
    test_doc.add_item(LamicoidItem(date_item="2023-10-01", numero_reference="REF001", description="Item 1", quantite=2, materiel="Bois"))
    
    main_win = QMainWindow()
    central_widget = QWidget()
    main_win.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    display_widget = LamicoidDisplayWidget(document=test_doc)
    
    layout.addWidget(display_widget)
    
    main_win.setWindowTitle("Test LamicoidDisplayWidget")
    main_win.resize(400, 300)
    main_win.show()

    # Appeler update_display pour tester le texte
    display_widget.update_display()

    sys.exit(app.exec_()) 