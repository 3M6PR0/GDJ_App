import sys
import os
import logging
import traceback
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
# from ui.main_window import MainWindow  # We'll launch this from the controller now
# from controllers.main_controller import MainController
# from updater.update_checker import check_for_updates
# Import the new welcome page
# from pages.welcome_page import WelcomePage
# Importer le loader et les chemins
# from utils.stylesheet_loader import load_stylesheet
# --- AJOUT IMPORT PREFERENCE --- 
from models.preference import Preference
# --- AJOUT IMPORT ICON LOADER --- 
from utils import icon_loader 
# --- AJOUT IMPORT POUR INITIALISATION DES SIGNAUX ---
from utils.signals import initialize_global_signals
# ----------------------------------------------------

# --- Configuration du Logger --- 
# Importer et appeler setup_logger TOUT AU DÉBUT
from utils.logger import setup_logger
setup_logger() # MODIFIÉ: Appel sans argument
# Maintenant, on peut utiliser logging.getLogger('GDJ_App') partout
logger = logging.getLogger('GDJ_App') # Récupérer le logger configuré
# --- AJOUT LOG DE VÉRIFICATION IMMÉDIAT --- 
logger.debug("--- Logger configuré dans main.py (Vérification immédiate) ---")
# ------------------------------------------
# ----------------------------- 

# --- Gestionnaire global d'exceptions --- 
# ... (global_exception_handler existant)

def main():
    logging.info("Entering main() function.")
    app = QApplication(sys.argv)
    logging.info("QApplication instance created.")
    
    # --- RÉTABLIR LA FERMETURE AUTO PAR DÉFAUT ---
    # app.setQuitOnLastWindowClosed(False) # On remet le comportement normal
    app.setQuitOnLastWindowClosed(True) # Comportement par défaut de Qt
    logger.info("app.quitOnLastWindowClosed set to default (True).")
    # --------------------------------------------
    
    # --- INITIALISATION DES SIGNAUX GLOBAUX ---
    try:
        initialize_global_signals(app_instance=app)
        logging.info("Global signals initialized successfully.")
    except Exception as e_signals_init:
        logger.critical(f"CRITICAL ERROR during global signals initialization: {e_signals_init}", exc_info=True)
        sys.exit(1) # Quitter si les signaux ne peuvent pas être initialisés
    # ------------------------------------------
    
    # --- IMPORTS LOCAUX À LA FONCTION main() (APRÈS INIT SIGNAUX) ---
    from utils.paths import get_resource_path # Gardé pour clarté, pourrait être global si non dépendant
    # from updater.update_checker import check_for_updates # Si nécessaire, déplacez aussi
    from controllers.main_controller import MainController # Import local
    from utils.stylesheet_loader import load_stylesheet # Import local
    from models.preference import Preference # Import local
    from utils import icon_loader # Import local
    # -----------------------------------------------------------------------------

    # --- LIRE LE THÈME PRÉFÉRÉ AU DÉMARRAGE ---
    initial_theme = 'Sombre' # Défaut sur "Sombre"
    try:
        logging.info("Reading initial theme preference...")
        temp_prefs = Preference() # Utilise l'import local Preference
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
    icon_loader.set_active_theme(initial_theme) # Utilise l'import local icon_loader
    # --------------------------------------------
    
    # --- Définition icône --- 
    try:
        icon_path = icon_loader.get_icon_path("logo-gdj.ico") # Utilise l'import local icon_loader
        if icon_path and os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            logging.info(f"Application icon set from: {icon_path}")
        else:
            logger.warning(f"Application icon (logo-gdj.ico) not found at calculated path: {icon_path}")
    except Exception as e_icon:
        logger.error(f"Error setting application icon: {e_icon}", exc_info=True)
    # --------------------------
    
    # --- Chargement QSS (utilise initial_theme, déjà correct) ---
    try:
        qss_files = ["resources/styles/global.qss", "resources/styles/frame.qss"]
        logging.info(f"Loading stylesheet with initial theme: '{initial_theme}'")
        combined_stylesheet = load_stylesheet(qss_files, theme_name=initial_theme) # Utilise l'import local load_stylesheet
        app.setStyleSheet(combined_stylesheet)
        logging.info("Global stylesheet applied.")
    except Exception as e_qss:
        logging.error(f"Error loading/applying stylesheet: {e_qss}", exc_info=True)
    # ------------------------------------------
    
    logging.info("Creating MainController instance...")
    controller = MainController() # Utilise l'import local MainController
    logging.info("MainController instance created.")

    logging.info("Calling controller.show_welcome_page()...")
    controller.show_welcome_page()
    logging.info("controller.show_welcome_page() finished.")

    logging.info("Starting QApplication event loop (app.exec_)...")
    exit_code = app.exec_()
    logging.info(f"QApplication event loop finished. Exit code: {exit_code}")
    sys.exit(exit_code)

if __name__ == '__main__':
    # Le bloc try-except global est déplacé pour entourer uniquement l'appel à main()
    # afin que les imports au niveau du module en dehors de main() ne soient pas affectés
    # s'ils ne sont pas censés l'être.
    try:
        logging.info("__name__ == '__main__', calling main().")
        main()
    except Exception as main_e:
        # S'assurer que le logger est disponible même en cas d'erreur très précoce
        # (normalement, setup_logger est déjà appelé)
        critical_logger = logging.getLogger('GDJ_App_CRITICAL')
        if not critical_logger.hasHandlers(): # Simple vérification pour éviter double config
            # Configuration minimale si le logger principal n'a pas fonctionné
            logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        critical_logger.exception("CRITICAL ERROR during script initialization or main execution:")
        sys.exit(1)
    else:
        # Ce cas est moins courant pour le point d'entrée principal.
        logging.warning("Script executed when __name__ != '__main__'")
