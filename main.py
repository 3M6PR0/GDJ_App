import sys
from PyQt5.QtWidgets import QApplication
# from ui.main_window import MainWindow  # We'll launch this from the controller now
from controllers.main_controller import MainController
from updater.update_checker import check_for_updates
# Import the new welcome page
from pages.welcome_page import WelcomePage

def main():
    app = QApplication(sys.argv)
    
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
