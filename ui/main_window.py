from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mon App Pro")
        self.resize(1000, 700)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self._create_menu()

    def _create_menu(self):
        menu_bar = self.menuBar()

        # Menu Fichier
        file_menu = menu_bar.addMenu("Fichier")
        self.action_new = QAction("Nouveau", self)
        self.action_open = QAction("Ouvrir", self)
        self.action_close = QAction("Fermer", self)
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_close)

        # Bouton Profil directement dans la barre
        self.action_profile = QAction("Profil", self)
        menu_bar.addAction(self.action_profile)

        # Autres menus
        options_menu = menu_bar.addMenu("Options")
        aide_menu = menu_bar.addMenu("Aide")

        # --- Ajout de l'action Notes de version ---
        self.actionAfficherNotesVersion = QAction("Notes de version", self)
        self.actionAfficherNotesVersion.setObjectName("actionAfficherNotesVersion")
        aide_menu.addAction(self.actionAfficherNotesVersion)
        # --- Fin Ajout ---
