from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtCore import QRectF, Qt, QSizeF, QPointF
from .base_item import EditableItemBase
from models.documents.lamicoid_2.elements import ElementImage

class ImageItem(EditableItemBase):
    def __init__(self, element_image: ElementImage, parent: QGraphicsItem = None):
        super().__init__(model_item=element_image, parent=parent)
        self.pixmap = QPixmap(element_image.chemin_fichier)
        self.setRect(0, 0, element_image.largeur_mm, element_image.hauteur_mm)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        if not self.pixmap.isNull():
            # Le rectangle englobant de l'item, qui peut être déformé.
            bounding_rect = self.rect()

            # La taille originale du pixmap.
            pixmap_size = QSizeF(self.pixmap.size())

            # On calcule la taille de l'image qui remplit le bounding_rect
            # tout en conservant le ratio.
            scaled_size = pixmap_size.scaled(bounding_rect.size(), Qt.KeepAspectRatio)

            # On calcule la position pour centrer l'image dans le bounding_rect.
            x = bounding_rect.x() + (bounding_rect.width() - scaled_size.width()) / 2
            y = bounding_rect.y() + (bounding_rect.height() - scaled_size.height()) / 2
            
            # Le rectangle final où dessiner, centré et avec le bon ratio.
            final_draw_rect = QRectF(x, y, scaled_size.width(), scaled_size.height())
            
            # On s'assure que le painter utilise un rendu de haute qualité
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # On dessine le pixmap dans le rectangle calculé.
            painter.drawPixmap(final_draw_rect, self.pixmap, QRectF(self.pixmap.rect()))
        else:
            painter.setPen(Qt.red)
            painter.drawRect(self.rect())
            painter.drawText(self.rect(), Qt.AlignCenter, "Image non trouvée")

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Surcharge pour mettre à jour le modèle après un déplacement ou redimensionnement."""
        if change == QGraphicsItem.ItemPositionChange:
            # Obtenir la zone de contenu (intérieur des marges)
            scene = self.scene()
            if scene and scene.views():
                view = scene.views()[0]
                if hasattr(view, 'content_rect_px'):
                    content_rect = view.content_rect_px
                    if not content_rect.isEmpty():
                        # Convertir la position proposée en coordonnées de scène
                        proposed_pos = value
                        current_rect = self.rect()
                        proposed_scene_rect = current_rect.translated(proposed_pos)
                        
                        # Vérifier si l'élément sort de la zone de contenu
                        constrained_pos = proposed_pos
                        
                        # Empêcher de sortir par la gauche
                        if proposed_scene_rect.left() < content_rect.left():
                            constrained_pos.setX(content_rect.left() - current_rect.left())
                        
                        # Empêcher de sortir par la droite
                        if proposed_scene_rect.right() > content_rect.right():
                            constrained_pos.setX(content_rect.right() - current_rect.right())
                        
                        # Empêcher de sortir par le haut
                        if proposed_scene_rect.top() < content_rect.top():
                            constrained_pos.setY(content_rect.top() - current_rect.top())
                        
                        # Empêcher de sortir par le bas
                        if proposed_scene_rect.bottom() > content_rect.bottom():
                            constrained_pos.setY(content_rect.bottom() - current_rect.bottom())
                        
                        # Appliquer les contraintes
                        value = constrained_pos
        
        elif change == QGraphicsItem.ItemPositionHasChanged:
            # Mettre à jour x_mm/y_mm en fonction de la position réelle de l'item dans la scène
            scene = self.scene()
            if scene and hasattr(scene.parent(), 'current_template') and scene.parent().current_template:
                from pages.documents.lamicoid_2.template_editor_view import _pixels_to_mm
                lamicoid_width = scene.parent().current_template.largeur_mm
                lamicoid_height = scene.parent().current_template.hauteur_mm
                # La position de l'item est relative au centre de la scène
                pos = self.pos()
                # On veut x_mm = (position en mm depuis le centre du lamicoid) + centre du lamicoid
                x_mm = lamicoid_width / 2 + _pixels_to_mm(pos.x())
                y_mm = lamicoid_height / 2 + _pixels_to_mm(pos.y())
                self.model_item.x_mm = x_mm
                self.model_item.y_mm = y_mm
        elif change == QGraphicsItem.ItemSelectedChange:
            # Optionnel : gérer la sélection si nécessaire
            pass
        return super().itemChange(change, value)

    def interactive_resize(self, mouse_pos: QPointF):
        """Surcharge pour forcer le maintien du ratio de l'image et contraindre aux marges."""
        if self.pixmap.isNull() or self.pixmap.height() == 0:
            super().interactive_resize(mouse_pos)
            return

        aspect_ratio = self.pixmap.width() / self.pixmap.height()
        min_size = self.handle_size * 2

        self.prepareGeometryChange()
        
        # Obtenir la zone de contenu (intérieur des marges)
        view = self.scene().views()[0]
        content_rect = view.content_rect_px
        
        new_rect = QRectF(self.rect())
        original_rect = self.mouse_press_rect
        diff = mouse_pos - self.mouse_press_pos
        
        # Calculer la nouvelle taille en maintenant le ratio
        if self.current_handle == 'bottom_right':
            new_width = original_rect.width() + diff.x()
            new_height = new_width / aspect_ratio
            new_rect.setWidth(new_width)
            new_rect.setHeight(new_height)
            
        elif self.current_handle == 'top_left':
            new_width = original_rect.width() - diff.x()
            new_height = new_width / aspect_ratio
            new_top_left = QPointF(original_rect.right() - new_width, original_rect.bottom() - new_height)
            new_rect.setTopLeft(new_top_left)

        elif self.current_handle == 'top_right':
            new_width = original_rect.width() + diff.x()
            new_height = new_width / aspect_ratio
            new_top_right = QPointF(original_rect.left() + new_width, original_rect.bottom() - new_height)
            new_rect.setTopRight(new_top_right)

        elif self.current_handle == 'bottom_left':
            new_width = original_rect.width() - diff.x()
            new_height = new_width / aspect_ratio
            new_bottom_left = QPointF(original_rect.right() - new_width, original_rect.top() + new_height)
            new_rect.setBottomLeft(new_bottom_left)

        # Vérifier la taille minimale
        if new_rect.width() < min_size or new_rect.height() < min_size:
            return

        # Convertir le rectangle en coordonnées de scène pour vérifier les contraintes
        scene_rect = self.mapRectToScene(new_rect)
        
        # Contraindre aux limites de la zone de contenu
        constrained_scene_rect = scene_rect
        
        # Empêcher de sortir par la gauche
        if constrained_scene_rect.left() < content_rect.left():
            constrained_scene_rect.setLeft(content_rect.left())
            # Ajuster la hauteur pour maintenir le ratio
            if self.current_handle in ['top_left', 'bottom_left']:
                new_width = constrained_scene_rect.width()
                new_height = new_width / aspect_ratio
                if self.current_handle == 'top_left':
                    constrained_scene_rect.setTop(constrained_scene_rect.bottom() - new_height)
                else:  # bottom_left
                    constrained_scene_rect.setBottom(constrained_scene_rect.top() + new_height)
        
        # Empêcher de sortir par la droite
        if constrained_scene_rect.right() > content_rect.right():
            constrained_scene_rect.setRight(content_rect.right())
            # Ajuster la hauteur pour maintenir le ratio
            if self.current_handle in ['top_right', 'bottom_right']:
                new_width = constrained_scene_rect.width()
                new_height = new_width / aspect_ratio
                if self.current_handle == 'top_right':
                    constrained_scene_rect.setTop(constrained_scene_rect.bottom() - new_height)
                else:  # bottom_right
                    constrained_scene_rect.setBottom(constrained_scene_rect.top() + new_height)
        
        # Empêcher de sortir par le haut
        if constrained_scene_rect.top() < content_rect.top():
            constrained_scene_rect.setTop(content_rect.top())
            # Ajuster la largeur pour maintenir le ratio
            if self.current_handle in ['top_left', 'top_right']:
                new_height = constrained_scene_rect.height()
                new_width = new_height * aspect_ratio
                if self.current_handle == 'top_left':
                    constrained_scene_rect.setLeft(constrained_scene_rect.right() - new_width)
                else:  # top_right
                    constrained_scene_rect.setRight(constrained_scene_rect.left() + new_width)
        
        # Empêcher de sortir par le bas
        if constrained_scene_rect.bottom() > content_rect.bottom():
            constrained_scene_rect.setBottom(content_rect.bottom())
            # Ajuster la largeur pour maintenir le ratio
            if self.current_handle in ['bottom_left', 'bottom_right']:
                new_height = constrained_scene_rect.height()
                new_width = new_height * aspect_ratio
                if self.current_handle == 'bottom_left':
                    constrained_scene_rect.setLeft(constrained_scene_rect.right() - new_width)
                else:  # bottom_right
                    constrained_scene_rect.setRight(constrained_scene_rect.left() + new_width)

        # Reconvertir en coordonnées locales de l'item
        final_rect = self.mapRectFromScene(constrained_scene_rect)
        
        # Vérifier à nouveau la taille minimale après contrainte
        if final_rect.width() < min_size or final_rect.height() < min_size:
            return

        self.setRect(final_rect)
        self.update_handles_pos()
        
        # Mettre à jour les dimensions dans le modèle
        from pages.documents.lamicoid_2.template_editor_view import _pixels_to_mm
        self.model_item.largeur_mm = _pixels_to_mm(final_rect.width())
        self.model_item.hauteur_mm = _pixels_to_mm(final_rect.height())

    def _update_bounding_box(self):
        self.setRect(0, 0, self.model_item.largeur_mm, self.model_item.hauteur_mm) 