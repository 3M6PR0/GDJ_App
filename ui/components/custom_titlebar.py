import sys
import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSlot as Slot, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

# --- Import CORRECT pour icon_loader --- 
from utils import icon_loader
# --- AJOUT IMPORTS ---
from utils.signals import signals
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
    # ---------------------------------------------------------------------

    def __init__(self, parent=None, title="Application", icon_base_name=None):
        super().__init__(parent)
        self.setFixedHeight(32) # Hauteur standard de la barre de titre
        self.pressing = False
        self.start_move_pos = QPoint()
        
        # --- AJOUT : Stocker noms icônes boutons --- 
        self._minimize_icon_base = "round_minimize.png"
        self._maximize_icon_base = "round_crop_square.png"
        self._restore_icon_base = "round_filter_none.png" 
        self._close_icon_base = "round_close.png"
        # --- AJOUT : État maximisé --- 
        self.is_maximized = False 
        # ------------------------------

        # Layout principal horizontal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 0, 0) # Marge gauche pour aérer, 0 ailleurs
        layout.setSpacing(0)

        # Icône (Optionnel)
        if icon_base_name:
             absolute_icon_path = icon_loader.get_icon_path(icon_base_name)
             if os.path.exists(absolute_icon_path):
                 icon_label = QLabel(self)
                 pixmap = QPixmap(absolute_icon_path)
                 icon_label.setPixmap(pixmap.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                 icon_label.setFixedSize(32, self.height()) # Ajuster largeur (26 + padding)
                 icon_label.setStyleSheet("background-color: transparent; padding-left: 5px;")
                 layout.addWidget(icon_label)
                 layout.addSpacing(5) # Petit espace après l'icône
             else:
                 print(f"WARN: Icône de fenêtre '{icon_base_name}' non trouvée: {absolute_icon_path}")

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

        except Exception as e:
            logger.error(f"Erreur maj icônes barre titre (thème: '{theme_name}'): {e}")
            # Fallback texte si erreur
            self.btn_minimize.setText("_")
            self.btn_maximize.setText("M/R")
            self.btn_close.setText("X")
    # ------------------------------------

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