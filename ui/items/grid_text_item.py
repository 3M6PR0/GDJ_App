from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor, QPen # Ajout pour les poignées
import math # Pour math.floor et math.ceil ou round

class GridTextItem(QGraphicsTextItem):
    handle_size = 8.0
    handle_space = -4.0 # Pour que le centre de la poignée soit sur le coin

    class ResizeHandle(QGraphicsEllipseItem):
        def __init__(self, parent, position_type):
            super().__init__(-GridTextItem.handle_size / 2, -GridTextItem.handle_size / 2, 
                             GridTextItem.handle_size, GridTextItem.handle_size, parent)
            self.parent_item = parent
            self.position_type = position_type # ex: "top_left", "bottom_right"
            self.setBrush(QBrush(QColor("blue")))
            self.setPen(QPen(QColor("black"), 1))
            self.setFlag(QGraphicsItem.ItemIsMovable) # Pour détecter le mouvement
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
            self.setZValue(10) # S'assurer qu'elles sont au-dessus de l'item texte
            self.hide() # Cachées par défaut

        def itemChange(self, change, value):
            if change == QGraphicsItem.ItemPositionChange and self.parent_item.isSelected():
                # Ici, nous allons notifier le parent pour qu'il se redimensionne
                # Pour l'instant, on va juste laisser bouger, le parent gèrera le snap
                new_pos_in_parent = value
                self.parent_item.handle_moved(self.position_type, new_pos_in_parent)
                return new_pos_in_parent # Retourner la nouvelle position pour que la poignée bouge
            return super().itemChange(change, value)

    def __init__(self, text="Nouveau Texte", editor_view=None, parent=None):
        super().__init__(parent)
        self.setPlainText(text)
        self.editor_view = editor_view # Référence à LamicoidEditorWidget
        self._is_selected = False # Etat de sélection interne
        
        self.setFlags(QGraphicsItem.ItemIsMovable | 
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges | # Important pour itemChange
                      QGraphicsItem.ItemIsFocusable # Pour que textInteractionFlags fonctionne bien
                      )
        self.setTextInteractionFlags(Qt.TextEditorInteraction) 

        self.handles = {}
        self._create_handles()
        self.update_handles_position()

    def _create_handles(self):
        """Crée les poignées de redimensionnement."""
        # Pour l'instant, 4 coins. On pourrait en ajouter plus tard.
        positions = {
            "top_left": None, "top_right": None,
            "bottom_left": None, "bottom_right": None
        }
        for pos_type in positions.keys():
            handle = GridTextItem.ResizeHandle(self, pos_type)
            self.handles[pos_type] = handle
            # Les poignées sont enfants de GridTextItem, leurs positions seront relatives

    def update_handles_position(self):
        """Met à jour la position des poignées en fonction du boundingRect de l'item."""
        # Utiliser super().boundingRect() pour obtenir le rectangle réel du texte,
        # indépendamment du padding ajouté pour la sélection.
        rect = super().boundingRect() 
        self.handles["top_left"].setPos(rect.topLeft())
        self.handles["top_right"].setPos(rect.topRight())
        self.handles["bottom_left"].setPos(rect.bottomLeft())
        self.handles["bottom_right"].setPos(rect.bottomRight())

    def show_handles(self, show=True):
        for handle in self.handles.values():
            handle.setVisible(show)

    def itemChange(self, change, value):
        # Gestion du magnétisme AVANT que la position ne change
        if self.editor_view and change == QGraphicsItem.ItemPositionChange: # <<< Changé ici: ItemPositionChange
            new_pos_candidate = value # value est la nouvelle position proposée
            grid_spacing_x, grid_spacing_y = self.editor_view.get_grid_spacing() 
            grid_origin_offset = self.editor_view.get_grid_origin_offset() 

            if grid_spacing_x > 0 and grid_spacing_y > 0: 
                relative_x = new_pos_candidate.x() - grid_origin_offset.x()
                relative_y = new_pos_candidate.y() - grid_origin_offset.y()

                snapped_relative_x = round(relative_x / grid_spacing_x) * grid_spacing_x
                snapped_relative_y = round(relative_y / grid_spacing_y) * grid_spacing_y
                
                snapped_scene_x = snapped_relative_x + grid_origin_offset.x()
                snapped_scene_y = snapped_relative_y + grid_origin_offset.y()
                
                snapped_pos = QPointF(snapped_scene_x, snapped_scene_y)
                # Si la position snappée est différente, on la retourne pour l'appliquer.
                # Ceci est la nouvelle position qui sera réellement définie pour l'item.
                if snapped_pos != self.pos(): # Important pour éviter une boucle si déjà snappé
                    # On ne met pas à jour les poignées ici directement,
                    # car ItemPositionHasChanged sera appelé ensuite.
                    return snapped_pos 
                # Si la position snappée est la même que la position actuelle,
                # et que c'est aussi la même que la candidate, on laisse Qt continuer.
                # Si elle est la même que l'actuelle mais différente de la candidate,
                # on retourne quand même la position actuelle pour éviter le changement.
                if new_pos_candidate == self.pos():
                    return new_pos_candidate # Laisser tel quel
                else:
                    return self.pos() # Forcer à rester à la position snappée actuelle
            
        # Gestion de la sélection pour afficher/cacher les poignées
        if change == QGraphicsItem.ItemSelectedHasChanged:
            is_selected = bool(value)
            self._is_selected = is_selected # Mettre à jour l'état interne
            self.show_handles(is_selected)
            if is_selected:
                self.update_handles_position()
            # Pas besoin de retourner super() ici, car on a déjà traité la valeur
            # et ItemSelectedHasChanged ne s'attend pas à ce que la valeur soit modifiée généralement.
            # Mais il est plus sûr de laisser Qt gérer la propagation de la valeur.
            # return value # Cette ligne est correcte

        # Gestion de la mise à jour des poignées APRES un changement de position effectif
        if change == QGraphicsItem.ItemPositionHasChanged: # <<< Note: ItemPositionHasChanged ici
             self.update_handles_position() 
             # Pas besoin de retourner value ici, car c'est une notification.
             # Le super().itemChange s'en chargera.

        return super().itemChange(change, value)

    def handle_moved(self, handle_type: str, new_handle_pos_in_item: QPointF):
        """Appelé par une poignée lorsqu'elle est déplacée."""
        if not self.editor_view:
            return

        current_rect = self.boundingRect() # Rectangle actuel de l'item dans ses propres coordonnées
        new_rect = QRectF(current_rect)

        # Convertir la nouvelle position de la poignée (qui est dans les coordonnées de l'item parent)
        # en coordonnées de la scène pour l'alignement sur la grille.
        # Position de l'item dans la scène
        item_scene_pos = self.scenePos()
        
        # La position de la poignée est déjà relative au GridTextItem.
        # new_handle_pos_in_item est la nouvelle position de la poignée DANS le système de coordonnées de GridTextItem.
        
        # On veut déterminer le nouveau coin de l'item dans les coordonnées de l'item lui-même.
        if handle_type == "top_left":
            new_rect.setTopLeft(new_handle_pos_in_item)
        elif handle_type == "top_right":
            new_rect.setTopRight(new_handle_pos_in_item)
        elif handle_type == "bottom_left":
            new_rect.setBottomLeft(new_handle_pos_in_item)
        elif handle_type == "bottom_right":
            new_rect.setBottomRight(new_handle_pos_in_item)
        
        # Normaliser le rectangle (s'assurer que topLeft est bien en haut à gauche)
        # Cela gère le cas où l'utilisateur "inverse" le rectangle en déplaçant une poignée au-delà de son opposée.
        normalized_rect = new_rect.normalized()

        # --- Logique de Snap du rectangle ---
        grid_spacing_x, grid_spacing_y = self.editor_view.get_grid_spacing()
        grid_origin_offset = self.editor_view.get_grid_origin_offset() # Coordonnées de scène

        # Les coordonnées du rectangle (normalized_rect) sont dans le système de coordonnées de l'item.
        # Pour le snap, il faut travailler avec les coordonnées de la scène.
        # Le nouveau coin supérieur gauche de l'item DANS LA SCENE sera : self.pos() + normalized_rect.topLeft()
        
        # Nouveau TopLeft de l'item dans la scène
        potential_item_scene_topLeft_x = self.pos().x() + normalized_rect.left()
        potential_item_scene_topLeft_y = self.pos().y() + normalized_rect.top()

        # Aligner ce TopLeft sur la grille
        relative_tl_x = potential_item_scene_topLeft_x - grid_origin_offset.x()
        relative_tl_y = potential_item_scene_topLeft_y - grid_origin_offset.y()
        
        snapped_relative_tl_x = round(relative_tl_x / grid_spacing_x) * grid_spacing_x
        snapped_relative_tl_y = round(relative_tl_y / grid_spacing_y) * grid_spacing_y

        snapped_item_scene_topLeft_x = snapped_relative_tl_x + grid_origin_offset.x()
        snapped_item_scene_topLeft_y = snapped_relative_tl_y + grid_origin_offset.y()

        # Calculer la nouvelle position de l'item dans la scène
        new_item_scene_pos_x = snapped_item_scene_topLeft_x
        new_item_scene_pos_y = snapped_item_scene_topLeft_y
        
        # Aligner la largeur et la hauteur sur la grille
        # La largeur et la hauteur sont calculées à partir des coins snappés.
        # On doit aussi aligner le coin inférieur droit.

        potential_item_scene_bottomRight_x = self.pos().x() + normalized_rect.right()
        potential_item_scene_bottomRight_y = self.pos().y() + normalized_rect.bottom()

        relative_br_x = potential_item_scene_bottomRight_x - grid_origin_offset.x()
        relative_br_y = potential_item_scene_bottomRight_y - grid_origin_offset.y()

        snapped_relative_br_x = round(relative_br_x / grid_spacing_x) * grid_spacing_x
        snapped_relative_br_y = round(relative_br_y / grid_spacing_y) * grid_spacing_y

        snapped_item_scene_bottomRight_x = snapped_relative_br_x + grid_origin_offset.x()
        snapped_item_scene_bottomRight_y = snapped_relative_br_y + grid_origin_offset.y()
        
        snapped_width = snapped_item_scene_bottomRight_x - snapped_item_scene_topLeft_x
        snapped_height = snapped_item_scene_bottomRight_y - snapped_item_scene_topLeft_y

        # Assurer une taille minimale (par exemple, l'espacement de la grille)
        snapped_width = max(snapped_width, grid_spacing_x)
        snapped_height = max(snapped_height, grid_spacing_y)

        # Avant de changer la géométrie, préparer la scène
        self.prepareGeometryChange()
        
        # Mettre à jour la position de l'item
        self.setPos(QPointF(new_item_scene_pos_x, new_item_scene_pos_y))
        
        # Mettre à jour la largeur du texte.
        # Note: QGraphicsTextItem n'a pas de setHeight. La hauteur est déterminée par le contenu.
        # Pour contrôler la hauteur, il faudrait utiliser un QGraphicsRectItem et y dessiner le texte,
        # ou limiter la hauteur du document texte, ce qui est plus complexe.
        # Pour l'instant, on contrôle seulement la largeur.
        # La largeur du texte est relative à l'item lui-même, donc pas de self.pos() ici.
        self.document().setTextWidth(snapped_width)

        # Après le changement, mettre à jour les poignées
        self.update_handles_position()
        
        # Il faut aussi remettre la poignée déplacée à sa nouvelle position snappée (relative à l'item)
        # C'est un peu délicat car la position de l'item a aussi changé.
        # Le plus simple est que update_handles_position() recalcule tout.

    # Surcharger boundingRect pour s'assurer qu'il est correct après le changement de largeur
    def boundingRect(self):
        # Le boundingRect de QGraphicsTextItem est basé sur son document.
        # Si on a fixé textWidth, il devrait être correct.
        # On peut ajouter un padding si les poignées dépassent légèrement.
        base_rect = super().boundingRect()
        if self._is_selected: # Utiliser l'état interne
             # Ajouter un padding pour les poignées pour s'assurer qu'elles sont incluses et peuvent être cliquées
             # handle_size est le diamètre, donc handle_size/2 est le rayon.
             padding = GridTextItem.handle_size 
             return base_rect.adjusted(-padding, -padding, padding, padding)
        return base_rect
    
    # Surcharger shape pour le clipping (optionnel, mais bon pour la performance)
    # def shape(self):
    #     path = QPainterPath()
    #     path.addRect(self.boundingRect())
    #     return path

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
    import sys

    app = QApplication(sys.argv)
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    
    class MockEditorView:
        def get_grid_spacing(self):
            return 20.0, 20.0 # Retourne maintenant un tuple
        def get_grid_origin_offset(self):
            return QPointF(10,10) 

    mock_editor = MockEditorView()

    item1 = GridTextItem("Texte Magnétique 1", editor_view=mock_editor)
    item1.setPos(15, 18) 
    scene.addItem(item1)
    item1.setSelected(True) # Pour voir les poignées

    item2 = GridTextItem("Texte Éditable 2", editor_view=mock_editor)
    item2.setPos(53, 57)
    scene.addItem(item2)
    
    view.setWindowTitle("Test GridTextItem - Poignées et Redimensionnement (WIP)")
    view.resize(600,400) # Un peu plus grand pour voir
    view.show()
    
    sys.exit(app.exec_()) 