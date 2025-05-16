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

    def handle_moved(self, handle_type: str, new_handle_local_pos: QPointF):
        """Appelé par une poignée lorsqu'elle est déplacée, avec ancrage du coin opposé."""
        if not self.editor_view:
            return

        grid_spacing_x, grid_spacing_y = self.editor_view.get_grid_spacing()
        grid_origin_offset = self.editor_view.get_grid_origin_offset()

        # Coin supérieur gauche actuel de l'item dans la scène
        current_item_scene_pos = self.pos()
        # Rectangle de texte actuel en coordonnées locales de l'item
        current_text_local_rect = super().boundingRect()
        # Largeur et hauteur actuelles du texte
        current_text_width = current_text_local_rect.width()
        current_text_height = current_text_local_rect.height()

        # Coins actuels du rectangle de texte en coordonnées de SCÈNE
        scene_topLeft = current_item_scene_pos + current_text_local_rect.topLeft() # Devrait être self.pos()
        scene_bottomRight = current_item_scene_pos + current_text_local_rect.bottomRight()
        # Pour être plus précis si le topLeft local n'est pas (0,0)
        scene_topRight = current_item_scene_pos + current_text_local_rect.topRight()
        scene_bottomLeft = current_item_scene_pos + current_text_local_rect.bottomLeft()

        # Position de la souris (où la poignée est déplacée) en coordonnées de SCÈNE
        # new_handle_local_pos est la position de la poignée dans les coordonnées locales de GridTextItem.
        # Pour obtenir la position de la souris en scène, il faut la mapper.
        # La poignée elle-même est un enfant, donc new_handle_local_pos est la position relative à GridTextItem.
        moving_corner_scene_target_pos = self.mapToScene(new_handle_local_pos)

        # Snapper cette position cible du coin mobile à la grille
        snapped_moving_corner_x = round((moving_corner_scene_target_pos.x() - grid_origin_offset.x()) / grid_spacing_x) * grid_spacing_x + grid_origin_offset.x()
        snapped_moving_corner_y = round((moving_corner_scene_target_pos.y() - grid_origin_offset.y()) / grid_spacing_y) * grid_spacing_y + grid_origin_offset.y()
        snapped_moving_corner_scene_pos = QPointF(snapped_moving_corner_x, snapped_moving_corner_y)

        # Déterminer le coin fixe et le nouveau rectangle cible dans la SCÈNE
        fixed_corner_scene_pos = QPointF()
        new_target_scene_rect = QRectF()

        if handle_type == "top_left":
            fixed_corner_scene_pos = scene_bottomRight
            new_target_scene_rect = QRectF(snapped_moving_corner_scene_pos, fixed_corner_scene_pos).normalized()
        elif handle_type == "top_right":
            fixed_corner_scene_pos = scene_bottomLeft
            # Construire le rect à partir des X et Y fixes et mobiles
            p1 = QPointF(fixed_corner_scene_pos.x(), snapped_moving_corner_scene_pos.y()) # Nouveau topLeft (X de l'ancre, Y du mobile)
            p2 = QPointF(snapped_moving_corner_scene_pos.x(), fixed_corner_scene_pos.y()) # Nouveau bottomRight (X du mobile, Y de l'ancre)
            new_target_scene_rect = QRectF(p1, p2).normalized()
        elif handle_type == "bottom_left":
            fixed_corner_scene_pos = scene_topRight
            p1 = QPointF(snapped_moving_corner_scene_pos.x(), fixed_corner_scene_pos.y()) # Nouveau topLeft (X du mobile, Y de l'ancre)
            p2 = QPointF(fixed_corner_scene_pos.x(), snapped_moving_corner_scene_pos.y()) # Nouveau bottomRight (X de l'ancre, Y du mobile)
            new_target_scene_rect = QRectF(p1, p2).normalized()
        elif handle_type == "bottom_right":
            fixed_corner_scene_pos = scene_topLeft 
            new_target_scene_rect = QRectF(fixed_corner_scene_pos, snapped_moving_corner_scene_pos).normalized()
        
        # Assurer une taille minimale pour la largeur et la hauteur du rectangle de SCÈNE
        new_width = new_target_scene_rect.width()
        new_height = new_target_scene_rect.height() # On aura besoin de la hauteur pour ajuster le rect si taille min affecte hauteur

        final_scene_width = max(new_width, grid_spacing_x)
        final_scene_height = max(new_height, grid_spacing_y) # Même si on ne fixe pas la hauteur du texte, le rect doit respecter la grille

        # Ajuster le rectangle de SCÈNE si la taille minimale l'a modifié
        # Ceci assure que le coin fixe reste fixe, et le coin mobile s'ajuste.
        if final_scene_width > new_width:
            if handle_type == "top_left" or handle_type == "bottom_left": # Le coin gauche bougeait
                new_target_scene_rect.setLeft(new_target_scene_rect.right() - final_scene_width)
            else: # Le coin droit bougeait (top_right or bottom_right)
                new_target_scene_rect.setRight(new_target_scene_rect.left() + final_scene_width)
        
        if final_scene_height > new_height:
            if handle_type == "top_left" or handle_type == "top_right": # Le coin haut bougeait
                new_target_scene_rect.setTop(new_target_scene_rect.bottom() - final_scene_height)
            else: # Le coin bas bougeait (bottom_left or bottom_right)
                new_target_scene_rect.setBottom(new_target_scene_rect.top() + final_scene_height)

        # Appliquer les changements
        print(f"handle_moved: type={handle_type}")
        print(f"  Initial self.pos(): {self.pos()}, Initial self.width: {self.document().textWidth()}")
        print(f"  Fixed corner (scene): {fixed_corner_scene_pos}")
        print(f"  Snapped moving corner (scene): {snapped_moving_corner_scene_pos}")
        print(f"  New target scene rect: {new_target_scene_rect}")
        print(f"  Applying self.setPos({new_target_scene_rect.topLeft()})")
        print(f"  Applying setTextWidth({new_target_scene_rect.width()})")

        self.prepareGeometryChange()
        
        self.setPos(new_target_scene_rect.topLeft()) # La nouvelle position de l'item est le topLeft du rect de scène
        self.document().setTextWidth(new_target_scene_rect.width()) # La largeur du texte est la largeur du rect de scène
        
        # La hauteur de QGraphicsTextItem est gérée par son contenu.
        # Si on voulait forcer une hauteur visuelle minimale (pas du texte mais de la zone d'interaction),
        # on pourrait avoir besoin d'un item conteneur ou de dessiner un fond nous-mêmes.
        # Pour l'instant, on se concentre sur la largeur.

        self.update_handles_position() # Mettre à jour la position des poignées

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