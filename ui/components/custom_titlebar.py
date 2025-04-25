import sys
import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, QMenu, QAction, QWidgetAction, QFrame
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSlot as Slot, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont

# --- Import CORRECT pour icon_loader --- 
from utils import icon_loader
# --- AJOUT IMPORTS ---
from utils.signals import signals
# --- AJOUT IMPORT SPÉCIFIQUE --- 
from utils.paths import get_resource_path 
import logging
logger = logging.getLogger(__name__)
# -------------------

# Utiliser les couleurs définies dans welcome_page ou les redéfinir/importer
# Pour simplifier, je vais utiliser des valeurs codées ici, mais l'idéal serait
# de partager les constantes de couleur.
TITLE_BAR_BACKGROUND = "#2b2b2b" # Devrait correspondre à DARK_WIDGET_BACKGROUND
TITLE_BAR_TEXT_COLOR = "#bbbbbb"
BUTTON_HOVER_BG = "#45494d" # ITEM_HOVER_BACKGROUND
BUTTON_CLOSE_HOVER_BG = "#c42b1c" # Rouge pour fermer

class CustomTitleBar(QWidget):
    # --- AJOUT SIGNAUX (même si on ne les utilise pas tous ici, 
    #                  c'est plus propre que l'accès direct à parent_window) --- 
    minimize_requested = pyqtSignal()
    maximize_restore_requested = pyqtSignal()
    close_requested = pyqtSignal()
    # --- AJOUT : Signal pour le nouveau bouton ---
    custom_action_requested = pyqtSignal()
    # --- AJOUT: Signal pour demander l'ouverture des paramètres ---
    settings_requested = pyqtSignal()
    # ---------------------------------------------------------------------

    def __init__(self, parent=None, title="Application", icon_base_name=None, show_menu_button_initially=False):
        super().__init__(parent)
        self.setFixedHeight(32) # Hauteur standard de la barre de titre
        self.pressing = False
        self.start_move_pos = QPoint()
        
        # --- AJOUT : Stocker noms icônes boutons --- 
        self._minimize_icon_base = "round_minimize.png"
        self._maximize_icon_base = "round_crop_square.png"
        self._restore_icon_base = "round_filter_none.png" 
        self._close_icon_base = "round_close.png"
        # --- AJOUT : Stocker aussi l'icône de la fenêtre --- 
        self._window_icon_base = icon_base_name 
        # -------------------------------------------------
        # --- AJOUT : État maximisé --- 
        self.is_maximized = False 
        # ------------------------------
        # --- AJOUT: Références aux boutons de menu ---
        self.btn_file = None
        self.btn_edit = None
        self.btn_view = None
        self.btn_help = None
        # --- AJOUT: Référence au QMenu Fichier ---
        self._file_menu = None
        # ----------------------------------------

        # Layout principal horizontal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 0, 0) # Marge gauche pour aérer, 0 ailleurs
        layout.setSpacing(0)

        # Icône (Optionnel) - Chargement SANS thème
        self.icon_label = QLabel(self) # Initialiser ici
        # --- Utiliser self._window_icon_base --- 
        if self._window_icon_base:
             try:
                 # Construire chemin base directement DANS images
                 relative_logo_path = f"resources/images/{self._window_icon_base}" # Utiliser /images/
                 absolute_icon_path = get_resource_path(relative_logo_path)
             except Exception as e_path:
                 logger.error(f"Erreur chemin logo '{self._window_icon_base}': {e_path}") # Utiliser l'attribut
                 absolute_icon_path = None
             
             if absolute_icon_path and os.path.exists(absolute_icon_path):
                 pixmap = QPixmap(absolute_icon_path)
                 # Mettre à jour self.icon_label existant
                 self.icon_label.setPixmap(pixmap.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                 self.icon_label.setFixedSize(32, self.height()) 
                 self.icon_label.setStyleSheet("background-color: transparent; padding-left: 5px;")
                 # --- Remettre l'ajout du widget ICI --- 
                 layout.addWidget(self.icon_label)
                 layout.addSpacing(5)
                 # -------------------------------------
             else:
                 logger.warning(f"Icône de fenêtre (base) '{self._window_icon_base}' non trouvée.") # Utiliser l'attribut
                 # Optionnel: Mettre un placeholder texte sur self.icon_label ?
                 # self.icon_label.setText("[X]")
        # --- Retirer l'ajout inconditionnel d'ici --- 
        # layout.addWidget(self.icon_label) 
        # layout.addSpacing(5)
        # -------------------------------------------

        # --- AJOUT: Nouveau bouton personnalisé (Déplacé ICI) ---
        btn_size = QSize(45, self.height()) # Garder définition taille
        self.btn_custom_action = QPushButton("", self)
        # TODO: Choisir un nom d'icône approprié dans icon_loader
        custom_icon_base = "round_menu.png" # Placeholder, à changer
        try:
            custom_icon_path = icon_loader.get_icon_path(custom_icon_base)
            self.btn_custom_action.setIcon(QIcon(custom_icon_path))
        except Exception as e:
            logger.error(f"Impossible charger icône bouton personnalisé '{custom_icon_base}': {e}")
            self.btn_custom_action.setText("?") # Texte de secours
        self.btn_custom_action.setIconSize(QSize(16, 16))
        self.btn_custom_action.setFixedSize(btn_size)
        self.btn_custom_action.setObjectName("TitleBarButton") # Même style que les autres
        self.btn_custom_action.setToolTip("Afficher le menu") # Tooltip mis à jour
        self.btn_custom_action.clicked.connect(self._show_menu_buttons) # <<< Ajouté
        self.btn_custom_action.setVisible(show_menu_button_initially) # <<< Visibilité initiale basée sur le paramètre
        layout.addWidget(self.btn_custom_action)
        layout.addSpacing(5) # Ajouter un espacement après le bouton
        # -------------------------------------------------------

        # --- AJOUT: Boutons de menu textuels ---
        menu_button_style = f"color: {TITLE_BAR_TEXT_COLOR}; background-color: transparent; border: none; padding: 5px; font-size: 9pt;"
        hover_style = f"background-color: {BUTTON_HOVER_BG};"
        
        # --- MODIFICATION: Bouton Fichier devient déclencheur de menu ---
        self.btn_file = QPushButton("Fichier", self)
        self.btn_file.setObjectName("TitleBarMenuButton")
        self.btn_file.setStyleSheet(f"QPushButton#TitleBarMenuButton {{ {menu_button_style} }} QPushButton#TitleBarMenuButton:hover {{ {hover_style} }}")
        self.btn_file.setVisible(False)
        self._create_file_menu() # Créer le menu associé
        self.btn_file.clicked.connect(self._show_file_menu) # Connecter au slot qui affiche le menu
        layout.addWidget(self.btn_file)

        self.btn_edit = QPushButton("Editer", self)
        self.btn_edit.setObjectName("TitleBarMenuButton")
        self.btn_edit.setStyleSheet(f"QPushButton#TitleBarMenuButton {{ {menu_button_style} }} QPushButton#TitleBarMenuButton:hover {{ {hover_style} }}")
        self.btn_edit.setVisible(False)
        # TODO: Connecter self.btn_edit.clicked
        layout.addWidget(self.btn_edit)

        self.btn_view = QPushButton("Vue", self)
        self.btn_view.setObjectName("TitleBarMenuButton")
        self.btn_view.setStyleSheet(f"QPushButton#TitleBarMenuButton {{ {menu_button_style} }} QPushButton#TitleBarMenuButton:hover {{ {hover_style} }}")
        self.btn_view.setVisible(False)
        # TODO: Connecter self.btn_view.clicked
        layout.addWidget(self.btn_view)

        self.btn_help = QPushButton("Aide", self)
        self.btn_help.setObjectName("TitleBarMenuButton")
        self.btn_help.setStyleSheet(f"QPushButton#TitleBarMenuButton {{ {menu_button_style} }} QPushButton#TitleBarMenuButton:hover {{ {hover_style} }}")
        self.btn_help.setVisible(False)
        # TODO: Connecter self.btn_help.clicked
        layout.addWidget(self.btn_help)
        # --------------------------------------

        # Titre
        self.title_label = QLabel(title, self)
        self.title_label.setStyleSheet(f"color: {TITLE_BAR_TEXT_COLOR}; font-size: 9pt;")
        layout.addWidget(self.title_label)

        layout.addStretch() # Pousser les boutons vers la droite

        # --- Boutons Min/Max/Close (Utiliser les noms base stockés) --- 
        btn_size = QSize(45, self.height())

        # Bouton Minimiser
        self.btn_minimize = QPushButton("", self)
        minimize_icon_path = icon_loader.get_icon_path(self._minimize_icon_base) # Utiliser nom base
        self.btn_minimize.setIcon(QIcon(minimize_icon_path))
        self.btn_minimize.setIconSize(QSize(16, 16))
        self.btn_minimize.setFixedSize(btn_size)
        self.btn_minimize.setObjectName("TitleBarButton")
        self.btn_minimize.setToolTip("Minimiser")
        self.btn_minimize.clicked.connect(self.minimize_window)
        layout.addWidget(self.btn_minimize)

        # Bouton Maximiser/Restaurer
        self.btn_maximize = QPushButton("", self)
        maximize_icon_path = icon_loader.get_icon_path(self._maximize_icon_base) # Utiliser nom base (état initial)
        self.btn_maximize.setIcon(QIcon(maximize_icon_path))
        self.btn_maximize.setIconSize(QSize(16, 16))
        self.btn_maximize.setFixedSize(btn_size)
        self.btn_maximize.setObjectName("TitleBarButton")
        self.btn_maximize.setToolTip("Agrandir")
        self.btn_maximize.setCheckable(True) # Garder pour la logique existante
        self.btn_maximize.clicked.connect(self.maximize_restore_window)
        layout.addWidget(self.btn_maximize)

        # Bouton Fermer
        self.btn_close = QPushButton("", self)
        close_icon_path = icon_loader.get_icon_path(self._close_icon_base) # Utiliser nom base
        self.btn_close.setIcon(QIcon(close_icon_path))
        self.btn_close.setIconSize(QSize(16, 16))
        self.btn_close.setFixedSize(btn_size)
        self.btn_close.setObjectName("TitleBarButtonClose")
        self.btn_close.setToolTip("Fermer")
        self.btn_close.clicked.connect(self.close_window)
        layout.addWidget(self.btn_close)
        
        # Appliquer le style de base à la barre elle-même
        self.setStyleSheet(f"""
            CustomTitleBar {{
                background-color: {TITLE_BAR_BACKGROUND};
                /* border-bottom: 1px solid #FF0000; Supprimer la bordure ici */
            }}
            #TitleBarButton, #TitleBarButtonClose {{
                background-color: transparent;
                border: none;
                font-size: 12pt; /* Ajuster taille symboles */
                font-family: "Segoe MDL2 Assets", "Segoe UI Symbol"; /* Polices pour symboles windows */
            }}
             #TitleBarButton:hover {{
                background-color: {BUTTON_HOVER_BG};
             }}
             #TitleBarButtonClose:hover {{
                background-color: {BUTTON_CLOSE_HOVER_BG};
             }}
             #TitleBarButton:pressed, #TitleBarButtonClose:pressed {{
                 background-color: #5a5d5e; /* Un gris plus foncé */
             }}
        """ )
        
        # --- Connexion signal thème --- 
        signals.theme_changed_signal.connect(self.update_theme_icons)
        # -----------------------------
        
        # --- Connexion titre parent INCHANGÉE --- 
        if parent: # Utiliser parent direct passé en argument
             parent.windowTitleChanged.connect(self.title_label.setText)
             # On pourrait toujours utiliser windowStateChanged ici si nécessaire

    def minimize_window(self):
        # --- Utiliser parent() pour obtenir la fenêtre --- 
        parent_window = self.parent() 
        if parent_window:
            parent_window.showMinimized()
        # Émettre signal (optionnel si on garde l'appel direct)
        self.minimize_requested.emit()

    def maximize_restore_window(self):
        parent_window = self.parent() # Utiliser parent()
        if parent_window:
            if parent_window.isMaximized():
                parent_window.showNormal()
                self.is_maximized = False # Mettre à jour état interne
            else:
                parent_window.showMaximized()
                self.is_maximized = True # Mettre à jour état interne
            self.update_maximize_restore_button() # Mettre à jour l'icône
        self.maximize_restore_requested.emit() # Émettre signal

    def close_window(self):
        parent_window = self.parent() # Utiliser parent()
        if parent_window:
            parent_window.close()
        self.close_requested.emit() # Émettre signal

    # --- Logique pour déplacer la fenêtre ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressing = True
            self.start_move_pos = event.globalPos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        parent_window = self.parent() # Utiliser parent()
        if self.pressing and parent_window:
            delta = event.globalPos() - self.start_move_pos
            parent_window.move(parent_window.pos() + delta)
            self.start_move_pos = event.globalPos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressing = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
         # Double-clic maximise/restaure
         if event.button() == Qt.LeftButton:
             self.maximize_restore_window()
         super().mouseDoubleClickEvent(event)

    # --- AJOUT : Méthode MAJ icône Max/Restore thème --- 
    def update_maximize_restore_button(self):
        """Met à jour l'icône et le tooltip du bouton max/restore via icon_loader."""
        if self.is_maximized:
            icon_base = self._restore_icon_base
            tooltip = "Restaurer"
        else:
            icon_base = self._maximize_icon_base
            tooltip = "Agrandir"
        try:
            icon_path = icon_loader.get_icon_path(icon_base)
            self.btn_maximize.setIcon(QIcon(icon_path))
            self.btn_maximize.setToolTip(tooltip)
        except Exception as e:
            logger.error(f"Impossible charger icône max/restore '{icon_base}': {e}")
            self.btn_maximize.setIcon(QIcon()) 
            self.btn_maximize.setText("M" if not self.is_maximized else "R") 
            self.btn_maximize.setToolTip(tooltip)
    # ---------------------------------------------------

    # --- AJOUT : Slot MAJ icônes thème --- 
    @Slot(str)
    def update_theme_icons(self, theme_name):
        """Met à jour les icônes Min/Max/Close en fonction du thème actif."""
        try:
            # Icône Minimiser
            min_icon_path = icon_loader.get_icon_path(self._minimize_icon_base)
            self.btn_minimize.setIcon(QIcon(min_icon_path))

            # Icône Maximiser/Restaurer (via sa méthode dédiée)
            self.update_maximize_restore_button()
            
            # Icône Fermer
            close_icon_path = icon_loader.get_icon_path(self._close_icon_base)
            self.btn_close.setIcon(QIcon(close_icon_path))

            # --- AJOUT: Mettre à jour icône bouton personnalisé ---
            try:
                # TODO: Utiliser le même nom d'icône que dans __init__
                custom_icon_base = "round_menu.png" # Placeholder
                custom_icon_path = icon_loader.get_icon_path(custom_icon_base)
                self.btn_custom_action.setIcon(QIcon(custom_icon_path))
            except Exception as e:
                 logger.error(f"Erreur maj icône bouton personnalisé (thème: '{theme_name}'): {e}")
                 self.btn_custom_action.setText("?") # Texte de secours
            # ----------------------------------------------------

        except Exception as e:
            logger.error(f"Erreur maj icônes barre titre (thème: '{theme_name}'): {e}")
            # Fallback texte si erreur
            self.btn_minimize.setText("_")
            self.btn_maximize.setText("M/R")
            self.btn_close.setText("X")
            self.btn_custom_action.setText("?") # Texte de secours
    # ------------------------------------

    # --- AJOUT: Méthode pour créer le menu Fichier ---
    def _create_file_menu(self):
        self._file_menu = QMenu(self)
        self._file_menu.setObjectName("TitleBarDropdownMenu") # Pour style éventuel
        self._file_menu.setMinimumWidth(220) # <<< AJOUT: Largeur minimale
        
        # Actions standard
        action_new = self._file_menu.addAction("Nouveau")
        action_open = self._file_menu.addAction("Ouvrir...")
        action_recent = self._file_menu.addAction("Recent")
        # TODO: Connecter action_new.triggered, action_open.triggered, etc.
        
        # --- Titre de section intégré au séparateur ---
        # self._file_menu.addSeparator() # <<< Supprimé
        # label_doc_actif = QLabel(\"Document Actif\")
        # label_doc_actif.setStyleSheet(f\"color: #999999; font-size: 8pt; padding-left: 15px; padding-top: 3px; padding-bottom: 3px; background-color: transparent;\")
        # widget_action_doc_actif = QWidgetAction(self._file_menu)
        # widget_action_doc_actif.setDefaultWidget(label_doc_actif)
        # self._file_menu.addAction(widget_action_doc_actif)

        title_widget_doc_actif = self._create_separator_with_title("Document Actif")
        widget_action_doc_actif = QWidgetAction(self._file_menu)
        widget_action_doc_actif.setDefaultWidget(title_widget_doc_actif)
        self._file_menu.addAction(widget_action_doc_actif)
        # ------------------------------------------------
        
        action_save = self._file_menu.addAction("Enregistrer")
        action_save_as = self._file_menu.addAction("Enregistrer sous...")
        action_close_doc = self._file_menu.addAction("Fermer")
        action_print_doc = self._file_menu.addAction("Print") # Renommé pour clarté
        # TODO: Connecter ces actions
        
        # --- Titre "Tous les documents" --- 
        # Assurer la suppression de l'ancien séparateur si présent
        # self._file_menu.addSeparator() 

        # --- Remplacement de l'ancien QLabel par le widget Séparateur+Titre ---
        # label_all_docs = QLabel(\"Tous les documents\")
        # label_all_docs.setStyleSheet(f\"color: #999999; font-size: 8pt; padding-left: 15px; padding-top: 3px; padding-bottom: 3px; background-color: transparent;\")
        # widget_action_all_docs = QWidgetAction(self._file_menu)
        # widget_action_all_docs.setDefaultWidget(label_all_docs)
        # self._file_menu.addAction(widget_action_all_docs)
        
        title_widget_all_docs = self._create_separator_with_title("Tous les documents")
        widget_action_all_docs = QWidgetAction(self._file_menu)
        widget_action_all_docs.setDefaultWidget(title_widget_all_docs)
        self._file_menu.addAction(widget_action_all_docs)
        # ---------------------------------------------------------------------
        
        action_save_all = self._file_menu.addAction("Enregistrer Tout") # Nom plus précis ?
        action_close_all = self._file_menu.addAction("Fermer Tout") # Nom plus précis ?
        action_print_all = self._file_menu.addAction("Print Tout") # Nom plus précis ?
        # TODO: Connecter ces actions

        # self._file_menu.addSeparator() # <<< SUPPRESSION DE CETTE LIGNE
        # --- Utilisation du widget séparateur + titre ---
        title_widget_app = self._create_separator_with_title("Application")
        widget_action_app = QWidgetAction(self._file_menu)
        widget_action_app.setDefaultWidget(title_widget_app)
        self._file_menu.addAction(widget_action_app)
        # -------------------------------------------------
        
        action_settings = self._file_menu.addAction("Parametres")
        action_quit = self._file_menu.addAction("Quitter")
        # --- Connexion de l'action Paramètres au signal ---
        action_settings.triggered.connect(self.settings_requested.emit)
        # -------------------------------------------------
        # action_quit.triggered.connect(self.close_window) # Exemple de connexion
        
        # Appliquer un style global au menu si nécessaire via QSS
        # self._file_menu.setStyleSheet(\"QMenu { ... } QMenu::item { ... } ... \")
        # --- AJOUT: Style QSS pour les effets hover/selected ---
        self._file_menu.setStyleSheet(f"""
            QMenu#TitleBarDropdownMenu {{
                background-color: {TITLE_BAR_BACKGROUND}; /* Fond du menu */
                border: 1px solid {BUTTON_HOVER_BG}; /* Bordure légère */
                color: {TITLE_BAR_TEXT_COLOR}; /* Couleur texte par défaut */
            }}
            QMenu#TitleBarDropdownMenu::item {{
                padding: 5px 20px; /* Espacement interne */
                background-color: transparent;
            }}
            /* Supprimer le style :disabled spécifique car on utilise QWidgetAction */
            /* QMenu#TitleBarDropdownMenu::item:disabled {{
                color: #888888; 
                background-color: transparent;
                 font-weight: bold; 
            }} */
            QMenu#TitleBarDropdownMenu::item:selected {{
                background-color: {BUTTON_HOVER_BG}; /* Couleur au survol/sélection */
                color: white; /* Couleur texte au survol/sélection */
            }}
            QMenu#TitleBarDropdownMenu::separator {{
                height: 1px;
                background-color: {BUTTON_HOVER_BG};
                margin-left: 10px;
                margin-right: 10px;
            }}
        """)
        # -------------------------------------------------------
    # --------------------------------------------------

    # --- AJOUT: Helper pour créer le widget Séparateur + Titre ---
    def _create_separator_with_title(self, text):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5) # Marges autour
        layout.setSpacing(8)

        line_style = f"color: {BUTTON_HOVER_BG}; background-color: {BUTTON_HOVER_BG}; min-height: 1px; max-height: 1px; border: none;"
        
        left_line = QFrame()
        left_line.setFrameShape(QFrame.HLine)
        left_line.setFrameShadow(QFrame.Plain)
        left_line.setStyleSheet(line_style)
        left_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        label = QLabel(text)
        label.setStyleSheet(f"color: #999999; font-size: 8pt; background-color: transparent; padding: 0px; margin: 0px;")
        label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        right_line = QFrame()
        right_line.setFrameShape(QFrame.HLine)
        right_line.setFrameShadow(QFrame.Plain)
        right_line.setStyleSheet(line_style)
        right_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.addWidget(left_line)
        layout.addWidget(label)
        layout.addWidget(right_line)
        
        widget.setLayout(layout)
        # S'assurer que le widget n'a pas de fond propre pour hériter du menu
        widget.setStyleSheet("background-color: transparent;") 
        return widget
    # ------------------------------------------------------------

    # --- AJOUT: Méthode pour afficher le menu Fichier ---
    def _show_file_menu(self):
        if self._file_menu:
            # Positionner le menu sous le bouton Fichier
            menu_pos = self.btn_file.mapToGlobal(QPoint(0, self.btn_file.height()))
            self._file_menu.exec_(menu_pos)
    # ----------------------------------------------------

    # --- AJOUT: Méthode pour afficher les boutons de menu ---
    def _show_menu_buttons(self):
        """Masque le bouton menu et le titre, affiche les boutons textuels."""
        self.btn_custom_action.setVisible(False)
        self.title_label.setVisible(False)
        
        self.btn_file.setVisible(True)
        self.btn_edit.setVisible(True)
        self.btn_view.setVisible(True)
        self.btn_help.setVisible(True)
        
        # Optionnel: Émettre un signal si nécessaire
        # self.custom_action_requested.emit() # Ou un nouveau signal menu_shown
    # -----------------------------------------------------

# --- Section pour tester la barre seule --- 
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
    
    app = QApplication(sys.argv)
    # Créer une fenêtre principale factice pour le test
    main_win = QMainWindow()
    main_win.setWindowTitle("Fenêtre de Test")
    main_win.setGeometry(100, 100, 600, 400)
    
    # Important: Rendre la fenêtre sans cadre pour le test
    main_win.setWindowFlags(Qt.FramelessWindowHint)
    
    # Widget central factice
    central_widget = QWidget()
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(0,0,0,0)
    main_layout.setSpacing(0)
    
    # Créer et ajouter la barre de titre personnalisée
    title_bar = CustomTitleBar(main_win, title="Test Titre Personnalisé")
    main_layout.addWidget(title_bar)
    
    # Ajouter un contenu factice
    content_label = QLabel("Contenu de la fenêtre principale")
    content_label.setAlignment(Qt.AlignCenter)
    main_layout.addWidget(content_label, 1) # Donner stretch au contenu
    
    main_win.setCentralWidget(central_widget)
    main_win.show()
    
    sys.exit(app.exec_()) 