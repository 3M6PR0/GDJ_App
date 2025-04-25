# windows/document_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt, QEvent
from ui.components.custom_titlebar import CustomTitleBar

class DocumentWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setObjectName("DocumentWindow")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self, title="Generateur de document Jacmar", icon_base_name="logo-gdj.png", show_menu_button_initially=True)
        main_layout.addWidget(self.title_bar)

        separator_line = QFrame(self)
        separator_line.setObjectName("TitleSeparatorLine")
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Plain)
        separator_line.setFixedHeight(1)
        main_layout.addWidget(separator_line)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.addWidget(QLabel("Fenêtre de document (Contenu à venir)"))
        main_layout.addWidget(content_widget, 1)

        self.setLayout(main_layout)
        print("DocumentWindow instance créée avec CustomTitleBar")

        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self and event.type() == QEvent.MouseButtonPress:
            if self.title_bar.btn_file and self.title_bar.btn_file.isVisible():
                if not self.title_bar.geometry().contains(event.pos()):
                    self.title_bar.show_initial_state()
        
        return super().eventFilter(obj, event)

# Optionnel: pour tester cette fenêtre seule
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = DocumentWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_()) 