from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mon App Pro")
        self.resize(1000, 700)
        self.settings_controller = None
        self.settings_page = None
        self._init_ui()
        self._create_menu()

    def _init_ui(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.tabs = QTabWidget()
        self.tabs.setObjectName("MainTabWidget")
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.add_settings_tab()

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

    def add_settings_tab(self):
        if not self.settings_page:
            from pages.settings.settings_page import SettingsPage
            from controllers.settings.settings_controller import SettingsController
            
            self.settings_page = SettingsPage(self)
            self.settings_controller = SettingsController(self.settings_page, None)
            
            index = self.tabs.addTab(self.settings_page, "Paramètres")
            print(f"Onglet Paramètres ajouté à l'index {index}")

    def navigate_to_settings_tab(self):
        print("Attempting to navigate to settings tab...")
        if not self.settings_page or not self.settings_controller:
            print("Settings tab/controller not initialized. Attempting to add it.")
            self.add_settings_tab()
            if not self.settings_page or not self.settings_controller:
                 print("ERROR: Failed to create Settings tab/controller on demand.")
                 return None
        
        target_index = -1
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) == self.settings_page:
                target_index = i
                break
                
        if target_index != -1:
            print(f"Found settings tab at index {target_index}. Switching...")
            self.tabs.setCurrentIndex(target_index)
            return self.settings_controller
        else:
            print("ERROR: Settings tab widget found, but could not find its index.")
            return None

    def set_main_controller(self, main_controller):
        if self.settings_controller:
             print("Setting main_controller reference in SettingsController.")
             self.settings_controller.main_controller = main_controller
        else:
             print("Warning: SettingsController not yet initialized when setting main_controller.")

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget == self.settings_page:
            print("Attempt to close Settings tab ignored.")
            return
        
        print(f"Closing tab at index {index}")
        self.tabs.removeTab(index)
        widget.deleteLater()
