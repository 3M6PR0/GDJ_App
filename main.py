import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from utils.paths import get_resource_path
import os
# from ui.main_window import MainWindow  # We'll launch this from the controller now
from controllers.main_controller import MainController
from updater.update_checker import check_for_updates
# Import the new welcome page
# from pages.welcome_page import WelcomePage
# Importer le loader et les chemins
from utils.stylesheet_loader import load_stylesheet

def main():
    app = QApplication(sys.argv)
    
    # --- DÉFINIR L'ICÔNE DE L'APPLICATION GLOBALE ---
    try:
        icon_path = get_resource_path("resources/images/logo-gdj.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            print(f"Icône de l'application définie sur : {icon_path}")
        else:
            print(f"Avertissement: Icône de l'application non trouvée à {icon_path}")
    except Exception as e:
        print(f"Erreur lors de la définition de l'icône de l'application: {e}")
    # --------------------------------------------------
    
    # --- Charger et appliquer la feuille de style globale ---
    try:
        # --- Définir directement les chemins relatifs --- 
        # Retirer: script_dir = os.path.dirname(os.path.abspath(__file__))
        # Retirer: global_qss_path = os.path.join(script_dir, 'resources', 'styles', 'global.qss')
        # Retirer: frame_qss_path = os.path.join(script_dir, 'resources', 'styles', 'frame.qss')
        
        # Passer les chemins RELATIFS à load_stylesheet
        qss_files = [
            "resources/styles/global.qss",
            "resources/styles/frame.qss",
            # Ajoutez d'autres fichiers QSS ici si nécessaire
            # "resources/styles/custom_titlebar.qss",
        ]
        
        # Charger, combiner et formater (load_stylesheet utilise get_resource_path)
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
