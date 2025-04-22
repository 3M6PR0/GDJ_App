import sys
import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QIcon, QPixmap

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

# Utiliser les couleurs définies dans welcome_page ou les redéfinir/importer
# Pour simplifier, je vais utiliser des valeurs codées ici, mais l'idéal serait
# de partager les constantes de couleur.
TITLE_BAR_BACKGROUND = "#2b2b2b" # Devrait correspondre à DARK_WIDGET_BACKGROUND
TITLE_BAR_TEXT_COLOR = "#bbbbbb"
BUTTON_HOVER_BG = "#45494d" # ITEM_HOVER_BACKGROUND
BUTTON_CLOSE_HOVER_BG = "#c42b1c" # Rouge pour fermer

class CustomTitleBar(QWidget):
    def __init__(self, parent=None, title="Application", icon_path=None):
        super().__init__(parent)
        self.parent_window = parent # Référence à la fenêtre principale
        self.setFixedHeight(32) # Hauteur standard de la barre de titre
        self.pressing = False
        self.start_move_pos = QPoint()

        # Layout principal horizontal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 0, 0) # Marge gauche pour aérer, 0 ailleurs
        layout.setSpacing(0)

        # Icône (Optionnel)
        if icon_path: # Vérifier si un chemin relatif est fourni
             absolute_icon_path = get_resource_path(icon_path)
             if os.path.exists(absolute_icon_path):
                 icon_label = QLabel(self)
                 pixmap = QPixmap(absolute_icon_path)
                 icon_label.setPixmap(pixmap.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                 icon_label.setFixedSize(32, self.height()) # Ajuster largeur (26 + padding)
                 icon_label.setStyleSheet("background-color: transparent; padding-left: 5px;")
                 layout.addWidget(icon_label)
                 layout.addSpacing(5) # Petit espace après l'icône
             else:
                 print(f"WARN: Icône de fenêtre non trouvée: {absolute_icon_path}")

        # Titre
        self.title_label = QLabel(title, self)
        self.title_label.setStyleSheet(f"color: {TITLE_BAR_TEXT_COLOR}; font-size: 9pt;")
        layout.addWidget(self.title_label)

        layout.addStretch() # Pousser les boutons vers la droite

        # --- Boutons Min/Max/Close ---
        btn_size = QSize(45, self.height()) # Largeur des boutons

        # Bouton Minimiser
        self.btn_minimize = QPushButton("", self) # Texte retiré
        # --- Utiliser get_resource_path --- 
        minimize_icon_path = get_resource_path("resources/icons/clear/round_minimize.png")
        self.btn_minimize.setIcon(QIcon(minimize_icon_path))
        self.btn_minimize.setIconSize(QSize(16, 16)) # Taille icône
        self.btn_minimize.setFixedSize(btn_size)
        self.btn_minimize.setObjectName("TitleBarButton")
        self.btn_minimize.setToolTip("Minimiser")
        self.btn_minimize.clicked.connect(self.minimize_window)
        layout.addWidget(self.btn_minimize)

        # Bouton Maximiser/Restaurer
        self.btn_maximize = QPushButton("", self) # Texte retiré
        # --- Utiliser get_resource_path --- 
        maximize_icon_path = get_resource_path("resources/icons/clear/round_crop_square.png")
        self.btn_maximize.setIcon(QIcon(maximize_icon_path))
        self.btn_maximize.setIconSize(QSize(16, 16)) # Taille icône
        self.btn_maximize.setFixedSize(btn_size)
        self.btn_maximize.setObjectName("TitleBarButton")
        self.btn_maximize.setToolTip("Agrandir")
        self.btn_maximize.setCheckable(True) # Pour suivre l'état max/normal
        self.btn_maximize.clicked.connect(self.maximize_restore_window)
        layout.addWidget(self.btn_maximize)

        # Bouton Fermer
        self.btn_close = QPushButton("", self) # Texte retiré
        # --- Utiliser get_resource_path --- 
        close_icon_path = get_resource_path("resources/icons/clear/round_close.png")
        self.btn_close.setIcon(QIcon(close_icon_path))
        self.btn_close.setIconSize(QSize(16, 16)) # Taille icône
        self.btn_close.setFixedSize(btn_size)
        self.btn_close.setObjectName("TitleBarButtonClose") # Nom différent pour style hover rouge
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
        
        # Mettre à jour l'icône du bouton maximiser si la fenêtre change d'état
        if self.parent_window:
             self.parent_window.windowTitleChanged.connect(self.title_label.setText)
             # Il faudra peut-être connecter windowStateChanged pour l'icône max/restore

    def minimize_window(self):
        if self.parent_window:
            self.parent_window.showMinimized()

    def maximize_restore_window(self):
        if self.parent_window:
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
                # TODO: Changer l'icône pour une icône "Restaurer" si disponible
                # self.btn_maximize.setIcon(QIcon("chemin/vers/icon_restore.png"))
                self.btn_maximize.setToolTip("Restaurer")
            else:
                self.parent_window.showMaximized()
                # TODO: S'assurer que l'icône est bien celle pour "Agrandir"
                # self.btn_maximize.setIcon(QIcon("resources/icons/clear/round_crop_square.png"))
                self.btn_maximize.setToolTip("Agrandir")

    def close_window(self):
        if self.parent_window:
            self.parent_window.close()

    # --- Logique pour déplacer la fenêtre ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressing = True
            self.start_move_pos = event.globalPos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.pressing and self.parent_window:
            delta = event.globalPos() - self.start_move_pos
            self.parent_window.move(self.parent_window.pos() + delta)
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