from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsEllipseItem, QApplication, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt5.QtCore import QRectF, Qt, QPointF, QTimer
from PyQt5.QtGui import QBrush, QPen, QColor, QPixmap, QImage, QPainter, QTextOption, QFont
import logging

logger = logging.getLogger('GDJ_App')

class GridRectangleItem(QGraphicsRectItem):
    handle_size_mm = 1.0
    handle_pen_width = 0.5

    class ResizeHandle(QGraphicsEllipseItem):
        def __init__(self, parent_item, position_type, editor_view):
            handle_size_px = editor_view.mm_to_pixels(GridRectangleItem.handle_size_mm) if editor_view else GridRectangleItem.handle_size_mm * 3.78 # fallback approx
            super().__init__(-handle_size_px / 2, -handle_size_px / 2, 
                             handle_size_px, handle_size_px, parent_item) 
            self.parent_rect_item = parent_item
            self.position_type = position_type
            self._is_being_dragged = False 
            self.drag_start_offset_in_handle = QPointF() # Ajout pour stocker l'offset du clic
            self.setBrush(QBrush(QColor("red"))) 
            self.setPen(QPen(QColor("black"), GridRectangleItem.handle_pen_width))
            self.setFlag(QGraphicsItem.ItemIsMovable) 
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges) 
            self.setZValue(10) 
            self.hide() 

        def mousePressEvent(self, event):
            self._is_being_dragged = True
            self.drag_start_offset_in_handle = event.pos() 
            # logger.debug(f"ResizeHandle MOUSE PRESS: {self.position_type}, offset={self.drag_start_offset_in_handle}")
            super().mousePressEvent(event)
            if not event.isAccepted():
                event.accept()

        def mouseMoveEvent(self, event):
            if self._is_being_dragged:
                delta = event.pos() - self.drag_start_offset_in_handle
                new_pos_candidate = self.pos() + delta
                # logger.debug(f"ResizeHandle MOUSE MOVE DRAG: {self.position_type}, new_pos={new_pos_candidate}")
                self.setPos(new_pos_candidate) 
                event.accept() 
            else:
                super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event):
            super().mouseReleaseEvent(event) 
            self._is_being_dragged = False
            # logger.debug(f"ResizeHandle MOUSE RELEASE: {self.position_type}, is_dragging={self._is_being_dragged}")


        def itemChange(self, change, value):
            parent_selected = self.parent_rect_item.isSelected()
            is_parent_updating_handles = getattr(self.parent_rect_item, '_is_updating_handles', False)

            if is_parent_updating_handles:
                return super().itemChange(change, value)

            if change == QGraphicsItem.ItemPositionHasChanged and parent_selected and self._is_being_dragged:
                # logger.debug(f"ResizeHandle ItemChange - ItemPositionHasChanged for {self.position_type}: new_pos={value}")
                self.parent_rect_item.handle_moved(self.position_type, value) # value est la nouvelle pos de la poignée
                return value 
            
            return super().itemChange(change, value)

    def __init__(self, initial_rect_local: QRectF, editor_view=None, parent=None, image_path: str = None, text: str = None):
        super().__init__(initial_rect_local, parent)
        self.editor_view = editor_view
        self._is_selected = False
        self._is_updating_handles = False
        self._is_resizing_via_handle = False
        # self.current_rect_local = initial_rect_local # Redondant, self.rect() est la source de vérité

        self.setBrush(QBrush(QColor(180, 180, 255, 150))) 
        self.setPen(QPen(QColor("navy"), 1, Qt.SolidLine))

        self.setFlags(QGraphicsItem.ItemIsMovable | 
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemClipsChildrenToShape)
        self.setFiltersChildEvents(False)
        
        self.handles = {}
        self._create_handles()
        # Déterminer si c'est un item texte basé sur la présence de l'argument text
        self.is_text_item = text is not None

        # Initialisation des attributs d'image
        self.image_path = image_path
        self.pixmap_item: QGraphicsPixmapItem | None = None # Pour stocker l'item image enfant
        self.original_pil_image: Image.Image | None = None
        self.cached_qimage: QImage | None = None

        if self.image_path:
            self.load_image(self.image_path)
        
        # Initialisation pour le texte
        self._text = text if text is not None else ""
        self.text_item = QGraphicsTextItem(self) # Enfant du GridRectangleItem
        self.text_item.setPlainText(self._text)
        # Rendre le texte non interactif par défaut, l'interaction sera gérée par le parent
        self.text_item.setTextInteractionFlags(Qt.NoTextInteraction) 
        # self.text_item.setFocusPolicy(Qt.NoFocus) # SUPPRIMÉ: QGraphicsItem n'a pas cette méthode
        # Passer les événements de souris non gérés au parent (GridRectangleItem)
        # self.text_item.setAcceptedMouseButtons(Qt.NoButton) # Ceci pourrait être trop restrictif

        self._setup_text_item_properties()

        self.update_handles_position() # Assurer que les poignées sont positionnées initialement
        self.update_text_item_geometry() # Positionner et dimensionner le texte initialement

    def _setup_text_item_properties(self):
        # Définir des propriétés de base pour le texte
        font = QFont("Arial", 10) # Police et taille par défaut
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(QColor("black"))
        
        # Centrer le texte verticalement et horizontalement par défaut
        # Qt.AlignVCenter pour le vertical, Qt.AlignHCenter pour l'horizontal
        # Note: Pour QGraphicsTextItem, le contrôle fin du layout se fait souvent
        # en ajustant son rect et en utilisant document().setTextWidth()
        # ou en utilisant QGraphicsSimpleTextItem pour un alignement plus direct.
        # Ici, nous allons gérer la position et la largeur du document.
        
        # Le QGraphicsTextItem lui-même sera positionné à (0,0) dans les coordonnées du parent (GridRectangleItem)
        # et sa largeur sera ajustée. L'alignement interne se fera via les options du document.
        text_option = QTextOption(self.text_item.document().defaultTextOption())
        text_option.setAlignment(Qt.AlignCenter) # Centre horizontalement et verticalement
        self.text_item.document().setDefaultTextOption(text_option)

    def set_text(self, text: str):
        self._text = text
        self.text_item.setPlainText(self._text)
        self.update_text_item_geometry() # Mettre à jour si le texte change la géométrie (moins probable pour setPlainText)

    def get_text(self) -> str:
        return self.text_item.toPlainText() # Lire directement depuis QGraphicsTextItem pour la synchro

    def update_text_item_geometry(self):
        # Le rect du GridRectangleItem est dans ses propres coordonnées (commence à 0,0)
        item_local_rect = self.rect()
        
        # La position du QGraphicsTextItem est relative au GridRectangleItem.
        # On le place au coin supérieur gauche du rectangle.
        self.text_item.setPos(item_local_rect.topLeft())
        
        # Ajuster la largeur du document texte pour qu'il s'adapte au rectangle
        # Cela active le word-wrapping.
        self.text_item.setTextWidth(item_local_rect.width())
        
        # Pour centrer verticalement le texte à l'intérieur du rectangle,
        # on peut ajuster la position Y du QGraphicsTextItem.
        # Cela nécessite de connaître la hauteur du bloc de texte.
        # Note: QGraphicsTextItem ne fournit pas directement une méthode simple pour
        # obtenir la hauteur rendue du texte qui s'adapte parfaitement.
        # On pourrait utiliser text_item.boundingRect().height() APRES avoir défini la largeur
        # et le contenu, mais cela peut créer des dépendances cycliques si appelé trop tôt.

        # Une approche simple : on assume que l'alignement via QTextOption suffit pour le moment.
        # Si un ajustement vertical plus précis est nécessaire, il faudra des calculs plus complexes.
        
        # S'assurer que le text_item est visible
        self.text_item.setVisible(True)

    def setRect(self, rect: QRectF):
        # logger.debug(f"GridRectangleItem setRect: {rect}, current pos: {self.pos()}")
        super().setRect(rect)
        self._is_updating_handles = True # Drapeau pour éviter la récursion
        self.update_handles_position()
        self.update_text_item_geometry() # Mettre à jour la géométrie du texte
        QTimer.singleShot(0, lambda: setattr(self, '_is_updating_handles', False))


    def _create_handles(self):
        positions = ["top_left", "top_right", "bottom_left", "bottom_right"]
        for pos_type in positions:
            handle = GridRectangleItem.ResizeHandle(self, pos_type, self.editor_view)
            self.handles[pos_type] = handle

    def update_handles_position(self):
        if self._is_updating_handles and not self._is_resizing_via_handle: # Éviter si le parent met déjà à jour sauf si c'est un redimensionnement
            return
        # logger.debug(f"GridRectangleItem update_handles_position - rect: {self.rect()}")
        item_local_rect = self.rect() 
        self.handles["top_left"].setPos(item_local_rect.topLeft())
        self.handles["top_right"].setPos(item_local_rect.topRight())
        self.handles["bottom_left"].setPos(item_local_rect.bottomLeft())
        self.handles["bottom_right"].setPos(item_local_rect.bottomRight())

    def show_handles(self, show=True):
        # logger.debug(f"GridRectangleItem show_handles: {show}")
        for handle in self.handles.values():
            handle.setVisible(show)

    def itemChange(self, change, value):
        # logger.debug(f"GridRectangleItem itemChange: {change}, value: {value}, resizing_via_handle: {self._is_resizing_via_handle}")
        original_value_from_super = super().itemChange(change, value)

        if change == QGraphicsItem.ItemSelectedHasChanged:
            is_selected = bool(value) 
            self._is_selected = is_selected
            self.show_handles(is_selected)
            if is_selected:
                self._is_updating_handles = True 
                self.update_handles_position()
                QTimer.singleShot(0, lambda: setattr(self, '_is_updating_handles', False))
                # Si c'est un item texte et qu'il est sélectionné, le rendre éditable
                if self.is_text_item:
                    self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
                    self.text_item.setFocus(Qt.MouseFocusReason) # Donner le focus pour l'édition
            else:
                # Si désélectionné, rendre non éditable
                if self.is_text_item:
                    self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
                    # Optionnel: effacer le focus si l'item texte l'a toujours
                    if self.text_item.hasFocus():
                        self.text_item.clearFocus()
            return original_value_from_super
        
        elif change == QGraphicsItem.ItemPositionHasChanged: 
            # Ceci est appelé APRES que la position a changé.
            # 'value' est la nouvelle position (self.pos()).
            if not self._is_resizing_via_handle: 
                # logger.debug(f"GridRectangleItem: ItemPositionHasChanged (item DRAG to {value}). Updating handles.")
                self._is_updating_handles = True
                self.update_handles_position()
                # self.update_text_item_geometry() # Le texte suit l'item, pas besoin de recalculer ici
                QTimer.singleShot(0, lambda: setattr(self, '_is_updating_handles', False))
            # else:
                # logger.debug(f"GridRectangleItem: ItemPositionHasChanged (RESIZE). _is_resizing_via_handle is TRUE. Handles/image updated by setRect via handle_moved.")
            return original_value_from_super

        # Gestion du snapping et des marges lors du déplacement de l'item entier (pas redimensionnement)
        if self.editor_view and change == QGraphicsItem.ItemPositionChange and not self._is_resizing_via_handle:
            new_pos_candidate_from_qt = value 
            
            grid_spacing_x, grid_spacing_y = self.editor_view.get_grid_spacing()
            grid_origin_offset = self.editor_view.get_grid_origin_offset()
            snapped_pos = new_pos_candidate_from_qt
            if grid_spacing_x > 0 and grid_spacing_y > 0:
                snapped_x = round((new_pos_candidate_from_qt.x() - grid_origin_offset.x()) / grid_spacing_x) * grid_spacing_x + grid_origin_offset.x()
                snapped_y = round((new_pos_candidate_from_qt.y() - grid_origin_offset.y()) / grid_spacing_y) * grid_spacing_y + grid_origin_offset.y()
                snapped_pos = QPointF(snapped_x, snapped_y)
            
            margin_rect_scene = self.editor_view.get_margin_scene_rect()
            current_item_local_rect = self.rect() 
            if margin_rect_scene and current_item_local_rect.isValid():
                candidate_item_scene_rect = QRectF(snapped_pos, current_item_local_rect.size())
                final_pos = snapped_pos 
                if candidate_item_scene_rect.left() < margin_rect_scene.left(): final_pos.setX(margin_rect_scene.left())
                if candidate_item_scene_rect.right() > margin_rect_scene.right(): final_pos.setX(margin_rect_scene.right() - current_item_local_rect.width())
                if candidate_item_scene_rect.top() < margin_rect_scene.top(): final_pos.setY(margin_rect_scene.top())
                if candidate_item_scene_rect.bottom() > margin_rect_scene.bottom(): final_pos.setY(margin_rect_scene.bottom() - current_item_local_rect.height())
                if current_item_local_rect.width() > margin_rect_scene.width(): final_pos.setX(margin_rect_scene.left()) 
                if current_item_local_rect.height() > margin_rect_scene.height(): final_pos.setY(margin_rect_scene.top())
                # logger.debug(f"GridRectangleItem ItemPositionChange (contraint/snappé) : {final_pos}")
                return final_pos 
            # logger.debug(f"GridRectangleItem ItemPositionChange (snappé seulement) : {snapped_pos}")
            return snapped_pos
            
        return original_value_from_super


    def handle_moved(self, handle_type: str, new_handle_local_pos: QPointF):
        # logger.debug(f"GridRectangleItem handle_moved: type={handle_type}, new_handle_pos={new_handle_local_pos}")
        if self._is_updating_handles: 
            # logger.debug(f"GridRectangleItem.handle_moved sortie précoce: _is_updating_handles={self._is_updating_handles}")
            return

        self.prepareGeometryChange() 
        self._is_resizing_via_handle = True 
        self._is_updating_handles = True 

        current_rect_local = self.rect() 
        current_pos_scene = self.pos()   
        
        new_rect_local = QRectF(current_rect_local) 
        delta_pos_scene = QPointF(0,0) 

        # Snapping des coordonnées de la poignée (converties en scène) AVANT de calculer le nouveau rect
        new_handle_scene_pos = self.mapToScene(new_handle_local_pos) # Position de la poignée dans la scène
        snapped_handle_scene_pos = new_handle_scene_pos # Initialiser
        new_handle_local_pos_snapped = new_handle_local_pos # Initialiser avec la valeur non snappée

        if self.editor_view:
            grid_spacing_x, grid_spacing_y = self.editor_view.get_grid_spacing()
            grid_origin_offset = self.editor_view.get_grid_origin_offset() # Ceci est dans les coordonnées de la SCENE
            
            # new_handle_scene_pos est déjà dans les coordonnées de la scène.
            # L'origine de la grille (grid_origin_offset) est le coin supérieur gauche de la zone de contenu.
            if grid_spacing_x > 0 and grid_spacing_y > 0:
                snapped_x = round((new_handle_scene_pos.x() - grid_origin_offset.x()) / grid_spacing_x) * grid_spacing_x + grid_origin_offset.x()
                snapped_y = round((new_handle_scene_pos.y() - grid_origin_offset.y()) / grid_spacing_y) * grid_spacing_y + grid_origin_offset.y()
                snapped_handle_scene_pos = QPointF(snapped_x, snapped_y)
            
            # Reconvertir la position snappée de la poignée en coordonnées locales de l'item parent (GridRectangleItem)
            # La position de l'item (self.pos()) est le décalage entre les coordonnées de la scène et les coordonnées locales de l'item.
            # Donc, local_pos = scene_pos - self.pos()
            new_handle_local_pos_snapped = snapped_handle_scene_pos - self.pos()


        if handle_type == "top_left":
            fixed_br_local = current_rect_local.bottomRight()
            new_tl_local = new_handle_local_pos_snapped
            candidate_rect = QRectF(new_tl_local, fixed_br_local).normalized()
            delta_pos_scene = candidate_rect.topLeft() 
            new_rect_local = QRectF(0, 0, candidate_rect.width(), candidate_rect.height())
        elif handle_type == "bottom_right":
            new_br_local = new_handle_local_pos_snapped
            new_rect_local = QRectF(current_rect_local.topLeft(), new_br_local).normalized()
        elif handle_type == "top_right":
            fixed_bl_local = current_rect_local.bottomLeft() 
            new_tr_local = new_handle_local_pos_snapped
            candidate_rect = QRectF(QPointF(fixed_bl_local.x(), new_tr_local.y()), 
                                   QPointF(new_tr_local.x(), fixed_bl_local.y())).normalized()
            delta_pos_scene = QPointF(0, candidate_rect.top()) 
            new_rect_local = QRectF(0, 0, candidate_rect.width(), candidate_rect.height())
        elif handle_type == "bottom_left":
            fixed_tr_local = current_rect_local.topRight() 
            new_bl_local = new_handle_local_pos_snapped
            candidate_rect = QRectF(QPointF(new_bl_local.x(), fixed_tr_local.y()),
                                   QPointF(fixed_tr_local.x(), new_bl_local.y())).normalized()
            delta_pos_scene = QPointF(candidate_rect.left(), 0) 

        min_dim_mm = 2.0 
        min_width_scene_units = self.editor_view.mm_to_pixels(min_dim_mm, self.editor_view.logicalDpiX()) if self.editor_view else 10
        min_height_scene_units = self.editor_view.mm_to_pixels(min_dim_mm, self.editor_view.logicalDpiY()) if self.editor_view else 10
        
        original_width_before_min = new_rect_local.width()
        original_height_before_min = new_rect_local.height()

        width_adjusted = False
        height_adjusted = False

        if new_rect_local.width() < min_width_scene_units:
            new_rect_local.setWidth(min_width_scene_units)
            width_adjusted = True
        if new_rect_local.height() < min_height_scene_units:
            new_rect_local.setHeight(min_height_scene_units)
            height_adjusted = True

        # Ajuster delta_pos_scene si la taille minimale a changé les dimensions depuis le coin "fixe"
        if width_adjusted:
            if handle_type == "top_left" or handle_type == "bottom_left": # Le bord droit est fixe ou se déplace moins
                 delta_pos_scene.setX(delta_pos_scene.x() + (original_width_before_min - min_width_scene_units))
        if height_adjusted:
            if handle_type == "top_left" or handle_type == "top_right": # Le bord bas est fixe ou se déplace moins
                delta_pos_scene.setY(delta_pos_scene.y() + (original_height_before_min - min_height_scene_units))
        
        # Contraindre le rectangle redimensionné aux marges de la vue
        if self.editor_view:
            margin_rect_scene = self.editor_view.get_margin_scene_rect()
            if margin_rect_scene:
                # Position candidate de l'item après redimensionnement (avant contrainte de marge)
                candidate_item_pos_scene = current_pos_scene + delta_pos_scene
                # Rect candidate de l'item dans la scène
                candidate_item_scene_rect = QRectF(candidate_item_pos_scene, new_rect_local.size())

                final_pos_scene = candidate_item_pos_scene
                final_rect_local_size = new_rect_local.size()

                # Gauche
                if candidate_item_scene_rect.left() < margin_rect_scene.left():
                    final_pos_scene.setX(margin_rect_scene.left())
                # Droite (si l'item dépasse ET que sa largeur est inférieure ou égale à la marge)
                if candidate_item_scene_rect.right() > margin_rect_scene.right() and final_rect_local_size.width() <= margin_rect_scene.width():
                    final_pos_scene.setX(margin_rect_scene.right() - final_rect_local_size.width())
                elif final_rect_local_size.width() > margin_rect_scene.width(): # Si l'item est plus large que la marge
                    final_pos_scene.setX(margin_rect_scene.left())
                    final_rect_local_size.setWidth(margin_rect_scene.width())
                
                # Haut
                if candidate_item_scene_rect.top() < margin_rect_scene.top():
                    final_pos_scene.setY(margin_rect_scene.top())
                # Bas (si l'item dépasse ET que sa hauteur est inférieure ou égale à la marge)
                if candidate_item_scene_rect.bottom() > margin_rect_scene.bottom() and final_rect_local_size.height() <= margin_rect_scene.height():
                    final_pos_scene.setY(margin_rect_scene.bottom() - final_rect_local_size.height())
                elif final_rect_local_size.height() > margin_rect_scene.height(): # Si l'item est plus haut que la marge
                    final_pos_scene.setY(margin_rect_scene.top())
                    final_rect_local_size.setHeight(margin_rect_scene.height())
                
                # Appliquer la position et la taille contraintes
                delta_pos_scene = final_pos_scene - current_pos_scene
                new_rect_local = QRectF(0,0, final_rect_local_size.width(), final_rect_local_size.height())


        if delta_pos_scene != QPointF(0,0):
            self.setPos(current_pos_scene + delta_pos_scene)
        
        if new_rect_local != self.rect(): # setRect seulement si nécessaire
             self.setRect(new_rect_local) 
        else: # Si le rect n'a pas changé (ex: contraint à la même taille), s'assurer que les poignées et l'image sont OK
            self.update_handles_position()
            self.update_text_item_geometry() # S'assurer que le texte est toujours correct

        # logger.debug(f"GridRectangleItem handle_moved FIN: new_pos={self.pos()}, new_rect={self.rect()}")
        QTimer.singleShot(0, lambda: setattr(self, '_is_resizing_via_handle', False))
        QTimer.singleShot(0, lambda: setattr(self, '_is_updating_handles', False))

    def boundingRect(self):
        base = self.rect()
        if not self._is_selected or not self.editor_view:
            return base
        try:
            handle_size_px_screen = self.editor_view.mm_to_pixels(self.handle_size_mm)
            view_transform = self.editor_view.transform()
            padding_x = handle_size_px_screen / view_transform.m11() if view_transform.m11() != 0 else handle_size_px_screen
            padding_y = handle_size_px_screen / view_transform.m22() if view_transform.m22() != 0 else handle_size_px_screen
            pen_width_px_screen = self.editor_view.mm_to_pixels(self.handle_pen_width)
            padding_x += pen_width_px_screen / view_transform.m11() if view_transform.m11() != 0 else pen_width_px_screen
            padding_y += pen_width_px_screen / view_transform.m22() if view_transform.m22() != 0 else pen_width_px_screen
            extra_padding = max(abs(padding_x), abs(padding_y)) 
            return base.adjusted(-extra_padding, -extra_padding, extra_padding, extra_padding)
        except Exception as e: # Fallback en cas d'erreur (ex: editor_view non initialisé complètement)
            # logger.warning(f"Erreur dans boundingRect de GridRectangleItem: {e}")
            return base.adjusted(-5, -5, 5, 5) # Petit padding fixe 