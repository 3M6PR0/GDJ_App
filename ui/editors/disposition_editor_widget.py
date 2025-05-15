from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QPushButton, QGraphicsItem, QGraphicsPathItem, QGraphicsLineItem, QMessageBox, QRubberBand, QApplication, QGraphicsSimpleTextItem
from PyQt5.QtCore import Qt, QRectF, QLineF, QPoint, QSize, QPointF
from PyQt5.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath, QFont, QFontMetrics
import logging

logger = logging.getLogger('GDJ_App')

# Clé pour marquer l'item de fond de page
PAGE_BACKGROUND_ITEM_KEY = QGraphicsItem.UserType + 1

# Constantes pour la grille et la page
DEFAULT_CELL_WIDTH = 40  # pixels
DEFAULT_CELL_HEIGHT = 40  # pixels
PAGE_MARGIN = 20          # pixels de marge autour de la page dans la scène
DEFAULT_ROWS = 1
DEFAULT_COLS = 1
CORNER_RADIUS = 10        # pixels pour les coins arrondis de la page

# Constantes pour les règles
DEFAULT_DPI = 96.0  # Points par pouce, pour la conversion en mm
RULER_THICKNESS = 20 # Épaisseur des règles en pixels
RULER_TEXT_MARGIN = 10 # Marge pour le texte dans les règles (augmentée)

SELECTED_CELL_BRUSH = QBrush(QColor(173, 216, 230, 128)) # Bleu clair semi-transparent
NORMAL_CELL_BRUSH = QBrush(Qt.transparent)
CELL_BORDER_PEN = QPen(QColor("#C0C0C0"), 0.5, Qt.DotLine) # Pointillés légers pour les cellules

# Structure pour stocker les détails du contenu préservé
# (content_type, actual_text_if_any)
PreservedContentDetails = tuple[str, str | None]

INCH_TO_MM = 25.4

def pixels_to_mm(pixels: float, dpi: float) -> float:
    return (pixels / dpi) * INCH_TO_MM

class AbstractRulerItem(QGraphicsItem):
    def __init__(self, parent: QGraphicsItem | None = None):
        super().__init__(parent)
        self._length_pixels: float = 0
        # Liste de tuples: (position_pixel, label_mm_str)
        self._divisions: list[tuple[float, str]] = []
        self._total_label_mm: str = "0mm"
        self.setZValue(10) # S'assurer que les règles sont au-dessus des autres éléments
        self._font = QFont("Arial", 7)
        self._pen = QPen(Qt.black, 1)
        self._text_pen = QPen(Qt.black, 1)

    def set_config(self, length_pixels: float, divisions_pixels_labels: list[tuple[float, str]], total_label_mm: str):
        self.prepareGeometryChange()
        self._length_pixels = length_pixels
        self._divisions = divisions_pixels_labels
        self._total_label_mm = total_label_mm
        self.update()

    def boundingRect(self) -> QRectF:
        # Implémentation spécifique dans les classes dérivées
        raise NotImplementedError

    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: QWidget | None = None):
        # Implémentation spécifique dans les classes dérivées
        raise NotImplementedError

class HorizontalRulerItem(AbstractRulerItem):
    def boundingRect(self) -> QRectF:
        return QRectF(0, -RULER_THICKNESS, self._length_pixels, RULER_THICKNESS)

    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: QWidget | None = None):
        painter.setFont(self._font)
        painter.setPen(self._pen)

        # Ligne de base de la règle
        painter.drawLine(QPointF(0, 0), QPointF(self._length_pixels, 0))

        # Afficher seulement le label total centré
        painter.setPen(self._text_pen)
        # Le texte est dans le boundingRect de la règle, qui va de y=-RULER_THICKNESS à y=0.
        # On veut centrer le texte dans cet espace.
        text_rect = QRectF(0, -RULER_THICKNESS + RULER_TEXT_MARGIN, self._length_pixels, RULER_THICKNESS - RULER_TEXT_MARGIN * 2)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextDontClip, self._total_label_mm)

class VerticalRulerItem(AbstractRulerItem):
    def boundingRect(self) -> QRectF:
        # Estimation de la largeur pour le texte (ex: "100 mm")
        # Une QFontMetrics pourrait être utilisée ici pour plus de précision si nécessaire,
        # mais une estimation fixe est plus simple pour l'instant.
        text_label_width_estimate = 40  # pixels, assez pour "XXX mm"
        # La règle elle-même n'a plus besoin d'une "épaisseur" si la ligne est à x=0
        # Le boundingRect inclut la ligne (à x=0) et le texte à droite.
        return QRectF(0, 0, RULER_TEXT_MARGIN + text_label_width_estimate, self._length_pixels)

    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget: QWidget | None = None):
        painter.setFont(self._font)
        painter.setPen(self._pen)

        # Ligne de base de la règle à x=0 (bord gauche du boundingRect)
        painter.drawLine(QPointF(0, 0), QPointF(0, self._length_pixels))

        # Afficher le label total à droite de la ligne, centré verticalement
        painter.setPen(self._text_pen)
        
        # Le texte est positionné à RULER_TEXT_MARGIN de la ligne (qui est à x=0).
        # Il s'étend sur la largeur restante du boundingRect.
        text_render_rect = QRectF(
            RULER_TEXT_MARGIN,  # Début X du texte
            0,                  # Début Y du texte (sera centré verticalement)
            self.boundingRect().width() - RULER_TEXT_MARGIN, # Largeur dispo pour le texte
            self._length_pixels # Hauteur totale pour centrage vertical
        )
        # Aligner à gauche dans son rect disponible, et centré verticalement.
        painter.drawText(text_render_rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextDontClip, self._total_label_mm)

class CellItem(QGraphicsRectItem):
    def __init__(self, row: int, col: int, rect: QRectF, editor_widget: 'DispositionEditorWidget', graphics_parent: QGraphicsItem | None = None):
        # Initialiser sans rectangle pour éviter confusion, nous allons gérer pos et rect manuellement.
        # Appeler avec seulement le parent si on ne spécifie pas le rect ici.
        super().__init__(graphics_parent)
        self.row = row
        self.col = col
        self.editor_widget = editor_widget
        self._is_selected = False
        self._is_part_of_merged_cell = False
        self._is_master_cell = False
        self.content_type: str | None = None
        self.actual_text: str | None = None # Pour stocker le texte réel si content_type est "Texte"
        self.content_placeholder_item: QGraphicsSimpleTextItem | None = None
        
        # Définir la position et le rectangle local
        self.setPos(rect.topLeft())
        self.setRect(QRectF(0, 0, rect.width(), rect.height()))

        self.setAcceptHoverEvents(True)
        self.setBrush(NORMAL_CELL_BRUSH)
        self.setPen(CELL_BORDER_PEN)

    def mousePressEvent(self, event: 'QGraphicsSceneMouseEvent'):
        # Laisser SelectableGraphicsView gérer entièrement la sélection.
        # Appeler super() est une bonne pratique pour la gestion des événements standard de QGraphicsItem.
        super().mousePressEvent(event)
        # Ne PAS faire event.accept() ici si nous voulons que l'événement puisse se propager
        # (bien que dans notre cas, la vue capture l'événement QMouseEvent en premier).

    def set_selected(self, selected: bool):
        if self._is_selected != selected:
            self._is_selected = selected
            self.setBrush(SELECTED_CELL_BRUSH if self._is_selected else NORMAL_CELL_BRUSH)
            self.update()

    def is_selected(self) -> bool:
        return self._is_selected

    def set_merged_state(self, is_master: bool, is_part_of_merged: bool, display_rect: QRectF | None = None):
        self._is_master_cell = is_master
        self._is_part_of_merged_cell = is_part_of_merged

        if is_master:
            # C'est la cellule maître d'une fusion
            if display_rect:
                self.setPos(display_rect.topLeft())
                self.setRect(QRectF(0, 0, display_rect.width(), display_rect.height()))
            self.setPen(CELL_BORDER_PEN) 
            self.setBrush(SELECTED_CELL_BRUSH if self._is_selected else NORMAL_CELL_BRUSH)
            self.setVisible(True)
        elif is_part_of_merged: # et pas maître (implicite)
            # C'est une cellule esclave d'une fusion
            # Son rect et pos originaux sont conservés depuis l'init.
            # Elle devient simplement invisible.
            self.setVisible(False)
        else:
            # C'est une cellule normale, non fusionnée
            if display_rect: # display_rect est son rect original sur la scène
                self.setPos(display_rect.topLeft())
                self.setRect(QRectF(0, 0, display_rect.width(), display_rect.height()))
            self.setPen(CELL_BORDER_PEN)
            self.setBrush(NORMAL_CELL_BRUSH if not self._is_selected else SELECTED_CELL_BRUSH)
            self.setVisible(True)
        self.update()

class SelectableGraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent_editor: 'DispositionEditorWidget'):
        super().__init__(scene, parent_editor)
        self.editor_widget = parent_editor
        
        self.selection_origin: QPoint | None = None
        self.pressed_item_on_mouse_down: CellItem | None = None
        self.is_dragging_selection_rect: bool = False
        
        self.rubber_band_selection = QRubberBand(QRubberBand.Rectangle, self)
        self.rubber_band_selection.hide()

    def mousePressEvent(self, event: 'QMouseEvent'):
        if event.button() == Qt.LeftButton:
            self.selection_origin = event.pos()
            item_at_press = self.itemAt(self.selection_origin)
            self.pressed_item_on_mouse_down = item_at_press if isinstance(item_at_press, CellItem) else None
            self.is_dragging_selection_rect = False # Réinitialiser au début de chaque pression
            # Nous gérons l'événement, donc pas d'appel à super() pour le clic gauche ici
            # pour éviter que QGraphicsView ne fasse son propre traitement de drag (comme le panoramique si activé)
            # qui pourrait interférer. Notre DragMode est NoDrag, mais c'est plus propre.
            event.accept() 
        else:
            # Pour les autres boutons, laisser le comportement par défaut
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: 'QMouseEvent'):
        if not (event.buttons() & Qt.LeftButton) or not self.selection_origin:
            super().mouseMoveEvent(event)
            return

        if not self.is_dragging_selection_rect:
            distance = (event.pos() - self.selection_origin).manhattanLength()
            if distance > QApplication.startDragDistance():
                self.is_dragging_selection_rect = True
                self.editor_widget.clear_selection()
                self.rubber_band_selection.show()
            else:
                # Pas encore un drag, laisser la vue gérer d'autres types de mouvements si nécessaire
                super().mouseMoveEvent(event)
                return
        
        # Si on est ici, self.is_dragging_selection_rect est True.
        # Convertir QRectF en QRect pour setGeometry
        selection_geometry_f = QRectF(self.selection_origin, event.pos()).normalized()
        self.rubber_band_selection.setGeometry(selection_geometry_f.toRect())
        self._update_selection_from_rubber_band()
        event.accept()

    def _update_selection_from_rubber_band(self):
        if not self.rubber_band_selection or self.rubber_band_selection.isHidden():
            return

        rect_in_view_coords = self.rubber_band_selection.geometry()
        selection_rect_scene = self.mapToScene(rect_in_view_coords).boundingRect()
        
        current_selection_candidate = set()
        # Itérer sur toutes les cellules existantes dans l'éditeur
        all_cells_in_editor = [cell for row in self.editor_widget.cell_items for cell in row if cell]

        for cell_item in all_cells_in_editor:
            if cell_item.isVisible() and cell_item.sceneBoundingRect().intersects(selection_rect_scene):
                current_selection_candidate.add(cell_item)

        # Cellules à sélectionner (celles dans le rubber_band qui ne sont pas déjà dans selected_cells)
        cells_to_select_now = current_selection_candidate - self.editor_widget.selected_cells
        for cell in cells_to_select_now:
            if cell not in self.editor_widget.selected_cells:
                cell.set_selected(True)
                self.editor_widget._handle_cell_selection_toggled(cell, True)

        # Cellules à désélectionner (celles dans selected_cells qui ne sont plus dans le rubber_band)
        cells_to_deselect_now = self.editor_widget.selected_cells - current_selection_candidate
        for cell in cells_to_deselect_now:
            if cell in self.editor_widget.selected_cells:
                cell.set_selected(False)
                self.editor_widget._handle_cell_selection_toggled(cell, False)

    def mouseReleaseEvent(self, event: 'QMouseEvent'):
        if event.button() == Qt.LeftButton:
            if self.is_dragging_selection_rect:
                # Drag terminé, la sélection a été mise à jour par mouseMoveEvent
                self.rubber_band_selection.hide()
            else:
                # C'était un clic simple
                self.editor_widget.clear_selection()
                if self.pressed_item_on_mouse_down: # Si un CellItem a été cliqué
                    self.pressed_item_on_mouse_down.set_selected(True)
                    self.editor_widget._handle_cell_selection_toggled(self.pressed_item_on_mouse_down, True)
            
            # Réinitialisation
            self.selection_origin = None
            self.pressed_item_on_mouse_down = None
            self.is_dragging_selection_rect = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class DispositionEditorWidget(QWidget):
    """
    Widget destiné à l'édition visuelle des dispositions (templates) Lamicoid.
    Utilise QGraphicsView pour permettre de définir des zones (texte, image, etc.)
    sur une page dont la taille est basée sur une grille.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DispositionEditorWidget")
        
        self.dpi = DEFAULT_DPI
        self.scene_items_counter = 0 
        self.page_background_item = None
        self.grid_lines = []
        self.cell_items: list[list[CellItem | None]] = []
        self.selected_cells = set()
        self.merged_regions = []

        self.horizontal_ruler_item: HorizontalRulerItem | None = None
        self.vertical_ruler_item: VerticalRulerItem | None = None

        self.num_rows = DEFAULT_ROWS
        self.num_cols = DEFAULT_COLS
        self.column_widths = [DEFAULT_CELL_WIDTH] * self.num_cols
        self.cell_height = DEFAULT_CELL_HEIGHT # Reste scalaire pour l'instant
        self.corner_radius = CORNER_RADIUS

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.scene = QGraphicsScene(self)
        self.view = SelectableGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setBackgroundBrush(QBrush(QColor("#E0E0E0")))
        self.view.setDragMode(QGraphicsView.NoDrag)
        layout.addWidget(self.view)
        logger.debug("DispositionEditorWidget initialisé avec SelectableGraphicsView.")

    def _text_width(self, text: str) -> float:
        if not text: # Gérer le cas où le texte est None ou vide
            return 0.0
        if not hasattr(self, '_font_metrics_for_calc'):
            # Utiliser la même police/taille que pour les placeholders
            font = QFont("Arial", 8)
            self._font_metrics_for_calc = QFontMetrics(font)
        return self._font_metrics_for_calc.boundingRect(text).width()

    def _calculate_required_width_for_column(self, col_idx: int) -> float:
        """Calcule la largeur requise pour une colonne en fonction de son contenu."""
        if not (0 <= col_idx < self.num_cols):
            logger.error(f"_calculate_required_width_for_column appelé avec col_idx invalide: {col_idx}")
            return DEFAULT_CELL_WIDTH

        max_w = DEFAULT_CELL_WIDTH

        # 1. Vérifier les cellules simples dans cette colonne
        for r in range(self.num_rows):
            if r < len(self.cell_items) and col_idx < len(self.cell_items[r]):
                cell = self.cell_items[r][col_idx]
                if cell and cell.content_type == "Texte" and cell.actual_text:
                    # Est-ce une cellule simple (non maître d'une fusion qui commence ici, et non esclave) ?
                    is_master_here, is_slave, _, _ = self._get_cell_merged_state(r, col_idx, QRectF()) # Le rect est factice
                    if not is_master_here and not is_slave:
                        required_cell_width = self._text_width(cell.actual_text) + 8 # Marge de 8px
                        max_w = max(max_w, required_cell_width)
            else:
                logger.warning(f"Accès hors limites à cell_items dans _calculate_required_width_for_column pour ({r},{col_idx})")


        # 2. Vérifier les fusions qui se terminent sur cette colonne
        for region in self.merged_regions:
            region_col_start = region['col']
            region_colspan = region['colspan']
            region_col_end = region_col_start + region_colspan - 1

            if region_col_end == col_idx: # Cette fusion se termine sur la colonne actuelle
                master_cell_row, master_cell_col = region['row'], region['col']
                if master_cell_row < len(self.cell_items) and \
                   master_cell_col < len(self.cell_items[master_cell_row]):
                    master_cell = self.cell_items[master_cell_row][master_cell_col]
                    if master_cell and master_cell.content_type == "Texte" and master_cell.actual_text:
                        fusion_text_total_width = self._text_width(master_cell.actual_text) + 8 # Marge
                        
                        width_of_fusion_cols_before_this_one = 0
                        if region_colspan > 1: # Si la fusion couvre plus d'une colonne
                            for c_fus_idx in range(region_col_start, col_idx): # Colonnes de la fusion AVANT la col_idx actuelle
                                if 0 <= c_fus_idx < len(self.column_widths):
                                    width_of_fusion_cols_before_this_one += self.column_widths[c_fus_idx]
                                else:
                                    logger.error(f"Index de colonne {c_fus_idx} hors limites pour column_widths lors du calcul de la largeur de fusion.")
                                    # Difficile de récupérer ici, la largeur de fusion sera fausse
                                    
                        # La largeur que cette dernière colonne doit avoir pour satisfaire le texte de la fusion
                        required_for_this_col_due_to_fusion = fusion_text_total_width - width_of_fusion_cols_before_this_one
                        required_for_this_col_due_to_fusion = max(DEFAULT_CELL_WIDTH, required_for_this_col_due_to_fusion)
                        max_w = max(max_w, required_for_this_col_due_to_fusion)
                else:
                    logger.warning(f"Accès hors limites à cell_items pour la cellule maître ({master_cell_row},{master_cell_col}) d'une fusion.")
        return max_w

    def _update_page_layout(self, preserved_content_details: dict[tuple[int, int], PreservedContentDetails] | None = None):
        """ Met à jour la taille et l'apparence du fond de page et de la scène. """
        if preserved_content_details is None:
            preserved_content_details = {}
            
        page_width = sum(self.column_widths) # Modifié
        page_height = self.num_rows * self.cell_height # Inchangé pour l'instant

        scene_width = page_width + 2 * PAGE_MARGIN
        scene_height = page_height + 2 * PAGE_MARGIN
        self.scene.setSceneRect(0, 0, scene_width, scene_height)

        background_rect_dims = QRectF(PAGE_MARGIN, PAGE_MARGIN, page_width, page_height)
        
        path = QPainterPath()
        path.addRoundedRect(background_rect_dims, self.corner_radius, self.corner_radius)

        if self.page_background_item is None:
            self.page_background_item = QGraphicsPathItem(path)
            self.page_background_item.setBrush(QBrush(Qt.white))
            self.page_background_item.setPen(QPen(QColor("#B0B0B0"), 1))
            self.page_background_item.setZValue(-1) 
            self.page_background_item.setData(PAGE_BACKGROUND_ITEM_KEY, True)
            self.scene.addItem(self.page_background_item)
        else:
            self.page_background_item.setPath(path)
        
        # Gestion des règles
        page_width_px = sum(self.column_widths)
        page_height_px = self.num_rows * self.cell_height

        # Règle Horizontale
        if self.horizontal_ruler_item is None:
            self.horizontal_ruler_item = HorizontalRulerItem()
            self.scene.addItem(self.horizontal_ruler_item)
        
        total_width_mm_str = f"{pixels_to_mm(page_width_px, self.dpi):.0f} mm"
        self.horizontal_ruler_item.set_config(page_width_px, [], total_width_mm_str) # Passer une liste vide pour les divisions
        # Positionner la ligne de base (y=0 local) de la règle horizontale
        # pour qu'il y ait RULER_TEXT_MARGIN entre le haut du Lamicoid et la ligne de la règle.
        self.horizontal_ruler_item.setPos(PAGE_MARGIN, PAGE_MARGIN - RULER_TEXT_MARGIN)

        # Règle Verticale
        if self.vertical_ruler_item is None:
            self.vertical_ruler_item = VerticalRulerItem()
            self.scene.addItem(self.vertical_ruler_item)
        
        total_height_mm_str = f"{pixels_to_mm(page_height_px, self.dpi):.0f} mm"
        self.vertical_ruler_item.set_config(page_height_px, [], total_height_mm_str) # Passer une liste vide pour les divisions
        self.vertical_ruler_item.setPos(PAGE_MARGIN + page_width_px + RULER_TEXT_MARGIN, PAGE_MARGIN)

        for line_item in self.grid_lines:
            self.scene.removeItem(line_item)
        self.grid_lines.clear()

        if hasattr(self, 'cell_items'):
            for r_idx in range(len(self.cell_items)):
                for c_idx in range(len(self.cell_items[r_idx])):
                    if self.cell_items[r_idx][c_idx]:
                        old_cell = self.cell_items[r_idx][c_idx]
                        if old_cell in self.selected_cells:
                            self.selected_cells.remove(old_cell)
                        self.scene.removeItem(old_cell) 
        
        self.cell_items = [[None for _ in range(self.num_cols)] for _ in range(self.num_rows)]

        grid_pen = QPen(QColor("#D0D0D0"), 0.5, Qt.SolidLine)
        current_x = PAGE_MARGIN
        for i in range(self.num_cols):
            if i > 0: # Pas de ligne verticale avant la première colonne
                line = QGraphicsLineItem(QLineF(current_x, PAGE_MARGIN, current_x, PAGE_MARGIN + page_height))
                line.setPen(grid_pen)
                line.setZValue(-0.5)
                self.scene.addItem(line)
                self.grid_lines.append(line)
            # current_x est déjà prêt pour la prochaine cellule/ligne verticale
            if i < self.num_cols: # S'assurer de ne pas dépasser l'index pour column_widths
                 current_x += self.column_widths[i]

        for i in range(1, self.num_rows):
            y = PAGE_MARGIN + i * self.cell_height
            line = QGraphicsLineItem(QLineF(PAGE_MARGIN, y, PAGE_MARGIN + page_width, y))
            line.setPen(grid_pen)
            line.setZValue(-0.5)
            self.scene.addItem(line)
            self.grid_lines.append(line)
            
        current_x_offset = PAGE_MARGIN
        logger.debug(f"Dans _update_page_layout, preserved_content_details keys: {list(preserved_content_details.keys()) if preserved_content_details else 'None'}")
        for c in range(self.num_cols):
            current_y_offset = PAGE_MARGIN
            current_col_width = self.column_widths[c]
            for r in range(self.num_rows):
                cell_rect = QRectF(current_x_offset, current_y_offset, current_col_width, self.cell_height)
                cell_item = CellItem(r, c, cell_rect, editor_widget=self, graphics_parent=None)
                
                is_master, is_slave, merged_cell_rect, original_cell_rect_for_slave = self._get_cell_merged_state(r, c, cell_rect)
                
                cell_item.set_selected(False)
                if is_master or is_slave:
                    cell_item.set_merged_state(is_master, True, merged_cell_rect if is_master else original_cell_rect_for_slave)
                else:
                    cell_item.set_merged_state(False, False, cell_rect)
                
                cell_item.setZValue(-0.2)
                self.scene.addItem(cell_item)
                self.cell_items[r][c] = cell_item
                
                # Log de débogage pour la restauration du contenu
                if preserved_content_details:
                    is_in_preserved = (r, c) in preserved_content_details
                    logger.debug(f"  _update_page_layout: Cell ({r},{c}), in preserved: {is_in_preserved}, is_master: {is_master}, is_slave: {is_slave}")
                    if is_in_preserved:
                        content_type_str, actual_text_str = preserved_content_details[(r, c)]
                        if is_master or (not is_master and not is_slave):
                             self._recreate_placeholder_for_cell(cell_item, content_type_str, actual_text_str)
                current_y_offset += self.cell_height
            current_x_offset += current_col_width

        self._draw_grid_lines(page_width, page_height)
        logger.debug(f"Page layout updated: {self.num_rows}x{self.num_cols} cells. Page width: {page_width}. Cells created: {self.num_rows*self.num_cols}")

    def _recreate_placeholder_for_cell(self, cell_item: CellItem, content_type: str, actual_text: str | None):
        """ Recrée un placeholder pour une cellule donnée. """
        if cell_item.content_placeholder_item and cell_item.content_placeholder_item.scene():
            self.scene.removeItem(cell_item.content_placeholder_item)
        
        cell_item.content_type = content_type
        cell_item.actual_text = actual_text

        display_text = actual_text if content_type == "Texte" and actual_text is not None else content_type.capitalize()
        if content_type == "Texte" and actual_text == "":
            display_text = "[Texte vide]"
            
        font = QFont("Arial", 8)
        # fm = QFontMetrics(font) # Plus besoin pour elidedText ici
        # cell_width = cell_item.boundingRect().width()
        
        # # Laisser une petite marge pour que le texte ne touche pas les bords
        # available_width = int(cell_width - 4) # par exemple, 2 pixels de marge de chaque côté
        
        # elided_text = fm.elidedText(display_text, Qt.ElideRight, available_width) # Supprimé
            
        new_placeholder = QGraphicsSimpleTextItem(display_text, parent=cell_item) # Utilise display_text directement
        new_placeholder.setFont(font)
        new_placeholder.setBrush(QBrush(Qt.black))
        
        cell_local_rect = cell_item.boundingRect()
        placeholder_bound_rect = new_placeholder.boundingRect()
        
        # Logs détaillés pour le débogage
        logger.debug(f"Cell ({cell_item.row},{cell_item.col}) - In _recreate_placeholder_for_cell:")
        logger.debug(f"  Text to display (len: {len(display_text if display_text else '')}): '{display_text[:100]}{'...' if display_text and len(display_text) > 100 else ''}'")
        logger.debug(f"  CellItem local_rect width: {cell_local_rect.width()}, height: {cell_local_rect.height()}")
        logger.debug(f"  Placeholder bounding_rect width: {placeholder_bound_rect.width()}, height: {placeholder_bound_rect.height()}")
        
        # Rétablir le centrage horizontal correct
        offset_x = (cell_local_rect.width() - placeholder_bound_rect.width()) / 2
        offset_y = (cell_local_rect.height() - placeholder_bound_rect.height()) / 2
        
        # Assurer que les offsets ne positionnent pas le texte en dehors si le texte est plus grand que la cellule
        # (bien que la logique de redimensionnement de colonne devrait empêcher cela pour la largeur)
        if offset_x < 0:
            offset_x = 0 # Aligner à gauche si le texte est plus large que la cellule
        if offset_y < 0:
            offset_y = 0 # Aligner en haut si le texte est plus haut que la cellule
            
        logger.debug(f"  Calculated offset_x (centered): {offset_x}, offset_y (centered): {offset_y}")
        
        new_placeholder.setPos(offset_x, offset_y)
        cell_item.content_placeholder_item = new_placeholder
        logger.debug(f"Placeholder '{display_text[:50]}{'...' if display_text and len(display_text) > 50 else ''}' recréé pour la cellule ({cell_item.row},{cell_item.col}). Positionné à ({offset_x},{offset_y})")

    def _get_cell_merged_state(self, row: int, col: int, original_cell_rect_at_current_pos: QRectF) -> tuple[bool, bool, QRectF | None, QRectF]:
        for region in self.merged_regions:
            r_start, c_start = region['row'], region['col']
            row_span, col_span = region['rowspan'], region['colspan']
            r_end, c_end = r_start + row_span - 1, c_start + col_span - 1

            if r_start <= row <= r_end and c_start <= col <= c_end:
                is_master = (row == r_start and col == c_start)
                
                # Calculer la largeur et la position x de la région fusionnée en sommant les largeurs de colonnes individuelles
                merged_region_x = PAGE_MARGIN + sum(self.column_widths[i] for i in range(c_start))
                merged_region_width = sum(self.column_widths[i] for i in range(c_start, c_start + col_span))
                
                master_rect = QRectF(
                    merged_region_x,
                    PAGE_MARGIN + r_start * self.cell_height,
                    merged_region_width,
                    row_span * self.cell_height 
                )
                # Pour une cellule esclave, son "original_rect" est celui passé en argument, 
                # qui est déjà calculé avec la bonne largeur de colonne et position x.
                return is_master, True, master_rect, original_cell_rect_at_current_pos
        return False, False, None, original_cell_rect_at_current_pos

    def _draw_grid_lines(self, page_width: float, page_height: float):
        for line_item in self.grid_lines:
            self.scene.removeItem(line_item)
        self.grid_lines.clear()
        grid_pen = QPen(QColor("#D0D0D0"), 0.5, Qt.SolidLine)

        current_x = PAGE_MARGIN
        for c_idx in range(self.num_cols):
            # Dessiner la ligne verticale *après* cette colonne, sauf pour la dernière
            if c_idx < self.num_cols -1: 
                current_x += self.column_widths[c_idx]
                should_draw_vertical_line = True
                # Vérifier si cette ligne verticale est à l'intérieur d'une fusion pour toutes les rangées
                for r_idx in range(self.num_rows):
                    if self._are_cells_in_same_merge(r_idx, c_idx, r_idx, c_idx + 1):
                        should_draw_vertical_line = False
                        break
                if should_draw_vertical_line:
                    line = QGraphicsLineItem(QLineF(current_x, PAGE_MARGIN, current_x, PAGE_MARGIN + page_height))
                    line.setPen(grid_pen)
                    line.setZValue(-0.5)
                    self.scene.addItem(line)
                    self.grid_lines.append(line)
            elif c_idx == self.num_cols -1: # S'assurer que current_x est bien à la fin de la dernière colonne
                 current_x += self.column_widths[c_idx]

        for r_idx in range(1, self.num_rows):
            y = PAGE_MARGIN + r_idx * self.cell_height
            should_draw_horizontal_line = True
            # Vérifier si cette ligne horizontale est à l'intérieur d'une fusion pour toutes les colonnes
            for c_idx in range(self.num_cols):
                 if self._are_cells_in_same_merge(r_idx -1, c_idx, r_idx, c_idx):
                    should_draw_horizontal_line = False
                    break
            if should_draw_horizontal_line:
                line = QGraphicsLineItem(QLineF(PAGE_MARGIN, y, PAGE_MARGIN + page_width, y)) # page_width est sum(column_widths)
                line.setPen(grid_pen)
                line.setZValue(-0.5)
                self.scene.addItem(line)
                self.grid_lines.append(line)

    def _are_cells_in_same_merge(self, r1, c1, r2, c2) -> bool:
        cell1_region = None
        for region in self.merged_regions:
            if region['row'] <= r1 < region['row'] + region['rowspan'] and \
               region['col'] <= c1 < region['col'] + region['colspan']:
                cell1_region = region
                break
        cell2_region = None
        for region in self.merged_regions:
            if region['row'] <= r2 < region['row'] + region['rowspan'] and \
               region['col'] <= c2 < region['col'] + region['colspan']:
                cell2_region = region
                break
        return cell1_region is not None and cell1_region == cell2_region

    def load_disposition(self, disposition_data=None):
        """
        Charge les données d'une disposition existante ou prépare un canevas vide.
        """
        self.scene.clear() # Vider la scène, y compris page_background_item et les anciennes grid_lines
        self.page_background_item = None 
        self.grid_lines.clear() # Assurer que notre liste est vide aussi
        self.selected_cells.clear()
        self.merged_regions.clear()
        self.scene_items_counter = 0
        
        content_to_load: dict[tuple[int,int], PreservedContentDetails] = {}

        if disposition_data:
            logger.info(f"Chargement des données de la disposition: {disposition_data.get('name', 'N/A')}")
            self.num_rows = disposition_data.get('num_rows', DEFAULT_ROWS)
            self.num_cols = disposition_data.get('num_cols', DEFAULT_COLS)
            # Charger les largeurs de colonnes si elles existent, sinon initialiser par défaut
            loaded_column_widths = disposition_data.get('column_widths')
            if loaded_column_widths and len(loaded_column_widths) == self.num_cols:
                self.column_widths = loaded_column_widths
            else:
                self.column_widths = [DEFAULT_CELL_WIDTH] * self.num_cols
            
            self.cell_height = disposition_data.get('cell_height', DEFAULT_CELL_HEIGHT) # Reste scalaire
            self.corner_radius = disposition_data.get('corner_radius', CORNER_RADIUS)
            self.merged_regions = disposition_data.get('merged_cells', [])
            cell_contents_data = disposition_data.get('cell_contents', {})
            for coord_str, content_details_list in cell_contents_data.items():
                try:
                    r_str, c_str = coord_str.strip("()").split(",")
                    r, c = int(r_str), int(c_str)
                    if isinstance(content_details_list, (list, tuple)) and len(content_details_list) == 2:
                         content_to_load[(r,c)] = (str(content_details_list[0]), content_details_list[1])
                    else:
                        logger.warning(f"Format de contenu de cellule incorrect pour {coord_str}: {content_details_list}")
                except ValueError as e:
                    logger.error(f"Erreur de parsing des coordonnées de cellule_contents '{coord_str}': {e}")
        else:
            self.num_rows = DEFAULT_ROWS
            self.num_cols = DEFAULT_COLS
            self.column_widths = [DEFAULT_CELL_WIDTH] * self.num_cols
            self.cell_height = DEFAULT_CELL_HEIGHT
            self.corner_radius = CORNER_RADIUS
            
        self._update_page_layout(preserved_content_details=content_to_load)

    def _handle_cell_selection_toggled(self, cell_item: CellItem, is_selected: bool):
        """ Gère la logique de sélection/désélection d'une cellule, notifiée par CellItem. """
        if is_selected:
            self.selected_cells.add(cell_item)
            logger.debug(f"Cell ({cell_item.row}, {cell_item.col}) ajoutée à la sélection de l'éditeur.")
        else:
            if cell_item in self.selected_cells:
                self.selected_cells.remove(cell_item)
            logger.debug(f"Cell ({cell_item.row}, {cell_item.col}) retirée de la sélection de l'éditeur.")

    def get_selected_cells_coords(self) -> list[tuple[int, int]]:
        """ Retourne les coordonnées (row, col) des cellules sélectionnées. """
        return sorted([(cell.row, cell.col) for cell in self.selected_cells])
    
    def clear_selection(self):
        """ Désélectionne toutes les cellules. """
        current_selection_copy = list(self.selected_cells)
        for cell_item_to_deselect in current_selection_copy:
            cell_item_to_deselect.set_selected(False)
            if cell_item_to_deselect in self.selected_cells:
                 self.selected_cells.remove(cell_item_to_deselect)
        logger.debug("Selection cleared in editor.")

    def merge_selected_cells(self):
        if not self.selected_cells:
            QMessageBox.information(self, "Fusion", "Aucune cellule sélectionnée.")
            return

        preserved_content = self._collect_current_content_details()
        new_content_map: dict[tuple[int,int], PreservedContentDetails] = {}
        unit_coords_for_new_merge = set()
        selected_existing_merge_regions_to_absorb = []

        for cell_item in self.selected_cells:
            is_master_of_existing_region = False
            if cell_item._is_master_cell and cell_item._is_part_of_merged_cell:
                for existing_region in self.merged_regions:
                    if existing_region['row'] == cell_item.row and \
                       existing_region['col'] == cell_item.col:
                        for r_offset in range(existing_region['rowspan']):
                            for c_offset in range(existing_region['colspan']):
                                unit_coords_for_new_merge.add(
                                    (existing_region['row'] + r_offset, existing_region['col'] + c_offset)
                                )
                        if existing_region not in selected_existing_merge_regions_to_absorb:
                            selected_existing_merge_regions_to_absorb.append(existing_region)
                        is_master_of_existing_region = True
                        break 
            
            if not is_master_of_existing_region and not cell_item._is_part_of_merged_cell:
                 unit_coords_for_new_merge.add((cell_item.row, cell_item.col))
            elif not is_master_of_existing_region and cell_item._is_part_of_merged_cell and not cell_item._is_master_cell:
                logger.warning(f"Cellule esclave ({cell_item.row},{cell_item.col}) trouvée dans la sélection. Elle sera ignorée.")

        if not unit_coords_for_new_merge:
            QMessageBox.information(self, "Fusion", "Aucune cellule valide (unitaire ou maître de fusion) trouvée dans la sélection.")
            self.clear_selection()
            return

        min_row = min(r for r, c in unit_coords_for_new_merge)
        max_row = max(r for r, c in unit_coords_for_new_merge)
        min_col = min(c for r, c in unit_coords_for_new_merge)
        max_col = max(c for r, c in unit_coords_for_new_merge)

        new_rowspan = max_row - min_row + 1
        new_colspan = max_col - min_col + 1

        expected_cells_in_rectangle = set()
        for r_idx in range(min_row, max_row + 1):
            for c_idx in range(min_col, max_col + 1):
                expected_cells_in_rectangle.add((r_idx, c_idx))
        
        if unit_coords_for_new_merge != expected_cells_in_rectangle:
            QMessageBox.warning(self, "Fusion", "La sélection pour la fusion doit former un rectangle plein de cellules unitaires de base.")
            self.clear_selection()
            return

        final_merged_regions = [
            region for region in self.merged_regions 
            if region not in selected_existing_merge_regions_to_absorb
        ]
        
        for existing_region in final_merged_regions:
            r, c, rs, cs = existing_region['row'], existing_region['col'], existing_region['rowspan'], existing_region['colspan']
            overlap = not (min_col + new_colspan <= c or \
                           min_col >= c + cs or \
                           min_row + new_rowspan <= r or \
                           min_row >= r + rs)
            if overlap:
                QMessageBox.warning(self, "Fusion", "La fusion proposée chevaucherait une autre fusion existante non sélectionnée. Veuillez ajuster votre sélection.")
                self.clear_selection()
                return

        final_merged_regions.append({
            'row': min_row, 'col': min_col, 'rowspan': new_rowspan, 'colspan': new_colspan
        })
        self.merged_regions = final_merged_regions
        logger.info(f"Fusion effectuée : {new_rowspan}x{new_colspan} cellules à partir de ({min_row},{min_col}). {len(selected_existing_merge_regions_to_absorb)} régions existantes absorbées.")
        
        content_of_master_cell_details = preserved_content.get((min_row, min_col))
        for (r_orig, c_orig), content_details in preserved_content.items():
            is_inside_newly_merged_region = False
            if min_row <= r_orig <= max_row and min_col <= c_orig <= max_col:
                is_inside_newly_merged_region = True
            part_of_absorbed_region = False
            for absorbed_region in selected_existing_merge_regions_to_absorb:
                if absorbed_region['row'] <= r_orig < absorbed_region['row'] + absorbed_region['rowspan'] and \
                   absorbed_region['col'] <= c_orig < absorbed_region['col'] + absorbed_region['colspan']:
                    part_of_absorbed_region = True
                    break
            if not is_inside_newly_merged_region and not part_of_absorbed_region:
                new_content_map[(r_orig, c_orig)] = content_details
        if content_of_master_cell_details:
            new_content_map[(min_row, min_col)] = content_of_master_cell_details
        self._update_page_layout(preserved_content_details=new_content_map)
        self.clear_selection()

    def split_selected_cells(self):
        selected_master_cells_to_split = []
        for cell_item in self.selected_cells:
            if cell_item._is_master_cell and cell_item._is_part_of_merged_cell:
                selected_master_cells_to_split.append(cell_item)

        if not selected_master_cells_to_split:
            QMessageBox.information(self, "Défusion", "Aucune cellule fusionnée (cellule maître) n'est sélectionnée pour la défusion.")
            return

        preserved_content = self._collect_current_content_details()
        new_content_map: dict[tuple[int,int], PreservedContentDetails] = {}
        content_from_split_masters: dict[tuple[int,int], PreservedContentDetails] = {}

        regions_to_remove = []
        for master_cell in selected_master_cells_to_split:
            if (master_cell.row, master_cell.col) in preserved_content:
                content_from_split_masters[(master_cell.row, master_cell.col)] = preserved_content[(master_cell.row, master_cell.col)]
            for region in self.merged_regions:
                if region['row'] == master_cell.row and region['col'] == master_cell.col:
                    regions_to_remove.append(region)
                    break 
        
        if not regions_to_remove:
            logger.warning("Tentative de défusionner des cellules maîtres sélectionnées mais aucune région correspondante trouvée.")
            QMessageBox.warning(self, "Défusion", "Incohérence détectée. Impossible de trouver les régions à défusionner.")
            return

        current_merged_regions_after_split = [r for r in self.merged_regions if r not in regions_to_remove]
        self.merged_regions = current_merged_regions_after_split

        for (r_orig, c_orig), content_details in preserved_content.items():
            is_part_of_a_just_split_region = False
            for removed_region in regions_to_remove:
                if removed_region['row'] <= r_orig < removed_region['row'] + removed_region['rowspan'] and \
                   removed_region['col'] <= c_orig < removed_region['col'] + removed_region['colspan']:
                    is_part_of_a_just_split_region = True
                    break
            if not is_part_of_a_just_split_region:
                new_content_map[(r_orig, c_orig)] = content_details
        for (r_master, c_master), master_content_details in content_from_split_masters.items():
            new_content_map[(r_master, c_master)] = master_content_details
        logger.info(f"{len(regions_to_remove)} région(s) fusionnée(s) défusionnée(s).")
        self._update_page_layout(preserved_content_details=new_content_map)
        self.clear_selection()

    def _collect_current_content_details(self) -> dict[tuple[int, int], PreservedContentDetails]:
        """ Collecte les types de contenu actuels de toutes les cellules. """
        content_map: dict[tuple[int,int], PreservedContentDetails] = {}
        if hasattr(self, 'cell_items') and self.cell_items:
            for r_idx in range(len(self.cell_items)):
                for c_idx in range(len(self.cell_items[r_idx])):
                    cell = self.cell_items[r_idx][c_idx]
                    if cell and cell.content_type:
                        content_map[(cell.row, cell.col)] = (cell.content_type, cell.actual_text)
        return content_map

    def _add_column_at_end(self):
        preserved_content = self._collect_current_content_details()
        self.num_cols += 1
        self.column_widths.append(DEFAULT_CELL_WIDTH) # Ajouter une largeur par défaut pour la nouvelle colonne
        logger.debug(f"Colonne ajoutée à la fin. Total colonnes: {self.num_cols}, Largeurs: {self.column_widths}")
        self._update_page_layout(preserved_content_details=preserved_content)

    def _insert_column_before_index(self, target_index: int):
        preserved_content = self._collect_current_content_details()
        new_content_map: dict[tuple[int,int], PreservedContentDetails] = {}

        if not (0 <= target_index <= self.num_cols):
            logger.error(f"Indice d'insertion de colonne invalide: {target_index}. Max: {self.num_cols}")
            # Fallback: ajouter à la fin si l'index est mauvais, pour éviter une erreur plus grave.
            # Cependant, _add_column_at_end gère son propre preserved_content. 
            # Pour simplifier, on pourrait juste retourner ici ou logguer l'erreur.
            # La logique de décalage des fusions et du contenu ci-dessous pourrait mal se comporter.
            # Pour l'instant, on laisse la logique de décalage s'exécuter, elle devrait être inoffensive si target_index est hors limites.
            pass 

        self.num_cols += 1
        # Insérer une largeur par défaut pour la nouvelle colonne à l'index cible
        if 0 <= target_index < len(self.column_widths):
            self.column_widths.insert(target_index, DEFAULT_CELL_WIDTH)
        else: # Si target_index == self.num_cols (ancienne valeur), c'est un ajout à la fin
            self.column_widths.append(DEFAULT_CELL_WIDTH)

        new_merged_regions = []
        for region in self.merged_regions:
            r, c, rs, cs = region['row'], region['col'], region['rowspan'], region['colspan']
            if c >= target_index:
                region['col'] = c + 1
            elif c < target_index < c + cs:
                region['colspan'] = cs + 1
            new_merged_regions.append(region)
        self.merged_regions = new_merged_regions

        for (r_orig, c_orig), content_details in preserved_content.items():
            if c_orig >= target_index:
                new_content_map[(r_orig, c_orig + 1)] = content_details
            else:
                new_content_map[(r_orig, c_orig)] = content_details

        logger.debug(f"Colonne insérée avant l'index {target_index}. Total colonnes: {self.num_cols}. Largeurs: {self.column_widths}")
        self._update_page_layout(preserved_content_details=new_content_map)

    def add_column(self):
        if not self.selected_cells:
            self._add_column_at_end()
        else:
            selected_coords = self.get_selected_cells_coords()
            if not selected_coords:
                self._add_column_at_end()
                return
            max_selected_col = -1
            for r,c in selected_coords:
                if c > max_selected_col:
                    max_selected_col = c
            insertion_target_index = max_selected_col + 1
            self._insert_column_before_index(insertion_target_index)
        self.clear_selection()

    def _add_row_at_end(self):
        preserved_content = self._collect_current_content_details()
        self.num_rows += 1
        logger.debug(f"Rangée ajoutée à la fin. Total rangées: {self.num_rows}")
        self._update_page_layout(preserved_content_details=preserved_content)

    def _insert_row_before_index(self, target_index: int):
        preserved_content = self._collect_current_content_details()
        new_content_map: dict[tuple[int,int], PreservedContentDetails] = {}

        if not (0 <= target_index <= self.num_rows):
            logger.error(f"Indice d'insertion de rangée invalide: {target_index}. Max: {self.num_rows}")
            pass

        self.num_rows += 1
        new_merged_regions = []
        for region in self.merged_regions:
            r, c, rs, cs = region['row'], region['col'], region['rowspan'], region['colspan']
            if r >= target_index:
                region['row'] = r + 1
            elif r < target_index < r + rs:
                region['rowspan'] = rs + 1
            new_merged_regions.append(region)
        self.merged_regions = new_merged_regions

        for (r_orig, c_orig), content_details in preserved_content.items():
            if r_orig >= target_index:
                new_content_map[(r_orig + 1, c_orig)] = content_details
            else:
                new_content_map[(r_orig, c_orig)] = content_details

        logger.debug(f"Rangée insérée avant l'index {target_index}. Total rangées: {self.num_rows}")
        self._update_page_layout(preserved_content_details=new_content_map)

    def add_row(self):
        if not self.selected_cells:
            self._add_row_at_end()
        else:
            selected_coords = self.get_selected_cells_coords()
            if not selected_coords:
                self._add_row_at_end()
                return
            max_selected_row = -1
            for r,c in selected_coords:
                 if r > max_selected_row:
                    max_selected_row = r
            insertion_target_index = max_selected_row + 1
            self._insert_row_before_index(insertion_target_index)
        self.clear_selection()

    def add_new_zone(self):
        """ Ajoute un nouveau rectangle (zone) à la scène. """
        # Positionnement relatif au coin haut-gauche de la page (background_item)
        # et non de la scène.
        page_origin_x = PAGE_MARGIN 
        page_origin_y = PAGE_MARGIN
        
        # Positionnement simple pour éviter la superposition exacte au début
        # Les coordonnées sont relatives au coin de la page blanche
        offset_x = (self.scene_items_counter % self.num_cols) * (self.column_widths[self.scene_items_counter % self.num_cols] / 2)
        offset_y = (self.scene_items_counter // self.num_cols) * (self.cell_height / 2)
        
        zone_width = self.column_widths[self.scene_items_counter % self.num_cols] * 0.8
        zone_height = self.cell_height * 0.8
        
        # Vérifier que la nouvelle zone ne dépasse pas les limites de la page
        max_x_on_page = (sum(self.column_widths) - zone_width)
        max_y_on_page = (self.num_rows * self.cell_height) - zone_height
        
        final_x_on_page = min(offset_x, max_x_on_page)
        final_y_on_page = min(offset_y, max_y_on_page)
        
        # Coordonnées pour QGraphicsRectItem sont relatives à la scène
        scene_x = page_origin_x + final_x_on_page
        scene_y = page_origin_y + final_y_on_page
        
        zone_rect = QGraphicsRectItem(QRectF(scene_x, scene_y, zone_width, zone_height))
        
        zone_rect.setBrush(QBrush(Qt.cyan))
        zone_rect.setPen(QPen(Qt.darkCyan, 2))
        zone_rect.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsFocusable)
        
        self.scene.addItem(zone_rect)
        self.scene_items_counter += 1
        logger.debug(f"Nouvelle zone (rectangle) ajoutée. Coords scène: ({scene_x},{scene_y}). Total zones: {self.scene_items_counter}")

    def get_disposition_data(self):
        """ Récupère les données de la disposition éditée. """
        logger.info("Récupération des données de la disposition.")
        
        # Ancienne logique pour les "zones" (rectangles génériques), peut être conservée ou supprimée
        # si le contenu est uniquement géré par les cellules maintenant.
        # Pour l'instant, on la laisse mais elle n'est pas prioritaire.
        zones_data = []
        # for item in self.scene.items():
        #     if item.data(PAGE_BACKGROUND_ITEM_KEY): 
        #         continue
        #     if isinstance(item, QGraphicsRectItem) and not isinstance(item, CellItem):
        #         rect = item.rect()
        #         page_relative_x = rect.x() - PAGE_MARGIN
        #         page_relative_y = rect.y() - PAGE_MARGIN
        #         zones_data.append({
        #             "id": str(item), 
        #             "type": "rectangle",
        #             "x": page_relative_x,
        #             "y": page_relative_y,
        #             "width": rect.width(), 
        #             "height": rect.height()
        #         })

        cell_contents_to_save = {}
        if hasattr(self, 'cell_items') and self.cell_items:
            for r_idx in range(len(self.cell_items)):
                for c_idx in range(len(self.cell_items[r_idx])):
                    cell = self.cell_items[r_idx][c_idx]
                    if cell and cell.content_type:
                        # Utiliser une clé string "(r,c)" pour la sérialisation JSON
                        coord_key = f"({cell.row},{cell.col})"
                        cell_contents_to_save[coord_key] = [cell.content_type, cell.actual_text]
        
        return {
            "name": "nom_a_definir_via_LamicoidPage",
            "num_rows": self.num_rows,
            "num_cols": self.num_cols,
            "column_widths": list(self.column_widths), # Sauvegarder les largeurs de colonnes
            "cell_height": self.cell_height, # Reste scalaire
            "corner_radius": self.corner_radius,
            "merged_cells": list(self.merged_regions),
            "cell_contents": cell_contents_to_save,
            "zones": zones_data
        }

    def delete_rows(self, row_indices_to_delete: list[int]):
        if not row_indices_to_delete:
            return
        
        preserved_content = self._collect_current_content_details()
        new_content_map: dict[tuple[int,int], PreservedContentDetails] = {}

        unique_sorted_rows = sorted(list(set(row_indices_to_delete)), reverse=True)

        if self.num_rows == 1 and len(unique_sorted_rows) >= 1:
            QMessageBox.information(self, "Suppression Rangées", "Impossible de supprimer la dernière rangée.")
            return
        
        if len(unique_sorted_rows) >= self.num_rows:
            logger.warning(f"Tentative de supprimer toutes les {self.num_rows} rangées. Limitation à {self.num_rows -1} suppressions.")
            unique_sorted_rows = unique_sorted_rows[:self.num_rows - 1]
            if not unique_sorted_rows:
                QMessageBox.information(self, "Suppression Rangées", "Impossible de supprimer la dernière rangée.")
                return

        if not all(0 <= r_idx < self.num_rows for r_idx in unique_sorted_rows):
            logger.error(f"Tentative de suppression de rangées avec des indices invalides: {unique_sorted_rows}. Max: {self.num_rows-1}")
            QMessageBox.warning(self, "Erreur", "Indices de rangées invalides pour la suppression.")
            return

        logger.info(f"Suppression des rangées aux indices: {unique_sorted_rows}")

        new_merged_regions = []
        for region in self.merged_regions:
            r, c, rs, cs = region['row'], region['col'], region['rowspan'], region['colspan']
            region_end_row = r + rs -1
            
            affected_by_deletion = False
            num_deleted_rows_within_region = 0
            for del_r_idx in unique_sorted_rows:
                if r <= del_r_idx <= region_end_row:
                    num_deleted_rows_within_region += 1
                    affected_by_deletion = True
            
            if affected_by_deletion:
                if num_deleted_rows_within_region >= rs:
                    continue 
                else:
                    region['rowspan'] = rs - num_deleted_rows_within_region
                    num_deleted_rows_above_or_at_region_start = sum(1 for del_idx in unique_sorted_rows if del_idx < r + num_deleted_rows_within_region and del_idx >= r)
                    region['row'] = r - num_deleted_rows_above_or_at_region_start
                    new_merged_regions.append(region)
            else:
                shift_down_count = sum(1 for del_idx in unique_sorted_rows if del_idx < r)
                region['row'] = r - shift_down_count
                new_merged_regions.append(region)
        self.merged_regions = new_merged_regions
        
        for (r_orig, c_orig), content_details in preserved_content.items():
            if r_orig in unique_sorted_rows: # La rangée de cette cellule est supprimée
                continue # Ne pas ajouter ce contenu
            
            num_deleted_rows_above = sum(1 for del_idx in unique_sorted_rows if del_idx < r_orig)
            new_r = r_orig - num_deleted_rows_above
            new_content_map[(new_r, c_orig)] = content_details

        self.num_rows -= len(unique_sorted_rows)
        
        self._update_page_layout(preserved_content_details=new_content_map)
        self.clear_selection()
        logger.info(f"{len(unique_sorted_rows)} rangée(s) supprimée(s). Total rangées restantes: {self.num_rows}")

    def delete_columns(self, col_indices_to_delete: list[int]):
        if not col_indices_to_delete:
            return
        
        preserved_content = self._collect_current_content_details()
        new_content_map: dict[tuple[int,int], PreservedContentDetails] = {}
        
        unique_sorted_cols = sorted(list(set(col_indices_to_delete)), reverse=True)

        if self.num_cols == 1 and len(unique_sorted_cols) >=1:
             QMessageBox.information(self, "Suppression Colonnes", "Impossible de supprimer la dernière colonne.")
             return
        if len(unique_sorted_cols) >= self.num_cols:
            logger.warning(f"Tentative de supprimer toutes les {self.num_cols} colonnes. Limitation à {self.num_cols -1} suppressions.")
            unique_sorted_cols = unique_sorted_cols[:self.num_cols -1]
            if not unique_sorted_cols:
                QMessageBox.information(self, "Suppression Colonnes", "Impossible de supprimer la dernière colonne.")
                return
        if not all(0 <= c_idx < self.num_cols for c_idx in unique_sorted_cols):
            logger.error(f"Tentative de suppression de colonnes avec des indices invalides: {unique_sorted_cols}. Max: {self.num_cols-1}")
            QMessageBox.warning(self, "Erreur", "Indices de colonnes invalides pour la suppression.")
            return
        
        logger.info(f"Suppression des colonnes aux indices: {unique_sorted_cols}")
        
        # Reconstruire self.column_widths en ne gardant que les largeurs des colonnes non supprimées
        new_column_widths_temp = []
        for i, width in enumerate(self.column_widths):
            if i not in unique_sorted_cols: # unique_sorted_cols contient les indices à supprimer
                new_column_widths_temp.append(width)
        self.column_widths = new_column_widths_temp
        
        new_merged_regions = []
        for region in self.merged_regions:
            r, c, rs, cs = region['row'], region['col'], region['rowspan'], region['colspan']
            region_end_col = c + cs - 1

            affected_by_deletion = False
            num_deleted_cols_within_region = 0
            for del_c_idx in unique_sorted_cols:
                if c <= del_c_idx <= region_end_col:
                    num_deleted_cols_within_region +=1
                    affected_by_deletion = True
            
            if affected_by_deletion:
                if num_deleted_cols_within_region >= cs:
                    continue
                else:
                    region['colspan'] = cs - num_deleted_cols_within_region
                    num_deleted_cols_before_or_at_region_start = sum(1 for del_idx in unique_sorted_cols if del_idx < c + num_deleted_cols_within_region and del_idx >=c)
                    region['col'] = c - num_deleted_cols_before_or_at_region_start
                    new_merged_regions.append(region)
            else:
                shift_left_count = sum(1 for del_idx in unique_sorted_cols if del_idx < c)
                region['col'] = c - shift_left_count
                new_merged_regions.append(region)
        self.merged_regions = new_merged_regions

        for (r_orig, c_orig), content_details in preserved_content.items():
            if c_orig in unique_sorted_cols: # La colonne de cette cellule est supprimée
                continue # Ne pas ajouter ce contenu
            
            num_deleted_cols_before = sum(1 for del_idx in unique_sorted_cols if del_idx < c_orig)
            new_c = c_orig - num_deleted_cols_before
            new_content_map[(r_orig, new_c)] = content_details
                
        self.num_cols -= len(unique_sorted_cols)

        self._update_page_layout(preserved_content_details=new_content_map)
        self.clear_selection()
        logger.info(f"{len(unique_sorted_cols)} colonne(s) supprimée(s). Total colonnes restantes: {self.num_cols}. Largeurs: {self.column_widths}")

    def set_cell_content(self, target_row: int, target_col: int, content_type: str, actual_text: str | None = None):
        cell_to_modify: CellItem | None = None

        # Vérifier si la cible est une cellule maître d'une fusion
        is_master_of_fusion, is_slave, merged_rect, original_rect = self._get_cell_merged_state(target_row, target_col, QRectF())
        
        if is_master_of_fusion:
            # La cellule cible est la maître d'une fusion existante.
            # Assurons-nous d'obtenir l'objet CellItem correct.
            if 0 <= target_row < len(self.cell_items) and 0 <= target_col < len(self.cell_items[target_row]):
                cell_to_modify = self.cell_items[target_row][target_col]
            else:
                 logger.error(f"Cellule maître ({target_row},{target_col}) hors limites après vérification de fusion.")
                 return 
            logger.info(f"La cellule ({target_row},{target_col}) est maître d'une fusion. Contenu appliqué à elle.")
        elif is_slave: 
            logger.warning(f"Tentative d'ajout de contenu à une cellule esclave ({target_row},{target_col}). Ignoré.")
            QMessageBox.warning(self, "Action impossible", "Impossible d'ajouter du contenu directement à une cellule esclave d'une fusion.")
            return
        elif 0 <= target_row < self.num_rows and 0 <= target_col < self.num_cols and \
             0 <= target_row < len(self.cell_items) and 0 <= target_col < len(self.cell_items[target_row]):
            cell_to_modify = self.cell_items[target_row][target_col]
        else:
            logger.error(f"Cellule cible ({target_row},{target_col}) hors limites pour set_cell_content.")
            return

        if not cell_to_modify:
            logger.error(f"Impossible de trouver CellItem à ({target_row},{target_col}) pour set_cell_content après toutes les vérifications.")
            return

        # Utiliser _recreate_placeholder_for_cell pour la création/mise à jour du placeholder
        self._recreate_placeholder_for_cell(cell_to_modify, content_type, actual_text)

        # --- Logique de redimensionnement de colonne (unifiée) ---
        needs_layout_update_for_resize = False
        col_idx_to_adjust = -1  # Colonne dont la largeur sera modifiée ou recalculée

        # 1. Déterminer quelle colonne est "responsable" ou affectée par le changement
        #    sur cell_to_modify.
        is_master, is_slave, _, _ = self._get_cell_merged_state(
            cell_to_modify.row, cell_to_modify.col, QRectF() # Rect factice
        )

        master_region_of_modified_cell: dict | None = None
        if is_master:
            for region in self.merged_regions:
                if region['row'] == cell_to_modify.row and region['col'] == cell_to_modify.col:
                    master_region_of_modified_cell = region
                    break
            if not master_region_of_modified_cell:
                logger.error(f"Cellule ({cell_to_modify.row},{cell_to_modify.col}) est maître mais sa région de fusion n'a pas été trouvée. Redimensionnement annulé.")
                # Si master_region_of_modified_cell reste None, col_idx_to_adjust restera -1 (ou une autre valeur sentinelle si besoin)

        if master_region_of_modified_cell: # Si la cellule modifiée est le maître d'une fusion
            # La colonne à ajuster est la dernière colonne de cette fusion
            col_idx_to_adjust = master_region_of_modified_cell['col'] + master_region_of_modified_cell['colspan'] - 1
        elif not is_slave: # Si la cellule modifiée est une cellule simple (non maître, non esclave)
            col_idx_to_adjust = cell_to_modify.col
        # Si c'est une cellule esclave (is_slave est True), col_idx_to_adjust reste -1.
        # La modification du contenu d'une esclave est déjà empêchée plus haut.

        # 2. Si une colonne pertinente a été identifiée, calculer sa nouvelle largeur requise
        if col_idx_to_adjust >= 0: # Uniquement si une colonne valide est à ajuster
            if not (0 <= col_idx_to_adjust < self.num_cols):
                logger.error(f"Indice de colonne à ajuster ({col_idx_to_adjust}) est hors limites (0-{self.num_cols - 1}). Redimensionnement annulé.")
            else:
                current_width_of_col_to_adjust = self.column_widths[col_idx_to_adjust]
                
                # _calculate_required_width_for_column scanne TOUTES les cellules pertinentes
                # pour col_idx_to_adjust et retourne la largeur max nécessaire.
                # Elle utilise le contenu actualisé de cell_to_modify car _recreate_placeholder_for_cell
                # a mis à jour cell_to_modify.actual_text et cell_to_modify.content_type.
                required_width_for_col = self._calculate_required_width_for_column(col_idx_to_adjust)
                
                if abs(current_width_of_col_to_adjust - required_width_for_col) > 1e-6: # Comparaison de floats
                    self.column_widths[col_idx_to_adjust] = required_width_for_col
                    needs_layout_update_for_resize = True
                    logger.info(f"Colonne {col_idx_to_adjust} (ou dernière colonne d'une fusion) redimensionnée à {required_width_for_col:.2f}px en fonction du contenu global de la colonne.")

        # 3. Mettre à jour la disposition si un redimensionnement a eu lieu
        if needs_layout_update_for_resize:
            preserved_content_details_before_resize = self._collect_current_content_details()
            self._update_page_layout(preserved_content_details=preserved_content_details_before_resize)
        # --- Fin de la logique de redimensionnement ---

        logger.info(f"Contenu '{content_type}' (texte: '{actual_text if actual_text else ''}') appliqué à la cellule ({target_row},{target_col}).")

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QHBoxLayout, QWidget as TestWidget
    import sys

    app = QApplication(sys.argv)
    main_win = QMainWindow()
    
    central_w = TestWidget() # Renommer pour éviter conflit avec QWidget de PyQt5.QtWidgets
    main_layout = QVBoxLayout(central_w)
    main_win.setCentralWidget(central_w)

    editor = DispositionEditorWidget()
    # Charger une disposition vide au démarrage du test
    editor.load_disposition() 
    
    controls_layout = QHBoxLayout()
    add_zone_btn = QPushButton("Ajouter Zone")
    add_zone_btn.clicked.connect(editor.add_new_zone)
    controls_layout.addWidget(add_zone_btn)

    add_row_btn = QPushButton("Ajouter Rangée")
    add_row_btn.clicked.connect(editor.add_row)
    controls_layout.addWidget(add_row_btn)

    add_col_btn = QPushButton("Ajouter Colonne")
    add_col_btn.clicked.connect(editor.add_column)
    controls_layout.addWidget(add_col_btn)
    
    main_layout.addLayout(controls_layout)
    main_layout.addWidget(editor)
    
    main_win.setWindowTitle("Test DispositionEditorWidget avec Grille Dynamique")
    main_win.resize(700, 600) # Taille un peu plus grande pour voir la scène
    main_win.show()
    sys.exit(app.exec_()) 