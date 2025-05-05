# controllers/settings_window_controller.py
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QAbstractButton # Pour typer le slot _change_page

import logging
# logger = logging.getLogger(__name__) # <- Commenté
logger = logging.getLogger('GDJ_App') # <- Utiliser le logger configuré

# Importer les contrôleurs des sous-pages
from controllers.preferences.preferences_controller import PreferencesController
from controllers.about.about_controller import AboutController
from controllers.settings.settings_controller import SettingsController

class SettingsWindowController(QObject):
    def __init__(self, view: 'SettingsWindow', main_controller=None):
        super().__init__()
        self.view = view
        self.main_controller = main_controller # Référence au contrôleur principal si besoin
        
        # Instancier les contrôleurs des sous-pages
        # Il faut leur passer les instances des pages depuis la vue
        self.preferences_controller = PreferencesController(
            self.view.get_page_widget("Preference")
            # Pas besoin de main_controller ici a priori
        )
        
        self.about_controller = AboutController(
            self.view.get_page_widget("A Propos"),
            version_str=self.view.version_str # Passer la version depuis la vue
        )
        
        # Le SettingsController (mises à jour) a besoin du main_controller
        self.settings_updates_controller = SettingsController(
            self.view.get_page_widget("Updates"),
            self.main_controller
        )
        
        logger.info("SettingsWindowController initialized with sub-controllers.")

    @pyqtSlot(QAbstractButton)
    def change_page(self, button: QAbstractButton):
        """Slot appelé quand un bouton de navigation principal est cliqué."""
        page_name = button.text().strip() # Utiliser le texte du bouton comme clé
        logger.info(f"SettingsWindowController: Navigation requested to '{page_name}'")
        
        page_widget = self.view.get_page_widget(page_name)
        
        if page_widget:
            self.view.stacked_widget.setCurrentWidget(page_widget)
            logger.info(f"SettingsWindowController: Switched to page '{page_name}'")
        else:
            logger.warning(f"SettingsWindowController: Page widget not found for name '{page_name}'")
            
    @pyqtSlot()
    def show_updates_page(self):
        """Slot appelé quand le bouton 'Mises à jour' est cliqué."""
        logger.info("SettingsWindowController: Navigation requested to Updates page (via button)")
        page_widget = self.view.get_page_widget("Updates")
        if page_widget:
            self.view.stacked_widget.setCurrentWidget(page_widget)
            # Décocher les autres boutons de navigation principale
            self.view.sidebar_button_group.setExclusive(False) # Permettre de tout décocher
            for btn in self.view.nav_buttons.values():
                btn.setChecked(False)
            self.view.sidebar_button_group.setExclusive(True) # Rétablir l'exclusivité
            logger.info("SettingsWindowController: Switched to Updates page.")
        else:
            logger.warning("SettingsWindowController: Updates page widget not found.") 