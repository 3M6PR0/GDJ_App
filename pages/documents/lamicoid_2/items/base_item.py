import logging
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem, QStyle
from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QPainterPath, QTransform
import math

from models.documents.lamicoid_2.elements import ElementTemplateBase

logger = logging.getLogger('GDJ_App')

class EditableItemBase(QGraphicsRectItem):
    """
    Classe de base pour tous les éléments graphiques éditables sur la scène.
    Fournit une bordure de sélection et la gestion de la sélection.
    """
    def __init__(self, model_item: ElementTemplateBase, parent: QGraphicsItem = None):
        super().__init__(parent)
        self.model_item = model_item
        self.handle_size = 6.0
        self.handles = {}
        self.current_handle = None
        self.mouse_press_pos = None
        self.mouse_press_rect = None
        self.mouse_press_item_pos = None
        self.mouse_press_pos_scene = None

        self.setAcceptHoverEvents(True)
        
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        # Définir le style par défaut (bordure invisible)
        self._default_pen = QPen(Qt.transparent, 1, Qt.SolidLine)
        self.setPen(self._default_pen)

    def boundingRect(self) -> QRectF:
        """
        Retourne le rectangle englobant.
        Cette zone doit inclure le rectangle de base, la largeur du stylo,
        et la taille des poignées de redimensionnement si l'objet est sélectionné.
        """
        pen_width = self.pen().widthF()
        half_pen_width = pen_width / 2.0

        # Marge pour les poignées, uniquement si sélectionné
        handle_margin = self.handle_size / 2.0 if self.isSelected() else 0.0

        # La marge totale est la somme de la marge du stylo et des poignées
        margin = half_pen_width + handle_margin
        
        # On part du rectangle de base de l'item
        base_rect = self.rect()

        # Et on l'ajuste pour inclure les marges
        return base_rect.adjusted(-margin, -margin, margin, margin)

    def shape(self) -> QPainterPath:
        """
        Définit la forme de collision de l'item.
        Inclut le rectangle principal et les poignées si sélectionné.
        """
        path = QPainterPath()
        path.addRect(self.rect())
        if self.isSelected():
            for handle_rect in self.handles.values():
                path.addRect(handle_rect)
        return path

    def paint(self, painter: QPainter, option, widget=None):
        """Dessine l'item et ses poignées de redimensionnement si sélectionné."""
        super().paint(painter, option, widget)

        if self.isSelected():
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor("#007ACC")))
            painter.setPen(QPen(QColor(Qt.white), 1))

            for handle, rect in self.handles.items():
                painter.drawEllipse(rect)

    def itemChange(self, change, value):
        """Appelé lorsque l'état de l'item change. Gère la sélection et les contraintes de position."""
        if change == QGraphicsItem.ItemSelectedChange:
            self.update_selection_visuals(bool(value))
        
        elif change == QGraphicsItem.ItemPositionChange and self.scene():
            # C'est ici que la magie opère.
            # 'value' est la nouvelle position proposée par Qt.
            # Nous la modifions et la retournons.
            
            # 1. Magnétiser à la grille
            snapped_pos = self._snap_point_to_grid(value)
            
            # 2. Contraindre aux marges
            view = self.scene().views()[0]
            content_rect = None
            if hasattr(view, 'get_margin_scene_rect'):
                content_rect = view.get_margin_scene_rect()

            if not content_rect or content_rect.isEmpty():
                return snapped_pos # Pas de contrainte, on retourne juste la position magnétisée

            # Appliquer la contrainte universelle
            constrained_pos = self._constrain_rotated_item_to_boundary(snapped_pos, content_rect)
            return constrained_pos

        return super().itemChange(change, value)

    def update_selection_visuals(self, is_selected: bool):
        """Met à jour l'apparence de l'item en fonction de son état de sélection."""
        if is_selected:
            selection_pen = QPen(QColor("#007ACC"), 0.5)
            selection_pen.setStyle(Qt.DashLine)
            self.setPen(selection_pen)
        else:
            # Rétablir l'apparence par défaut
            self.setPen(self._default_pen)
        
        # Mettre à jour la position des poignées
        if is_selected:
            self.update_handles_pos()
        
        self.update()

    def update_handles_pos(self):
        """Met à jour la position des poignées de redimensionnement."""
        s = self.handle_size
        r = self.rect()
        self.handles['top_left'] = QRectF(r.left() - s/2, r.top() - s/2, s, s)
        self.handles['top_right'] = QRectF(r.right() - s/2, r.top() - s/2, s, s)
        self.handles['bottom_left'] = QRectF(r.left() - s/2, r.bottom() - s/2, s, s)
        self.handles['bottom_right'] = QRectF(r.right() - s/2, r.bottom() - s/2, s, s)

    def hoverMoveEvent(self, event):
        """Change le curseur si la souris est sur une poignée."""
        handle = self.handle_at(event.pos())
        if handle:
            rotation = self.rotation()

            # Inverser les curseurs pour les rotations de 90/270 degrés
            swap_cursors = (abs(rotation - 90) < 1) or (abs(rotation - 270) < 1)

            if handle in ['top_left', 'bottom_right']:
                self.setCursor(Qt.SizeBDiagCursor if swap_cursors else Qt.SizeFDiagCursor)
            elif handle in ['top_right', 'bottom_left']:
                self.setCursor(Qt.SizeFDiagCursor if swap_cursors else Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)
    
    def mousePressEvent(self, event):
        """Initialise le redimensionnement ou le déplacement."""
        self.current_handle = self.handle_at(event.pos())
        if self.current_handle:
            self.mouse_press_rect = self.rect()
            self.mouse_press_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Effectue le redimensionnement ou délègue le déplacement à la classe de base."""
        if self.current_handle:
            self.interactive_resize(event.pos())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Finalise l'opération."""
        self.current_handle = None
        self.mouse_press_rect = None
        self.mouse_press_pos = None
        super().mouseReleaseEvent(event)

    def handle_at(self, pos: QPointF):
        """Retourne la poignée à une position donnée, ou None."""
        for handle, rect in self.handles.items():
            if rect.contains(pos):
                return handle
        return None

    def _constrain_point_to_boundary(self, point: QPointF, boundary: QRectF) -> QPointF:
        """Contraint un point à rester à l'intérieur d'un rectangle de délimitation."""
        new_x = max(boundary.left(), min(point.x(), boundary.right()))
        new_y = max(boundary.top(), min(point.y(), boundary.bottom()))
        return QPointF(new_x, new_y)

    def _snap_point_to_grid(self, point: QPointF) -> QPointF:
        """Aligne un point sur la grille de la vue, si elle existe."""
        if not self.scene() or not self.scene().views():
            return point
        
        view = self.scene().views()[0]
        # Vérifie si la vue a les propriétés nécessaires (duck typing)
        if not hasattr(view, 'grid_spacing') or not hasattr(view, 'grid_offset'):
            return point

        grid_spacing = view.grid_spacing
        if grid_spacing <= 0:
            return point
        
        # Convertir le point de la scène en coordonnées locales de l'item parent (la grille)
        # Ici on suppose que l'item est un enfant direct de la scène, ce qui est le cas.
        # Les coordonnées de la grille sont déjà dans le système de la scène.
        grid_offset = view.grid_offset
        
        # Coordonnées relatives à l'origine de la grille
        relative_point = point - grid_offset
        
        # Calculer les coordonnées alignées
        snapped_x = round(relative_point.x() / grid_spacing) * grid_spacing
        snapped_y = round(relative_point.y() / grid_spacing) * grid_spacing

        # Reconvertir en coordonnées de la scène
        return QPointF(snapped_x, snapped_y) + grid_offset

    def interactive_resize(self, mouse_pos: QPointF):
        """Met à jour le rectangle de l'item pendant un redimensionnement interactif."""
        min_size = self.handle_size

        self.prepareGeometryChange()

        # 1. Calculer la nouvelle position du coin (item coords)
        diff_item_coords = mouse_pos - self.mouse_press_pos
        handle_type = self.current_handle
        
        if handle_type == 'top_left':
            new_corner_pos_item = self.mouse_press_rect.topLeft() + diff_item_coords
        elif handle_type == 'top_right':
            new_corner_pos_item = self.mouse_press_rect.topRight() + diff_item_coords
        elif handle_type == 'bottom_left':
            new_corner_pos_item = self.mouse_press_rect.bottomLeft() + diff_item_coords
        elif handle_type == 'bottom_right':
            new_corner_pos_item = self.mouse_press_rect.bottomRight() + diff_item_coords
        else: return

        # 2. Magnétiser et contraindre cette position
        view = self.scene().views()[0]
        content_rect = view.content_rect_px
        
        snapped_scene_pos = self._snap_point_to_grid(self.mapToScene(new_corner_pos_item))
        constrained_scene_pos = self._constrain_point_to_boundary(snapped_scene_pos, content_rect)
        final_corner_pos_item = self.mapFromScene(constrained_scene_pos)

        # 3. Reconstruire le rectangle à partir d'un coin fixe et du nouveau coin mobile
        final_rect = QRectF()
        if handle_type == 'top_left':
            fixed_corner = self.mouse_press_rect.bottomRight()
            final_rect = QRectF(final_corner_pos_item, fixed_corner)
        elif handle_type == 'top_right':
            fixed_corner = self.mouse_press_rect.bottomLeft()
            final_rect = QRectF(fixed_corner, final_corner_pos_item)
        elif handle_type == 'bottom_left':
            fixed_corner = self.mouse_press_rect.topRight()
            # On doit construire le rect avec les bons points
            final_rect = QRectF(QPointF(final_corner_pos_item.x(), fixed_corner.y()), 
                                QPointF(fixed_corner.x(), final_corner_pos_item.y()))
        elif handle_type == 'bottom_right':
            fixed_corner = self.mouse_press_rect.topLeft()
            final_rect = QRectF(fixed_corner, final_corner_pos_item)

        # 4. Normaliser et s'assurer de la taille minimale
        final_rect = final_rect.normalized()
        
        if final_rect.width() < min_size:
            final_rect.setWidth(min_size)
        if final_rect.height() < min_size:
            final_rect.setHeight(min_size)

        # 5. Vérifier que le nouveau rectangle, une fois roté, reste dans les limites.
        #    On utilise la même logique de transformation que pour les contraintes de déplacement.
        transform = QTransform()
        origin = self.transformOriginPoint()
        transform.translate(origin.x(), origin.y())
        transform.rotate(self.rotation())
        transform.translate(-origin.x(), -origin.y())
        
        # Le rectangle englobant de la nouvelle taille, roté, en coordonnées de scène
        scene_bounding_rect = transform.mapRect(final_rect).translated(self.pos())

        # Si le nouveau rectangle dépasse les limites, on annule le redimensionnement.
        # C'est l'approche la plus stable.
        if (scene_bounding_rect.left() < content_rect.left() or
            scene_bounding_rect.right() > content_rect.right() or
            scene_bounding_rect.top() < content_rect.top() or
            scene_bounding_rect.bottom() > content_rect.bottom()):
            return # Annuler le redimensionnement

        # Si tout est bon, on applique le nouveau rectangle.
        self.setRect(final_rect)
        self.setTransformOriginPoint(final_rect.center()) # Assurer l'origine pour la rotation
        self.update_handles_pos()
        self.update()

    def get_model_id(self) -> str:
        """Retourne l'ID du modèle de données associé."""
        return self.model_item.element_id 

    def _constrain_rotated_item_to_boundary(self, proposed_pos: QPointF, content_rect: QRectF) -> QPointF:
        """Contraint un élément (roté ou non) à rester dans les limites de la zone de contenu."""
        
        # 1. Calculer le rectangle englobant de l'item à sa position proposée DANS LA SCENE.
        #    On utilise QTransform pour simuler la transformation que Qt applique à l'item.
        item_local_rect = self.rect()
        
        transform = QTransform()
        # La transformation se fait par rapport au point d'origine de la transformation de l'item
        origin = self.transformOriginPoint()
        
        # On construit la transformation: translation vers l'origine, rotation, puis retour.
        transform.translate(origin.x(), origin.y())
        transform.rotate(self.rotation())
        transform.translate(-origin.x(), -origin.y())
        
        # On obtient le rectangle englobant de l'item roté, mais toujours en coordonnées locales (autour de 0,0)
        rotated_local_bounding_rect = transform.mapRect(item_local_rect)
        
        # On translate ce rectangle à la position proposée dans la scène pour obtenir sa position finale.
        scene_bounding_rect = rotated_local_bounding_rect.translated(proposed_pos)
        
        # 2. Calculer le décalage (dx, dy) nécessaire si l'item dépasse les limites.
        dx = 0
        if scene_bounding_rect.left() < content_rect.left():
            dx = content_rect.left() - scene_bounding_rect.left()
        elif scene_bounding_rect.right() > content_rect.right():
            dx = content_rect.right() - scene_bounding_rect.right()

        dy = 0
        if scene_bounding_rect.top() < content_rect.top():
            dy = content_rect.top() - scene_bounding_rect.top()
        elif scene_bounding_rect.bottom() > content_rect.bottom():
            dy = content_rect.bottom() - scene_bounding_rect.bottom()
            
        # 3. Appliquer le décalage à la position proposée.
        return proposed_pos + QPointF(dx, dy) 