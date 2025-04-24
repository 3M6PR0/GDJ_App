import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSpacerItem, QSizePolicy,
                             QStackedWidget, QButtonGroup, QAbstractButton)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot as Slot
from PyQt5.QtGui import QIcon, QPixmap, QFont

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path
from utils import icon_loader

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
# --- AJOUT IMPORTS POUR SETTINGS ---
from pages.settings.settings_page import SettingsPage
from controllers.settings.settings_controller import SettingsController

# --- AJOUT IMPORTS --- 
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot as Slot
# -------------------

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path
from utils import icon_loader
# --- AJOUT IMPORT --- 
from utils.signals import signals 

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
# --- AJOUT IMPORTS POUR SETTINGS ---
from pages.settings.settings_page import SettingsPage
from controllers.settings.settings_controller import SettingsController

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

        # Section Préférences (créée AVANT DocumentsController)
        self.preferences_page_instance = PreferencesPage()
        # Le contrôleur principal n'est pas passé ici pour l'instant
        self.preferences_controller_instance = PreferencesController(self.preferences_page_instance)

        # --- Instancier les pages/contrôleurs principaux --- 
        self.documents_page_instance = DocumentsPage()
        # Passer l'instance de preferences_controller_instance ici
        self.documents_controller_instance = DocumentsController(
            self.documents_page_instance,
            self.controller, # Le main_controller
            self.preferences_controller_instance # La référence directe
        )
        
        # Section A Propos
        self.about_page_instance = AboutPage()
        self.about_controller_instance = AboutController(self.about_page_instance, version_str=self.version_str)
        
        # --- AJOUT INSTANCES SETTINGS --- 
        self.settings_page_instance = SettingsPage()
        # Passer le main_controller au SettingsController
        self.settings_controller_instance = SettingsController(self.settings_page_instance, self.controller)
        
        self.stacked_widget = QStackedWidget()
        
        self.init_ui()
        
    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0,0,0,0)
        outer_layout.setSpacing(0)

        # --- Utiliser icon_loader pour l'icône de la barre de titre --- 
        self.title_bar = CustomTitleBar(self, title=f"Bienvenue dans {self.app_name}", 
                                        icon_base_name="logo-gdj.png")
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
        # --- Revenir à get_resource_path pour le logo --- 
        logo_pixmap = QPixmap(get_resource_path("resources/images/logo-gdj.png"))
        # ------------------------------------------------
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
        # --- Associer nom de bouton à nom d'icône --- 
        button_info = {
            "Documents": "round_description.png", 
            "Preference": "round_tune.png", 
            "A Propos": "round_info.png"
        }
        # Stocker les boutons pour référence
        self.nav_buttons = {}
        # --- Boucle modifiée pour ajouter les icônes --- 
        for name, icon_name in button_info.items():
            btn_container = QFrame()
            btn_container.setObjectName("SidebarButtonContainer")
            btn_container.setProperty("checked", name == "Documents") # Check "Documents" par défaut
            btn_hbox = QHBoxLayout(btn_container)
            btn_hbox.setContentsMargins(8, 6, 8, 6)
            btn_hbox.setSpacing(8) # Augmenter l'espacement pour l'icône
            
            # Créer le bouton
            btn = QPushButton(name) 
            btn.setObjectName("SidebarButton")
            btn.setCheckable(True)
            btn.setChecked(name == "Documents")
            
            # Ajouter l'icône via icon_loader
            icon_path = icon_loader.get_icon_path(icon_name)
            icon = QIcon(icon_path)
            if not icon.isNull():
                btn.setIcon(icon)
                btn.setIconSize(QSize(16, 16))
            else:
                print(f"WARN: Icône {icon_name} non trouvée: {icon_path}")
            
            btn_hbox.addWidget(btn, 1)
            self.sidebar_button_group.addButton(btn)
            # Retirer le spacer pour que le texte soit centré avec l'icône
            # placeholder = QSpacerItem(16, 16, QSizePolicy.Fixed, QSizePolicy.Fixed)
            # btn_hbox.addSpacerItem(placeholder)
            button_layout.addWidget(btn_container)
            self.nav_buttons[name] = btn # Stocker référence
            
            # Connexion pour style au survol/check (inchangé)
            btn.toggled.connect(
                lambda state, c=btn_container: (
                    c.setProperty("checked", state), 
                    c.style().unpolish(c), 
                    c.style().polish(c)   
                )
            )
        # -------------------------------------------------
        sidebar_layout.addLayout(button_layout)
        sidebar_layout.addStretch()

        # Bouton Settings 
        settings_layout = QHBoxLayout()
        settings_layout.setContentsMargins(12, 0, 12, 5)
        # --- Stocker référence au bouton et nom icône --- 
        self.btn_settings = QPushButton()
        self._settings_icon_base = "round_settings.png"
        # -------------------------------------------------
        settings_icon_path = icon_loader.get_icon_path(self._settings_icon_base)
        settings_icon = QIcon(settings_icon_path)
        if not settings_icon.isNull():
            self.btn_settings.setIcon(settings_icon)
            self.btn_settings.setIconSize(QSize(18, 18))
        else:
            print(f"WARN: Icône Settings non trouvée: {settings_icon_path}, utilisation texte.")
            self.btn_settings.setText("⚙")
            self.btn_settings.setFont(QFont("Arial", 12))
        self.btn_settings.setObjectName("SettingsButton")
        self.btn_settings.setFixedSize(26, 26)
        self.btn_settings.setFlat(True)
        self.btn_settings.setToolTip("Préférences")
        self.btn_settings.clicked.connect(self._show_settings_page_from_button)
        
        settings_layout.addWidget(self.btn_settings)
        settings_layout.addStretch()
        sidebar_layout.addLayout(settings_layout)

        # Connecter le groupe de boutons APRES que tous les boutons (...) existent
        self.sidebar_button_group.buttonClicked.connect(self._change_page)

        # --- Connecter le signal de thème pour l'icône Settings --- 
        signals.theme_changed_signal.connect(self._update_settings_icon)
        # ----------------------------------------------------------

        # --- Sélectionner la page par défaut (Documents) --- 
        # Trouver le bouton "Documents" et le checker au démarrage
        for btn in self.sidebar_button_group.buttons():
            if btn.text() == "Documents":
                btn.setChecked(True)
                # Peut-être appeler _change_page ici aussi pour initialiser correctement ?
                # self._change_page(btn) # Assure que la page est affichée
                break
        
        main_layout.addWidget(sidebar)

        # --- Zone de Contenu Principal (QStackedWidget) --- 
        self.stacked_widget.setObjectName("ContentArea")

        # --- AJOUTER SETTINGS PAGE AU STACKED WIDGET --- 
        self.stacked_widget.addWidget(self.documents_page_instance)
        self.stacked_widget.addWidget(self.preferences_page_instance) 
        self.stacked_widget.addWidget(self.about_page_instance)
        self.stacked_widget.addWidget(self.settings_page_instance)
        
        main_layout.addWidget(self.stacked_widget, 1) 

        main_content_widget.setLayout(main_layout)
        outer_layout.addWidget(main_content_widget, 1)

        self.setMinimumSize(1000, 700)

    # --- NOUVELLE MÉTHODE SLOT pour bouton settings ---
    @Slot()
    def _show_settings_page_from_button(self):
        """Slot spécifique pour le clic sur le bouton engrenage."""
        print("Settings button clicked, showing Settings Page...")
        # Assurer qu'aucun bouton latéral n'est coché
        # Désélectionner tous les boutons peut causer des problèmes si un doit rester actif
        # Alternative: Ne rien faire ici et laisser le bouton actif précédent l'être.
        # Ou: Créer un bouton "Paramètres" dans la liste latérale et le cocher ici.
        # Pour l'instant, on change juste la page :
        self.stacked_widget.setCurrentWidget(self.settings_page_instance)
        # Optionnel: décocher le bouton latéral actif s'il y en a un
        checked_button = self.sidebar_button_group.checkedButton()
        if checked_button:
            # Mettre le groupe temporairement non exclusif pour permettre la décochage
            self.sidebar_button_group.setExclusive(False)
            checked_button.setChecked(False)
            self.sidebar_button_group.setExclusive(True)
            print(f"  Unchecked sidebar button: {checked_button.text()}")

    def navigate_to_section(self, section_name):
        """Trouve le bouton correspondant ou gère le cas spécial 'Paramètres'."""
        print(f"Attempting programmatic navigation to section: {section_name}")
        
        # --- CAS SPÉCIAL POUR PARAMÈTRES --- 
        if section_name == "Paramètres":
             print("  Special case: Navigating to Settings page directly.")
             self._show_settings_page_from_button() # Appeler la méthode du bouton engrenage
             return True # Indiquer le succès
        # ----------------------------------
        
        button_found = False
        target_button = None
        for btn in self.sidebar_button_group.buttons():
            if btn.text() == section_name:
                target_button = btn
                button_found = True
                break
        
        if button_found and target_button:
            if not target_button.isChecked(): 
                print(f"  Button '{section_name}' found. Setting checked to True...")
                target_button.setChecked(True) # Déclenchera _change_page
            else:
                print(f"  Button '{section_name}' already checked. Triggering _change_page manually...")
                self._change_page(target_button) # Appeler manuellement si déjà coché
            return True # Indiquer le succès
        else:
            print(f"  Button for section '{section_name}' not found in sidebar.")
            return False # Indiquer l'échec

    # --- AJOUT DE LA MÉTHODE GETTER --- 
    def get_settings_controller(self):
        """Retourne l'instance du SettingsController gérée par cette page."""
        return self.settings_controller_instance
    # ---------------------------------

    @Slot(QAbstractButton)
    def _change_page(self, button: QAbstractButton): 
        """Change la page affichée et gère la navigation vers les notes de version."""
        button_text = button.text() 
        target_widget = None 
        call_default_page = True # Variable pour savoir s'il faut appeler show_default_page
        
        if button_text == "Documents":
            target_widget = self.documents_page_instance
            controller_instance = self.documents_controller_instance
            
        elif button_text == "A Propos":
            target_widget = self.about_page_instance
            controller_instance = self.about_controller_instance
            
            # --- LOGIQUE SPÉCIFIQUE POUR NOTES DE VERSION --- 
            # Vérifier si on doit aller aux notes APRES avoir sélectionné "A Propos"
            if self.controller and self.controller.navigate_to_notes_after_welcome:
                print("DEBUG _change_page: 'A Propos' selected AND navigation flag is True.")
                if hasattr(controller_instance, 'activate_release_notes_tab'):
                    try:
                        controller_instance.activate_release_notes_tab()
                        print("  Called activate_release_notes_tab on AboutController.")
                        # Important: Remettre le flag à False pour éviter de le refaire
                        self.controller.navigate_to_notes_after_welcome = False
                        print("  Navigation flag reset to False.")
                        call_default_page = False # Ne pas appeler show_default_page si on a activé les notes
                    except Exception as e:
                         print(f"  ERROR calling activate_release_notes_tab: {e}")
                else:
                    print("  ERROR: AboutController does not have activate_release_notes_tab method.")
            # --- FIN LOGIQUE NOTES --- 

        elif button_text == "Preference":
            target_widget = self.preferences_page_instance
            controller_instance = self.preferences_controller_instance
            call_default_page = False # Pas de page par défaut pour Préférences

        else:
            print(f"Debug: Bouton non reconnu: {button_text} (from button: {button})")
            return

        # Appel show_default_page si nécessaire (uniquement si on n'a pas activé les notes)
        if call_default_page and hasattr(controller_instance, 'show_default_page'):
            print(f"Debug: Calling {controller_instance.__class__.__name__}.show_default_page()")
            controller_instance.show_default_page()
        elif call_default_page:
             print(f"Warning: show_default_page not found on {controller_instance.__class__.__name__}")

        # Changer la page affichée
        if target_widget:
            self.stacked_widget.setCurrentWidget(target_widget)
            print(f"Debug: Page changed to {button_text} (Widget: {target_widget})")
        else:
            print(f"Error: target_widget is None for button {button_text}")

    # --- AJOUT : Slot pour gérer la maximisation/restauration --- 
    # (Doit être présent si la barre de titre l'utilise)
    @Slot()
    def _handle_maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        # Informer la barre de titre si elle existe et a la méthode
        if hasattr(self, 'title_bar') and hasattr(self.title_bar, 'setMaximizedState'):
             self.title_bar.setMaximizedState(self.isMaximized())

    # --- AJOUT : Slot pour mettre à jour l'icône Settings --- 
    @Slot(str)
    def _update_settings_icon(self, theme_name):
        try:
            new_icon_path = icon_loader.get_icon_path(self._settings_icon_base)
            new_icon = QIcon(new_icon_path)
            if not new_icon.isNull():
                self.btn_settings.setIcon(new_icon)
            else:
                # Fallback texte
                self.btn_settings.setIcon(QIcon()) 
                self.btn_settings.setText("⚙") 
                self.btn_settings.setFont(QFont("Arial", 12))
        except Exception as e:
            print(f"ERROR: Erreur lors de la mise à jour de l'icône Settings : {e}")
            self.btn_settings.setIcon(QIcon())
            self.btn_settings.setText("⚙") 
            self.btn_settings.setFont(QFont("Arial", 12))
    # ---------------------------------------------------------

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