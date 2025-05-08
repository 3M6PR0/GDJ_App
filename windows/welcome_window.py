# windows/welcome_window.py
# (Contenu de l'ancien pages/welcome_page.py avec remplacement)

import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSpacerItem, QSizePolicy,
                             QStackedWidget, QButtonGroup, QAbstractButton)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot as Slot
from PyQt5.QtGui import QIcon, QPixmap, QFont
import logging
# --- DÉPLACER CETTE LIGNE AU NIVEAU DU MODULE ---
logger = logging.getLogger('GDJ_App') 
# -----------------------------------------------

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
# --- MODIFICATION: Importer SEULEMENT la page Preferences --- 
from pages.preferences.preferences_page import PreferencesPage
# from controllers.preferences.preferences_controller import PreferencesController # <- Supprimé
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
# --- MODIFICATION: Importer SEULEMENT la page Preferences --- 
from pages.preferences.preferences_page import PreferencesPage
# from controllers.preferences.preferences_controller import PreferencesController # <- Supprimé
# --- AJOUT IMPORTS POUR SETTINGS --- 
from pages.settings.settings_page import SettingsPage
from controllers.settings.settings_controller import SettingsController

# --- WelcomeWindow (Anciennement WelcomePage) --- 
class WelcomeWindow(QWidget): # RENOMMÉ
    def __init__(self, controller, app_name="GDJ", version_str="?.?.?"):
        logger.critical(">>> ENTERING WelcomeWindow __init__ <<< START") # Log critique entrée
        super().__init__()
        self.controller = controller
        self.app_name = app_name
        self.version_str = version_str
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)
        self.setObjectName("WelcomeWindow") 

        # --- MODIFICATION: Ne plus instancier PreferencesController ici --- 
        # L'instance globale Preference est chargée via Preference.get_instance()
        # Le PreferencesController sera instancié SEULEMENT si la page est affichée,
        # et il utilisera le Singleton Preference.
        self.preferences_page_instance = PreferencesPage()
        self.preferences_controller_instance = None # <- AJOUT: Initialiser à None
        # ----------------------------------------------------------------

        # --- Instancier UNIQUEMENT les pages ici --- 
        self.documents_page_instance = DocumentsPage()
        # --- SUPPRESSION INSTANCIATION CONTRÔLEUR ICI ---
        # self.documents_controller_instance = DocumentsController(...)
        # ------------------------------------------------
        self.about_page_instance = AboutPage()
        # --- SUPPRESSION INSTANCIATION CONTRÔLEUR ICI ---
        # self.about_controller_instance = AboutController(...)
        # ------------------------------------------------
        self.settings_page_instance = SettingsPage()
        # --- SUPPRESSION INSTANCIATION CONTRÔLEUR ICI ---
        # self.settings_controller_instance = SettingsController(...)
        # ------------------------------------------------
        
        self.stacked_widget = QStackedWidget()
        
        try:
            self.init_ui()
            logger.info("WelcomeWindow UI initialized successfully.")
        except Exception as e_init_ui:
            logger.critical(f"CRITICAL ERROR during WelcomeWindow init_ui: {e_init_ui}", exc_info=True)
            # Que faire ici? La fenêtre risque de ne pas être utilisable.
            # On pourrait essayer de juste montrer une erreur simple?
            # self.setup_error_ui(e_init_ui)
            logger.critical("<<< EXITING WelcomeWindow __init__ DUE TO UI ERROR <<<")
            # Lever l'exception pour que le contrôleur sache qu'il y a eu un problème?
            raise # Propage l'erreur au MainController

        logger.critical("<<< EXITING WelcomeWindow __init__ <<< END") # Log critique sortie

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
                # Utiliser le logger ici
                logger.warning(f"Icône {icon_name} non trouvée: {icon_path}")
            
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
            # Utiliser le logger ici
            logger.warning(f"Icône Settings non trouvée: {settings_icon_path}, utilisation texte.")
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

        # --- Panneau de contenu principal ---
        content_panel = QFrame()
        content_panel.setObjectName("ContentPanel")
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Ajouter les pages AU STACK ICI (AVANT instanciation des contrôleurs)
        self.stacked_widget.addWidget(self.documents_page_instance) # Index 0
        self.stacked_widget.addWidget(self.preferences_page_instance) # Index 1
        self.stacked_widget.addWidget(self.about_page_instance)      # Index 2
        self.stacked_widget.addWidget(self.settings_page_instance)   # Index 3
        
        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_panel, 1)

        outer_layout.addWidget(main_content_widget)
        
        # --- AJOUT: Instancier les contrôleurs ICI, APRÈS que l'UI est prête --- 
        logger.debug("*** WelcomeWindow.init_ui: STARTING CONTROLLER INSTANTIATION ***")
        
        # Documents
        logger.debug("  -> Instantiating DocumentsController...")
        if self.documents_page_instance:
            logger.debug("--- Vérification du format logger AVANT DocumentsController ---")
            try:
                self.documents_controller_instance = DocumentsController(
                    self.documents_page_instance,
                    self.controller # Le main_controller
                )
                logger.debug("  -> DocumentsController INSTANTIATED.")
                if hasattr(self.documents_controller_instance, 'request_settings_page'):
                     self.documents_controller_instance.request_settings_page.connect(self.show_settings_page)
            except Exception as e:
                logger.error(f"Erreur instanciation DocumentsController: {e}", exc_info=True)
                self.documents_controller_instance = None
        else:
            logger.error("WelcomeWindow: Impossible d'instancier DocumentsController car documents_page_instance est None.")

        # A Propos
        try:
            logger.debug("  -> Instantiating AboutController...")
            self.about_controller_instance = AboutController(
                self.about_page_instance, 
                version_str=self.version_str
            )
            logger.debug("  -> AboutController INSTANTIATED.")
        except Exception as e:
             logger.error(f"Erreur instanciation AboutController: {e}", exc_info=True)
             self.about_controller_instance = None
        
        # Settings
        try:
            logger.debug("  -> Instantiating SettingsController...")
            self.settings_controller_instance = SettingsController(
                self.settings_page_instance, 
                self.controller # Le main_controller
            )
            logger.debug("  -> SettingsController INSTANTIATED.")
        except Exception as e:
             logger.error(f"Erreur instanciation SettingsController: {e}", exc_info=True)
             self.settings_controller_instance = None
        logger.debug("*** WelcomeWindow.init_ui: FINISHED CONTROLLER INSTANTIATION ***")
        # ----------------------------------------------------------------------

        # Afficher la page par défaut (Documents)
        self.navigate_to_section("Documents")

    @Slot()
    def show_settings_page(self): # Nouvelle méthode pour afficher Settings
         logger.debug("WelcomeWindow: Showing Settings page via show_settings_page")
         # Décocher les autres boutons
         for btn in self.sidebar_button_group.buttons():
             btn.setChecked(False)
         # Afficher la page dans le stack
         self.stacked_widget.setCurrentIndex(3) 

    # --- Méthode pour afficher Settings via clic bouton (EXISTANTE, ajustée) ---
    @Slot()
    def _show_settings_page_from_button(self):
        logger.debug("WelcomeWindow: Showing Settings page via _show_settings_page_from_button")
        # Décocher les autres boutons
        for btn in self.sidebar_button_group.buttons():
             btn.setChecked(False)
        # Afficher la page dans le stack
        self.stacked_widget.setCurrentIndex(3) # Index 3 pour Settings
        # --- AJOUT: Instancier PreferencesController si besoin --- 
        # Vérifier si un contrôleur existe déjà pour la page des préférences
        # Ce n'est plus nécessaire car Settings a son propre contrôleur
        # if self.preferences_page_instance and not hasattr(self.preferences_page_instance, '_controller_attached'):
        #     try:
        #         # PAS BESOIN D'INSTANCIER PREFERENCESCONTROLLER ICI
        #         # pref_controller = PreferencesController(self.preferences_page_instance, self.controller)
        #         # self.preferences_page_instance._controller_attached = True # Marqueur
        #         print("WelcomeWindow: PreferencesController NOT instantiated here anymore.")
        #     except Exception as e:
        #         print(f"ERROR Instantiating PreferencesController on demand: {e}")
        # -----------------------------------------------------------

    def navigate_to_section(self, section_name):
        """ Navigue vers une section spécifique (ex: "A Propos") après l'init. """
        logger.debug(f"navigate_to_section called with: {section_name}")
        button_to_check = None
        target_page = None

        # --- AJOUT DU CAS DOCUMENTS --- 
        if section_name == "Documents":
            button_to_check = self.nav_buttons.get("Documents")
            target_page = self.documents_page_instance
        # -------------------------------
        elif section_name == "A Propos":
            button_to_check = self.nav_buttons.get("A Propos")
            target_page = self.about_page_instance
        elif section_name == "Paramètres": # Pour la nav auto vers MàJ
             button_to_check = None # Settings n'a pas de bouton nav principal
             target_page = self.settings_page_instance
        # Ajouter d'autres sections si nécessaire
        elif section_name == "Preference": # Exemple si on réactive la navigation directe
            button_to_check = self.nav_buttons.get("Preference")
            target_page = self.preferences_page_instance
        # etc...

        if target_page:
            index = self.stacked_widget.indexOf(target_page)
            if index != -1:
                self.stacked_widget.setCurrentIndex(index)
                logger.debug(f"Switched to page index {index} for section '{section_name}'.")
                
                # Gérer l'état des boutons de navigation
                if button_to_check:
                    logger.debug(f"Attempting to check button '{button_to_check.text()}'.")
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
                    logger.debug("Special condition: Navigating to 'A Propos' and need to show Release Notes.")
                    if hasattr(self.about_controller_instance, 'activate_release_notes_tab'):
                         logger.debug("Calling about_controller_instance.activate_release_notes_tab()...")
                         self.about_controller_instance.activate_release_notes_tab()
                         # Réinitialiser le flag dans le contrôleur principal APRÈS navigation réussie
                         logger.debug("Resetting navigate_to_notes_after_welcome flag in main_controller.")
                         self.controller.navigate_to_notes_after_welcome = False 
                    else:
                         logger.error("ERROR: about_controller_instance does not have 'activate_release_notes_tab' method.")
                # -----------------------------------------------------------------------------------
                return True # Navigation réussie (au moins changement de page)
            else:
                logger.error(f"ERROR: Could not find index for target_page of section '{section_name}'.")
                return False
        else:
            logger.error(f"ERROR: No target page defined for section_name '{section_name}'.")
            return False

    # --- AJOUT : Méthode pour récupérer le SettingsController ---
    def get_settings_controller(self):
        """Retourne l'instance du SettingsController."""
        return self.settings_controller_instance
    # ----------------------------------------------------------

    @Slot(QAbstractButton)
    def _change_page(self, button: QAbstractButton): 
        logger.debug(f"Sidebar button clicked: {button.text()}")
        page_map = {
            "Documents": self.documents_page_instance,
            "Preference": self.preferences_page_instance,
            "A Propos": self.about_page_instance,
        }
        page_widget = page_map.get(button.text())
        
        if page_widget:
            # --- AJOUT: Instanciation du PreferencesController à la demande --- 
            button_text = button.text()
            if button_text == "Preference" and self.preferences_controller_instance is None:
                try:
                    logger.debug("Instantiating PreferencesController on demand...")
                    from controllers.preferences.preferences_controller import PreferencesController 
                    self.preferences_controller_instance = PreferencesController(
                        self.preferences_page_instance, 
                        self.controller # Passer le main controller
                    )
                    logger.debug("PreferencesController instantiated.")
                except ImportError as ie:
                    logger.error(f"ERROR: Could not import PreferencesController: {ie}")
                    # Gérer l'erreur: Afficher un message? Désactiver le bouton?
                    return 
                except Exception as e:
                    logger.error(f"ERROR: Failed to instantiate PreferencesController: {e}")
                    # Gérer l'erreur
                    return
            # ------------------------------------------------------------------
            
            index = self.stacked_widget.indexOf(page_widget)
            if index != -1:
                self.stacked_widget.setCurrentIndex(index)
                logger.debug(f"Switched to page: {button.text()} (index {index})")
            else:
                logger.error(f"ERROR: Page for button '{button.text()}' not found in stacked widget.")
        else:
            logger.warning(f"Warning: No page associated with button '{button.text()}'.")

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
                  logger.error(f"ERROR updating settings icon: {e}")
                  self.btn_settings.setIcon(QIcon())
                  self.btn_settings.setText("?")
    # ---------------------------------------------

    def closeEvent(self, event):
        """Surcharge pour gérer l'événement de fermeture."""
        logger.debug("WelcomeWindow closeEvent received.")
        # Nous n'avons plus besoin des logs critiques ou de la pile d'appel ici.
        # QApplication gérera la fermeture de l'application si c'est la dernière fenêtre
        # et que quitOnLastWindowClosed est True (ce qui est le cas par défaut maintenant).
        event.accept() # Accepter simplement l'événement de fermeture.

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