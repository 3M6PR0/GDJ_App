# pages/documents/documents_page.py # <- Chemin mis à jour
# Définit l'interface utilisateur (QWidget) principale pour la section Documents.
# Sert de point d'entrée et peut contenir la navigation vers les sous-pages.

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QFrame, QSpacerItem, QSizePolicy, QLineEdit, QScrollArea, QListWidgetItem,
    QMenu, QAction, QStackedWidget, QComboBox, QFormLayout
)
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QColor, QBrush, QPen, QPainter

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
    def __init__(self, name, path_str, icon_initials="?", list_item=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.path_str = path_str
        self.icon_initials = icon_initials
        # setStyleSheet transparent retiré (devrait être géré par QListWidget::item)
        self.setMouseTracking(True)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 5, 5)
        layout.setSpacing(8)

        icon_widget = ProjectIconWidget(self.icon_initials)
        layout.addWidget(icon_widget)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(-2)
        self.name_label = QLabel(name)
        self.name_label.setObjectName("ProjectListName") # ID pour style
        # setFont retiré
        # setStyleSheet retiré
        self.path_label = QLabel(path_str)
        self.path_label.setObjectName("ProjectListPath") # ID pour style
        # setFont retiré
        # setStyleSheet retiré
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.path_label)
        text_layout.addStretch()

        layout.addLayout(text_layout)
        layout.addStretch(1)
        
        self.options_button = QPushButton("...")
        self.options_button.setObjectName("ItemOptionsButton") # Style via QSS
        self.options_button.setFixedSize(20, 20)
        self.options_button.setVisible(False)
        # setStyleSheet retiré
        self.options_button.clicked.connect(self._show_context_menu)
        layout.addWidget(self.options_button, 0, Qt.AlignRight | Qt.AlignVCenter)

    # enterEvent et leaveEvent restent pour la visibilité du bouton
    def enterEvent(self, event):
        self.options_button.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.options_button.setVisible(False)
        super().leaveEvent(event)

    def _show_context_menu(self):
        # Le style du menu devrait être défini dans global.qss
        menu = QMenu(self)
        # Actions...
        pass

# --- Classe DocumentsPage (Nettoyée) --- 
class DocumentsPage(QWidget):
    open_document_requested = pyqtSignal()
    open_specific_document_requested = pyqtSignal(str)

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
        # Utiliser le même ID que les boutons Retour/Notes
        self.btn_new.setObjectName("TopNavButton") 
        self.btn_new.setFixedHeight(26)
        
        self.btn_open = QPushButton("Ouvrir")
        # Utiliser le même ID que les boutons Retour/Notes
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
                item.setSizeHint(item_widget.sizeHint())
                self.recent_list_widget.addItem(item)
                self.recent_list_widget.setItemWidget(item, item_widget)
        self.recent_list_widget.itemDoubleClicked.connect(self._on_recent_item_activated)
        
        # Ajouter la liste directement au layout du Frame
        main_doc_box_layout.addWidget(self.recent_list_widget, 1)
        
        # Ajouter le Frame principal au layout de la page
        list_page_layout.addWidget(main_doc_box, 1)
        self.documents_stack.addWidget(self.documents_list_page)

        # --- Page 1.2: Nouvelle Page Document --- 
        self.documents_new_page = QWidget()
        new_page_container_layout = QVBoxLayout(self.documents_new_page)
        new_page_container_layout.setContentsMargins(10, 10, 10, 10)
        new_page_container_layout.setSpacing(10)

        # Utiliser le composant Frame avec titre
        new_doc_box = Frame(title="Créer un nouveau document") 
        new_doc_box_layout = new_doc_box.get_content_layout()
        # Marges/Spacing gérés par Frame
        
        self.btn_back_to_list = QPushButton("Retour") 
        self.btn_back_to_list.setObjectName("TopNavButton") # ID pour style QSS
        self.btn_back_to_list.setFixedWidth(80)
        
        new_doc_form_layout = QFormLayout()
        new_doc_form_layout.setContentsMargins(15, 10, 15, 10) # Ajouter marges internes au contenu
        new_doc_form_layout.setSpacing(10)
        new_doc_form_layout.setVerticalSpacing(12)
        label_doc_type = QLabel("Document:") # Style via QLabel dans QFormLayout (QSS)
        label_doc_type.setObjectName("FormLabel") # ID optionnel
        # setStyleSheet supprimé
        cb_new_doc_type = QComboBox() # Style via QComboBox (QSS)
        cb_new_doc_type.addItems(["Document Standard", "Rapport Mensuel", "Présentation Client", "Autre..."])
        new_doc_form_layout.addRow(label_doc_type, cb_new_doc_type)
        # ... (Autres champs)
        
        new_doc_box_layout.addLayout(new_doc_form_layout)
        new_doc_box_layout.addStretch(1)

        new_page_container_layout.addWidget(new_doc_box, 0) # Ne pas étirer la boîte
        new_page_container_layout.addStretch(1) # Ajouter un espace extensible en dessous
        new_page_container_layout.addWidget(self.btn_back_to_list, 0, Qt.AlignBottom | Qt.AlignLeft)

        self.documents_stack.addWidget(self.documents_new_page)
        page_documents_layout.addWidget(self.documents_stack)

        # Appel à apply_styles supprimé

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

    # Méthode _create_dashboard_box supprimée (remplacée par Frame)
    # Méthode apply_styles supprimée

print("DocumentsPage (dans pages/documents/) defined") 