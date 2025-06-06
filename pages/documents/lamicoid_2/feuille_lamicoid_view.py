"""Définit le widget d'affichage pour la FeuilleLamicoid."""

import logging
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen

from models.documents.lamicoid_2.feuille_lamicoid import FeuilleLamicoid

logger = logging.getLogger('GDJ_App')

class FeuilleLamicoidView(QGraphicsView):
    """
    Vue interactive pour afficher et manipuler une FeuilleLamicoid.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setInteractive(True)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configure l'apparence initiale de la vue."""
        self.scene.setBackgroundBrush(QBrush(QColor("#5a5d5e")))
        
    def display_feuille(self, feuille: FeuilleLamicoid):
        """
        Affiche la feuille et son contenu dans la scène.
        """
        self.scene.clear()
        
        # Définir la taille de la scène pour correspondre à la feuille
        self.scene.setSceneRect(0, 0, feuille.largeur_feuille_mm, feuille.hauteur_feuille_mm)

        # Dessiner le rectangle représentant la feuille
        sheet_rect = QGraphicsRectItem(0, 0, feuille.largeur_feuille_mm, feuille.hauteur_feuille_mm)
        sheet_rect.setBrush(QBrush(Qt.white))
        sheet_rect.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        self.scene.addItem(sheet_rect)
        
        # Ajouter ici la logique pour dessiner les lamicoids
        logger.info(f"Affichage de la feuille {feuille.largeur_feuille_mm}x{feuille.hauteur_feuille_mm} mm.")
        
        # Centrer la vue sur la feuille
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def clear_view(self):
        """Nettoie la scène."""
        self.scene.clear()
        
    def resizeEvent(self, event):
        """Ajuste la vue lorsque le widget est redimensionné."""
        super().resizeEvent(event)
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio) 