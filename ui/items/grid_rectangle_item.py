from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsEllipseItem, QApplication
from PyQt5.QtCore import QRectF, Qt, QPointF, QTimer
from PyQt5.QtGui import QBrush, QPen, QColor
import logging # Pour le débogage

logger = logging.getLogger('GDJ_App') # Pour le débogage

class GridRectangleItem(QGraphicsRectItem):
    handle_size_mm = 1.0 # Taille de la poignée en mm
    handle_pen_width = 0.5 # Épaisseur du trait de la poignée

    class ResizeHandle(QGraphicsEllipseItem):
        def __init__(self, parent_item, position_type, editor_view):
            handle_size_px = editor_view.mm_to_pixels(GridRectangleItem.handle_size_mm) if editor_view else GridRectangleItem.handle_size_mm * 3.78 # fallback approx
            # Centre la poignée sur le coin
            super().__init__(-handle_size_px / 2, -handle_size_px / 2, 
                             handle_size_px, handle_size_px, parent_item) # Rétablissement de parent_item
            self.parent_rect_item = parent_item
            self.position_type = position_type
            self._is_being_dragged = False # Nouveau drapeau pour la poignée
            self.setBrush(QBrush(QColor("red"))) # Poignées rouges pour les distinguer
            self.setPen(QPen(QColor("black"), GridRectangleItem.handle_pen_width))
            self.setFlag(QGraphicsItem.ItemIsMovable) # Pour détecter le mouvement
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges) # Pour itemChange
            self.setZValue(10) # Au-dessus de l'item rectangle
            self.hide() # Cachées par défaut

        def mousePressEvent(self, event):
            self._is_being_dragged = True
            self.drag_start_offset_in_handle = event.pos() # Stocker la position du clic DANS la poignée
            print(f"ResizeHandle MOUSE PRESS: {self.position_type}, _is_being_dragged = {self._is_being_dragged}, drag_start_offset={self.drag_start_offset_in_handle}")
            super().mousePressEvent(event)
            # Assurons-nous que l'événement est accepté par la poignée pour qu'elle gère le drag.
            if not event.isAccepted():
                print(f"ResizeHandle MOUSE PRESS: Event NOT accepted by super, accepting now.")
                event.accept()
            else:
                print(f"ResizeHandle MOUSE PRESS: Event was accepted by super.")

        def mouseMoveEvent(self, event):
            print(f"ResizeHandle MOUSE MOVE START: Type={self.position_type}, Dragging={self._is_being_dragged}, HandleLocalPos_Initial={self.pos()}, EventMouseLocalPos={event.pos()}")
            
            if self.scene():
                grabber = self.scene().mouseGrabberItem()
                print(f"ResizeHandle MOUSE MOVE: Mouse Grabber is: {'self' if grabber == self else grabber}")
            
            if self._is_being_dragged:
                if not hasattr(self, 'drag_start_offset_in_handle'): 
                    # Mesure de sécurité, ne devrait pas se produire si mousePressEvent est toujours appelé avant.
                    self.drag_start_offset_in_handle = event.pos()
                    print(f"ResizeHandle MOUSE MOVE: WARNING - drag_start_offset_in_handle was not set! Initializing now. This might lead to a jump.")

                # Calculer le delta du mouvement de la souris par rapport au point de clic initial dans la poignée
                delta = event.pos() - self.drag_start_offset_in_handle
                
                # La nouvelle position candidate pour le coin supérieur gauche de la poignée
                # est sa position actuelle plus ce delta.
                new_pos_candidate = self.pos() + delta
                
                print(f"ResizeHandle MOUSE MOVE: drag_start_offset={self.drag_start_offset_in_handle}, current_event_pos={event.pos()}, delta={delta}, old_handle_pos={self.pos()}, new_handle_pos_candidate={new_pos_candidate}")
                
                # Déplacer la poignée à cette nouvelle position.
                # Ceci devrait déclencher itemChange avec ItemPositionHasChanged si la position change réellement.
                self.setPos(new_pos_candidate) 
                
                # L'événement a été géré.
                print(f"ResizeHandle MOUSE MOVE: Manually called setPos. Event accepted.")
                event.accept() # Accepter l'événement pour indiquer qu'il est géré.

            else: # Pas en train de draguer
                super().mouseMoveEvent(event) # Comportement par défaut QGraphicsItem
            
            print(f"ResizeHandle MOUSE MOVE END: Type={self.position_type}, FinalHandleLocalPos={self.pos()}")

        def mouseReleaseEvent(self, event):
            # Il est crucial d'appeler super() d'abord, car cela peut déclencher le dernier ItemPositionHasChanged.
            super().mouseReleaseEvent(event)
            self._is_being_dragged = False
            print(f"ResizeHandle MOUSE RELEASE: {self.position_type}, _is_being_dragged = {self._is_being_dragged}")

        def itemChange(self, change, value):
            # Log d'entrée très détaillé
            parent_selected = self.parent_rect_item.isSelected()
            is_parent_updating_handles = self.parent_rect_item._is_updating_handles if hasattr(self.parent_rect_item, '_is_updating_handles') else 'N/A'
            print(f">>> ResizeHandle itemChange ENTER: Evt={change}, Val={value}, Sel={parent_selected}, ParentUpdatingH={is_parent_updating_handles}, Dragging={self._is_being_dragged}, CurrentHandleLocalPos={self.pos()} <<<")
            
            # Appel à super().itemChange en premier pour obtenir la valeur qu'il retournerait
            original_value_to_return = super().itemChange(change, value) 

            # Garde principale si le parent met à jour les poignées
            if hasattr(self.parent_rect_item, '_is_updating_handles') and self.parent_rect_item._is_updating_handles:
                print(f">>> ResizeHandle itemChange: Parent is updating handles. Returning super's result: {original_value_to_return} <<<")
                return original_value_to_return

            # Logique pour appeler handle_moved si la position a changé PENDANT un drag
            if change == QGraphicsItem.ItemPositionHasChanged and parent_selected and self._is_being_dragged:
                print(f">>> ResizeHandle itemChange: ItemPositionHasChanged WHILE DRAGGING. Calling parent.handle_moved. CurrentHandleLocalPos={self.pos()} <<<")
                self.parent_rect_item.handle_moved(self.position_type, self.pos())
                # La position a déjà changé. self.pos() est la nouvelle position.
                # itemChange doit retourner cette nouvelle position.
                new_pos_to_return = self.pos()
                print(f">>> ResizeHandle itemChange: Returning self.pos() = {new_pos_to_return} after handle_moved <<<")
                return new_pos_to_return 
            
            print(f">>> ResizeHandle itemChange EXIT: Returning super's result: {original_value_to_return} <<<")
            return original_value_to_return

    def __init__(self, initial_rect_local: QRectF, editor_view=None, parent=None):
        super().__init__(initial_rect_local, parent)
        self.editor_view = editor_view
        self._is_selected = False
        self._is_updating_handles = False # Drapeau pour la mise à jour des poignées
        self._is_resizing_via_handle = False # Nouveau drapeau pour le redimensionnement
        self.current_rect_local = initial_rect_local

        self.setBrush(QBrush(QColor(180, 180, 255, 150))) 
        self.setPen(QPen(QColor("navy"), 1, Qt.SolidLine))

        self.setFlags(QGraphicsItem.ItemIsMovable | 
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.setFiltersChildEvents(False) # L'enfant (poignée) reçoit les événements en premier.
        
        self.handles = {}
        self._create_handles()
        self.update_handles_position()

    def _create_handles(self):
        positions = ["top_left", "top_right", "bottom_left", "bottom_right"]
        for pos_type in positions:
            handle = GridRectangleItem.ResizeHandle(self, pos_type, self.editor_view)
            self.handles[pos_type] = handle

    def update_handles_position(self):
        # Les poignées sont positionnées aux coins du rectangle local de l'item
        # Le rect() de QGraphicsRectItem est déjà dans ses coordonnées locales.
        item_local_rect = self.rect() 
        self.handles["top_left"].setPos(item_local_rect.topLeft())
        self.handles["top_right"].setPos(item_local_rect.topRight())
        self.handles["bottom_left"].setPos(item_local_rect.bottomLeft())
        self.handles["bottom_right"].setPos(item_local_rect.bottomRight())

    def show_handles(self, show=True):
        for handle in self.handles.values():
            handle.setVisible(show)

    def itemChange(self, change, value):
        # Mouvement de l'item GridRectangleItem LUI-MEME
        if self.editor_view and change == QGraphicsItem.ItemPositionChange:
            new_pos_candidate = value

            if self._is_resizing_via_handle:
                # Si le redimensionnement via une poignée est en cours, handle_moved a déjà
                # calculé une position alignée sur la grille. On accepte cette position.
                return new_pos_candidate
            else:
                # Mouvement direct de l'item par l'utilisateur, on applique le magnétisme.
                grid_spacing_x, grid_spacing_y = self.editor_view.get_grid_spacing()
                grid_origin_offset = self.editor_view.get_grid_origin_offset()

                if grid_spacing_x > 0 and grid_spacing_y > 0:
                    snapped_x = round((new_pos_candidate.x() - grid_origin_offset.x()) / grid_spacing_x) * grid_spacing_x + grid_origin_offset.x()
                    snapped_y = round((new_pos_candidate.y() - grid_origin_offset.y()) / grid_spacing_y) * grid_spacing_y + grid_origin_offset.y()
                    snapped_pos = QPointF(snapped_x, snapped_y)
                    
                    # Si le snapping a effectivement modifié la position candidate
                    if snapped_pos != new_pos_candidate:
                        return snapped_pos
                # Retourne la position candidate (inchangée si pas de snapping ou snapping n'a rien fait)
                return new_pos_candidate
        
        # Sélection de l'item
        if change == QGraphicsItem.ItemSelectedHasChanged:
            is_selected = bool(value)
            self._is_selected = is_selected
            self.show_handles(is_selected)
            if is_selected:
                # Lorsque l'item est sélectionné, positionner les poignées.
                # _is_updating_handles est mis à True pour que les appels setPos sur les poignées
                # (dans update_handles_position qui suit) n'appellent pas handle_moved via la garde _is_updating_handles.
                self._is_updating_handles = True 
                self.update_handles_position()
                # Utiliser QTimer.singleShot pour s'assurer que _is_updating_handles est remis à False
                # APRÈS que tous les événements de positionnement des poignées aient été traités.
                QTimer.singleShot(0, lambda: setattr(self, '_is_updating_handles', False))
        
        # Après que la position a changé (pour mettre à jour les poignées si l'item entier a bougé)
        if change == QGraphicsItem.ItemPositionHasChanged: # Mouvement de l'item GridRectangleItem lui-même
            if not self._is_resizing_via_handle: # Ne pas le faire si c'est handle_moved qui a bougé l'item
                self._is_updating_handles = True
                self.update_handles_position()
                self._is_updating_handles = False

        return super().itemChange(change, value)

    def handle_moved(self, handle_type: str, new_handle_local_pos: QPointF):
        print("!!!!!!!!!!!! JE SUIS ENTRÉ DANS HANDLE_MOVED !!!!!!!!!!!!") # DEBUG PRINT
        if not self.editor_view:
            return

        # Cette garde est importante si handle_moved cause indirectement un autre appel à handle_moved
        # avant que _is_resizing_via_handle ne soit remis à False.
        # Cependant, le flux principal est géré par _is_being_dragged dans ResizeHandle.
        if self._is_updating_handles: 
             print("!!!!!!!!!!!! SORTIE PRÉCOCE DE HANDLE_MOVED car _is_updating_handles (du parent) est True !!!!!!!!!!!!")
             return

        self._is_resizing_via_handle = True # Indiquer que le redimensionnement a commencé

        logger.debug(f"--- handle_moved START: type={handle_type} ---")
        logger.debug(f"Initial item state: pos={self.pos()}, rect={self.rect()}")
        
        grid_spacing_x, grid_spacing_y = self.editor_view.get_grid_spacing()
        grid_origin_offset = self.editor_view.get_grid_origin_offset()
        
        # Coordonnées actuelles de l'item (position de son coin sup gauche local dans la scène)
        current_item_scene_pos = self.pos()
        # Rectangle actuel de l'item, dans ses propres coordonnées locales (son topLeft est (0,0))
        current_local_rect = self.rect()

        # Déterminer les coins du rectangle actuel en coordonnées de SCÈNE
        scene_topLeft = current_item_scene_pos + current_local_rect.topLeft()
        scene_bottomRight = current_item_scene_pos + current_local_rect.bottomRight()
        scene_topRight = current_item_scene_pos + current_local_rect.topRight()
        scene_bottomLeft = current_item_scene_pos + current_local_rect.bottomLeft()
        logger.debug(f"Initial SCENE corners: TL={scene_topLeft}, TR={scene_topRight}, BL={scene_bottomLeft}, BR={scene_bottomRight}") # DEBUG

        # La nouvelle position de la poignée (fournie en local) est mappée en SCÈNE
        # C'est la position cible du coin que l'on déplace
        moving_corner_target_scene_pos = self.mapToScene(new_handle_local_pos)
        logger.debug(f"Handle new local pos={new_handle_local_pos}, mapped to SCENE target={moving_corner_target_scene_pos}") # DEBUG


        # Snapper cette position cible à la grille
        snapped_moving_x = round((moving_corner_target_scene_pos.x() - grid_origin_offset.x()) / grid_spacing_x) * grid_spacing_x + grid_origin_offset.x()
        snapped_moving_y = round((moving_corner_target_scene_pos.y() - grid_origin_offset.y()) / grid_spacing_y) * grid_spacing_y + grid_origin_offset.y()
        snapped_moving_corner_scene_pos = QPointF(snapped_moving_x, snapped_moving_y)
        logger.debug(f"Snapped moving corner SCENE pos (before margin clamp)={snapped_moving_corner_scene_pos}") # DEBUG

        # Récupérer les limites de la marge depuis l'éditeur
        margin_rect_scene = self.editor_view.get_margin_scene_rect()

        if margin_rect_scene:
            # Contraindre la position snappée à l'intérieur de la marge
            clamped_x = max(margin_rect_scene.left(), min(snapped_moving_corner_scene_pos.x(), margin_rect_scene.right()))
            clamped_y = max(margin_rect_scene.top(), min(snapped_moving_corner_scene_pos.y(), margin_rect_scene.bottom()))
            
            original_snapped_pos = snapped_moving_corner_scene_pos
            snapped_moving_corner_scene_pos = QPointF(clamped_x, clamped_y)
            if original_snapped_pos != snapped_moving_corner_scene_pos:
                 logger.debug(f"Snapped moving corner SCENE pos CLAMPED to margin: from {original_snapped_pos} to {snapped_moving_corner_scene_pos}") # DEBUG
        else:
            logger.warning("handle_moved: Margin rect not available from editor_view, cannot clamp to margin.")

        # Déterminer le coin fixe et le nouveau rectangle en SCÈNE
        fixed_corner_scene_pos = QPointF()
        new_target_scene_rect = QRectF()

        if handle_type == "top_left":
            fixed_corner_scene_pos = scene_bottomRight
            new_target_scene_rect = QRectF(snapped_moving_corner_scene_pos, fixed_corner_scene_pos).normalized()
        elif handle_type == "top_right":
            fixed_corner_scene_pos = scene_bottomLeft
            p1 = QPointF(fixed_corner_scene_pos.x(), snapped_moving_corner_scene_pos.y())
            p2 = QPointF(snapped_moving_corner_scene_pos.x(), fixed_corner_scene_pos.y())
            new_target_scene_rect = QRectF(p1, p2).normalized()
        elif handle_type == "bottom_left":
            fixed_corner_scene_pos = scene_topRight
            p1 = QPointF(snapped_moving_corner_scene_pos.x(), fixed_corner_scene_pos.y())
            p2 = QPointF(fixed_corner_scene_pos.x(), snapped_moving_corner_scene_pos.y())
            new_target_scene_rect = QRectF(p1, p2).normalized()
        elif handle_type == "bottom_right":
            fixed_corner_scene_pos = scene_topLeft
            new_target_scene_rect = QRectF(fixed_corner_scene_pos, snapped_moving_corner_scene_pos).normalized()
        
        logger.debug(f"Expected fixed SCENE corner={fixed_corner_scene_pos} for handle {handle_type}") # DEBUG
        logger.debug(f"Calculated new target SCENE rect (before min size adj)={new_target_scene_rect}") # DEBUG


        # Assurer une taille minimale (au moins un pas de grille)
        min_width_px = grid_spacing_x
        min_height_px = grid_spacing_y

        # Largeur et hauteur cibles basées sur le coin mobile snappé et le coin fixe
        # new_target_scene_rect a déjà été calculé et normalisé à partir de ces points
        current_target_width = new_target_scene_rect.width()
        current_target_height = new_target_scene_rect.height()

        final_width = max(current_target_width, min_width_px)
        final_height = max(current_target_height, min_height_px)

        # Recalculer le new_target_scene_rect en utilisant le fixed_corner_scene_pos
        # et les final_width, final_height pour s'assurer que le coin fixe est respecté.
        if handle_type == "top_left":
            # Le coin fixe est bottomRight (fixed_corner_scene_pos)
            # Le coin mobile est topLeft (snapped_moving_corner_scene_pos, qui a défini le topLeft initial de new_target_scene_rect)
            new_tl_x = fixed_corner_scene_pos.x() - final_width
            new_tl_y = fixed_corner_scene_pos.y() - final_height
            new_target_scene_rect = QRectF(QPointF(new_tl_x, new_tl_y), fixed_corner_scene_pos).normalized()
        elif handle_type == "bottom_right":
            # Le coin fixe est topLeft (fixed_corner_scene_pos)
            # Le coin mobile est bottomRight
            new_br_x = fixed_corner_scene_pos.x() + final_width
            new_br_y = fixed_corner_scene_pos.y() + final_height
            new_target_scene_rect = QRectF(fixed_corner_scene_pos, QPointF(new_br_x, new_br_y)).normalized()
        elif handle_type == "top_right":
            # Le coin fixe est bottomLeft (fixed_corner_scene_pos)
            # Le coin mobile est topRight
            new_tr_x = fixed_corner_scene_pos.x() + final_width
            new_tr_y = fixed_corner_scene_pos.y() - final_height # y diminue pour monter
            # Le nouveau topLeft est (fixed_corner_scene_pos.x(), new_tr_y)
            # Le nouveau bottomRight est (new_tr_x, fixed_corner_scene_pos.y())
            new_target_scene_rect = QRectF(QPointF(fixed_corner_scene_pos.x(), new_tr_y), QPointF(new_tr_x, fixed_corner_scene_pos.y())).normalized()
        elif handle_type == "bottom_left":
            # Le coin fixe est topRight (fixed_corner_scene_pos)
            # Le coin mobile est bottomLeft
            new_bl_x = fixed_corner_scene_pos.x() - final_width # x diminue pour aller à gauche
            new_bl_y = fixed_corner_scene_pos.y() + final_height
            # Le nouveau topLeft est (new_bl_x, fixed_corner_scene_pos.y())
            # Le nouveau bottomRight est (fixed_corner_scene_pos.x(), new_bl_y)
            new_target_scene_rect = QRectF(QPointF(new_bl_x, fixed_corner_scene_pos.y()), QPointF(fixed_corner_scene_pos.x(), new_bl_y)).normalized()
        
        logger.debug(f"Recalculated new target SCENE rect (after min size adj)={new_target_scene_rect}") # DEBUG
        
        # Le QGraphicsRectItem est défini par un QRectF dans ses propres coordonnées locales.
        # Sa position (self.pos()) est le coin supérieur gauche de ce rectangle local dans la scène.
        # Donc, on met à jour self.pos() et on ajuste le rectangle local.
        self.prepareGeometryChange()
        
        new_local_rect_width = new_target_scene_rect.width()
        new_local_rect_height = new_target_scene_rect.height()
        
        logger.debug(f"Before setPos/setRect: Current item pos={self.pos()}, rect={self.rect()}") # DEBUG
        self.setPos(new_target_scene_rect.topLeft()) 
        self.setRect(0, 0, new_local_rect_width, new_local_rect_height) # Rectangle local commence à 0,0
        logger.debug(f"After setPos/setRect: New item pos={self.pos()}, rect={self.rect()}") # DEBUG

        # Vérification des coins finaux en scène
        final_scene_topLeft = self.pos() + self.rect().topLeft()
        final_scene_topRight = self.pos() + self.rect().topRight()
        final_scene_bottomLeft = self.pos() + self.rect().bottomLeft()
        final_scene_bottomRight = self.pos() + self.rect().bottomRight()
        logger.debug(f"Final SCENE corners: TL={final_scene_topLeft}, TR={final_scene_topRight}, BL={final_scene_bottomLeft}, BR={final_scene_bottomRight}") # DEBUG
        logger.debug(f"Compare fixed corner: Expected={fixed_corner_scene_pos}, Actual corresponding final corner based on handle_type:") # DEBUG
        if handle_type == "top_left": logger.debug(f"  BR: Expected={fixed_corner_scene_pos}, Actual={final_scene_bottomRight}") # DEBUG
        elif handle_type == "top_right": logger.debug(f"  BL: Expected={fixed_corner_scene_pos}, Actual={final_scene_bottomLeft}") # DEBUG
        elif handle_type == "bottom_left": logger.debug(f"  TR: Expected={fixed_corner_scene_pos}, Actual={final_scene_topRight}") # DEBUG
        elif handle_type == "bottom_right": logger.debug(f"  TL: Expected={fixed_corner_scene_pos}, Actual={final_scene_topLeft}") # DEBUG

        self._is_updating_handles = True
        self.update_handles_position()
        self._is_updating_handles = False
        
        self._is_resizing_via_handle = False # Indiquer que le redimensionnement est terminé
        logger.debug(f"--- handle_moved END ---")
        # logger.debug(f"Rect resized: scene_rect={new_target_scene_rect}, local_rect={self.rect()}, pos={self.pos()}")

    def boundingRect(self):
        base_rect = super().boundingRect() # C'est self.rect()
        if self._is_selected:
            # Assurer que les poignées sont cliquables
            # La taille de la poignée en pixels doit être calculée ici aussi si editor_view est disponible
            handle_size_px = self.editor_view.mm_to_pixels(GridRectangleItem.handle_size_mm) if self.editor_view else GridRectangleItem.handle_size_mm * 3.78
            padding = handle_size_px 
            return base_rect.adjusted(-padding, -padding, padding, padding)
        return base_rect 