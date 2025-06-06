"""Définit l'item graphique pour un élément de texte."""

from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from models.documents.lamicoid_2.elements import ElementTexte

class TexteItem(QGraphicsTextItem):
    """
    Un QGraphicsTextItem qui représente un ElementTexte et peut être
    déplacé dans la scène.
    """
    def __init__(self, element_texte: ElementTexte, parent=None):
        super().__init__(parent)
        self.element_data = element_texte

        self.setPlainText(self.element_data.contenu)
        
        font = QFont(self.element_data.nom_police, self.element_data.taille_police_pt)
        self.setFont(font)

        self.setPos(self.element_data.x_mm, self.element_data.y_mm)

        # Rendre l'item déplaçable
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
    
    def mouseReleaseEvent(self, event):
        """Met à jour les coordonnées dans le modèle de données après un déplacement."""
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            self.element_data.x_mm = self.x()
            self.element_data.y_mm = self.y()
            print(f"Nouvelle position pour {self.element_data.element_id}: ({self.element_data.x_mm}, {self.element_data.y_mm})") 