import sys
from PyQt5.QtWidgets import QApplication
# from ui.main_window import MainWindow  # We'll launch this from the controller now
from controllers.main_controller import MainController
from updater.update_checker import check_for_updates
# Import the new welcome page
# from pages.welcome_page import WelcomePage
# Importer le loader et les chemins
from utils.stylesheet_loader import load_stylesheet
import os # Pour construire les chemins

def main():
    app = QApplication(sys.argv)
    
    # --- Charger et appliquer la feuille de style globale ---
    try:
        # Définir les chemins vers les fichiers QSS
        # Utiliser os.path.join pour la compatibilité multi-OS
        script_dir = os.path.dirname(os.path.abspath(__file__))
        global_qss_path = os.path.join(script_dir, 'resources', 'styles', 'global.qss')
        frame_qss_path = os.path.join(script_dir, 'resources', 'styles', 'frame.qss')
        # Ajouter d'autres fichiers QSS spécifiques ici si nécessaire
        # custom_titlebar_qss_path = os.path.join(script_dir, 'resources', 'styles', 'custom_titlebar.qss')
        
        qss_files = [
            global_qss_path,
            frame_qss_path,
            # custom_titlebar_qss_path,
        ]
        
        # Charger, combiner et formater
        combined_stylesheet = load_stylesheet(qss_files)
        
        # Appliquer à l'application
        app.setStyleSheet(combined_stylesheet)
        print("Feuille de style globale appliquée.")
    except Exception as e:
        print(f"Erreur lors du chargement ou de l'application de la feuille de style: {e}")
    # --- Fin chargement style ---
    
    # We need a controller instance first, which will manage windows
    controller = MainController()
    
    # Show the Welcome Page initially
    # The controller will be passed to it, and the welcome page will use the 
    # controller to open the main window later.
    controller.show_welcome_page() 
    
    # window = MainWindow() # Old way
    # controller = MainController(window) # Old way
    # window.show() # Old way
    
    # Update check can still run early
    check_for_updates()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
