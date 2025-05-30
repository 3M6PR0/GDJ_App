# pages/documents/documents_recent_list_page.py
# Affiche la liste des documents récents et les boutons d'action.

import sys
import os
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QFrame, QSpacerItem, QSizePolicy, QLineEdit, QScrollArea, QListWidgetItem,
    QMenu, QAction, QAbstractItemView, QApplication
)
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal, QUrl, pyqtSlot as Slot, QEvent
from PyQt5.QtGui import QIcon, QPixmap, QColor, QBrush, QPen, QPainter, QDesktopServices

# Importer le composant Frame
from ui.components.frame import Frame

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path
from utils import icon_loader, theme
# --- AJOUT IMPORT --- 
from utils.signals import signals 
# -------------------

logger = logging.getLogger('GDJ_App')

# --- Classe HoverButton (peut être supprimée si non utilisée) --- 
class HoverButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._normal_color = "#bbbbbb"
        self._normal_background = "transparent"
        self._hover_color = "#ffffff"
        self._hover_background = "#0054b8"
        self._padding = "4px 8px" # Utiliser PADDING_SMALL/MEDIUM
        self._radius = "4px" 
        self._apply_style(self._normal_background, self._normal_color)
        
    def _apply_style(self, bg_color, text_color):
        self.setStyleSheet(f'''
            QPushButton {{ 
                background-color: {bg_color}; color: {text_color}; 
                border: none; padding: {self._padding}; border-radius: {self._radius};
                text-align: center; min-width: 60px; 
            }}
            QPushButton:pressed {{ background-color: #003d82; color: {self._hover_color}; }}
        ''')
    def enterEvent(self, event): self._apply_style(self._hover_background, self._hover_color); super().enterEvent(event)
    def leaveEvent(self, event): self._apply_style(self._normal_background, self._normal_color); super().leaveEvent(event)

# --- ProjectIconWidget --- 
class ProjectIconWidget(QWidget):
    _COLOR_MAP = {"GD": "#4CAF50", "LV": "#FFC107", "DEFAULT": "#757575"}
    def __init__(self, initials="?", size=26, parent=None):
        super().__init__(parent)
        self.initials = initials.upper()[:2]
        self.setFixedSize(size, size)
        self.color = QColor(self._COLOR_MAP.get(self.initials, self._COLOR_MAP["DEFAULT"]))
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 4, 4)
        painter.setPen(QPen(Qt.white))
        font_metrics = painter.fontMetrics()
        painter.drawText(self.rect().adjusted(0, 1, 0, 0), Qt.AlignCenter, self.initials)

# --- ProjectListItemWidget --- 
class ProjectListItemWidget(QWidget):
    open_requested = pyqtSignal(str)
    browse_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    def __init__(self, name, path_str, icon_initials="?", list_widget_item=None, parent_list_widget=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.path_str = path_str
        self.icon_initials = icon_initials
        self._options_icon_base = "round_more_vert.png"
        self.list_widget_item = list_widget_item
        self.parent_list_widget = parent_list_widget
        self.setMouseTracking(True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 5, 5); layout.setSpacing(8)
        icon_widget = ProjectIconWidget(self.icon_initials); layout.addWidget(icon_widget)
        text_layout = QVBoxLayout(); text_layout.setSpacing(-2)
        self.name_label = QLabel(name); self.name_label.setObjectName("ProjectListName")
        self.path_label = QLabel(path_str); self.path_label.setObjectName("ProjectListPath")
        text_layout.addWidget(self.name_label); text_layout.addWidget(self.path_label); text_layout.addStretch()
        layout.addLayout(text_layout); layout.addStretch(1)
        options_icon_path = icon_loader.get_icon_path(self._options_icon_base)
        self.options_button = QPushButton("")
        self.options_button.setIcon(QIcon(options_icon_path))
        self.options_button.setIconSize(QSize(16, 16)); self.options_button.setObjectName("ItemOptionsButton")
        self.options_button.setFixedSize(20, 20); self.options_button.setVisible(False)
        self.options_button.setToolTip("Options"); self.options_button.clicked.connect(self._show_context_menu)
        layout.addWidget(self.options_button, 0, Qt.AlignRight | Qt.AlignVCenter)
        signals.theme_changed_signal.connect(self.update_theme_icons)
    def enterEvent(self, event): self.options_button.setVisible(True); super().enterEvent(event)
    def leaveEvent(self, event): self.options_button.setVisible(False); super().leaveEvent(event)
    def _create_context_menu(self):
        menu = QMenu(self)
        menu.setObjectName("RecentItemContextMenu")
        # --- AJOUT: Appliquer le style des ITEMS directement --- 
        # (Repris de la tentative précédente qui fonctionnait pour les items)
        item_styles = """
            QMenu#RecentItemContextMenu::item {
                background-color: transparent; 
                color: #bbbbbb; /* Texte clair par défaut */
                padding: 4px 20px 4px 10px; 
                border-radius: 4px; 
                margin: 1px; 
            }
            QMenu#RecentItemContextMenu::item:selected { /* Hover */
                background-color: #0054b8; /* Couleur accent */
                color: #ffffff; /* Texte sur accent */
            }
            QMenu#RecentItemContextMenu::item:pressed { /* Click */
                background-color: #003d82; /* Couleur accent pressé */
                color: #ffffff; 
            }
            QMenu#RecentItemContextMenu::separator {
                height: 1px;
                background-color: #5a5d5e; /* Gris clair */
                margin: 4px 0px; 
            }
            QMenu#RecentItemContextMenu::item:disabled {
                color: #808080; /* Texte désactivé */
                background-color: transparent;
            }
        """
        menu.setStyleSheet(item_styles)
        # ---------------------------------------------------
        actions = {"Ouvrir le document": self._handle_open, 
                   "Ouvrir dans le navigateur": self._handle_browse,
                   "Copier le chemin": self._handle_copy,
                   None: None, # Separator
                   "Retirer des documents recents": self._handle_remove}
        for text, handler in actions.items():
            if text is None: menu.addSeparator()
            else: menu.addAction(QAction(text, self, triggered=handler))
        return menu
    def _show_context_menu(self): 
        menu = self._create_context_menu()
        original_item = None
        if self.parent_list_widget:
            original_item = self.parent_list_widget.currentItem()
            if self.list_widget_item:
                self.parent_list_widget.setCurrentItem(self.list_widget_item)
        try:
            menu.exec_(self.options_button.mapToGlobal(QPoint(0, self.options_button.height())))
        finally:
            if self.parent_list_widget:
                self.parent_list_widget.setCurrentItem(None)
    def contextMenuEvent(self, event): 
        menu = self._create_context_menu()
        original_item = None
        if self.parent_list_widget:
            original_item = self.parent_list_widget.currentItem()
            if self.list_widget_item:
                self.parent_list_widget.setCurrentItem(self.list_widget_item)
        try:
            menu.exec_(event.globalPos())
        finally:
            if self.parent_list_widget:
                self.parent_list_widget.setCurrentItem(None)
    def _handle_open(self): self.open_requested.emit(self.path_str)
    def _handle_browse(self): dir_path = os.path.dirname(self.path_str); QDesktopServices.openUrl(QUrl.fromLocalFile(dir_path)); self.browse_requested.emit(dir_path)
    def _handle_copy(self): QApplication.clipboard().setText(self.path_str); logger.info(f"Action: Copié {self.path_str}")
    def _handle_remove(self): self.remove_requested.emit(self.path_str)
    @Slot(str)
    def update_theme_icons(self, theme_name):
        try:
            new_icon_path = icon_loader.get_icon_path(self._options_icon_base)
            new_icon = QIcon(new_icon_path)
            if not new_icon.isNull():
                self.options_button.setIcon(new_icon)
            else:
                self.options_button.setIcon(QIcon())
                self.options_button.setText("...")
        except Exception as e:
            logger.error(f"ERROR: Updating icon for ProjectListItemWidget '{self.name}': {e}")
            self.options_button.setIcon(QIcon())
            self.options_button.setText("...")
        
        try:
            current_theme_colors = theme.get_theme_vars(theme_name)
            primary_color = current_theme_colors.get("COLOR_TEXT_PRIMARY", "#bbbbbb")
            secondary_color = current_theme_colors.get("COLOR_TEXT_SECONDARY", "#bbbbbb")
            self.name_label.setStyleSheet(f"QLabel#ProjectListName {{ color: {primary_color}; background-color: transparent; }}")
            self.path_label.setStyleSheet(f"QLabel#ProjectListPath {{ color: {secondary_color}; background-color: transparent; }}")
        except Exception as e:
            logger.error(f"ERROR: Updating label colors in ProjectListItemWidget '{self.name}': {e}")

# --- Classe DocumentsRecentListPage --- 
class DocumentsRecentListPage(QWidget):
    # Définir les signaux émis par cette page
    open_document_requested = pyqtSignal() # Pour le bouton "Ouvrir" général
    new_document_requested = pyqtSignal() # Pour le bouton "Nouveau"
    open_specific_document_requested = pyqtSignal(str) # Depuis un item
    remove_document_requested = pyqtSignal(str) # Depuis le menu item
    # browse_document_requested = pyqtSignal(str) # Pas forcément utile au niveau page?

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentsRecentListPageWidget")
        self._setup_ui()
        self._load_project_data()
        logger.info("DocumentsRecentListPage initialized")

    def _setup_ui(self):
        list_page_layout = QVBoxLayout(self)
        list_page_layout.setContentsMargins(10, 10, 10, 10)
        list_page_layout.setSpacing(10)
        
        # --- Créer le contenu de l'en-tête --- 
        top_bar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Recherche de documents")
        self.search_input.setObjectName("SearchInput") 
        self.search_input.setFixedHeight(26) 
        top_bar_layout.addWidget(self.search_input, 1)
        
        self.btn_new = QPushButton("Nouveau")
        self.btn_new.setObjectName("TopNavButton")
        self.btn_new.setFixedHeight(26)
        self.btn_new.clicked.connect(self.new_document_requested.emit) # Émettre signal
        
        self.btn_open = QPushButton("Ouvrir")
        self.btn_open.setObjectName("TopNavButton")
        self.btn_open.setFixedHeight(26)
        self.btn_open.clicked.connect(self.open_document_requested.emit) # Émettre signal
        
        top_bar_layout.addWidget(self.btn_new)
        top_bar_layout.addWidget(self.btn_open)

        header_container = QWidget()
        header_container.setObjectName("FrameHeaderContainer") 
        header_container.setLayout(top_bar_layout)

        # --- Créer le Frame avec l'en-tête --- 
        main_doc_box = Frame(header_widget=header_container) 
        main_doc_box_layout = main_doc_box.get_content_layout()

        # --- Créer la liste --- 
        self.recent_list_widget = QListWidget() 
        self.recent_list_widget.setObjectName("ProjectList")
        self.recent_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.recent_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.recent_list_widget.setFocusPolicy(Qt.NoFocus)
        # --- Vérifier que cette ligne est bien commentée --- 
        # self.recent_list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        # --------------------------------------------------
        self.recent_list_widget.itemClicked.connect(self._on_recent_item_activated) 
        
        # --- AJOUT: Installer le filtre d'événements --- 
        self.recent_list_widget.viewport().installEventFilter(self)
        # ----------------------------------------------

        # Ajouter la liste au layout du Frame
        main_doc_box_layout.addWidget(self.recent_list_widget, 1)
        
        # Ajouter le Frame au layout de la page
        list_page_layout.addWidget(main_doc_box, 1)
        
        # Charger les données initiales
        # Retiré: self.populate_list() # Le contrôleur s'en chargera

    # --- AJOUT: Implémentation du filtre d'événements --- 
    def eventFilter(self, source, event):
        # Filtrer les clics sur le viewport de la liste
        if source is self.recent_list_widget.viewport() and event.type() == QEvent.MouseButtonPress:
            # Vérifier si un item est sous le curseur au moment du clic
            item_at_click = self.recent_list_widget.itemAt(event.pos())
            if item_at_click:
                # Si un item est cliqué, on intercepte l'événement pour 
                # empêcher la sélection visuelle par défaut (car on gère 
                # la surbrillance via setCurrentItem uniquement pour le menu)
                # On laisse cependant itemClicked se déclencher si besoin
                logger.debug(f"DEBUG: Click intercepté sur item: {self.recent_list_widget.itemWidget(item_at_click).name}")
                # ATTENTION: Cela peut potentiellement bloquer d'autres interactions
                # return True # Bloque complètement l'événement (peut-être trop)
                pass # Laisser l'événement continuer mais la sélection visuelle ne devrait pas changer ? A tester
        
        # Laisser les autres événements passer
        return super().eventFilter(source, event)
    # ---------------------------------------------------

    def populate_list(self, projects):
        """Vide et remplit la liste avec les données fournies ou des placeholders."""
        self.recent_list_widget.clear()
        # Si aucune donnée n'est fournie par le contrôleur, utiliser les placeholders
        if projects is None:
            projects = self._load_project_data() # Re-appeler le chargement placeholder
        
        if projects:
             for project_data in projects:
                item = QListWidgetItem(self.recent_list_widget)
                item_widget = ProjectListItemWidget(
                    project_data["name"],
                    project_data["path"],
                    project_data.get("icon", "?"),
                    list_widget_item=item,
                    parent_list_widget=self.recent_list_widget
                )
                # Connecter les signaux de l'item à ceux de la page
                item_widget.open_requested.connect(self.open_specific_document_requested)
                item_widget.remove_requested.connect(self.remove_document_requested)
                # item_widget.browse_requested.connect(self.browse_document_requested)
                
                item.setSizeHint(item_widget.sizeHint())
                self.recent_list_widget.addItem(item)
                self.recent_list_widget.setItemWidget(item, item_widget)
        
    # Restaurer la méthode pour charger les données placeholder
    def _load_project_data(self):
        """Charge les données de projets (placeholder)."""
        logger.info("DocumentsRecentListPage: Chargement des données de projets (placeholder)...")
        return [
            {"name": "GDJ", "path": "~/PycharmProjects/GDJ", "icon": "GD"},
            {"name": "GDJ_App", "path": "~/PycharmProjects/GDJ_App", "icon": "GD"},
            {"name": "LiveVision", "path": "~/PycharmProjects/LiveVision", "icon": "LV"},
        ] 

    def _on_recent_item_activated(self, item):
        """Gère le clic sur un item de la liste."""
        widget_item = self.recent_list_widget.itemWidget(item)
        if isinstance(widget_item, ProjectListItemWidget):
            document_path = widget_item.path_str
            logger.info(f"DocumentsRecentListPage: Item clicked - {document_path}")
            self.open_specific_document_requested.emit(os.path.expanduser(document_path))

logger.info("DocumentsRecentListPage defined") 