import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSpacerItem, QSizePolicy,
                             QStackedWidget, QButtonGroup)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

# Importer la barre de titre personnalisée
from ui.components.custom_titlebar import CustomTitleBar

# Importer les nouvelles pages/contrôleurs
from pages.about.about_page import AboutPage
from controllers.about.about_controller import AboutController
from pages.documents.documents_page import DocumentsPage 
from controllers.documents.documents_controller import DocumentsController
# --- Importer PreferencesPage et PreferencesController --- 
from pages.preferences.preferences_page import PreferencesPage
from controllers.preferences.preferences_controller import PreferencesController

# --- WelcomePage (Nettoyée) --- 
class WelcomePage(QWidget):
    def __init__(self, controller, app_name="GDJ", version_str="?.?.?"):
        super().__init__()
        self.controller = controller
        self.app_name = app_name
        self.version_str = version_str
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)
        self.setObjectName("WelcomeWindow") 

        # --- Instancier les pages/contrôleurs principaux --- 
        self.documents_page_instance = DocumentsPage()
        self.documents_controller_instance = DocumentsController(self.documents_page_instance, self.controller)
        
        # Section Préférences
        self.preferences_page_instance = PreferencesPage()
        # Le contrôleur principal n'est pas passé ici pour l'instant
        self.preferences_controller_instance = PreferencesController(self.preferences_page_instance)

        # Section A Propos
        self.about_page_instance = AboutPage()
        self.about_controller_instance = AboutController(self.about_page_instance, version_str=self.version_str)
        
        self.stacked_widget = QStackedWidget()
        
        self.init_ui()
        
    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0,0,0,0)
        outer_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self, title=f"Bienvenue dans {self.app_name}", icon_path="resources/images/logo-gdj.png") 
        outer_layout.addWidget(self.title_bar)

        separator_line = QFrame(self)
        separator_line.setObjectName("TitleSeparatorLine")
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Plain)
        separator_line.setFixedHeight(1)
        outer_layout.addWidget(separator_line)

        main_content_widget = QWidget()
        main_layout = QHBoxLayout(main_content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Barre Latérale Gauche (Inchangée) ---
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(170)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 8, 0, 8)
        sidebar_layout.setSpacing(3)
        
        # Section Logo (Inchangée)
        logo_section_layout = QHBoxLayout()
        logo_section_layout.setContentsMargins(12, 8, 12, 15)
        logo_section_layout.setSpacing(8)
        logo_label = QLabel()
        logo_label.setObjectName("SidebarLogoLabel")
        logo_pixmap = QPixmap("resources/images/logo-gdj.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("GDJ")
        logo_label.setFixedSize(64, 64)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_section_layout.addWidget(logo_label, 0, Qt.AlignTop)
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        app_name_label = QLabel(self.app_name)
        app_name_label.setObjectName("SidebarAppName")
        version_label = QLabel(self.version_str)
        version_label.setObjectName("SidebarVersion")
        text_layout.addWidget(app_name_label)
        text_layout.addWidget(version_label)
        logo_section_layout.addLayout(text_layout, 0)
        logo_section_layout.addStretch()
        sidebar_layout.addLayout(logo_section_layout)

        # Boutons de navigation (Inchangés)
        self.sidebar_button_group = QButtonGroup(self)
        self.sidebar_button_group.setExclusive(True)
        button_layout = QVBoxLayout()
        button_layout.setSpacing(1)
        button_layout.setContentsMargins(5, 0, 5, 0)
        button_info = {"Documents": True, "Preference": False, "A Propos": False}
        for name, checked in button_info.items():
            btn_container = QFrame()
            btn_container.setObjectName("SidebarButtonContainer")
            btn_container.setProperty("checked", checked)
            btn_hbox = QHBoxLayout(btn_container)
            btn_hbox.setContentsMargins(8, 6, 8, 6)
            btn_hbox.setSpacing(5)
            btn = QPushButton(name)
            btn.setObjectName("SidebarButton")
            btn.setCheckable(True)
            btn.setChecked(checked)
            btn_hbox.addWidget(btn, 1)
            self.sidebar_button_group.addButton(btn)
            placeholder = QSpacerItem(16, 16, QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn_hbox.addSpacerItem(placeholder)
            button_layout.addWidget(btn_container)
            btn.toggled.connect(
                lambda state, c=btn_container: (
                    c.setProperty("checked", state), 
                    c.style().unpolish(c), 
                    c.style().polish(c)   
                )
            )
        sidebar_layout.addLayout(button_layout)
        sidebar_layout.addStretch()
        self.sidebar_button_group.buttonClicked.connect(self._change_page)

        # Bouton Settings (Inchangé)
        settings_layout = QHBoxLayout()
        settings_layout.setContentsMargins(12, 0, 12, 5)
        btn_settings = QPushButton("⚙")
        btn_settings.setObjectName("SettingsButton")
        btn_settings.setFixedSize(26, 26)
        settings_layout.addWidget(btn_settings)
        settings_layout.addStretch()
        sidebar_layout.addLayout(settings_layout)
        main_layout.addWidget(sidebar)

        # --- Zone de Contenu Principal (QStackedWidget) --- 
        self.stacked_widget.setObjectName("ContentArea")

        # --- Ajout des PAGES INSTANCIÉES au QStackedWidget --- 
        self.stacked_widget.addWidget(self.documents_page_instance)
        self.stacked_widget.addWidget(self.preferences_page_instance) # Utiliser l'instance
        self.stacked_widget.addWidget(self.about_page_instance)
        
        main_layout.addWidget(self.stacked_widget, 1) 

        main_content_widget.setLayout(main_layout)
        outer_layout.addWidget(main_content_widget, 1)

        self.setMinimumSize(1000, 700)

    # --- _change_page (CORRIGÉ pour accepter le bouton) ---
    def _change_page(self, button): # Accepter l'objet bouton
        """Change la page affichée dans le QStackedWidget central."""
        button_text = button.text() # Récupérer le texte du bouton
        target_widget = None # Initialiser à None
        if button_text == "Documents":
            target_widget = self.documents_page_instance
            # CORRECTION: Utiliser l'instance directe du contrôleur
            if hasattr(self.documents_controller_instance, 'show_default_page'):
                print("Debug: Calling DocumentsController.show_default_page()")
                self.documents_controller_instance.show_default_page()
            else:
                print("Warning: show_default_page not found on documents_controller_instance")

        elif button_text == "A Propos":
            target_widget = self.about_page_instance
            # CORRECTION: Utiliser l'instance directe du contrôleur
            if hasattr(self.about_controller_instance, 'show_default_page'):
                print("Debug: Calling AboutController.show_default_page()")
                self.about_controller_instance.show_default_page()
            else:
                print("Warning: show_default_page not found on about_controller_instance")

        elif button_text == "Preference":
            target_widget = self.preferences_page_instance
            # Pas de show_default_page nécessaire pour Préférences pour l'instant

        else:
            print(f"Debug: Bouton non reconnu: {button_text} (from button: {button})") # Log amélioré
            return

        # Vérifier si target_widget a été assigné avant de l'utiliser
        if target_widget:
            self.stacked_widget.setCurrentWidget(target_widget)
            print(f"Debug: Changement de page vers {button_text} (Widget: {target_widget})")
        else:
            print(f"Error: target_widget is None for button {button_text}")

# --- Section pour tester la page seule (Inchangée) --- 
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    
    class DummyController:
        def open_document(self): print("Action: Ouvrir Document")
        def open_specific_document(self, path): print(f"Action: Ouvrir Document Spécifique: {path}")
        def create_new_document(self): print("Action: Créer Nouveau Document")

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    controller = DummyController()
    welcome_window = WelcomePage(controller)
    welcome_window.show()
    sys.exit(app.exec_()) 