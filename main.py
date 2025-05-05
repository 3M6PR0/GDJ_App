import sys
import os
import logging
import traceback
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from utils.paths import get_resource_path
# from ui.main_window import MainWindow  # We'll launch this from the controller now
from controllers.main_controller import MainController
from updater.update_checker import check_for_updates
# Import the new welcome page
# from pages.welcome_page import WelcomePage
# Importer le loader et les chemins
from utils.stylesheet_loader import load_stylesheet
# --- AJOUT IMPORT PREFERENCE --- 
from models.preference import Preference
# --- AJOUT IMPORT ICON LOADER --- 
from utils import icon_loader 

# --- Configuration du Logger --- 
# Importer et appeler setup_logger TOUT AU DÉBUT
from utils.logger import setup_logger
setup_logger(level=logging.DEBUG) # Utiliser DEBUG pendant le dév.
# Maintenant, on peut utiliser logging.getLogger('GDJ_App') partout
logger = logging.getLogger('GDJ_App') # Récupérer le logger configuré
# --- AJOUT LOG DE VÉRIFICATION IMMÉDIAT --- 
logger.info("--- Logger configuré dans main.py (Vérification immédiate) ---")
# ------------------------------------------
# ----------------------------- 

# --- Gestionnaire global d'exceptions --- 
# ... (global_exception_handler existant)

try:
    # --- IMPORTS --- 
    import logging # Assurer import
    logging.info("Imports successful.")

    # --- LIRE LE THÈME PRÉFÉRÉ AU DÉMARRAGE --- 
    initial_theme = 'Sombre' # Défaut sur "Sombre"
    try:
        logging.info("Reading initial theme preference...")
        temp_prefs = Preference()
        temp_prefs.load()
        loaded_theme = temp_prefs.application.theme
        # --- Valider avec "Clair" ou "Sombre" --- 
        if loaded_theme in ['Clair', 'Sombre']:
            initial_theme = loaded_theme
            logging.info(f"Initial theme set to '{initial_theme}' from preferences.")
        else:
            logging.warning(f"Invalid theme value '{loaded_theme}' in preferences. Using default '{initial_theme}'.")
    except AttributeError:
         # --- Message et défaut mis à jour --- 
         logging.warning("Attribute 'application.theme' not found in preferences. Using default 'Sombre'.")
         initial_theme = 'Sombre' 
    except FileNotFoundError:
         # --- Message et défaut mis à jour --- 
         logging.warning("Preference file not found. Using default theme 'Sombre'.")
         initial_theme = 'Sombre' 
    except Exception as e_prefs:
        # --- Défaut mis à jour --- 
        logging.error(f"Error loading preferences to read initial theme: {e_prefs}. Using default '{initial_theme}'.", exc_info=True)
    # --- DÉFINIR LE THÈME INITIAL POUR LES ICÔNES --- 
    icon_loader.set_active_theme(initial_theme)
    # --------------------------------------------

    def main():
        logging.info("Entering main() function.")
        app = QApplication(sys.argv)
        logging.info("QApplication instance created.")
        
        # --- Définition icône --- 
        try:
            # --- Utiliser icon_loader --- 
            icon_path = icon_loader.get_icon_path("logo-gdj.ico") 
            if icon_path and os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
                logging.info(f"Application icon set from: {icon_path}")
            else:
                logging.warning(f"Application icon (logo-gdj.ico) not found at calculated path: {icon_path}")
        except Exception as e_icon:
            logging.error(f"Error setting application icon: {e_icon}", exc_info=True)
        # --------------------------
        
        # --- Chargement QSS (utilise initial_theme, déjà correct) ---
        try:
            qss_files = ["resources/styles/global.qss", "resources/styles/frame.qss"]
            logging.info(f"Loading stylesheet with initial theme: '{initial_theme}'")
            combined_stylesheet = load_stylesheet(qss_files, theme_name=initial_theme)
            app.setStyleSheet(combined_stylesheet)
            logging.info("Global stylesheet applied.")
        except Exception as e_qss:
            logging.error(f"Error loading/applying stylesheet: {e_qss}", exc_info=True)
        # ------------------------------------------
        
        logging.info("Creating MainController instance...")
        # Note: MainController n'a plus besoin du flag post_install pour le thème
        controller = MainController()
        logging.info("MainController instance created.")

        logging.info("Calling controller.show_welcome_page()...")
        controller.show_welcome_page()
        logging.info("controller.show_welcome_page() finished.")

        logging.info("Starting QApplication event loop (app.exec_)...")
        exit_code = app.exec_()
        logging.info(f"QApplication event loop finished. Exit code: {exit_code}")
        sys.exit(exit_code)

    if __name__ == '__main__':
        logging.info("__name__ == '__main__', calling main().")
        main()
    else:
        logging.warning("Script executed when __name__ != '__main__'")

except Exception as main_e:
    logging.exception("CRITICAL ERROR during script initialization or main execution:")
    print(f"CRITICAL ERROR: {main_e}")
    traceback.print_exc()
    sys.exit(1)
