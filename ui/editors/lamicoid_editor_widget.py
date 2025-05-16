from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPathItem, QGraphicsLineItem
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QBrush, QPen, QColor, QPainterPath, QTransform, QPainter, QPalette
import logging
from typing import List

from ui.items.grid_text_item import GridTextItem
from ui.items.grid_rectangle_item import GridRectangleItem

logger = logging.getLogger('GDJ_App')

# Conversion (peut être déplacé dans un fichier utils plus tard)
DEFAULT_DPI = 96.0
INCH_TO_MM = 25.4

def global_mm_to_pixels(mm: float, dpi: float = DEFAULT_DPI) -> float:
    return (mm / INCH_TO_MM) * dpi

def global_pixels_to_mm(pixels: float, dpi: float = DEFAULT_DPI) -> float:
    return (pixels / dpi) * INCH_TO_MM

class LamicoidEditorWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LamicoidEditorWidget")
        
        self.current_width_px: float = 200.0
        self.current_height_px: float = 150.0
        self.current_corner_radius_px: float = 10.0
        self.current_margin_px: float = 5.0

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        self.lamicoid_item: QGraphicsPathItem | None = None
        self.margin_item: QGraphicsPathItem | None = None # Pour visualiser la marge
        self.grid_lines: List[QGraphicsLineItem] = [] # Pour stocker les lignes de la grille

        self.grid_spacing_px: float = 20.0 # Sera mis à jour par set_lamicoid_properties

        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag) # Permettre de "tirer" la vue
        self.centerOn(0,0) # Centrer la vue initialement

        self._draw_lamicoid()
        logger.debug("LamicoidEditorWidget initialisé avec QGraphicsView.")

    def add_editor_item(self, item_type: str):
        """Ajoute un nouvel item à l'éditeur, basé sur item_type."""
        if item_type == "texte":
            text_item = GridTextItem("Texte", editor_view=self)
            
            initial_pos = QPointF(0,0) # Position par défaut si pas de marge/grille
            grid_spacing_x, grid_spacing_y = self.get_grid_spacing()
            grid_origin_offset = self.get_grid_origin_offset()

            if self.margin_item and grid_spacing_x > 0 and grid_spacing_y > 0:
                # Tenter de placer au coin supérieur gauche de la zone de marge, aligné
                # Coordonnées du coin supérieur gauche de la zone de marge (déjà dans les coordonnées de scène)
                desired_pos_in_scene = grid_origin_offset 
                
                # Coordonnées relatives à l'origine de la grille
                relative_x = desired_pos_in_scene.x() - grid_origin_offset.x() # Sera 0
                relative_y = desired_pos_in_scene.y() - grid_origin_offset.y() # Sera 0

                # Aligner ces coordonnées relatives (devrait rester 0,0 si desired_pos est bien l'origine de la grille)
                # Mais si on voulait un autre point, cette logique serait utile.
                # Pour le coin sup gauche, c'est déjà aligné par définition de grid_origin_offset.
                snapped_relative_x = round(relative_x / grid_spacing_x) * grid_spacing_x
                snapped_relative_y = round(relative_y / grid_spacing_y) * grid_spacing_y
                
                # Reconvertir en coordonnées de scène
                initial_pos = QPointF(snapped_relative_x + grid_origin_offset.x(), 
                                        snapped_relative_y + grid_origin_offset.y())
            else: # Pas de grille ou marge, on utilise le coin supérieur gauche du lamicoid s'il existe
                if self.lamicoid_item:
                    lamicoid_rect_in_scene = self.lamicoid_item.mapToScene(self.lamicoid_item.boundingRect()).boundingRect()
                    initial_pos = lamicoid_rect_in_scene.topLeft()


            text_item.setPos(initial_pos) 
            self._scene.addItem(text_item)
            logger.debug(f"GridTextItem ajouté à la scène à {initial_pos} (aligné)")
        elif item_type == "rectangle":
            grid_spacing_x, grid_spacing_y = self.get_grid_spacing()
            grid_origin_offset = self.get_grid_origin_offset()

            if not (grid_spacing_x > 0 and grid_spacing_y > 0 and self.margin_item):
                logger.warning("Impossible d'ajouter un rectangle : grille non définie ou marge absente.")
                return

            # Position initiale du coin supérieur gauche du rectangle, alignée sur la grille
            # (identique à la logique pour GridTextItem)
            rect_start_pos_scene = grid_origin_offset

            # Définir une taille initiale pour le rectangle, par exemple 2x2 cellules de grille
            rect_width_px = 2 * grid_spacing_x
            rect_height_px = 2 * grid_spacing_y
            
            # Le QGraphicsRectItem est défini par son coin sup gauche et sa largeur/hauteur
            # Ses coordonnées sont relatives à sa propre position (self.pos() de l'item).
            # Si on veut que le rect_start_pos_scene soit le coin sup gauche du rectangle DANS LA SCENE,
            # alors le QRectF de construction doit avoir son topLeft à (0,0) et on setPos() l'item.
            initial_local_rect = QRectF(0, 0, rect_width_px, rect_height_px)
            
            rectangle_item = GridRectangleItem(initial_local_rect, editor_view=self)
            rectangle_item.setPos(rect_start_pos_scene)
            
            self._scene.addItem(rectangle_item)
            logger.debug(f"GridRectangleItem ajouté à la scène à {rect_start_pos_scene} avec taille {rect_width_px}x{rect_height_px}")
        else:
            logger.warning(f"Type d'item inconnu demandé pour ajout: {item_type}")

    def set_lamicoid_properties(self, width_px: float, height_px: float, 
                                corner_radius_px: float, margin_px: float, 
                                grid_spacing_px: float):
        self.current_width_px = max(1.0, width_px)
        self.current_height_px = max(1.0, height_px)
        self.current_corner_radius_px = max(0.0, corner_radius_px)
        self.current_margin_px = max(0.0, margin_px)
        self.grid_spacing_px = max(0.1, grid_spacing_px)

        # Le rayon ne peut pas être plus grand que la moitié de la plus petite dimension
        max_radius_from_width = self.current_width_px / 2
        max_radius_from_height = self.current_height_px / 2
        self.current_corner_radius_px = min(self.current_corner_radius_px, max_radius_from_width, max_radius_from_height)

        # La marge ne peut pas être plus grande que la moitié de la plus petite dimension (après déduction du rayon pour être sûr)
        # ou simplement plus grande que la moitié de la dimension
        max_margin_from_width = (self.current_width_px - 2 * self.current_corner_radius_px) / 2
        max_margin_from_height = (self.current_height_px - 2 * self.current_corner_radius_px) / 2
        # On s'assure que la marge n'est pas négative si le rayon est grand
        self.current_margin_px = min(self.current_margin_px, max(0, max_margin_from_width), max(0, max_margin_from_height))
        
        logger.debug(f"Lamicoid properties set: W={self.current_width_px}px, H={self.current_height_px}px, R={self.current_corner_radius_px}px, M={self.current_margin_px}px")
        self._draw_lamicoid()

    def _draw_lamicoid(self):
        if self.lamicoid_item:
            self._scene.removeItem(self.lamicoid_item)
            self.lamicoid_item = None
        if self.margin_item:
            self._scene.removeItem(self.margin_item)
            self.margin_item = None
        
        for line in self.grid_lines:
            self._scene.removeItem(line)
        self.grid_lines.clear()

        # Dessiner le Lamicoid (bord extérieur)
        path = QPainterPath()
        rect = QRectF(-self.current_width_px / 2, -self.current_height_px / 2, 
                      self.current_width_px, self.current_height_px)
        path.addRoundedRect(rect, self.current_corner_radius_px, self.current_corner_radius_px)
        
        self.lamicoid_item = QGraphicsPathItem(path)
        self.lamicoid_item.setBrush(QBrush(QColor(220, 220, 220))) # Couleur de fond du Lamicoid
        self.lamicoid_item.setPen(QPen(Qt.black, 1)) # Bordure du Lamicoid
        self.lamicoid_item.setZValue(-10) # <<< Pour s'assurer qu'il est en arrière-plan
        self._scene.addItem(self.lamicoid_item)

        # Dessiner la marge (bord intérieur)
        margin_width = self.current_width_px - (2 * self.current_margin_px)
        margin_height = self.current_height_px - (2 * self.current_margin_px)
        
        # Le rayon de la marge doit aussi être ajusté si la marge est grande
        # On veut que le "coin" de la zone de contenu soit aussi arrondi
        # Le rayon intérieur est le rayon extérieur moins la marge.
        inner_radius = max(0.0, self.current_corner_radius_px - self.current_margin_px)

        if margin_width > 0 and margin_height > 0:
            margin_path = QPainterPath()
            margin_rect = QRectF(-margin_width / 2, -margin_height / 2, 
                                 margin_width, margin_height)
            margin_path.addRoundedRect(margin_rect, inner_radius, inner_radius)
            
            self.margin_item = QGraphicsPathItem(margin_path)
            # Marge souvent juste une ligne pointillée ou une couleur différente pour la zone de contenu
            pen = QPen(QColor(150, 150, 255), 1, Qt.DashLine)
            self.margin_item.setPen(pen)
            self.margin_item.setZValue(-9) # <<< Légèrement au-dessus du lamicoid, mais sous les items
            # self.margin_item.setBrush(QBrush(Qt.white)) # Si on veut un fond pour la zone de contenu
            self._scene.addItem(self.margin_item)
            
            # Dessiner la grille à l'intérieur de la zone de marge
            self._draw_grid_within_rect(margin_rect)

        # Mettre à jour la taille de la scène pour qu'elle contienne le lamicoid et un peu de marge
        scene_padding = 20 # un peu d'espace autour
        self._scene.setSceneRect(
            rect.adjusted(-scene_padding, -scene_padding, scene_padding, scene_padding)
        )
        self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)

    def _draw_grid_within_rect(self, rect: QRectF):
        """Dessine une grille à l'intérieur du QRectF fourni."""
        if self.grid_spacing_px <= 0:
            return

        grid_pen = QPen(QColor(200, 200, 200), 0.5) # Couleur et épaisseur de la grille

        # Lignes Verticales
        x_start = rect.left()
        x_end = rect.right()
        y_top = rect.top()
        y_bottom = rect.bottom()

        current_x = x_start
        while current_x <= x_end:
            line = QGraphicsLineItem(current_x, y_top, current_x, y_bottom)
            line.setPen(grid_pen)
            line.setZValue(-8) # <<< Grille au-dessus de la marge mais sous les items
            self._scene.addItem(line)
            self.grid_lines.append(line)
            current_x += self.grid_spacing_px

        # Lignes Horizontales
        current_y = y_top
        while current_y <= y_bottom:
            line = QGraphicsLineItem(x_start, current_y, x_end, current_y)
            line.setPen(grid_pen)
            line.setZValue(-8) # <<< Grille au-dessus de la marge mais sous les items
            self._scene.addItem(line)
            self.grid_lines.append(line)
            current_y += self.grid_spacing_px
        
        logger.debug(f"Grille dessinée à l'intérieur de {rect} avec espacement {self.grid_spacing_px}px")

    def get_grid_spacing(self) -> tuple[float, float]:
        """Retourne l'espacement actuel de la grille (x, y) en pixels."""
        return (self.grid_spacing_px, self.grid_spacing_px)

    def get_grid_origin_offset(self) -> QPointF:
        """
        Retourne le décalage de l'origine de la grille (coin supérieur gauche de la zone de contenu)
        par rapport à l'origine de la scène.
        """
        if self.margin_item:
            # margin_item est déjà positionné correctement dans la scène (centré).
            # Son propre boundingRect().topLeft() sera relatif à sa propre position,
            # qui est (0,0) si non transformé.
            # Ce que nous voulons, c'est le coin supérieur gauche de la *zone* qu'il représente.
            # Le margin_rect dans _draw_lamicoid est déjà dans le système de coordonnées centré.
            margin_width = self.current_width_px - (2 * self.current_margin_px)
            margin_height = self.current_height_px - (2 * self.current_margin_px)
            if margin_width > 0 and margin_height > 0:
                return QPointF(-margin_width / 2, -margin_height / 2)
        
        # Si pas de marge ou marge trop grande, il n'y a pas de grille définie clairement
        # ou elle est à l'origine de la scène pour l'instant.
        # Cela pourrait nécessiter une gestion plus fine si on veut une grille même sans marge visible.
        # Pour l'instant, on retourne un point qui correspond au centre de la vue si pas de marge.
        # Ou peut-être le coin supérieur gauche du lamicoid_item lui-même ?
        # Le GridTextItem s'attend à un offset pour la grille, donc (0,0) relatif à la scène
        # n'est pas idéal si le lamicoid n'est pas à (0,0).
        # Cependant, les items sont ajoutés à la scène, et leur position est relative à la scène.
        # Le lamicoid et la marge sont dessinés centrés à (0,0) dans la scène.
        # Donc, le coin sup gauche de la zone de marge est (-margin_width/2, -margin_height/2).
        logger.warning("get_grid_origin_offset appelé alors que margin_item n'est pas défini ou la zone de marge est invalide. Retourne QPointF(0,0).")
        return QPointF(0.0, 0.0) # Valeur par défaut si pas de marge

    def clear(self): # Méthode pour effacer l'éditeur si besoin
        if self.lamicoid_item:
            self._scene.removeItem(self.lamicoid_item)
            self.lamicoid_item = None
        if self.margin_item:
            self._scene.removeItem(self.margin_item)
            self.margin_item = None
        # On pourrait aussi cacher la vue ou afficher un message
        logger.debug("Lamicoid editor cleared.")

    def resizeEvent(self, event):
        # S'assurer que la vue est bien ajustée après un redimensionnement de la fenêtre
        super().resizeEvent(event)
        if self.lamicoid_item: # Si quelque chose est dessiné
            self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)

    @staticmethod
    def mm_to_pixels(mm: float, dpi: float = DEFAULT_DPI) -> float:
        return global_mm_to_pixels(mm, dpi)

    @staticmethod
    def pixels_to_mm(pixels: float, dpi: float = DEFAULT_DPI) -> float:
        return global_pixels_to_mm(pixels, dpi)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMainWindow
    import sys

    app = QApplication(sys.argv)
    
    # Pour tester directement avec des valeurs simulées de LamicoidPage
    main_window = QMainWindow()
    editor = LamicoidEditorWidget()
    main_window.setCentralWidget(editor)
    main_window.setWindowTitle("Test LamicoidEditorWidget Direct")
    main_window.setGeometry(100, 100, 700, 500)
    main_window.show()

    # Simuler un appel depuis LamicoidPage après un petit délai
    from PyQt5.QtCore import QTimer
    def test_properties():
        # Valeurs typiques en pixels (converties depuis mm)
        # 85mm x 55mm, rayon 3mm, marge 5mm (DPI 96)
        # 85mm -> (85/25.4)*96 = 321 pixels
        # 55mm -> (55/25.4)*96 = 207 pixels
        # 3mm  -> (3/25.4)*96  = 11 pixels
        # 5mm  -> (5/25.4)*96  = 19 pixels
        editor.set_lamicoid_properties(
            width_px=321, 
            height_px=207, 
            corner_radius_px=11, 
            margin_px=19,
            grid_spacing_px=editor.mm_to_pixels(1.0) # Exemple pour le test, 1mm en pixels
        )
    QTimer.singleShot(500, test_properties)
    
    sys.exit(app.exec_()) 