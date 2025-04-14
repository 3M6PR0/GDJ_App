import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from controllers.main_controller import MainController
from updater.update_checker import check_for_updates

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    controller = MainController(window)
    window.show()
    check_for_updates()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
