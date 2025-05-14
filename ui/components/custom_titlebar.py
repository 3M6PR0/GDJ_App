import sys
import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, QMenu, QAction, QWidgetAction, QFrame, QFileDialog
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSlot as Slot, pyqtSignal, QEvent, QTimer, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QFont, QCursor, QDesktopServices

# --- Import CORRECT pour icon_loader --- 
from utils import icon_loader
# --- AJOUT IMPORTS ---
from utils.signals import signals
# --- AJOUT IMPORT SPÉCIFIQUE --- 
from utils.paths import get_resource_path 
import logging
# Initialisation du logger applicatif
logger = logging.getLogger('GDJ_App') 
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
    # --- MODIFICATION : Renommer le signal --- 
    new_document_requested = pyqtSignal() # <<< RENOMMÉ
    # --- AJOUT: Signal pour demander l'ouverture des paramètres ---
    settings_requested = pyqtSignal()
    # --- AJOUT SIGNAUX FERMETURE ONGLETS --- 
    close_active_document_requested = pyqtSignal()
    close_all_documents_requested = pyqtSignal()
    # --- AJOUT SIGNAUX SAUVEGARDE ---
    save_document_requested = pyqtSignal()
    save_document_as_requested = pyqtSignal()
    # ---------------------------------------

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
        self.btn_file.clicked.connect(self._show_file_menu) # <<< AJOUT: Reconnecter clic
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

    # --- AJOUT: Méthode pour revenir à l'état initial ---
    def show_initial_state(self):
        """Cache les boutons de menu textuels et affiche le bouton menu + titre."""
        # Cacher les boutons textuels
        if self.btn_file: self.btn_file.hide()
        if self.btn_edit: self.btn_edit.hide()
        if self.btn_view: self.btn_view.hide()
        if self.btn_help: self.btn_help.hide()
        
        # Cacher les menus déroulants (au cas où)
        if self._file_menu: self._file_menu.hide()
        # TODO: Cacher les autres menus (edit, view, help) quand ils seront implémentés
        
        # Afficher le bouton menu icône (si la fenêtre l'utilise)
        # Il faut savoir si on DOIT l'afficher. On peut le déduire de la visibilité
        # initiale passée ou d'un flag interne.
        # Pour l'instant, on suppose qu'on doit le réafficher s'il était prévu.
        # -> On va plutôt se baser sur la visibilité actuelle des boutons texte
        #    Si on appelle cette fonction, c'est qu'ils étaient visibles.
        if self.btn_custom_action: # S'assurer qu'il existe
             self.btn_custom_action.setVisible(True) # Le rendre visible
             
        # Afficher le titre
        if self.title_label: self.title_label.setVisible(True)
        
    # ------------------------------------------------------

    # --- AJOUT/Modification: Gestion du clic sur la barre elle-même ---
    def mousePressEvent(self, event):
        # Si les boutons de menu textuels sont visibles...
        if self.btn_file and self.btn_file.isVisible():
            # Vérifier si le clic est sur l'un des boutons/menus actifs
            clicked_on_active_widget = False
            active_widgets = [ # Liste des widgets qui maintiennent le menu ouvert
                self.btn_file, self.btn_edit, self.btn_view, self.btn_help, 
                self.btn_minimize, self.btn_maximize, self.btn_close,
                self.btn_custom_action # Le bouton menu icône lui-même
            ]
            if self._file_menu and self._file_menu.isVisible():
                 active_widgets.append(self._file_menu)
            # TODO: Ajouter les autres menus déroulants à `active_widgets` quand ils existeront

            for widget in active_widgets:
                if widget and widget.isVisible() and widget.rect().contains(widget.mapFromGlobal(event.globalPos())):
                    clicked_on_active_widget = True
                    break
            
            # Si le clic n'était sur AUCUN widget actif, revenir à l'état initial
            if not clicked_on_active_widget:
                self.show_initial_state()
                # On ne propage pas forcément l'événement pour éviter le déplacement
                # return # Ou laisser passer pour le déplacement ? À tester.

        # --- Logique originale pour déplacer la fenêtre --- (Exécutée si menu texte pas visible ou clic sur zone active)
        if event.button() == Qt.LeftButton:
            # On vérifie si le clic n'était pas sur un bouton AVANT de démarrer le déplacement
            is_on_button = False
            # Vérifier tous les boutons potentiellement cliquables
            all_buttons = [self.btn_custom_action, self.btn_file, self.btn_edit, self.btn_view, self.btn_help, self.btn_minimize, self.btn_maximize, self.btn_close]
            for btn in all_buttons:
                 if btn and btn.isVisible() and btn.rect().contains(btn.mapFromGlobal(event.globalPos())):
                      is_on_button = True
                      break
            
            if not is_on_button:
                self.pressing = True
                self.start_move_pos = event.globalPos()
        # ------------------------------------------------
        super().mousePressEvent(event) # Laisser le parent gérer (important!)
    # ---------------------------------------------------------------

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
        self._file_menu.setObjectName("TitleBarDropdownMenu")
        self._file_menu.setMinimumWidth(220)
        
        # Logique de reconstruction propre du menu Fichier pour insérer correctement
        self._file_menu.clear() # Nettoyer le menu existant pour le reconstruire proprement

        action_new = QAction(QIcon(icon_loader.get_icon_path("round_note_add.png")), "Nouveau", self)
        action_new.setShortcut(Qt.CTRL | Qt.Key_N)
        action_new.triggered.connect(self._handle_new_action)
        self._file_menu.addAction(action_new)
        
        action_open = QAction(QIcon(icon_loader.get_icon_path("round_folder_open.png")), "Ouvrir...", self) # AJOUT Icône
        action_open.setShortcut(Qt.CTRL | Qt.Key_O) # AJOUT Raccourci
        # action_open.triggered.connect(self._handle_open_action) # TODO: Créer et connecter _handle_open_action
        self._file_menu.addAction(action_open)
        
        # action_recent = self._file_menu.addAction("Recent") # Laisser pour plus tard
        # TODO: Connecter action_open.triggered, action_recent.triggered

        title_widget_doc_actif = self._create_separator_with_title("Document Actif")
        widget_action_doc_actif = QWidgetAction(self._file_menu)
        widget_action_doc_actif.setDefaultWidget(title_widget_doc_actif)
        self._file_menu.addAction(widget_action_doc_actif)
        
        # Nos nouvelles actions Sauvegarder / Sauvegarder sous
        action_save = QAction(QIcon(icon_loader.get_icon_path("round_save.png")), "Enregistrer", self) # AJOUT Icône
        action_save.setShortcut(Qt.CTRL | Qt.Key_S) # AJOUT Raccourci Ctrl+S
        action_save_as = QAction(QIcon(icon_loader.get_icon_path("round_save_as.png")), "Enregistrer sous...", self) # AJOUT Icône
        # Pas de raccourci standard évident pour "Enregistrer sous", mais Ctrl+Shift+S est courant
        action_save_as.setShortcut(Qt.CTRL | Qt.SHIFT | Qt.Key_S) # AJOUT Raccourci Ctrl+Shift+S
        
        # Ajouter les actions au menu (elles étaient déjà ajoutées par addAction, mais on les recrée pour icônes/raccourcis)
        # Pour éviter les doublons, il faut vérifier si elles existent ou les remplacer.
        # Solution plus simple: modifier les actions existantes si possible, ou les insérer correctement.
        # Ici, je vais supposer qu'on remplace les anciennes si elles existaient sans icône/raccourci.
        # Pour une meilleure gestion, il faudrait une méthode pour obtenir/créer une action.

        # On retire les anciennes actions si elles ont été créées par self._file_menu.addAction("Texte")
        # Ceci est une simplification. Idéalement, on construirait le menu plus dynamiquement.
        # Si les actions "Enregistrer" et "Enregistrer sous..." étaient déjà là, il faut les gérer.
        # Pour l'instant, je vais les ajouter après "Nouveau" et "Ouvrir" pour plus de clarté.

        # Les actions existantes dans _create_file_menu sont:
        # action_new = QAction(...)
        # self._file_menu.addAction(action_new)
        # action_open = self._file_menu.addAction("Ouvrir...")
        # action_recent = self._file_menu.addAction("Recent")
        # ... séparateur ...
        # action_save = self._file_menu.addAction("Enregistrer") <-- CELLE-CI
        # action_save_as = self._file_menu.addAction("Enregistrer sous...") <-- ET CELLE-CI
        # action_close_doc = self._file_menu.addAction("Fermer")
        # action_print_doc = self._file_menu.addAction("Imprimer")

        # Logique de reconstruction propre du menu Fichier pour insérer correctement
        self._file_menu.clear() # Nettoyer le menu existant pour le reconstruire proprement

        action_new = QAction(QIcon(icon_loader.get_icon_path("round_note_add.png")), "Nouveau", self)
        action_new.setShortcut(Qt.CTRL | Qt.Key_N)
        action_new.triggered.connect(self._handle_new_action)
        self._file_menu.addAction(action_new)
        
        action_open = QAction(QIcon(icon_loader.get_icon_path("round_folder_open.png")), "Ouvrir...", self) # AJOUT Icône
        action_open.setShortcut(Qt.CTRL | Qt.Key_O) # AJOUT Raccourci
        # action_open.triggered.connect(self._handle_open_action) # TODO: Créer et connecter _handle_open_action
        self._file_menu.addAction(action_open)
        
        # action_recent = self._file_menu.addAction("Recent") # Laisser pour plus tard
        # TODO: Connecter action_open.triggered, action_recent.triggered

        title_widget_doc_actif = self._create_separator_with_title("Document Actif")
        widget_action_doc_actif = QWidgetAction(self._file_menu)
        widget_action_doc_actif.setDefaultWidget(title_widget_doc_actif)
        self._file_menu.addAction(widget_action_doc_actif)
        
        # Nos nouvelles actions Sauvegarder / Sauvegarder sous
        action_save.triggered.connect(self.save_document_requested.emit) 
        self._file_menu.addAction(action_save)
        action_save_as.triggered.connect(self.save_document_as_requested.emit)
        self._file_menu.addAction(action_save_as)
        
        action_close_doc = QAction(QIcon(icon_loader.get_icon_path("round_close_doc.png")), "Fermer", self) # AJOUT Icône
        action_close_doc.setShortcut(Qt.CTRL | Qt.Key_W) # AJOUT Raccourci
        action_close_doc.triggered.connect(self.close_active_document_requested.emit)
        self._file_menu.addAction(action_close_doc)
        
        action_print_doc = QAction(QIcon(icon_loader.get_icon_path("round_print.png")), "Imprimer", self) # AJOUT Icône
        action_print_doc.setShortcut(Qt.CTRL | Qt.Key_P) # AJOUT Raccourci
        action_print_doc.triggered.connect(self._handle_print_active_document)
        self._file_menu.addAction(action_print_doc)
        
        title_widget_all_docs = self._create_separator_with_title("Tous les documents")
        widget_action_all_docs = QWidgetAction(self._file_menu)
        widget_action_all_docs.setDefaultWidget(title_widget_all_docs)
        self._file_menu.addAction(widget_action_all_docs)
        
        action_save_all = QAction(QIcon(icon_loader.get_icon_path("round_save_all.png")), "Enregistrer Tout", self) # AJOUT Icône
        # action_save_all.triggered.connect(self._handle_save_all_action) # TODO
        self._file_menu.addAction(action_save_all)
        
        action_close_all = QAction(QIcon(icon_loader.get_icon_path("round_close_all_docs.png")), "Fermer Tout", self) # AJOUT Icône
        action_close_all.triggered.connect(self.close_all_documents_requested.emit)
        self._file_menu.addAction(action_close_all)
        
        # action_print_all = self._file_menu.addAction("Imprimer Tout") # Laisser pour plus tard

        title_widget_app = self._create_separator_with_title("Application")
        widget_action_app = QWidgetAction(self._file_menu)
        widget_action_app.setDefaultWidget(title_widget_app)
        self._file_menu.addAction(widget_action_app)
        
        action_settings = QAction(QIcon(icon_loader.get_icon_path("round_settings.png")), "Paramètres", self) # AJOUT Icône
        action_settings.triggered.connect(self.settings_requested.emit)
        self._file_menu.addAction(action_settings)
        
        action_quit = QAction(QIcon(icon_loader.get_icon_path("round_exit_to_app.png")), "Quitter", self) # AJOUT Icône
        action_quit.setShortcut(Qt.CTRL | Qt.Key_Q) # AJOUT Raccourci
        action_quit.triggered.connect(self.close_window) 
        self._file_menu.addAction(action_quit)
        
        # Appliquer un style global au menu si nécessaire via QSS
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

    # --- _show_file_menu inchangé (utilise popup) --- 
    def _show_file_menu(self):
        if self._file_menu and not self._file_menu.isVisible():
            menu_pos = self.btn_file.mapToGlobal(QPoint(0, self.btn_file.height()))
            self._file_menu.popup(menu_pos)
    # ----------------------------------------------------

    # --- AJOUT: Méthode pour afficher les boutons de menu ---
    def _show_menu_buttons(self):
        """Masque le bouton menu et le titre, affiche les boutons textuels."""
        # Cacher l'état initial
        if self.btn_custom_action: self.btn_custom_action.setVisible(False)
        if self.title_label: self.title_label.setVisible(False)
        
        # Afficher les boutons textuels
        if self.btn_file: self.btn_file.setVisible(True)
        if self.btn_edit: self.btn_edit.setVisible(True)
        if self.btn_view: self.btn_view.setVisible(True)
        if self.btn_help: self.btn_help.setVisible(True)
    # -----------------------------------------------------

    # --- NOUVELLE MÉTHODE: Gérer le clic sur l'action "Nouveau" --- 
    @Slot()
    def _handle_new_action(self):
        """Émet le signal lorsque l'action Nouveau est cliquée."""
        logger.info("CustomTitleBar: Action 'Nouveau' cliquée, émission de new_document_requested.")
        self.new_document_requested.emit()
    # -----------------------------------------------------------

    # --- NOUVELLE MÉTHODE POUR GÉRER L'IMPRESSION DU DOCUMENT ACTIF ---
    @Slot()
    def _handle_print_active_document(self):
        logger.debug("Action Imprimer document actif déclenchée.")
        parent_window = self.parent()
        if not parent_window:
            logger.warning("Impossible d'obtenir la fenêtre parente pour l'impression.")
            # TODO: Afficher un message à l'utilisateur ?
            return

        active_document = None
        if hasattr(parent_window, 'get_active_document'):
            active_document = parent_window.get_active_document()
        else:
            logger.warning("La fenêtre parente n'a pas de méthode 'get_active_document'.")
            # TODO: Afficher un message à l'utilisateur ?
            return

        if active_document is None:
            logger.info("Aucun document actif à imprimer.")
            # TODO: Afficher un message à l'utilisateur (ex: barre de statut ou QMessageBox.information)
            # from PyQt5.QtWidgets import QMessageBox
            # QMessageBox.information(parent_window, "Impression", "Aucun document actif à imprimer.")
            return

        if not hasattr(active_document, 'export_to_pdf') or not callable(getattr(active_document, 'export_to_pdf')):
            logger.warning(f"Le document actif de type '{type(active_document).__name__}' n'a pas de méthode export_to_pdf.")
            # from PyQt5.QtWidgets import QMessageBox
            # QMessageBox.warning(parent_window, "Impression", "Ce type de document ne peut pas être imprimé.")
            return
            
        # Proposer un nom de fichier basé sur le titre du document ou un nom par défaut
        default_filename = "impression.pdf"
        if hasattr(active_document, 'title') and active_document.title:
            # Nettoyer le titre pour qu'il soit un nom de fichier valide
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in active_document.title).rstrip()
            default_filename = f"{safe_title}.pdf"
        elif hasattr(active_document, 'nom_fichier') and active_document.nom_fichier: # Fallback si nom_fichier existe
            base, _ = os.path.splitext(active_document.nom_fichier)
            default_filename = f"{base}_impression.pdf"

        # Ouvrir la boîte de dialogue pour choisir l'emplacement de sauvegarde
        # Le répertoire initial pourrait être le dernier utilisé ou le répertoire des documents de l'utilisateur
        # Pour l'instant, on laisse le système choisir le répertoire par défaut.
        file_path, _ = QFileDialog.getSaveFileName(
            parent_window, 
            "Enregistrer le PDF sous...", 
            default_filename, # Nom de fichier suggéré
            "Documents PDF (*.pdf);;Tous les fichiers (*)"
        )

        if file_path:
            try:
                logger.info(f"Tentative d'exportation du document actif vers : {file_path}")
                active_document.export_to_pdf(file_path)
                logger.info(f"PDF généré avec succès : {file_path}")
                
                # Ouvrir le PDF avec l'application par défaut
                success = QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                if not success:
                    logger.error(f"Impossible d'ouvrir le PDF généré : {file_path}")
                    # from PyQt5.QtWidgets import QMessageBox
                    # QMessageBox.warning(parent_window, "Ouverture PDF", f"Impossible d'ouvrir le fichier PDF généré.\n{file_path}")
            except Exception as e:
                logger.error(f"Erreur lors de la génération ou de l'ouverture du PDF : {e}", exc_info=True)
                # from PyQt5.QtWidgets import QMessageBox
                # QMessageBox.critical(parent_window, "Erreur d'impression", f"Une erreur est survenue lors de la génération du PDF:\n{e}")
        else:
            logger.info("L'opération d'impression a été annulée par l'utilisateur.")
    # -----------------------------------------------------------------------

    def eventFilter(self, obj, event):
        # ... existing code ...
        return super().eventFilter(obj, event)

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