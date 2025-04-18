import sys
import os # Ajout pour les chemins d'icônes
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QFrame, QSpacerItem, 
                             QSizePolicy, QLineEdit, QScrollArea, QListWidgetItem, 
                             QMenu, QAction, QStackedWidget, QButtonGroup,
                             QGridLayout, QFormLayout, QComboBox, QCheckBox, QFileDialog, QTextBrowser) # Ajout QLineEdit, QScrollArea, QListWidgetItem, QMenu, QAction, QStackedWidget, QButtonGroup, QGridLayout, QFormLayout, QComboBox, QCheckBox, QFileDialog, QTextBrowser
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, pyqtProperty, QEasingCurve, QPropertyAnimation, pyqtSignal # Ajouts pour ToggleSwitch
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPalette, QFont, QPainter, QPen, QBrush, QFontMetrics # Ajout QFontMetrics

# Import pour lecture fichier et markdown
import markdown 

# Couleurs encore plus affinées - **FOCUS SUR LES FONDS**
DARK_BACKGROUND = "#313335" # Sidebar (moins sombre)
DARK_WIDGET_BACKGROUND = "#2b2b2b" # ContentArea (plus sombre)
DARK_TEXT_COLOR = "#bbbbbb"
DARK_SECONDARY_TEXT_COLOR = "#808080"
DARK_SIDEBAR_TEXT_INACTIVE = "#999999"
DARK_BORDER_COLOR = "#4a4d4f"
ACCENT_COLOR = "#0054b8" # Nouveau bleu demandé
ITEM_HOVER_BACKGROUND = "#45494d"
ITEM_SELECTED_BACKGROUND = "#0054b8" # Nouveau bleu demandé
ACTION_BUTTON_BACKGROUND = "#3c3f41"
ACTION_BUTTON_BORDER = "#3c3f41"
ACTION_BUTTON_HOVER_BORDER = "#606366"
SEARCH_BACKGROUND = "#353739"
SEARCH_BORDER = "#5a5d5e"
BADGE_BACKGROUND = "#6e7072"
BADGE_TEXT = "#d0d0d0"
BADGE_SELECTED_BACKGROUND = "#d5d5d5"
BADGE_SELECTED_TEXT = "#333333"
LOGO_BACKGROUND = "#1c6b9e" # Bleu plus proche du logo Pycharm

# --- Constantes (Ajout couleur pour les "boîtes" de dashboard) ---
BOX_BACKGROUND = ACTION_BUTTON_BACKGROUND # Réutiliser une couleur existante pour les boîtes

# Polices - Essai d'ajustement des tailles relatives
DEFAULT_FONT = QFont("Segoe UI", 9)
SMALL_FONT = QFont("Segoe UI", 8)
SIDEBAR_FONT = QFont("Segoe UI", 9)
SIDEBAR_APPNAME_FONT = QFont("Segoe UI", 9) # Non Gras
SIDEBAR_VERSION_FONT = QFont("Segoe UI", 8)
PROJECT_NAME_FONT = QFont("Segoe UI", 9)
PROJECT_PATH_FONT = QFont("Segoe UI", 8)
SETTINGS_ICON_FONT = QFont("Segoe UI", 12)
LOGO_FONT = QFont("Segoe UI", 9)

# Placeholder pour les données de projets récents
def get_recent_projects_data():
    return [
        {"name": "GDJ", "path": "~/PycharmProjects/GDJ", "icon": "GD"},
        {"name": "GDJ_App", "path": "~/PycharmProjects/GDJ_App", "icon": "GD"},
        {"name": "LiveVision", "path": "~/PycharmProjects/LiveVision", "icon": "LV"},
        {"name": "LiveVision2", "path": "~/PycharmProjects/LiveVision2", "icon": "LV"},
        {"name": "ExpenseReport", "path": "~/PycharmProjects/ExpenseReport", "icon": "ER"},
        {"name": "Py3M6", "path": "~/PycharmProjects/Py3M6", "icon": "PM"},
        {"name": "VSB", "path": "~/PycharmProjects/VSB", "icon": "VS"},
        {"name": "api4robots", "path": "~/PycharmProjects/api4robots", "icon": "A"},
        {"name": "Vision Test", "path": "~/Desktop/Jacmar/Projects/VancouverAutomation/Vision Test", "icon": "VT"},
        {"name": "Vision_AI", "path": "~/PycharmProjects/Vision_AI", "icon": "VA"}
    ]

# --- Classe SimpleToggle --- 
class SimpleToggle(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, checked_color=ACCENT_COLOR, unchecked_color=DARK_SECONDARY_TEXT_COLOR):
        super().__init__(parent)
        self.setFixedSize(50, 22) # Taille ajustée
        self.setCursor(Qt.PointingHandCursor)
        self._checked = False
        self._checked_color = QColor(checked_color)
        self._unchecked_color = QColor(unchecked_color)

    def isChecked(self): 
        return self._checked

    def setChecked(self, checked):
        if self._checked == checked:
            return
        self._checked = checked
        self.toggled.emit(self._checked) 
        self.update() # Redessiner pour refléter le nouvel état

    def toggle(self):
        self.setChecked(not self.isChecked())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        height = self.height()
        width = self.width()
        radius = height / 2
        # Utiliser la division entière // pour garantir un int
        handle_radius = (height - 6) // 2 
        handle_diameter = 2 * handle_radius
        
        # Fond arrondi (identique)
        painter.setPen(Qt.NoPen)
        bg_color = self._checked_color if self._checked else self._unchecked_color
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(self.rect(), radius, radius)
        
        # --- Dessiner la poignée ronde --- 
        painter.setBrush(QBrush(Qt.white)) # Couleur de la poignée
        painter.setPen(Qt.NoPen) # Pas de bordure pour la poignée
        
        # Calculer la position X de la poignée
        padding = 3 # Espace depuis le bord
        handle_x = padding if not self._checked else width - handle_diameter - padding
        
        # Dessiner la poignée (cercle)
        handle_rect = QRect(handle_x, padding, handle_diameter, handle_diameter)
        painter.drawEllipse(handle_rect)
        # --- Fin dessin poignée --- 

# Widget d'icône projet (ajustement taille/radius)
class ProjectIconWidget(QWidget):
    _COLOR_MAP = {
        "GD": "#4CAF50", "LV": "#FFC107", "ER": "#03A9F4", 
        "PM": "#9C27B0", "VS": "#E91E63", "A": "#00BCD4", 
        "VT": "#FF5722", "VA": "#673AB7", "DEFAULT": "#757575" 
    }
    def __init__(self, initials="?", size=26, parent=None): # Légèrement plus petit
        super().__init__(parent)
        self.initials = initials.upper()[:2]
        self.setFixedSize(size, size)
        self.color = QColor(self._COLOR_MAP.get(self.initials, self._COLOR_MAP["DEFAULT"]))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        border_radius = 4 # Plus arrondi comme Pycharm
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), border_radius, border_radius)
        painter.setPen(QPen(Qt.white))
        font = QFont(DEFAULT_FONT)
        font.setBold(True)
        font_size = max(7, int(self.height() * 0.4)) # Police icône plus petite
        font.setPointSize(font_size)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self.initials)

# Widget Item Projet (Correction fond initial)
class ProjectListItemWidget(QWidget):
    def __init__(self, name, path_str, icon_initials="?", list_item=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.path_str = path_str
        self.icon_initials = icon_initials
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 5, 5)
        layout.setSpacing(8)

        icon_widget = ProjectIconWidget(self.icon_initials)
        icon_widget.setAutoFillBackground(False)
        layout.addWidget(icon_widget)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(-2)
        self.name_label = QLabel(name)
        self.name_label.setFont(PROJECT_NAME_FONT)
        self.name_label.setStyleSheet(f"color: {DARK_TEXT_COLOR}; margin-bottom: -2px; background-color: transparent;")
        self.path_label = QLabel(path_str)
        self.path_label.setFont(PROJECT_PATH_FONT)
        self.path_label.setStyleSheet(f"color: {DARK_SECONDARY_TEXT_COLOR}; margin-top: 0px; background-color: transparent;")
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.path_label)
        text_layout.addStretch()

        layout.addLayout(text_layout)
        layout.addStretch(1)
        
        self.options_button = QPushButton("...")
        self.options_button.setObjectName("ItemOptionsButton")
        self.options_button.setFixedSize(20, 20)
        self.options_button.setVisible(False)
        self.options_button.clicked.connect(self._show_context_menu)
        self.options_button.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.options_button, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.setStyleSheet("background-color: transparent;")
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self.options_button.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.options_button.setVisible(False)
        super().leaveEvent(event)

    def _show_context_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {DARK_BACKGROUND}; 
                border: 1px solid #5f6367;
                color: {DARK_TEXT_COLOR};
                padding: 5px;
                border-radius: 4px;
            }}
            QMenu::item {{
                padding: 6px 20px 6px 20px;
                background-color: transparent;
                border-radius: 3px;
            }}
            QMenu::item:selected {{ 
                background-color: {ACCENT_COLOR};
                color: white;
            }}
            QMenu::item:disabled {{
                color: #777777; 
            }}
            QMenu::separator {{
                height: 1px;
                background-color: #5f6367;
                margin: 5px 2px;
            }}
        """)
        
        # --- ACTIONS TRADUITES ET FILTRÉES --- 
        open_action = QAction("Ouvrir la sélection", self)
        open_action.triggered.connect(lambda: print(f"Action: Ouvrir {self.name}"))
        menu.addAction(open_action)

        show_explorer_action = QAction("Afficher dans l'explorateur", self)
        show_explorer_action.triggered.connect(lambda: print(f"Action: Afficher {self.name} dans l'explorateur"))
        menu.addAction(show_explorer_action)

        copy_path_action = QAction("Copier le chemin", self)
        copy_path_action.setShortcut("Ctrl+Shift+C")
        copy_path_action.triggered.connect(lambda: print(f"Action: Copier chemin pour {self.name} ({self.path_str})"))
        menu.addAction(copy_path_action)

        menu.addSeparator()

        remove_action = QAction("Retirer des projets récents...", self)
        remove_action.triggered.connect(lambda: print(f"Action: Retirer {self.name}"))
        menu.addAction(remove_action)
        # --- FIN ACTIONS --- 
        
        button_pos = self.options_button.mapToGlobal(QPoint(0, self.options_button.height()))
        menu.exec_(button_pos)

# --- WelcomePage (MODIFIÉ: Utilisation QStackedWidget) --- 
class WelcomePage(QWidget):
    def __init__(self, controller, app_name="GDJ", version_str="?.?.?"):
        super().__init__()
        self.controller = controller
        self.app_name = app_name
        self.version_str = version_str
        self.setFont(DEFAULT_FONT)
        # Garder références aux pages pour le slot
        self.documents_widget = QWidget()
        self.preferences_widget = QWidget()
        self.about_widget = QWidget()
        self.stacked_widget = QStackedWidget()
        self.init_ui()
        self.apply_dark_theme()
        
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Barre Latérale Gauche (avec QButtonGroup) ---
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(170)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 8, 0, 8)
        sidebar_layout.setSpacing(3)
        
        # Section Logo / Nom / Version (Utilisation des variables)
        logo_section_layout = QHBoxLayout()
        logo_section_layout.setContentsMargins(12, 8, 12, 15)
        logo_section_layout.setSpacing(8)
        
        logo_label = QLabel("PC") # Garder logo générique
        logo_label.setFont(LOGO_FONT)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(32, 32)
        logo_label.setStyleSheet(f"background-color: {LOGO_BACKGROUND}; color: white; border-radius: 5px;")
        logo_section_layout.addWidget(logo_label, 0, Qt.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        
        # Utiliser self.app_name
        app_name_label = QLabel(self.app_name)
        app_name_label.setFont(SIDEBAR_APPNAME_FONT)
        app_name_label.setStyleSheet(f"color: {DARK_TEXT_COLOR}; padding-top: 0px; padding-bottom: 0px; background-color: transparent;")
        
        # Utiliser self.version_str
        version_label = QLabel(self.version_str)
        version_label.setFont(SIDEBAR_VERSION_FONT)
        version_label.setStyleSheet(f"color: {DARK_SECONDARY_TEXT_COLOR}; padding-top: 0px; background-color: transparent;")
        
        text_layout.addWidget(app_name_label)
        text_layout.addWidget(version_label)
        # text_layout.addStretch() # Pas de stretch
        
        logo_section_layout.addLayout(text_layout, 0)
        logo_section_layout.addStretch()
        sidebar_layout.addLayout(logo_section_layout)

        # Boutons de navigation + QButtonGroup
        self.sidebar_button_group = QButtonGroup(self) # Créer le groupe
        self.sidebar_button_group.setExclusive(True) # Assurer l'exclusivité
        
        button_layout = QVBoxLayout()
        button_layout.setSpacing(1)
        button_layout.setContentsMargins(5, 0, 5, 0)
        button_info = {"Documents": True, "Preference": False, "A Propos": False}
        for name, checked in button_info.items():
            btn_container = QFrame()
            btn_container.setObjectName("SidebarButtonContainer")
            # Définir la propriété 'checked' initiale pour le QSS
            btn_container.setProperty("checked", checked)
            
            btn_hbox = QHBoxLayout(btn_container)
            btn_hbox.setContentsMargins(8, 6, 8, 6)
            btn_hbox.setSpacing(5)
            
            btn = QPushButton(name)
            btn.setObjectName("SidebarButton")
            btn.setCheckable(True)
            btn.setChecked(checked) # L'état logique est géré par QButtonGroup
            btn.setFont(SIDEBAR_FONT)
            btn_hbox.addWidget(btn, 1)
            
            self.sidebar_button_group.addButton(btn)
            
            # Placeholder pour alignement
            placeholder = QSpacerItem(16, 16, QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn_hbox.addSpacerItem(placeholder)
                 
            button_layout.addWidget(btn_container)
            # Rétablir la connexion pour que le style QSS suive l'état du bouton
            # Connecter toggled du bouton pour mettre à jour la propriété du conteneur
            # ET forcer la réévaluation du style
            btn.toggled.connect(
                lambda state, c=btn_container: (
                    c.setProperty("checked", state), 
                    c.style().unpolish(c), # Forcer la suppression de l'ancien style
                    c.style().polish(c)   # Forcer l'application du nouveau style
                )
            )
            
        sidebar_layout.addLayout(button_layout)
        sidebar_layout.addStretch()

        # Connecter le clic du groupe au slot de changement de page
        # Note: buttonClicked émet le bouton cliqué
        self.sidebar_button_group.buttonClicked.connect(self._change_page)

        # Bouton Settings
        settings_layout = QHBoxLayout()
        settings_layout.setContentsMargins(12, 0, 12, 5)
        btn_settings = QPushButton("⚙")
        btn_settings.setFont(SETTINGS_ICON_FONT)
        btn_settings.setObjectName("SettingsButton")
        btn_settings.setFixedSize(26, 26)
        settings_layout.addWidget(btn_settings)
        settings_layout.addStretch()
        sidebar_layout.addLayout(settings_layout)
        main_layout.addWidget(sidebar)

        # --- Zone de Contenu Principale (QStackedWidget) ---
        self.stacked_widget.setObjectName("ContentArea")

        # --- Page 1: Documents (MODIFIÉ: Contient son propre QStackedWidget) --- 
        self.documents_widget = QWidget() 
        page_documents_layout = QVBoxLayout(self.documents_widget)
        page_documents_layout.setContentsMargins(0, 0, 0, 0) # Pas de marge externe pour le stack
        page_documents_layout.setSpacing(0)

        # Créer le QStackedWidget *interne* à la page Documents
        self.documents_stack = QStackedWidget()
        # self.documents_stack.setObjectName("DocumentsStack") # Optionnel

        # --- Page 1.1: Liste des Documents (MODIFIÉ: 2 QFrames) ---
        self.documents_list_page = QWidget()
        list_page_layout = QVBoxLayout(self.documents_list_page)
        list_page_layout.setContentsMargins(10, 10, 10, 10)
        list_page_layout.setSpacing(10) # Espace entre les 2 QFrames
        
        # --- Première boîte QFrame (Recherche et boutons) ---
        top_doc_box = QFrame() # Anciennement documents_box
        top_doc_box.setObjectName("DashboardBox")
        top_doc_box.setMinimumWidth(400)
        # Layout intérieur pour la première boîte
        top_doc_box_layout = QVBoxLayout(top_doc_box) 
        top_doc_box_layout.setContentsMargins(15, 8, 15, 10)
        top_doc_box_layout.setSpacing(10)
        
        # Barre Supérieure (recherche + boutons) - Reste ici
        top_bar_layout = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText("Recherche de documents")
        search_input.setObjectName("SearchInput")
        search_input.setFixedHeight(26)
        top_bar_layout.addWidget(search_input, 1)
        # Bouton Ouvrir (reste ici)
        btn_open = QPushButton("Ouvrir")
        btn_open.setObjectName("TopNavButton") # <- Changer objectName
        btn_open.setFixedHeight(26)
        btn_open.setFont(DEFAULT_FONT)
        btn_open.clicked.connect(self.controller.open_document) 
        # Bouton Nouveau (connecté pour changer de page interne)
        btn_new = QPushButton("Nouveau")
        btn_new.setObjectName("TopNavButton") # <- Changer objectName
        btn_new.setFixedHeight(26)
        btn_new.setFont(DEFAULT_FONT)
        btn_new.clicked.connect(self._show_new_document_page) 
        top_bar_layout.addWidget(btn_new)
        top_bar_layout.addWidget(btn_open)
        # Ajouter la top bar au layout de la première boîte
        top_doc_box_layout.addLayout(top_bar_layout)
        # NE PAS ajouter de stretch ici pour que la boîte prenne sa taille naturelle

        # Ajouter la première boîte au layout principal de la page
        list_page_layout.addWidget(top_doc_box) # Pas de stretch vertical

        # --- Deuxième boîte QFrame (Liste des projets) ---
        list_doc_box = QFrame()
        list_doc_box.setObjectName("DashboardBox")
        list_doc_box.setMinimumWidth(400)
        # Layout intérieur pour la deuxième boîte
        list_doc_box_layout = QVBoxLayout(list_doc_box)
        list_doc_box_layout.setContentsMargins(5, 5, 5, 5) # Marges réduites pour la liste
        list_doc_box_layout.setSpacing(0)
        
        # Liste des Projets Récents (Déplacée ici)
        self.recent_list_widget = QListWidget()
        self.recent_list_widget.setObjectName("ProjectList")
        # ... (Configuration QListWidget: scrollbars, focus policy) ...
        self.recent_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.recent_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.recent_list_widget.setFocusPolicy(Qt.NoFocus)
        # Peuplement (identique)
        projects = get_recent_projects_data()
        if projects: # ... peuplement ...
             for project_data in projects:
                item = QListWidgetItem(self.recent_list_widget)
                # Recréation complète pour éviter problème de référence
                item_widget = ProjectListItemWidget(
                    project_data["name"],
                    project_data["path"],
                    project_data.get("icon", "?")
                )
                item.setSizeHint(item_widget.sizeHint())
                self.recent_list_widget.addItem(item)
                self.recent_list_widget.setItemWidget(item, item_widget)
        self.recent_list_widget.itemDoubleClicked.connect(self.on_recent_item_activated)
        
        # Ajouter la liste au layout de la deuxième boîte (AVEC stretch)
        list_doc_box_layout.addWidget(self.recent_list_widget, 1)
        
        # Ajouter la deuxième boîte au layout principal de la page (AVEC stretch vertical)
        list_page_layout.addWidget(list_doc_box, 1)
        
        # Ajouter la page liste (maintenant avec 2 boîtes) au stack interne
        self.documents_stack.addWidget(self.documents_list_page)

        # --- Page 1.2: Nouvelle Page Document (MODIFIÉ: Contenu dans DashboardBox) ---
        self.documents_new_page = QWidget()
        # Layout principal pour cette page (pour contenir la box)
        new_page_container_layout = QVBoxLayout(self.documents_new_page)
        new_page_container_layout.setContentsMargins(10, 10, 10, 10)
        new_page_container_layout.setSpacing(10)

        # Créer la première boîte QFrame
        new_doc_box = QFrame()
        new_doc_box.setObjectName("DashboardBox")
        new_doc_box.setMinimumWidth(400) # Garder largeur min cohérente
        
        # Layout *intérieur* de la boîte
        new_doc_box_layout = QVBoxLayout(new_doc_box)
        new_doc_box_layout.setContentsMargins(15, 8, 15, 10) # Marges internes
        new_doc_box_layout.setSpacing(10)

        # Bouton Retour (créé mais PAS ajouté ici)
        btn_back_to_list = QPushButton("Retour") 
        btn_back_to_list.setObjectName("ActionButton")
        btn_back_to_list.setFixedWidth(80) 
        btn_back_to_list.clicked.connect(self._show_document_list_page)
        
        # --- Contenu Formulaire --- 
        new_doc_form_layout = QFormLayout()
        new_doc_form_layout.setContentsMargins(0, 5, 0, 5) # Ajuster marges internes si besoin
        new_doc_form_layout.setSpacing(10)
        new_doc_form_layout.setVerticalSpacing(12)
        
        label_doc_type = QLabel("Document:")
        label_doc_type.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        cb_new_doc_type = QComboBox()
        cb_new_doc_type.addItems(["Document Standard", "Rapport Mensuel", "Présentation Client", "Autre..."])
        # Appliquer style QComboBox si nécessaire (hérité via #PreferencesPage?)
        # Mieux vaut cibler plus spécifiquement
        # cb_new_doc_type.setStyleSheet(f"...") 
        new_doc_form_layout.addRow(label_doc_type, cb_new_doc_type)

        # Ajouter le formulaire au layout intérieur de la boîte
        new_doc_box_layout.addLayout(new_doc_form_layout)
        new_doc_box_layout.addStretch(1) # Ajouter un stretch pour pousser le formulaire vers le haut
        # --- Fin Contenu Formulaire --- 

        # Ajouter la première boîte au layout principal de la page (SANS étirement vertical)
        new_page_container_layout.addWidget(new_doc_box, 0) # <- Stretch factor 0
        
        # --- Création et ajout de la deuxième boîte --- 
        second_new_doc_box = QFrame()
        second_new_doc_box.setObjectName("DashboardBox")
        second_new_doc_box.setMinimumWidth(400)
        
        second_new_doc_box_layout = QVBoxLayout(second_new_doc_box)
        second_new_doc_box_layout.setContentsMargins(15, 8, 15, 10)
        second_new_doc_box_layout.setSpacing(10)
        
        placeholder_label_2 = QLabel("Contenu du deuxième QFrame ici...")
        placeholder_label_2.setAlignment(Qt.AlignCenter)
        second_new_doc_box_layout.addWidget(placeholder_label_2, 1) # Donner stretch au placeholder
        
        # Ajouter la deuxième boîte au layout principal (AVEC étirement vertical)
        new_page_container_layout.addWidget(second_new_doc_box, 1) # <- Stretch factor 1 (inchangé, mais explicite)
        # --- Fin deuxième boîte --- 

        # Ajouter le bouton Retour au layout principal (en bas à gauche)
        new_page_container_layout.addWidget(btn_back_to_list, 0, Qt.AlignBottom | Qt.AlignLeft)

        # Ajouter la nouvelle page (contenant la box et le bouton) au stack interne
        self.documents_stack.addWidget(self.documents_new_page)

        # Ajouter le stack interne au layout principal de l'onglet Documents
        page_documents_layout.addWidget(self.documents_stack)
        
        # Ajouter la page Documents (contenant le stack interne) au StackedWidget principal
        self.stacked_widget.addWidget(self.documents_widget)

        # --- Page 2: Préférences (Structure et contenu identiques) --- 
        self.preferences_widget = QWidget()
        prefs_main_layout = QGridLayout(self.preferences_widget)
        prefs_main_layout.setSpacing(15)
        prefs_main_layout.setContentsMargins(10, 10, 10, 10)

        # Garder une référence au label image
        self.signature_image_label = None 
        
        # Section "Mon profile"
        profile_box, box_content_layout_prof = self._create_dashboard_box("Mon profile") 
        profile_form_layout = QFormLayout() 
        profile_form_layout.setContentsMargins(15, 10, 15, 15) 
        profile_form_layout.setSpacing(10)
        profile_form_layout.setVerticalSpacing(12)
        
        # Créer et styler les labels directement (Nouvel essai)
        label_nom = QLabel("Nom:")
        label_nom.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        profile_form_layout.addRow(label_nom, QLineEdit(placeholderText="Entrez votre nom"))
        
        label_prenom = QLabel("Prénom:")
        label_prenom.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        profile_form_layout.addRow(label_prenom, QLineEdit(placeholderText="Entrez votre prénom"))
        
        label_tel = QLabel("Numéro de téléphone:")
        label_tel.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        profile_form_layout.addRow(label_tel, QLineEdit(placeholderText="XXX-XXX-XXXX"))
        
        label_courriel = QLabel("Courriel:")
        label_courriel.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        profile_form_layout.addRow(label_courriel, QLineEdit(placeholderText="nom@example.com"))
        
        # --- Ligne Signature --- 
        label_signature = QLabel("Signature Numerique:")
        label_signature.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        
        # Conteneur pour bouton + et image
        signature_widget_container = QWidget()
        signature_widget_container.setStyleSheet("background: transparent;")
        signature_layout = QHBoxLayout(signature_widget_container)
        signature_layout.setContentsMargins(0, 0, 0, 0)
        signature_layout.setSpacing(5) # Espace entre bouton et image

        btn_plus_signature = QPushButton("+")
        btn_plus_signature.setObjectName("PlusButton")
        btn_plus_signature.setFixedSize(24, 24)
        btn_plus_signature.clicked.connect(self._select_signature_image) # Connecter le slot

        # Label pour afficher l'image
        self.signature_image_label = QLabel()
        self.signature_image_label.setMinimumHeight(24) # Définir hauteur minimale
        # Supprimer la bordure et le fond du style
        self.signature_image_label.setStyleSheet("background: transparent;") # Rendre complètement transparent
        self.signature_image_label.setAlignment(Qt.AlignCenter)
        self.signature_image_label.setText("...") # Placeholder texte

        signature_layout.addWidget(btn_plus_signature)         
        signature_layout.addWidget(self.signature_image_label, 1) # Ajouter label image avec stretch factor 1
        # signature_layout.addStretch(1) # Supprimer le stretch final
        
        profile_form_layout.addRow(label_signature, signature_widget_container) # Ajouter la ligne au formulaire
        # --- Fin Ligne Signature --- 
        
        box_content_layout_prof.addLayout(profile_form_layout) 
        box_content_layout_prof.addStretch(1)
        profile_box.setLayout(box_content_layout_prof)
        prefs_main_layout.addWidget(profile_box, 0, 0)

        # Section "Jacmar"
        jacmar_box, box_content_layout_jac = self._create_dashboard_box("Jacmar")
        jacmar_form_layout = QFormLayout()
        jacmar_form_layout.setContentsMargins(15, 10, 15, 15)
        jacmar_form_layout.setSpacing(10)
        jacmar_form_layout.setVerticalSpacing(12)
        
        # Créer et styler les labels directement (Nouvel essai)
        cb_emplacement = QComboBox(); cb_emplacement.addItems(["Jacmar", "Autre..."])
        label_emplacement = QLabel("Emplacement:")
        label_emplacement.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        jacmar_form_layout.addRow(label_emplacement, cb_emplacement)
        
        cb_dept = QComboBox(); cb_dept.addItems(["Ingénierie", "Production", "Ventes", "..."])
        label_dept = QLabel("Département:")
        label_dept.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        jacmar_form_layout.addRow(label_dept, cb_dept)
        
        cb_titre = QComboBox(); cb_titre.addItems(["Chargé de projet", "Technicien", "Directeur", "..."])
        label_titre = QLabel("Titre:")
        label_titre.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        jacmar_form_layout.addRow(label_titre, cb_titre)
        
        cb_super = QComboBox(); cb_super.addItems(["Personne A", "Personne B", "..."])
        label_super = QLabel("Superviseur:")
        label_super.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        jacmar_form_layout.addRow(label_super, cb_super)
        
        cb_plafond = QComboBox(); cb_plafond.addItems(["Standard", "Élevé", "Aucun", "..."])
        label_plafond = QLabel("Plafond de déplacement:")
        label_plafond.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        jacmar_form_layout.addRow(label_plafond, cb_plafond)
        
        box_content_layout_jac.addLayout(jacmar_form_layout)
        box_content_layout_jac.addStretch(1)
        prefs_main_layout.addWidget(jacmar_box, 0, 1)

        # Section "Application"
        app_box, box_content_layout_app = self._create_dashboard_box("Application")
        app_form_layout = QFormLayout()
        app_form_layout.setContentsMargins(15, 10, 15, 15)
        app_form_layout.setSpacing(10)
        app_form_layout.setVerticalSpacing(12)
        
        # Champ Thème (identique)
        cb_theme = QComboBox(); cb_theme.addItems(["Sombre (Défaut)", "Clair", "Système"]) 
        label_theme = QLabel("Thème:")
        label_theme.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        app_form_layout.addRow(label_theme, cb_theme)

        # --- Remplacement par SimpleToggle --- 
        label_auto_update = QLabel("Mise a jour automatique:")
        label_auto_update.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        toggle_auto_update = SimpleToggle()
        # Créer un conteneur et un layout pour centrer le toggle
        toggle_container_auto = QWidget()
        toggle_container_auto.setStyleSheet("background: transparent;")
        toggle_layout_auto = QHBoxLayout(toggle_container_auto)
        toggle_layout_auto.setContentsMargins(0, 0, 0, 0)
        toggle_layout_auto.addWidget(toggle_auto_update, 0, Qt.AlignLeft | Qt.AlignVCenter)
        toggle_layout_auto.addStretch(1)
        app_form_layout.addRow(label_auto_update, toggle_container_auto)

        label_show_notes = QLabel("Afficher la note de version:")
        label_show_notes.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        toggle_show_notes = SimpleToggle()
        # Créer un conteneur et un layout pour centrer le toggle
        toggle_container_notes = QWidget()
        toggle_container_notes.setStyleSheet("background: transparent;")
        toggle_layout_notes = QHBoxLayout(toggle_container_notes)
        toggle_layout_notes.setContentsMargins(0, 0, 0, 0)
        toggle_layout_notes.addWidget(toggle_show_notes, 0, Qt.AlignLeft | Qt.AlignVCenter)
        app_form_layout.addRow(label_show_notes, toggle_container_notes)
        # --- Fin Remplacement --- 
        
        box_content_layout_app.addLayout(app_form_layout)
        box_content_layout_app.addStretch(1)
        prefs_main_layout.addWidget(app_box, 1, 0)

        # Section "Gestion des preferences"
        mgmt_box, box_content_layout_mgmt = self._create_dashboard_box("Gestion des preferences") 

        # Layout pour les préférences (Formulaire)
        prefs_form_layout = QFormLayout()
        prefs_form_layout.setContentsMargins(15, 10, 15, 15) 
        prefs_form_layout.setSpacing(10)
        prefs_form_layout.setVerticalSpacing(12)

        # --- Ligne Exporter ---
        label_export = QLabel("Exporter:")
        label_export.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        btn_export = QPushButton("Exporter")
        btn_export.setObjectName("FormButton")
        # btn_export.clicked.connect(self.controller.export_preferences)
        prefs_form_layout.addRow(label_export, btn_export)

        # --- Ligne Importer ---
        label_import = QLabel("Importer:")
        label_import.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        btn_import = QPushButton("Importer")
        btn_import.setObjectName("FormButton") 
        # btn_import.clicked.connect(self.controller.import_preferences)
        prefs_form_layout.addRow(label_import, btn_import)

        # --- Ligne Sauvegarder ---
        label_save = QLabel("Sauvegarder:")
        label_save.setStyleSheet(f"background: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; min-height: 20px; padding: 4px 0px;")
        btn_save = QPushButton("Sauvegarder")
        btn_save.setObjectName("FormButton") 
        # btn_save.clicked.connect(self.controller.save_preferences)
        prefs_form_layout.addRow(label_save, btn_save)

        box_content_layout_mgmt.addLayout(prefs_form_layout) # Ajouter layout formulaire
        box_content_layout_mgmt.addStretch(1)
        prefs_main_layout.addWidget(mgmt_box, 1, 1)

        # Ajuster les spacers pour l'équilibre
        prefs_main_layout.setRowStretch(2, 1) # Étirer la ligne sous les boîtes
        prefs_main_layout.setColumnStretch(2, 1) # Étirer la colonne à droite
        # Supprimer les anciens spacers si la grille est pleine
        # prefs_main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), 2, 0) 
        # prefs_main_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 2) 

        self.stacked_widget.addWidget(self.preferences_widget)

        # --- Page 3: A Propos (RE-RE-MODIFIÉ: Devient QStackedWidget) ---
        self.about_widget = QWidget()
        about_page_container_layout = QVBoxLayout(self.about_widget)
        about_page_container_layout.setContentsMargins(10, 10, 10, 10)
        about_page_container_layout.setSpacing(10) # Espace entre stack et bouton

        # Créer le QStackedWidget interne
        self.about_stack = QStackedWidget()

        # --- Page 3.1: README --- 
        self.about_readme_page = QWidget()
        readme_page_layout = QVBoxLayout(self.about_readme_page)
        readme_page_layout.setContentsMargins(0,0,0,0) # Pas de marge pour que QFrame remplisse
        readme_page_layout.setSpacing(0)
        
        about_box = QFrame() # La QFrame pour le contenu README
        about_box.setObjectName("DashboardBox")
        about_box.setMinimumWidth(400)
        about_box_layout = QVBoxLayout(about_box)
        about_box_layout.setContentsMargins(15, 8, 15, 10)
        about_box_layout.setSpacing(10)
        self.readme_display = QTextBrowser()
        self.readme_display.setReadOnly(True)
        self.readme_display.setObjectName("ReadmeBrowser")
        self.readme_display.setOpenExternalLinks(True)
        readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
        html_content = "<p>Chargement...</p>"
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
                html_content = markdown.markdown(markdown_content, extensions=['fenced_code', 'tables', 'nl2br'])
        except FileNotFoundError: html_content = "<p style='color: red;'>Erreur : README.md introuvable.</p>"; print(f"Erreur: README non trouvé à {os.path.abspath(readme_path)}")
        except ImportError: html_content = "<p style='color: red;'>Erreur : Bibliothèque 'markdown' non installée...</p>"; print("Erreur: Bibliothèque 'markdown' non installée.")
        except Exception as e: html_content = f"<p style='color: red;'>Erreur README : {e}</p>"; print(f"Erreur README: {e}")
        self.readme_display.setHtml(html_content)
        about_box_layout.addWidget(self.readme_display, 1)
        readme_page_layout.addWidget(about_box) # Ajouter la QFrame au layout de la page
        self.about_stack.addWidget(self.about_readme_page) # Ajouter la page au stack

        # --- Page 3.2: Notes de Version --- 
        self.about_notes_page = QWidget()
        notes_page_layout = QVBoxLayout(self.about_notes_page)
        notes_page_layout.setContentsMargins(0,0,0,0) # Pas de marge pour que QFrame remplisse
        notes_page_layout.setSpacing(0)
        
        notes_box = QFrame() # La QFrame pour le contenu Notes
        notes_box.setObjectName("DashboardBox")
        notes_box.setMinimumWidth(400)
        notes_box_layout = QVBoxLayout(notes_box)
        notes_box_layout.setContentsMargins(15, 8, 15, 10)
        notes_box_layout.setSpacing(10)
        
        btn_back_to_readme = QPushButton("Retour") # Créer le bouton Retour
        btn_back_to_readme.setObjectName("ActionButton")
        btn_back_to_readme.setFixedWidth(80)
        btn_back_to_readme.clicked.connect(self._show_about_readme_page) # Connecter retour
        notes_box_layout.addWidget(btn_back_to_readme, 0, Qt.AlignLeft)
        
        self.notes_display = QTextBrowser() # QTextBrowser DANS la QFrame
        self.notes_display.setReadOnly(True)
        self.notes_display.setObjectName("NotesBrowser")
        notes_path = os.path.join(os.path.dirname(__file__), '..', 'RELEASE_NOTES.md')
        notes_html_content = ""
        try:
            with open(notes_path, 'r', encoding='utf-8') as f:
                 notes_markdown_content = f.read()
                 notes_html_content = markdown.markdown(notes_markdown_content, extensions=['fenced_code', 'tables', 'nl2br'])
        except FileNotFoundError: notes_html_content = "<p style='color: red;'>Erreur : RELEASE_NOTES.md introuvable.</p>"; print(f"Erreur: Fichier RELEASE_NOTES non trouvé à {os.path.abspath(notes_path)}")
        except ImportError: notes_html_content = "<p style='color: red;'>Erreur : Bibliothèque 'markdown' non installée.</p>"; print("Erreur: Bibliothèque 'markdown' non installée.")
        except Exception as e: notes_html_content = f"<p style='color: red;'>Erreur lors de la lecture ou conversion de RELEASE_NOTES : {e}</p>"; print(f"Erreur RELEASE_NOTES: {e}")
        self.notes_display.setHtml(notes_html_content)
        notes_box_layout.addWidget(self.notes_display, 1)
        
        notes_page_layout.addWidget(notes_box, 1) # Ajouter la QFrame au layout de la page (avec stretch)
        self.about_stack.addWidget(self.about_notes_page) # Ajouter la page au stack
        
        # Ajouter le bouton Retour au layout PRINCIPAL de la page Notes, en bas à gauche
        notes_page_layout.addWidget(btn_back_to_readme, 0, Qt.AlignBottom | Qt.AlignLeft)

        # --- Assemblage final Page A Propos ---
        # Ajouter le stack interne au layout principal de l'onglet
        about_page_container_layout.addWidget(self.about_stack, 1) # Donner stretch au stack

        # Ajouter le bouton "Note de version" en bas à droite
        self.btn_release_notes = QPushButton("Note de version") # <- self. ajouté
        self.btn_release_notes.setObjectName("ActionButton")
        self.btn_release_notes.clicked.connect(self._show_release_notes_page) # Connecter aller
        about_page_container_layout.addWidget(self.btn_release_notes, 0, Qt.AlignBottom | Qt.AlignRight)

        # Ajouter la page A Propos globale au StackedWidget principal
        self.stacked_widget.addWidget(self.about_widget)
        
        # --- Ajout du StackedWidget au layout principal (vérifié présent) --- 
        main_layout.addWidget(self.stacked_widget, 1) 

        # Titre fenêtre 
        self.setWindowTitle(f"Bienvenue dans {self.app_name}") 
        self.setMinimumSize(1000, 700)

    def _create_dashboard_box(self, title):
        """ Helper CORRIGÉ: Crée boîte, layout interne, titre et retourne boîte + layout interne. """
        box = QFrame()
        box.setObjectName("DashboardBox")
        box.setFrameShape(QFrame.StyledPanel)
        box.setMinimumWidth(400) # Définir une largeur minimale
        
        # Créer et définir le layout interne
        internal_layout = QVBoxLayout()
        internal_layout.setContentsMargins(0, 0, 0, 0)
        internal_layout.setSpacing(0)
        box.setLayout(internal_layout)

        title_label = QLabel(title)
        title_label.setObjectName("DashboardBoxTitle") 
        internal_layout.addWidget(title_label) # Ajouter titre au layout interne
        
        # Retourner la boîte ET le layout interne
        return box, internal_layout 

    def _change_page(self, button):
        """ Slot appelé quand un bouton de la sidebar est cliqué. """
        text = button.text()
        print(f"Changing page to: {text}") # Debug
        if text == "Documents":
            self.stacked_widget.setCurrentWidget(self.documents_widget)
            if hasattr(self, 'documents_stack'): 
                self.documents_stack.setCurrentWidget(self.documents_list_page)
        elif text == "Preference":
            self.stacked_widget.setCurrentWidget(self.preferences_widget)
        elif text == "A Propos":
            self.stacked_widget.setCurrentWidget(self.about_widget)
            # Réinitialiser le stack interne de "A Propos" à la page README
            if hasattr(self, 'about_stack') and hasattr(self, 'about_readme_page'): 
                self.about_stack.setCurrentWidget(self.about_readme_page)
            if hasattr(self, 'btn_release_notes'):
                self.btn_release_notes.setVisible(True) 
        else:
            # Cas par défaut
            self.stacked_widget.setCurrentIndex(0) 
            if hasattr(self, 'documents_stack'):
                self.documents_stack.setCurrentWidget(self.documents_list_page)
            if hasattr(self, 'about_stack') and hasattr(self, 'about_readme_page'):
                 self.about_stack.setCurrentWidget(self.about_readme_page)
                 if hasattr(self, 'btn_release_notes'): # Assurer visibilité bouton par défaut aussi
                     self.btn_release_notes.setVisible(True)

    def apply_dark_theme(self):
        # Styles restaurés + ajout hauteur fixe pour titres
        stylesheet = f"""
            QWidget {{ 
                color: {DARK_TEXT_COLOR};
                background-color: {DARK_WIDGET_BACKGROUND};
                font-family: \"Segoe UI\";
                font-size: 9pt;
                border: none;
            }}
            #Sidebar {{ background-color: {DARK_BACKGROUND}; }}
            /* ... Styles Barre Latérale (Boutons, Conteneurs, Badge, Settings) ... */
            QFrame#SidebarButtonContainer {{ background-color: transparent; border-radius: 4px; }}
            QFrame#SidebarButtonContainer:hover {{ background-color: {ITEM_HOVER_BACKGROUND}; }}
            QFrame#SidebarButtonContainer[checked="true"] {{ background-color: {ACCENT_COLOR}; }}
            QPushButton#SidebarButton {{ background-color: transparent; color: {DARK_SIDEBAR_TEXT_INACTIVE}; border: none; padding: 0px; text-align: left; }}
            QPushButton#SidebarButton:checked {{ color: white; font-weight: normal; }}
            QFrame#SidebarButtonContainer:hover QPushButton#SidebarButton:!checked {{ color: {DARK_TEXT_COLOR}; }}
            /* ... (Badge, SettingsButton styles) ... */
            QLabel#SidebarBadge {{ background-color: {BADGE_BACKGROUND}; color: {BADGE_TEXT}; border-radius: 8px; font-size: 7pt; font-weight: bold; min-width: 16px; max-width: 16px; min-height: 16px; max-height: 16px; padding: 1px 0px 0px 0px; }}
            QFrame#SidebarButtonContainer[checked="true"] QLabel#SidebarBadge {{ background-color: {BADGE_SELECTED_BACKGROUND}; color: {BADGE_SELECTED_TEXT}; }}
            QPushButton#SettingsButton {{ background-color: transparent; border: none; color: {DARK_SECONDARY_TEXT_COLOR}; padding: 0px; border-radius: 4px; }}
            QPushButton#SettingsButton:hover {{ background-color: {ITEM_HOVER_BACKGROUND}; }}

            #ContentArea {{
                background-color: {DARK_WIDGET_BACKGROUND};
                border-left: 1px solid {DARK_BACKGROUND};
            }}
            #ContentArea > QWidget {{ background-color: {DARK_WIDGET_BACKGROUND}; }}

            /* --- Style DashboardBox GÉNÉRALISÉ --- */
            /* Appliquer aux QFrame nommées DashboardBox DANS ContentArea */
            #ContentArea QFrame#DashboardBox {{
                background-color: {BOX_BACKGROUND};
                border-radius: 6px;
                /* margin: 5px; Retiré pour l'instant, géré par layout parent si besoin */
            }}
            
            /* --- Styles SPÉCIFIQUES Page Préférences --- */
            #ContentArea QFrame#DashboardBoxTitle {{ 
                 /* Style titre (hauteur fixe, etc.) */
                color: {DARK_TEXT_COLOR};
                font-weight: bold;
                font-size: 10pt;
                padding: 8px 0px 8px 15px;
                border-bottom: 1px solid {DARK_BORDER_COLOR};
                margin-bottom: 5px; 
                background-color: transparent; 
                min-height: 25px; 
                max-height: 25px; 
            }}
            /* Règle labels QFormLayout (laissée telle quelle, style direct prioritaire) */
            #ContentArea QFrame#DashboardBox QFormLayout QLabel {{
                 /* Style labels formulaire préférences (style direct prioritaire) */
                color: {DARK_SECONDARY_TEXT_COLOR};
                font-size: 9pt;
                background: transparent; 
                border: none; 
                padding: 4px 0px; 
                min-height: 20px;
            }}
            /* Style GÉNÉRALISÉ pour QLineEdit/QComboBox dans les boîtes */
            #ContentArea QFrame#DashboardBox QLineEdit, 
            #ContentArea QFrame#DashboardBox QComboBox {{
                background-color: {SEARCH_BACKGROUND};
                border: 1px solid {SEARCH_BORDER};
                border-radius: 4px;
                padding: 4px 6px;
                color: {DARK_TEXT_COLOR};
                min-height: 20px;
            }}
            #ContentArea QFrame#DashboardBox QLineEdit:focus, 
            #ContentArea QFrame#DashboardBox QComboBox:focus {{ 
                 border: 1px solid {ACCENT_COLOR};
            }}
            #ContentArea QFrame#DashboardBox QLineEdit::placeholder {{
                 color: {DARK_SECONDARY_TEXT_COLOR};
             }}
            /* Styles spécifiques QComboBox GÉNÉRALISÉS */
            #ContentArea QFrame#DashboardBox QComboBox::drop-down {{
                 border: none; 
                 subcontrol-origin: padding;
                 subcontrol-position: top right;
                 width: 15px;
            }}
            #ContentArea QFrame#DashboardBox QComboBox::down-arrow {{
                 width: 10px; 
                 height: 10px;
            }}
            #ContentArea QFrame#DashboardBox QComboBox QAbstractItemView {{
                 background-color: {ITEM_HOVER_BACKGROUND};
                 border: 1px solid {DARK_BORDER_COLOR};
                 selection-background-color: {ACCENT_COLOR};
                 color: {DARK_TEXT_COLOR};
                 padding: 2px;
            }}

            /* --- Autres styles --- */
            /* Style Liste Projets Récent (doit rester avec BOX_BACKGROUND) */
            #ProjectList {{
                background-color: {BOX_BACKGROUND}; 
                border: none;
            }}
            #ProjectList::item {{ border: none; padding: 0px; margin: 0px; background-color: transparent; color: transparent; }}
            #ProjectList::item:hover {{ background-color: {ITEM_SELECTED_BACKGROUND}; border-radius: 4px; }}
            #ProjectList::item:selected {{ background-color: {ITEM_SELECTED_BACKGROUND}; border-radius: 4px; }}
            
            QPushButton#ItemOptionsButton {{ background-color: transparent; color: {DARK_SECONDARY_TEXT_COLOR}; border: none; border-radius: 3px; font-weight: bold; padding: 0px 0px 2px 0px; }}
            QPushButton#ItemOptionsButton:hover {{ background-color: #5a5e61; color: {DARK_TEXT_COLOR}; }}
            
            /* Style Scrollbar (doit rester avec BOX_BACKGROUND) */
            QScrollBar:vertical {{
                border: none;
                background: {BOX_BACKGROUND}; 
                width: 14px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #5c5f61;
                min-height: 30px;
                border-radius: 7px;
                border: none;
            }}
            QScrollBar::handle:vertical:hover {{ background: #6c6f71; }}
            QScrollBar::handle:vertical:pressed {{ background: #7c7f81; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

            /* --- Nouveau style pour les boutons dans le formulaire --- */
            QPushButton#FormButton {{
                background-color: {ACTION_BUTTON_BACKGROUND};
                border: 1px solid {ACTION_BUTTON_BORDER};
                color: {DARK_TEXT_COLOR};
                padding: 3px 8px; /* Ajuster padding */
                border-radius: 4px;
                /* min-height: 20px; La taille fixe est définie dans init_ui */
                text-align: center;
            }}
            QPushButton#FormButton:hover {{
                background-color: #565a5e;
                border: 1px solid {ACTION_BUTTON_HOVER_BORDER};
            }}
            QPushButton#FormButton:pressed {{
                background-color: #606468;
            }}
            /* --- Fin nouveau style --- */

            /* --- Style pour le bouton Plus --- */
            QPushButton#PlusButton {{
                background-color: {ACTION_BUTTON_BACKGROUND};
                border: 1px solid {ACTION_BUTTON_BORDER};
                color: {DARK_TEXT_COLOR};
                border-radius: 4px; /* Ou 12px pour rond */
                font-weight: bold;
                padding: 0px; /* Ajuster si nécessaire pour centrer le + */
            }}
            QPushButton#PlusButton:hover {{
                background-color: #565a5e;
                border: 1px solid {ACTION_BUTTON_HOVER_BORDER};
            }}
            QPushButton#PlusButton:pressed {{
                background-color: #606468;
            }}
            /* --- Fin Style bouton Plus --- */

            /* --- Nouveau style pour boutons Nouveau/Ouvrir (type nav) --- */
            QPushButton#TopNavButton {{
                background-color: transparent;
                border: none;
                color: {DARK_TEXT_COLOR};
                padding: 4px 10px;
                border-radius: 4px;
                text-align: center;
            }}
            QPushButton#TopNavButton:hover {{
                background-color: {ACCENT_COLOR};
                color: white;
            }}
            QPushButton#TopNavButton:pressed {{
                background-color: #003d82;
            }}
            /* --- Fin nouveau style --- */

            /* --- Style pour le QTextBrowser du README (dans sa QFrame) --- */
            #ContentArea QFrame#DashboardBox QTextBrowser#ReadmeBrowser {{
                background-color: transparent;
                border: none;
                color: {DARK_TEXT_COLOR}; /* Couleur texte par défaut */
                /* Les styles spécifiques (h1, code, etc.) peuvent être surchargés */
                /* par le HTML généré ou des styles QSS plus fins */
            }}
            #ContentArea QFrame#DashboardBox QTextBrowser#ReadmeBrowser a {{
                color: {ACCENT_COLOR}; /* Couleur des liens */
                text-decoration: none;
            }}
             #ContentArea QFrame#DashboardBox QTextBrowser#ReadmeBrowser a:hover {{
                 text-decoration: underline;
             }}

            /* --- Style pour le QTextBrowser des Notes (DIRECTEMENT DANS la page - état restauré) --- */
            QTextBrowser#NotesBrowser {{
                background-color: transparent; 
                border: none;
                color: {DARK_TEXT_COLOR};
            }}
            QTextBrowser#NotesBrowser a {{
                color: {ACCENT_COLOR};
                text-decoration: none;
            }}
            QTextBrowser#NotesBrowser a:hover {{
                 text-decoration: underline;
            }}
            /* --- Fin style NotesBrowser --- */
        """
        self.setStyleSheet(stylesheet)
        self.preferences_widget.setObjectName("PreferencesPage")

    def on_recent_item_activated(self, item):
        list_widget = self.sender()
        widget_item = list_widget.itemWidget(item)
        if isinstance(widget_item, ProjectListItemWidget):
            document_path = widget_item.path_str
            print(f"Opening recent document: {document_path}")
            full_path = os.path.expanduser(document_path)
            self.controller.open_specific_document(full_path)

    def _select_signature_image(self):
        """ Ouvre une boîte de dialogue pour sélectionner une image et l'affiche. """
        # S'assurer que le label existe
        if not self.signature_image_label:
            print("Erreur: Le QLabel pour l'image n'existe pas.")
            return

        # Ouvrir le dialogue de fichier
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog # Décommenter si problème avec dialogue natif
        file_path, _ = QFileDialog.getOpenFileName(self,
                                                  "Sélectionner une image de signature",
                                                  "", # Répertoire initial
                                                  "Images (*.png *.jpg *.jpeg *.bmp)",
                                                  options=options)
        
        if file_path:
            # Charger le QPixmap
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                print(f"Erreur: Impossible de charger l'image depuis {file_path}")
                # Optionnel: Afficher une erreur dans le label
                self.signature_image_label.setText("Erreur")
                self.signature_image_label.setVisible(True)
                return

            # Redimensionner l'image pour s'adapter au label
            label_size = self.signature_image_label.size()
            scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Afficher l'image dans le label
            self.signature_image_label.setPixmap(scaled_pixmap)
            self.signature_image_label.setVisible(True) # Rendre visible
            print(f"Image sélectionnée: {file_path}")

    # --- Slots pour naviguer dans le stack Documents --- 
    def _show_new_document_page(self):
        self.documents_stack.setCurrentWidget(self.documents_new_page)

    def _show_document_list_page(self):
        self.documents_stack.setCurrentWidget(self.documents_list_page)

    # --- Slots pour naviguer dans le stack A Propos --- 
    def _show_release_notes_page(self):
        if hasattr(self, 'about_stack') and hasattr(self, 'about_notes_page'):
             self.about_stack.setCurrentWidget(self.about_notes_page)
        if hasattr(self, 'btn_release_notes'):
             self.btn_release_notes.setVisible(False) 

    def _show_about_readme_page(self):
        if hasattr(self, 'about_stack') and hasattr(self, 'about_readme_page'):
             self.about_stack.setCurrentWidget(self.about_readme_page)
        if hasattr(self, 'btn_release_notes'):
            self.btn_release_notes.setVisible(True) 

# --- Section pour tester la page seule --- 
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    
    class DummyController:
        def create_new_document(self): print("Action: Créer Nouveau Document")
        def open_document(self): print("Action: Ouvrir Document")
        def open_specific_document(self, path): print(f"Action: Ouvrir Document Spécifique: {path}")

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    controller = DummyController()
    welcome_window = WelcomePage(controller)
    welcome_window.show()
    sys.exit(app.exec_()) 