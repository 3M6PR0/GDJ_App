# windows/settings_window.py
import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QStackedWidget, QButtonGroup, 
                             QAbstractButton)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot as Slot
from PyQt5.QtGui import QIcon, QPixmap, QFont

from ui.components.custom_titlebar import CustomTitleBar
from utils.paths import get_resource_path
from utils import icon_loader
from utils.signals import signals # Importer signals pour le thème

# Importer les pages nécessaires
from pages.preferences.preferences_page import PreferencesPage
from pages.about.about_page import AboutPage
from pages.settings.settings_page import SettingsPage # Pour les mises à jour

# --- Importer le contrôleur --- 
from controllers.settings_window_controller import SettingsWindowController
# ----------------------------
import logging # Ajouter logging
logger = logging.getLogger(__name__)

class SettingsWindow(QWidget):
    # Signal pour demander la fermeture (si nécessaire)
    close_requested = pyqtSignal()
    
    # Signal pour changer de page (sera connecté au contrôleur)
    navigate_requested = pyqtSignal(str)

    def __init__(self, parent=None, version_str="?.?.?", main_controller=None): # Ajout main_controller
        super().__init__(parent)
        self.version_str = version_str
        self.main_controller = main_controller # Stocker la référence
        self.controller = None 
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setWindowModality(Qt.ApplicationModal)
        self.setObjectName("SettingsWindow")
        self.setWindowTitle("Paramètres")

        self._init_ui()
        self.resize(750, 550) # Taille par défaut un peu plus grande

        # --- Créer et lier le contrôleur APRÈS _init_ui --- 
        self.controller = SettingsWindowController(self, self.main_controller)
        self.set_controller(self.controller) # Connecter les signaux UI
        # --------------------------------------------------
        
        print("SettingsWindow instance créée")

    def set_controller(self, controller):
        self.controller = controller
        logger.info("SettingsWindow: Connecting UI signals to SettingsWindowController.")
        # Connecter les signaux UI au contrôleur ici si nécessaire
        try:
            self.sidebar_button_group.buttonClicked.connect(self.controller.change_page)
            self.btn_updates.clicked.connect(self.controller.show_updates_page)
            # Connecter le signal de thème
            signals.theme_changed_signal.connect(self._update_icons_theme)
            logger.info("SettingsWindow: UI signals connected successfully.")
        except Exception as e:
            logger.error(f"SettingsWindow: Error connecting signals: {e}", exc_info=True)

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self, title=self.windowTitle(), icon_base_name="logo-gdj.png")
        outer_layout.addWidget(self.title_bar)
        # Connecter les signaux de la barre de titre
        self.title_bar.close_requested.connect(self.close) # Fermer la fenêtre
        # Note: minimize/maximize sont gérés par CustomTitleBar lui-même

        # Optionnel: Ajouter un séparateur comme dans WelcomeWindow
        separator_line = QFrame(self)
        separator_line.setObjectName("TitleSeparatorLine") # Utiliser le même nom d'objet
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Plain)
        separator_line.setFixedHeight(1)
        outer_layout.addWidget(separator_line)

        main_content_widget = QWidget()
        main_layout = QHBoxLayout(main_content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Barre Latérale Gauche --- 
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar") # Même nom pour QSS
        sidebar.setFixedWidth(170)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 8, 0, 8)
        sidebar_layout.setSpacing(3)

        # Section Logo (similaire à WelcomeWindow)
        logo_section_layout = QHBoxLayout()
        logo_section_layout.setContentsMargins(12, 8, 12, 15)
        logo_section_layout.setSpacing(8)
        logo_label = QLabel()
        logo_label.setObjectName("SidebarLogoLabel")
        logo_pixmap = QPixmap(get_resource_path("resources/images/logo-gdj.png"))
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("GDJ") # Fallback
        logo_label.setFixedSize(64, 64)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_section_layout.addWidget(logo_label, 0, Qt.AlignTop)
        # --- Pas de texte AppName/Version ici, c'est la fenêtre Settings --- 
        # text_layout = QVBoxLayout()
        # ...
        # logo_section_layout.addLayout(text_layout, 0)
        logo_section_layout.addStretch()
        sidebar_layout.addLayout(logo_section_layout)

        # Boutons de navigation
        self.sidebar_button_group = QButtonGroup(self)
        self.sidebar_button_group.setExclusive(True)
        button_layout = QVBoxLayout()
        button_layout.setSpacing(1)
        button_layout.setContentsMargins(5, 0, 5, 0)
        
        # --- Boutons spécifiques à SettingsWindow ---
        self.nav_buttons = {}
        # Définir le bouton par défaut (ex: Préférences)
        default_button_name = "Preference"
        button_info = {
            "Preference": "round_tune.png", 
            "A Propos": "round_info.png"
            # Pas de "Documents"
        }
        self._icons_base = button_info.copy() # Copie pour mise à jour thème
        
        for name, icon_name in button_info.items():
            is_default = (name == default_button_name)
            btn_container = QFrame()
            btn_container.setObjectName("SidebarButtonContainer")
            btn_container.setProperty("checked", is_default)
            btn_hbox = QHBoxLayout(btn_container)
            btn_hbox.setContentsMargins(8, 6, 8, 6)
            btn_hbox.setSpacing(8)
            
            btn = QPushButton(name)
            btn.setObjectName("SidebarButton")
            btn.setCheckable(True)
            btn.setChecked(is_default)
            
            icon_path = icon_loader.get_icon_path(icon_name)
            icon = QIcon(icon_path)
            if not icon.isNull():
                btn.setIcon(icon)
                btn.setIconSize(QSize(16, 16))
            else:
                print(f"WARN: SettingsWindow - Icône {icon_name} non trouvée: {icon_path}")
            
            btn_hbox.addWidget(btn, 1)
            self.sidebar_button_group.addButton(btn)
            button_layout.addWidget(btn_container)
            self.nav_buttons[name] = btn
            
            # Connexion pour style
            btn.toggled.connect(
                lambda state, c=btn_container: (
                    c.setProperty("checked", state), 
                    c.style().unpolish(c), 
                    c.style().polish(c)   
                )
            )
        sidebar_layout.addLayout(button_layout)
        sidebar_layout.addStretch()

        # Bouton Mises à jour (remplace Settings de WelcomeWindow)
        updates_layout = QHBoxLayout()
        updates_layout.setContentsMargins(12, 0, 12, 5)
        self.btn_updates = QPushButton()
        self._updates_icon_base = "round_settings.png" # Utiliser l'icône settings
        self.btn_updates.setObjectName("SettingsButton") # Utiliser le même style
        self.btn_updates.setFixedSize(26, 26)
        self.btn_updates.setFlat(True)
        self.btn_updates.setToolTip("Vérifier les mises à jour")
        # La connexion au slot se fera dans set_controller
        self._update_single_icon(self.btn_updates, self._updates_icon_base) # Appliquer icône initiale
        
        updates_layout.addWidget(self.btn_updates)
        updates_layout.addStretch()
        sidebar_layout.addLayout(updates_layout)

        main_layout.addWidget(sidebar)

        # --- Zone de contenu principale (droite) --- 
        content_area = QFrame()
        content_area.setObjectName("ContentAreaFrame") # Utiliser le même nom
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0) # Pas de marges pour le StackedWidget
        content_layout.setSpacing(0)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("ContentArea") # Utiliser le même nom
        
        # Instancier les pages
        self.preferences_page = PreferencesPage()
        self.about_page = AboutPage()
        self.settings_updates_page = SettingsPage() # Renommé pour clarté
        
        # Ajouter les pages au StackedWidget
        self.stacked_widget.addWidget(self.preferences_page)
        self.stacked_widget.addWidget(self.about_page)
        self.stacked_widget.addWidget(self.settings_updates_page)
        
        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_area, 1)

        # Définir le layout principal du contenu
        main_content_widget.setLayout(main_layout)
        outer_layout.addWidget(main_content_widget, 1)

        self.setLayout(outer_layout)
        
        # Sélectionner la page par défaut (Préférences)
        self.stacked_widget.setCurrentWidget(self.preferences_page)
        # S'assurer que le bouton correspondant est coché visuellement
        if self.nav_buttons.get(default_button_name):
             self.nav_buttons[default_button_name].setChecked(True)

    def get_page_widget(self, page_name):
        """Retourne l'instance de la page demandée."""
        if page_name == "Preference":
            return self.preferences_page
        elif page_name == "A Propos":
            return self.about_page
        elif page_name == "Updates": # Nom interne pour la page settings
            return self.settings_updates_page
        return None

    # --- Méthodes pour la mise à jour des icônes thème --- 
    def _update_single_icon(self, button, icon_base_name):
        """Met à jour l'icône d'un bouton spécifique."""
        try:
            icon_path = icon_loader.get_icon_path(icon_base_name)
            icon = QIcon(icon_path)
            if not icon.isNull():
                button.setIcon(icon)
                # Ajuster la taille si nécessaire, ici on prend celle des nav buttons
                button.setIconSize(QSize(18, 18) if button == self.btn_updates else QSize(16, 16))
            else:
                logger.warning(f"SettingsWindow: Icône {icon_base_name} non trouvée: {icon_path}")
                button.setText("?") # Fallback texte
        except Exception as e:
            logger.error(f"SettingsWindow: Erreur MAJ icône {icon_base_name}: {e}")
            button.setText("?")
            
    @Slot(str)
    def _update_icons_theme(self, theme_name):
        """Met à jour toutes les icônes de la sidebar lors du changement de thème."""
        logger.info(f"SettingsWindow: Updating icons for theme '{theme_name}'")
        # Mettre à jour les boutons de navigation
        for name, button in self.nav_buttons.items():
            if name in self._icons_base:
                self._update_single_icon(button, self._icons_base[name])
            else:
                 logger.warning(f"SettingsWindow: No base icon name found for button '{name}'")
                 
        # Mettre à jour le bouton Mises à jour
        self._update_single_icon(self.btn_updates, self._updates_icon_base)
        # Mettre à jour l'icône de la barre de titre (si nécessaire)
        # self.title_bar.update_theme_icons(theme_name) # CustomTitleBar le fait déjà via signals

# Bloc de test mis à jour pour passer le main_controller (None ici)
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    from utils.stylesheet_loader import load_stylesheet
    import logging
    logging.basicConfig(level=logging.INFO) # Configurer logging pour le test
    
    app = QApplication(sys.argv)
    try:
        qss_files = ["resources/styles/global.qss", "resources/styles/frame.qss"]
        style = load_stylesheet(qss_files, theme_name="DARK")
        app.setStyleSheet(style)
        icon_loader.set_active_theme("DARK")
    except Exception as e:
        logger.error(f"Erreur chargement style/theme pour test: {e}", exc_info=True)
        
    # Simuler un main_controller minimal si nécessaire pour les tests
    class DummyMainController:
        pass
    main_controller_instance = DummyMainController()
    
    # Passer le main_controller factice
    window = SettingsWindow(version_str="1.0.0-test", main_controller=main_controller_instance)
    window.show()
    sys.exit(app.exec_()) 