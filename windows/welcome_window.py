# windows/welcome_window.py
# (Contenu de l'ancien pages/welcome_page.py avec remplacement)

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
# -------------------\

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

# --- WelcomeWindow (Anciennement WelcomePage) --- 
class WelcomeWindow(QWidget): # RENOMMÉ
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
        # -------------------------------------------------\
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
        self.btn_settings.setToolTip("Préférences") # Correction ToolTip
        self.btn_settings.clicked.connect(self._show_settings_page_from_button)
        
        settings_layout.addWidget(self.btn_settings)
        settings_layout.addStretch()
        sidebar_layout.addLayout(settings_layout)

        # Connecter le groupe de boutons APRES que tous les boutons (...) existent
        self.sidebar_button_group.buttonClicked.connect(self._change_page)

        # --- Connecter le signal de thème pour l'icône Settings --- 
        signals.theme_changed_signal.connect(self._update_settings_icon)
        # ----------------------------------------------------------\

        main_layout.addWidget(sidebar)

        # --- Zone de contenu principale (droite) --- 
        content_area = QFrame()
        content_area.setObjectName("ContentAreaFrame") # Nouveau nom pour style éventuel
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0) 
        content_layout.setSpacing(0)

        self.stacked_widget.setObjectName("ContentArea") # Donner un nom au QStackedWidget
        
        # Ajouter les pages au stacked widget
        self.stacked_widget.addWidget(self.documents_page_instance)
        self.stacked_widget.addWidget(self.preferences_page_instance)
        self.stacked_widget.addWidget(self.about_page_instance)
        self.stacked_widget.addWidget(self.settings_page_instance) # Ajouter Settings

        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_area, 1) # Donner plus d'espace à droite

        outer_layout.addWidget(main_content_widget, 1)

        # --- Redimensionner la fenêtre --- 
        self.resize(1000, 700) 
        # -------------------------------

        # --- Sélectionner la page par défaut (Documents) --- 
        # Trouver le bouton "Documents" et le checker au démarrage
        for btn in self.sidebar_button_group.buttons():
            if btn.text() == "Documents":
                btn.setChecked(True)
                # Peut-être appeler _change_page ici aussi pour initialiser correctement ?
                self._change_page(btn) # Assure que la page est affichée
                break
                
    @Slot()
    def _show_settings_page_from_button(self):
        """Slot pour le clic sur le bouton Settings. Affiche la page Settings."""
        print("Settings button clicked, changing page...")
        
        # Désélectionner les boutons de navigation principaux
        # car Settings n'est pas l'un d'eux.
        current_button = self.sidebar_button_group.checkedButton()
        if current_button:
            # Déchecker le bouton actuel SANS déclencher _change_page
            # En déconnectant temporairement le signal ou en utilisant blockSignals
            self.sidebar_button_group.setExclusive(False) # Permettre de déchecker
            current_button.setChecked(False)
            self.sidebar_button_group.setExclusive(True) # Rétablir l'exclusivité
            # Mettre à jour le style visuel du container du bouton déchecké
            if hasattr(current_button, 'parentWidget') and callable(current_button.parentWidget):
                container = current_button.parentWidget()
                if container and container.objectName() == "SidebarButtonContainer":
                     container.setProperty("checked", False)
                     container.style().unpolish(container)
                     container.style().polish(container)

        # Changer l'index du stacked widget
        index = self.stacked_widget.indexOf(self.settings_page_instance)
        if index != -1:
            self.stacked_widget.setCurrentIndex(index)
            print(f"Switched to Settings page (index {index}).")
        else:
            print("ERROR: Could not find Settings page index in stacked widget.")
            
    def navigate_to_section(self, section_name):
        """ Navigue vers une section spécifique (ex: "A Propos") après l'init. """
        print(f"navigate_to_section called with: {section_name}")
        button_to_check = None
        target_page = None

        if section_name == "A Propos":
            button_to_check = self.nav_buttons.get("A Propos")
            target_page = self.about_page_instance
        elif section_name == "Paramètres": # Pour la nav auto vers MàJ
             button_to_check = None # Settings n'a pas de bouton nav principal
             target_page = self.settings_page_instance
        # Ajouter d'autres sections si nécessaire
        # elif section_name == "Preference":
        #     button_to_check = self.nav_buttons.get("Preference")
        #     target_page = self.preferences_page_instance
        # etc...

        if target_page:
            index = self.stacked_widget.indexOf(target_page)
            if index != -1:
                self.stacked_widget.setCurrentIndex(index)
                print(f"Switched to page index {index} for section '{section_name}'.")
                
                # Gérer l'état des boutons de navigation
                if button_to_check:
                    print(f"Attempting to check button '{button_to_check.text()}'.")
                    # Désélectionner le bouton actuel d'abord (si différent)
                    current_button = self.sidebar_button_group.checkedButton()
                    if current_button and current_button != button_to_check:
                         self.sidebar_button_group.setExclusive(False)
                         current_button.setChecked(False)
                         self.sidebar_button_group.setExclusive(True)
                    # Checker le nouveau bouton (peut-être déjà fait par _change_page si appelé)
                    if not button_to_check.isChecked():
                        button_to_check.setChecked(True) 
                elif section_name == "Paramètres": # Cas spécial Settings
                     # Assurer qu'aucun bouton de nav n'est checké
                     current_button = self.sidebar_button_group.checkedButton()
                     if current_button:
                         self.sidebar_button_group.setExclusive(False)
                         current_button.setChecked(False)
                         self.sidebar_button_group.setExclusive(True)
                         # Mettre à jour style du container
                         if hasattr(current_button, 'parentWidget') and callable(current_button.parentWidget):
                             container = current_button.parentWidget()
                             if container and container.objectName() == "SidebarButtonContainer":
                                 container.setProperty("checked", False)
                                 container.style().unpolish(container)
                                 container.style().polish(container)
                
                # --- Si la navigation vers A Propos est demandée, activer l'onglet Release Notes --- 
                if section_name == "A Propos" and self.controller.navigate_to_notes_after_welcome:
                    print("Special condition: Navigating to 'A Propos' and need to show Release Notes.")
                    if hasattr(self.about_controller_instance, 'activate_release_notes_tab'):
                         print("Calling about_controller_instance.activate_release_notes_tab()...")
                         self.about_controller_instance.activate_release_notes_tab()
                         # Réinitialiser le flag dans le contrôleur principal APRÈS navigation réussie
                         print("Resetting navigate_to_notes_after_welcome flag in main_controller.")
                         self.controller.navigate_to_notes_after_welcome = False 
                    else:
                         print("ERROR: about_controller_instance does not have 'activate_release_notes_tab' method.")
                # -----------------------------------------------------------------------------------
                return True # Navigation réussie (au moins changement de page)
            else:
                print(f"ERROR: Could not find index for target_page of section '{section_name}'.")
                return False
        else:
            print(f"ERROR: No target page defined for section_name '{section_name}'.")
            return False

    # --- AJOUT : Méthode pour récupérer le SettingsController ---
    def get_settings_controller(self):
        """Retourne l'instance du SettingsController."""
        return self.settings_controller_instance
    # ----------------------------------------------------------

    @Slot(QAbstractButton)
    def _change_page(self, button: QAbstractButton): 
        print(f"Sidebar button clicked: {button.text()}")
        page_map = {
            "Documents": self.documents_page_instance,
            "Preference": self.preferences_page_instance,
            "A Propos": self.about_page_instance,
        }
        page_widget = page_map.get(button.text())
        
        if page_widget:
            index = self.stacked_widget.indexOf(page_widget)
            if index != -1:
                self.stacked_widget.setCurrentIndex(index)
                print(f"Switched to page: {button.text()} (index {index})")
            else:
                print(f"ERROR: Page for button '{button.text()}' not found in stacked widget.")
        else:
            print(f"Warning: No page associated with button '{button.text()}'.")

        # S'assurer que l'état visuel des autres boutons est correct
        # (Normalement géré par QButtonGroup et les connexions lambda, mais double check)
        for btn in self.sidebar_button_group.buttons():
            container = btn.parentWidget()
            is_checked = (btn == button)
            if container and container.objectName() == "SidebarButtonContainer":
                current_prop = container.property("checked")
                if current_prop != is_checked: # Seulement si changement nécessaire
                    container.setProperty("checked", is_checked)
                    container.style().unpolish(container)
                    container.style().polish(container)

    @Slot()
    def _handle_maximize_restore(self):
        # Logique pour maximiser/restaurer la fenêtre
        if self.isMaximized():
            self.showNormal()
            # Changer l'icône pour "maximiser"
            # self.title_bar.update_maximize_icon(False)
        else:
            self.showMaximized()
            # Changer l'icône pour "restaurer"
            # self.title_bar.update_maximize_icon(True)

    # --- AJOUT : Slot pour màj icône Settings ---
    @Slot(str)
    def _update_settings_icon(self, theme_name):
         if self.btn_settings and self._settings_icon_base:
             try:
                 absolute_icon_path = icon_loader.get_icon_path(self._settings_icon_base)
                 if os.path.exists(absolute_icon_path):
                     icon = QIcon(absolute_icon_path)
                     icon_size = self.btn_settings.iconSize() # Garder la taille existante
                     if not icon.isNull():
                         self.btn_settings.setIcon(icon)
                         self.btn_settings.setIconSize(icon_size) # Réappliquer la taille
                     else:
                         self.btn_settings.setIcon(QIcon()) # Icône vide si non trouvée
                         self.btn_settings.setText("?") # Placeholder
                 else:
                     self.btn_settings.setIcon(QIcon())
                     self.btn_settings.setText("?")
             except Exception as e:
                  print(f"ERROR updating settings icon: {e}")
                  self.btn_settings.setIcon(QIcon())
                  self.btn_settings.setText("?")
    # ---------------------------------------------

# Pour tester la page seule (optionnel)
if __name__ == '__main__':
    class DummyController:
        def navigate_to_notes_after_welcome(self): return False
        def apply_theme(self, name): print(f"Dummy apply_theme: {name}")
    
    app = QApplication(sys.argv)
    # Test avec le contrôleur factice
    welcome_window = WelcomeWindow(DummyController()) # RENOMMÉ
    welcome_window.show()
    sys.exit(app.exec_()) 