# pages/documents/documents_page.py # <- Chemin mis à jour
# Définit l'interface utilisateur (QWidget) principale pour la section Documents.
# Sert de point d'entrée et peut contenir la navigation vers les sous-pages.

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QFrame, QSpacerItem, QSizePolicy, QLineEdit, QScrollArea, QListWidgetItem,
    QMenu, QAction, QStackedWidget, QComboBox, QFormLayout, QAbstractItemView,
    QApplication
)
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QColor, QBrush, QPen, QPainter, QDesktopServices
# Importer la page de sélection de type
from pages.documents.documents_type_selection_page import DocumentsTypeSelectionPage

# Constantes de couleur/police/données supprimées

# --- Classe HoverButton --- 
# Sous-classe de QPushButton pour forcer le style au survol via setStyleSheet
class HoverButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        # Définir les couleurs ici (compromis car import thème échoue)
        self._normal_color = "#bbbbbb" # Valeur de COLOR_TEXT_PRIMARY
        self._normal_background = "transparent"
        self._hover_color = "#ffffff" # Valeur de COLOR_TEXT_ON_ACCENT
        self._hover_background = "#0054b8" # Valeur de COLOR_ACCENT
        # Récupérer padding/radius depuis QSS serait idéal, mais on met des valeurs par défaut
        self._padding = "4px 10px"
        self._radius = "4px" # Valeur de RADIUS_DEFAULT
        
        # Appliquer le style initial
        self._apply_style(self._normal_background, self._normal_color)
        
    def _apply_style(self, bg_color, text_color):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                padding: {self._padding};
                border-radius: {self._radius};
                text-align: center;
                min-width: 60px; 
            }}
            /* On pourrait ajouter :pressed ici aussi si nécessaire */
            QPushButton:pressed {{
                background-color: #003d82; /* ACCENT_PRESSED */ 
                color: {self._hover_color};
            }}
        """)

    def enterEvent(self, event):
        self._apply_style(self._hover_background, self._hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(self._normal_background, self._normal_color)
        super().leaveEvent(event)

# --- ProjectIconWidget (Nettoyé) ---
class ProjectIconWidget(QWidget):
    # _COLOR_MAP pourrait être déplacé dans theme.py si réutilisé ailleurs
    _COLOR_MAP = {
        "GD": "#4CAF50", "LV": "#FFC107", "ER": "#03A9F4", 
        "PM": "#9C27B0", "VS": "#E91E63", "A": "#00BCD4", 
        "VT": "#FF5722", "VA": "#673AB7", "DEFAULT": "#757575" 
    }
    def __init__(self, initials="?", size=26, parent=None):
        super().__init__(parent)
        self.initials = initials.upper()[:2]
        self.setFixedSize(size, size)
        self.color = QColor(self._COLOR_MAP.get(self.initials, self._COLOR_MAP["DEFAULT"]))
        # setAutoFillBackground(False) est le défaut, peut être retiré

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        border_radius = 4 # Pourrait venir de theme.RADIUS_DEFAULT si QSS ne suffit pas
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), border_radius, border_radius)
        painter.setPen(QPen(Qt.white)) # Couleur texte icône
        # La police devrait être définie par QSS global/spécifique
        # font = QFont(...) 
        # font.setBold(True)
        # font_size = max(7, int(self.height() * 0.4))
        # font.setPointSize(font_size)
        # painter.setFont(font)
        # Utiliser la police par défaut du painter, ajustée par QSS si nécessaire
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.horizontalAdvance(self.initials)
        # Essayer de centrer un peu mieux
        painter.drawText(self.rect().adjusted(0, 1, 0, 0), Qt.AlignCenter, self.initials) # Petit ajustement vertical

# --- ProjectListItemWidget (Nettoyé) ---
class ProjectListItemWidget(QWidget):
    # Définir les signaux pour les actions du menu
    open_requested = pyqtSignal(str)
    browse_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    # Pas besoin de signal pour copier

    def __init__(self, name, path_str, icon_initials="?", list_item=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.path_str = path_str # Stocker le chemin complet
        self.icon_initials = icon_initials
        self.setMouseTracking(True) 
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 5, 5)
        layout.setSpacing(8)

        icon_widget = ProjectIconWidget(self.icon_initials)
        layout.addWidget(icon_widget)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(-2)
        self.name_label = QLabel(name)
        self.name_label.setObjectName("ProjectListName")
        self.path_label = QLabel(path_str) # Afficher le chemin complet reçu
        self.path_label.setObjectName("ProjectListPath") 
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.path_label)
        text_layout.addStretch()

        layout.addLayout(text_layout)
        layout.addStretch(1)
        
        self.options_button = QPushButton("") 
        self.options_button.setIcon(QIcon("resources/icons/dark/round_more_vert.png"))
        self.options_button.setIconSize(QSize(16, 16)) 
        self.options_button.setObjectName("ItemOptionsButton") 
        self.options_button.setFixedSize(20, 20) 
        self.options_button.setVisible(False) 
        self.options_button.setToolTip("Options") 
        self.options_button.clicked.connect(self._show_context_menu)
        layout.addWidget(self.options_button, 0, Qt.AlignRight | Qt.AlignVCenter)

    # enterEvent/leaveEvent ne gèrent plus QUE la visibilité
    def enterEvent(self, event):
        self.options_button.setVisible(True)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.options_button.setVisible(False)
        super().leaveEvent(event)

    def _create_context_menu(self):
        """Crée et retourne le menu contextuel avec ses actions."""
        menu = QMenu(self)
        
        open_action = QAction("Ouvrir le document", self)
        open_action.triggered.connect(self._handle_open)
        menu.addAction(open_action)

        browse_action = QAction("Ouvrir dans le navigateur", self)
        browse_action.triggered.connect(self._handle_browse)
        menu.addAction(browse_action)

        copy_action = QAction("Copier le chemin", self)
        copy_action.triggered.connect(self._handle_copy)
        menu.addAction(copy_action)

        menu.addSeparator()

        remove_action = QAction("Retirer des documents recents", self)
        remove_action.triggered.connect(self._handle_remove)
        menu.addAction(remove_action)
        
        return menu

    def _show_context_menu(self):
        """Affiche le menu contextuel sous le bouton d'options."""
        menu = self._create_context_menu()
        # Positionner le menu sous le bouton
        button_pos = self.options_button.mapToGlobal(QPoint(0, self.options_button.height()))
        menu.exec_(button_pos)
        
    def contextMenuEvent(self, event):
        """Affiche le menu contextuel lors d'un clic droit sur l'item."""
        menu = self._create_context_menu()
        # Positionner le menu à la position globale du curseur
        menu.exec_(event.globalPos()) 

    # --- Slots pour les actions du menu --- 
    def _handle_open(self):
        print(f"Action: Ouvrir {self.path_str}")
        self.open_requested.emit(self.path_str)

    def _handle_browse(self):
        dir_path = os.path.dirname(self.path_str) # Obtenir le répertoire parent
        print(f"Action: Ouvrir répertoire {dir_path}")
        # Utiliser QDesktopServices pour ouvrir le dossier
        QDesktopServices.openUrl(QUrl.fromLocalFile(dir_path)) 
        # Émettre un signal si le parent doit être notifié
        self.browse_requested.emit(dir_path)

    def _handle_copy(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.path_str)
        print(f"Action: Copié {self.path_str}")
        # Pas besoin d'émettre de signal ici généralement

    def _handle_remove(self):
        print(f"Action: Retirer {self.path_str}")
        self.remove_requested.emit(self.path_str)

# --- Classe DocumentsPage (Nettoyée) --- 
class DocumentsPage(QWidget):
    open_document_requested = pyqtSignal()
    open_specific_document_requested = pyqtSignal(str)
    # Ajouter signal pour la navigation interne
    create_new_document_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentsPageWidget")
        self.init_ui()

    def init_ui(self):
        page_documents_layout = QVBoxLayout(self)
        page_documents_layout.setContentsMargins(0, 0, 0, 0)
        page_documents_layout.setSpacing(0)

        self.documents_stack = QStackedWidget()

        # --- Page 1.1: Liste des Documents --- 
        self.documents_list_page = QWidget()
        list_page_layout = QVBoxLayout(self.documents_list_page)
        list_page_layout.setContentsMargins(10, 10, 10, 10)
        list_page_layout.setSpacing(10)
        
        from ui.components.frame import Frame 

        # --- Créer le contenu de l'en-tête d'abord ---
        top_bar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Recherche de documents")
        self.search_input.setObjectName("SearchInput") 
        self.search_input.setFixedHeight(26) 
        top_bar_layout.addWidget(self.search_input, 1)
        
        self.btn_new = QPushButton("Nouveau")
        self.btn_new.setObjectName("TopNavButton")
        self.btn_new.setFixedHeight(26)
        self.btn_new.clicked.connect(self.show_type_selection_page) 
        
        self.btn_open = QPushButton("Ouvrir")
        self.btn_open.setObjectName("TopNavButton")
        self.btn_open.setFixedHeight(26)
        self.btn_open.clicked.connect(self.open_document_requested.emit)
        
        top_bar_layout.addWidget(self.btn_new)
        top_bar_layout.addWidget(self.btn_open)

        # Mettre ce layout dans un widget conteneur pour le passer au Frame
        header_container = QWidget()
        # Donner un ID pour le ciblage QSS
        header_container.setObjectName("FrameHeaderContainer") 
        header_container.setLayout(top_bar_layout)
        # Retiré: Style défini dans frame.qss maintenant
        # header_container.setStyleSheet("background-color: #3c3f41; border: none;")

        # --- Créer le Frame avec l'en-tête personnalisé ---
        # Pas de titre textuel ici
        main_doc_box = Frame(header_widget=header_container) 
        # Récupérer le layout *principal* du Frame (celui sous l'en-tête/séparateur)
        main_doc_box_layout = main_doc_box.get_content_layout()

        # --- Ajouter le contenu (liste) au layout principal du Frame ---
        # Note: Le séparateur est déjà ajouté par le Frame lui-même s'il a un en-tête.
        # Retiré: Ajout manuel du séparateur
        # manual_separator = QFrame()
        # ...
        # main_doc_box_layout.addWidget(manual_separator)

        self.recent_list_widget = QListWidget() 
        self.recent_list_widget.setObjectName("ProjectList")
        # ... (Configuration de la liste)
        self.recent_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.recent_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.recent_list_widget.setFocusPolicy(Qt.NoFocus)
        # Désactiver la sélection visuelle des items
        self.recent_list_widget.setSelectionMode(QAbstractItemView.NoSelection) 
        
        projects = self.load_project_data() 
        if projects:
             for project_data in projects:
                item = QListWidgetItem(self.recent_list_widget)
                # ... (Création ProjectListItemWidget)
                item_widget = ProjectListItemWidget(
                    project_data["name"],
                    project_data["path"],
                    project_data.get("icon", "?")
                )
                item_widget.open_requested.connect(self.open_specific_document_requested) # Connecter signal
                # Connecter autres signaux (browse, remove) si nécessaire au contrôleur
                item.setSizeHint(item_widget.sizeHint())
                self.recent_list_widget.addItem(item)
                self.recent_list_widget.setItemWidget(item, item_widget)
        self.recent_list_widget.itemClicked.connect(self._on_recent_item_activated)
        
        # Ajouter la liste directement au layout du Frame
        main_doc_box_layout.addWidget(self.recent_list_widget, 1)
        
        # Ajouter le Frame principal au layout de la page
        list_page_layout.addWidget(main_doc_box, 1)
        self.documents_stack.addWidget(self.documents_list_page)

        # --- Page 1.2: Instancier la VRAIE page de sélection de type --- 
        self.documents_type_selection_page = DocumentsTypeSelectionPage()
        # Connecter ses signaux
        self.documents_type_selection_page.create_requested.connect(self._handle_create_request)
        self.documents_type_selection_page.cancel_requested.connect(self.show_documents_list)
        # Ajouter la page de sélection au stack
        self.documents_stack.addWidget(self.documents_type_selection_page)

        page_documents_layout.addWidget(self.documents_stack)

    def load_project_data(self):
        # Remplacer ceci par la logique réelle de chargement des projets
        # (ex: lire un fichier de config, base de données...)
        print("DocumentsPage: Chargement des données de projets (placeholder)...")
        return [
            {"name": "GDJ", "path": "~/PycharmProjects/GDJ", "icon": "GD"},
            {"name": "GDJ_App", "path": "~/PycharmProjects/GDJ_App", "icon": "GD"},
            {"name": "LiveVision", "path": "~/PycharmProjects/LiveVision", "icon": "LV"},
        ] # Exemple limité

    def _on_recent_item_activated(self, item):
        widget_item = self.recent_list_widget.itemWidget(item)
        if isinstance(widget_item, ProjectListItemWidget):
            document_path = widget_item.path_str
            print(f"DocumentsPage: Item double clicked - {document_path}")
            full_path = os.path.expanduser(document_path)
            self.open_specific_document_requested.emit(full_path)

    # --- Méthodes de navigation et slots --- 
    def show_documents_list(self):
        self.documents_stack.setCurrentWidget(self.documents_list_page)
        
    def show_type_selection_page(self):
        print("DEBUG: show_type_selection_page() called")
        # Le contrôleur devrait remplir la combobox avant d'afficher
        # Exemple: self.controller.populate_doc_types(self.documents_type_selection_page)
        if self.documents_stack and self.documents_type_selection_page:
            print(f"DEBUG: Switching stack to {self.documents_type_selection_page}")
            self.documents_stack.setCurrentWidget(self.documents_type_selection_page)
        else:
            print("ERREUR: documents_stack ou documents_type_selection_page non initialisé!")
        
    def _handle_create_request(self, selected_type):
        print(f"DocumentsPage: Demande de création reçue pour type: {selected_type}")
        # Émettre un signal vers le contrôleur principal ou gérer ici
        self.create_new_document_requested.emit(selected_type)
        # Revenir à la liste après la demande?
        self.show_documents_list()

print("DocumentsPage (dans pages/documents/) defined") 