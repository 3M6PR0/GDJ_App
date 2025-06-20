"""Définit le widget d'affichage pour la FeuilleLamicoid."""

import logging
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsItemGroup
from PyQt5.QtCore import Qt, QLineF
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen

from models.documents.lamicoid_2.feuille_lamicoid import FeuilleLamicoid
from .items.texte_item import TexteItem
from .items.image_item import ImageItem
from models.documents.lamicoid_2.template_lamicoid import TemplateLamicoid
from models.documents.lamicoid_2.elements import ElementTexte, ElementImage

logger = logging.getLogger('GDJ_App')


class SheetItem(QGraphicsRectItem):
    """
    Un objet QGraphicsRectItem qui dessine une grille adaptative sur lui-même.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.minor_pen = QPen(QColor(240, 240, 240), 0)  # Gris très clair pour la grille de 1mm
        self.major_pen = QPen(QColor(210, 210, 210), 0)  # Gris plus foncé pour la grille de 10mm

    def set_background_color(self, color: QColor):
        """Définit la couleur de fond de la feuille."""
        self.setBrush(QBrush(color))

    def paint(self, painter: QPainter, option, widget=None):
        """Dessine la feuille puis la grille appropriée en fonction du niveau de zoom."""
        # 1. Dessiner le fond blanc et la bordure de la feuille
        super().paint(painter, option, widget)

        # 2. Déterminer le niveau de zoom pour une grille adaptative
        transform = painter.worldTransform()
        pixels_per_mm = transform.m11()  # Échelle horizontale (pixels par mm)

        rect = self.rect()

        # 3. Dessiner la grille en fonction du zoom
        if pixels_per_mm > 4.0:  # Si 1mm > 4 pixels, on dessine la grille fine
            self._draw_grid_lines(painter, rect, 1.0, self.minor_pen)
            self._draw_grid_lines(painter, rect, 10.0, self.major_pen)
        elif pixels_per_mm > 0.4: # Sinon, si 10mm > 4 pixels, on dessine la grille large
            self._draw_grid_lines(painter, rect, 10.0, self.major_pen)
        # Si le zoom est trop éloigné, aucune grille n'est dessinée pour garder la clarté.

    def _draw_grid_lines(self, painter, rect, spacing, pen):
        """Fonction helper pour dessiner un type de grille."""
        painter.setPen(pen)

        # Lignes verticales
        x = rect.left() + spacing
        while x < rect.right():
            painter.drawLine(QLineF(x, rect.top(), x, rect.bottom()))
            x += spacing

        # Lignes horizontales
        y = rect.top() + spacing
        while y < rect.bottom():
            painter.drawLine(QLineF(rect.left(), y, rect.right(), y))
            y += spacing


class FeuilleLamicoidView(QGraphicsView):
    """
    Vue interactive pour afficher et manipuler une FeuilleLamicoid.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: 0px")
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setInteractive(True)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.sheet_item = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configure l'apparence initiale de la vue."""
        self.scene.setBackgroundBrush(QBrush(Qt.NoBrush))
        
    def display_feuille(self, feuille: FeuilleLamicoid):
        """
        Affiche la feuille et son contenu dans la scène.
        """
        self.scene.clear()
        
        self.scene.setSceneRect(0, 0, feuille.largeur_feuille_mm, feuille.hauteur_feuille_mm)

        self.sheet_item = SheetItem(0, 0, feuille.largeur_feuille_mm, feuille.hauteur_feuille_mm)
        self.sheet_item.set_background_color(QColor("#B0B0B0")) # Gris par défaut
        self.sheet_item.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        self.scene.addItem(self.sheet_item)
        
        logger.info(f"Affichage de la feuille {feuille.largeur_feuille_mm}x{feuille.hauteur_feuille_mm} mm avec grille.")
        
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def clear_view(self):
        """Nettoie la scène."""
        self.scene.clear()
        self.sheet_item = None

    def set_sheet_color(self, color_name: str):
        """Change la couleur de fond de la feuille."""
        if not self.sheet_item:
            return

        color_map = {
            "Gris": QColor("#B0B0B0"),
            "Rouge": QColor("#B82B2B"),
            "Bleu": QColor("#3B5998"),
            "Vert": QColor("#5A8A3E"),
            "Jaune": QColor(Qt.yellow),
            "Blanc": QColor(Qt.white),
            "Noir": QColor(Qt.black)
        }
        color = color_map.get(color_name, QColor("#B0B0B0"))
        self.sheet_item.set_background_color(color)

    def zoom_in(self):
        """Zoome sur la vue."""
        self.scale(1.2, 1.2)

    def zoom_out(self):
        """Dézoome sur la vue."""
        self.scale(1/1.2, 1/1.2)

    def zoom_to_fit(self):
        """Ajuste le zoom pour que toute la feuille soit visible."""
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def wheelEvent(self, event):
        """Gère le zoom avec Ctrl+Molette et le panoramique avec la molette seule."""
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        """Ajuste la vue lorsque le widget est redimensionné."""
        super().resizeEvent(event)

    def add_lamicoid_from_template(self, template: TemplateLamicoid):
        """
        Crée un groupe d'items graphiques à partir d'un template et l'ajoute à la scène.
        """
        # Créer le groupe qui contiendra tous les éléments du lamicoid
        lamicoid_group = QGraphicsItemGroup()
        lamicoid_group.setFlag(QGraphicsItemGroup.ItemIsMovable)
        lamicoid_group.setFlag(QGraphicsItemGroup.ItemIsSelectable)
        
        # Créer le fond du lamicoid
        fond_rect = QGraphicsRectItem(0, 0, template.largeur_mm, template.hauteur_mm)
        fond_rect.setBrush(QColor("white"))
        fond_rect.setPen(QPen(QColor("black"), 0.5))
        lamicoid_group.addToGroup(fond_rect)
        
        # Ajouter les éléments du template au groupe
        for element in template.elements:
            item = None
            if isinstance(element, ElementTexte):
                item = TexteItem(element, use_mm=True) # Préciser que les unités sont déjà en mm
            elif isinstance(element, ElementImage):
                item = ImageItem(element, use_mm=True) # Préciser que les unités sont déjà en mm

            if item:
                # La position de l'élément est déjà relative au coin sup-gauche du lamicoid
                item.setPos(element.x_mm, element.y_mm)
                lamicoid_group.addToGroup(item)
                
        # Ajouter le groupe complet à la scène
        self.scene.addItem(lamicoid_group)

    def display_feuille(self, feuille_lamicoid: FeuilleLamicoid):
        """Affiche le contenu d'un objet FeuilleLamicoid."""
        self.feuille_lamicoid = feuille_lamicoid
        self.scene.clear()
        
        self.scene.setSceneRect(0, 0, feuille_lamicoid.largeur_feuille_mm, feuille_lamicoid.hauteur_feuille_mm)

        self.sheet_item = SheetItem(0, 0, feuille_lamicoid.largeur_feuille_mm, feuille_lamicoid.hauteur_feuille_mm)
        self.sheet_item.set_background_color(QColor("#B0B0B0")) # Gris par défaut
        self.sheet_item.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        self.scene.addItem(self.sheet_item)
        
        logger.info(f"Affichage de la feuille {feuille_lamicoid.largeur_feuille_mm}x{feuille_lamicoid.hauteur_feuille_mm} mm avec grille.")
        
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio) 