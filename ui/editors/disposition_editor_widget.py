from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QPushButton, QGraphicsItem, QGraphicsPathItem, QGraphicsLineItem, QMessageBox, QRubberBand, QApplication, QGraphicsSimpleTextItem
from PyQt5.QtCore import Qt, QRectF, QLineF, QPoint, QSize
from PyQt5.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath, QFont
import logging

logger = logging.getLogger('GDJ_App')

# Clé pour marquer l'item de fond de page
PAGE_BACKGROUND_ITEM_KEY = QGraphicsItem.UserType + 1

# Constantes pour la grille et la page
DEFAULT_CELL_WIDTH = 100  # pixels
DEFAULT_CELL_HEIGHT = 50  # pixels
PAGE_MARGIN = 20          # pixels de marge autour de la page dans la scène
DEFAULT_ROWS = 1
DEFAULT_COLS = 1
CORNER_RADIUS = 10        # pixels pour les coins arrondis de la page

SELECTED_CELL_BRUSH = QBrush(QColor(173, 216, 230, 128)) # Bleu clair semi-transparent
NORMAL_CELL_BRUSH = QBrush(Qt.transparent)
CELL_BORDER_PEN = QPen(QColor("#C0C0C0"), 0.5, Qt.DotLine) # Pointillés légers pour les cellules

# Structure pour stocker les détails du contenu préservé
# (content_type, actual_text_if_any)
PreservedContentDetails = tuple[str, str | None]

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
        
        self.scene_items_counter = 0 
        self.page_background_item = None
        self.grid_lines = []
        self.cell_items: list[list[CellItem | None]] = []
        self.selected_cells = set()
        self.merged_regions = []

        self.num_rows = DEFAULT_ROWS
        self.num_cols = DEFAULT_COLS
        self.cell_width = DEFAULT_CELL_WIDTH
        self.cell_height = DEFAULT_CELL_HEIGHT
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

    def _update_page_layout(self, preserved_content_details: dict[tuple[int, int], PreservedContentDetails] | None = None):
        """ Met à jour la taille et l'apparence du fond de page et de la scène. """
        if preserved_content_details is None:
            preserved_content_details = {}
            
        page_width = self.num_cols * self.cell_width
        page_height = self.num_rows * self.cell_height

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

        # Dessiner les nouvelles lignes de la grille
        grid_pen = QPen(QColor("#D0D0D0"), 0.5, Qt.SolidLine) # Pen fin et gris clair

        # Lignes verticales
        for i in range(1, self.num_cols):
            x = PAGE_MARGIN + i * self.cell_width
            line = QGraphicsLineItem(QLineF(x, PAGE_MARGIN, x, PAGE_MARGIN + page_height))
            line.setPen(grid_pen)
            line.setZValue(-0.5) # Juste au-dessus du fond de page, mais en dessous des zones
            self.scene.addItem(line)
            self.grid_lines.append(line)

        # Lignes horizontales
        for i in range(1, self.num_rows):
            y = PAGE_MARGIN + i * self.cell_height
            line = QGraphicsLineItem(QLineF(PAGE_MARGIN, y, PAGE_MARGIN + page_width, y))
            line.setPen(grid_pen)
            line.setZValue(-0.5)
            self.scene.addItem(line)
            self.grid_lines.append(line)

        # Créer les CellItem pour chaque cellule de la grille
        for r in range(self.num_rows):
            for c in range(self.num_cols):
                cell_x = PAGE_MARGIN + c * self.cell_width
                cell_y = PAGE_MARGIN + r * self.cell_height
                cell_rect = QRectF(cell_x, cell_y, self.cell_width, self.cell_height)
                
                cell_item = CellItem(r, c, cell_rect, editor_widget=self, graphics_parent=None)
                is_master, is_slave, merged_cell_rect, original_rect = self._get_cell_merged_state(r, c, cell_rect)
                
                cell_item.set_selected(False)
                if is_master or is_slave:
                    cell_item.set_merged_state(is_master, True, merged_cell_rect if is_master else original_rect)
                else:
                    cell_item.set_merged_state(False, False, original_rect)
                
                cell_item.setZValue(-0.2)
                self.scene.addItem(cell_item)
                self.cell_items[r][c] = cell_item
                
                if (r, c) in preserved_content_details:
                    content_type_str, actual_text_str = preserved_content_details[(r, c)]
                    current_is_master, current_is_slave, _, _ = self._get_cell_merged_state(r, c, QRectF())
                    if not current_is_slave:
                        self._recreate_placeholder_for_cell(cell_item, content_type_str, actual_text_str)

        self._draw_grid_lines(page_width, page_height)
        logger.debug(f"Page layout updated: {self.num_rows}x{self.num_cols} cells. Page size: {page_width}x{page_height}px. Scene size: {scene_width}x{scene_height}px. Cells created: {self.num_rows*self.num_cols}")

    def _recreate_placeholder_for_cell(self, cell_item: CellItem, content_type: str, actual_text: str | None):
        """ Recrée un placeholder pour une cellule donnée. """
        if cell_item.content_placeholder_item and cell_item.content_placeholder_item.scene():
            self.scene.removeItem(cell_item.content_placeholder_item)
        
        cell_item.content_type = content_type
        cell_item.actual_text = actual_text # Stocker aussi le texte réel sur la cellule

        display_text = actual_text if content_type == "Texte" and actual_text is not None else content_type.capitalize()
        if content_type == "Texte" and actual_text == "": # Afficher quelque chose si le texte est vide
            display_text = "[Texte vide]"
            
        new_placeholder = QGraphicsSimpleTextItem(display_text, parent=cell_item)
        new_placeholder.setFont(QFont("Arial", 8))
        new_placeholder.setBrush(QBrush(Qt.black))
        
        cell_local_rect = cell_item.boundingRect()
        placeholder_bound_rect = new_placeholder.boundingRect()
        
        offset_x = (cell_local_rect.width() - placeholder_bound_rect.width()) / 2
        offset_y = (cell_local_rect.height() - placeholder_bound_rect.height()) / 2
        
        new_placeholder.setPos(offset_x, offset_y)
        cell_item.content_placeholder_item = new_placeholder
        logger.debug(f"Placeholder '{display_text}' recréé pour la cellule ({cell_item.row},{cell_item.col}).")

    def _get_cell_merged_state(self, row: int, col: int, original_cell_rect: QRectF) -> tuple[bool, bool, QRectF | None, QRectF]:
        """ Vérifie si une cellule (row, col) est partie d'une fusion et retourne son état. """
        for region in self.merged_regions:
            r_start, c_start = region['row'], region['col']
            row_span, col_span = region['rowspan'], region['colspan']
            r_end, c_end = r_start + row_span - 1, c_start + col_span - 1

            if r_start <= row <= r_end and c_start <= col <= c_end:
                is_master = (row == r_start and col == c_start)
                merged_width = col_span * self.cell_width
                merged_height = row_span * self.cell_height
                master_rect = QRectF(
                    PAGE_MARGIN + c_start * self.cell_width,
                    PAGE_MARGIN + r_start * self.cell_height,
                    merged_width,
                    merged_height
                )
                return is_master, True, master_rect, original_cell_rect
        return False, False, None, original_cell_rect

    def _draw_grid_lines(self, page_width: float, page_height: float):
        """ Dessine les lignes de la grille, en omettant les lignes internes aux cellules fusionnées. """
        for line_item in self.grid_lines:
            self.scene.removeItem(line_item)
        self.grid_lines.clear()

        grid_pen = QPen(QColor("#D0D0D0"), 0.5, Qt.SolidLine)

        # Lignes verticales
        for c_idx in range(1, self.num_cols):
            should_draw = True
            for r_idx in range(self.num_rows):
                is_left_merged, _, _, _ = self._get_cell_merged_state(r_idx, c_idx -1, QRectF())
                is_right_merged, _, _, _ = self._get_cell_merged_state(r_idx, c_idx, QRectF())
                if self._are_cells_in_same_merge(r_idx, c_idx -1, r_idx, c_idx):
                    should_draw = False
                    break
            if should_draw:
                x = PAGE_MARGIN + c_idx * self.cell_width
                line = QGraphicsLineItem(QLineF(x, PAGE_MARGIN, x, PAGE_MARGIN + page_height))
                line.setPen(grid_pen)
                line.setZValue(-0.5)
                self.scene.addItem(line)
                self.grid_lines.append(line)

        # Lignes horizontales
        for r_idx in range(1, self.num_rows):
            should_draw = True
            for c_idx in range(self.num_cols):
                if self._are_cells_in_same_merge(r_idx -1, c_idx, r_idx, c_idx):
                    should_draw = False
                    break
            if should_draw:
                y = PAGE_MARGIN + r_idx * self.cell_height
                line = QGraphicsLineItem(QLineF(PAGE_MARGIN, y, PAGE_MARGIN + page_width, y))
                line.setPen(grid_pen)
                line.setZValue(-0.5)
                self.scene.addItem(line)
                self.grid_lines.append(line)

    def _are_cells_in_same_merge(self, r1, c1, r2, c2) -> bool:
        """ Vérifie si deux cellules adjacentes font partie de la même région fusionnée. """
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
            self.cell_width = disposition_data.get('cell_width', DEFAULT_CELL_WIDTH)
            self.cell_height = disposition_data.get('cell_height', DEFAULT_CELL_HEIGHT)
            self.corner_radius = disposition_data.get('corner_radius', CORNER_RADIUS)
            self.merged_regions = disposition_data.get('merged_cells', [])
            # Charger le contenu des cellules (nouveau)
            cell_contents_data = disposition_data.get('cell_contents', {})
            for coord_str, content_details_list in cell_contents_data.items():
                try:
                    r_str, c_str = coord_str.strip("()").split(",")
                    r, c = int(r_str), int(c_str)
                    # S'assurer que les détails sont bien une liste/tuple avec type et texte
                    if isinstance(content_details_list, (list, tuple)) and len(content_details_list) == 2:
                         content_to_load[(r,c)] = (str(content_details_list[0]), content_details_list[1]) # content_type, actual_text
                    else:
                        logger.warning(f"Format de contenu de cellule incorrect pour {coord_str}: {content_details_list}")
                except ValueError as e:
                    logger.error(f"Erreur de parsing des coordonnées de cellule_contents '{coord_str}': {e}")

        else:
            logger.info("Préparation de l'éditeur pour une nouvelle disposition.")
            self.num_rows = DEFAULT_ROWS
            self.num_cols = DEFAULT_COLS
            self.cell_width = DEFAULT_CELL_WIDTH
            self.cell_height = DEFAULT_CELL_HEIGHT
            self.corner_radius = CORNER_RADIUS
            
        self._update_page_layout(preserved_content_details=content_to_load)

        # La logique de chargement des anciennes "zones" peut être supprimée ou adaptée si nécessaire.
        # Pour l'instant, on se concentre sur le contenu basé sur les cellules.

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
        """ Ajoute une colonne à la fin de la grille. """
        # Pas besoin de décaler le contenu, car on ajoute à la fin.
        preserved_content = self._collect_current_content_details()
        self.num_cols += 1
        logger.debug(f"Colonne ajoutée à la fin. Total colonnes: {self.num_cols}")
        self._update_page_layout(preserved_content_details=preserved_content)

    def _insert_column_before_index(self, target_index: int):
        """ Insère une nouvelle colonne avant target_index et décale les suivantes. """
        preserved_content = self._collect_current_content_details()
        new_content_map: dict[tuple[int,int], PreservedContentDetails] = {}

        if not (0 <= target_index <= self.num_cols):
            logger.error(f"Indice d'insertion de colonne invalide: {target_index}. Max: {self.num_cols}")
            pass 

        self.num_cols += 1
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

        logger.debug(f"Colonne insérée avant l'index {target_index}. Total colonnes: {self.num_cols}")
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
        offset_x = (self.scene_items_counter % self.num_cols) * (self.cell_width / 2)
        offset_y = (self.scene_items_counter // self.num_cols) * (self.cell_height / 2)
        
        zone_width = self.cell_width * 0.8
        zone_height = self.cell_height * 0.8
        
        # Vérifier que la nouvelle zone ne dépasse pas les limites de la page
        max_x_on_page = (self.num_cols * self.cell_width) - zone_width
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
            "cell_width": self.cell_width,
            "cell_height": self.cell_height,
            "corner_radius": self.corner_radius,
            "merged_cells": list(self.merged_regions), # S'assurer que c'est une copie sérialisable
            "cell_contents": cell_contents_to_save, # Nouveau champ pour le contenu des cellules
            "zones": zones_data # Ancien champ, peut être déprécié
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

        if self.num_cols == 1 and len(unique_sorted_cols) >= 1:
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
        logger.info(f"{len(unique_sorted_cols)} colonne(s) supprimée(s). Total colonnes restantes: {self.num_cols}")

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