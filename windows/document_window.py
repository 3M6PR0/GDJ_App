# windows/document_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class DocumentWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau Document")
        self.setObjectName("DocumentWindow")
        # self.setWindowFlags(Qt.Window) # Utiliser les décorations standard pour l'instant

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Fenêtre de document (Contenu à venir)"))
        
        self.setLayout(layout)
        print("DocumentWindow instance créée")

# Optionnel: pour tester cette fenêtre seule
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = DocumentWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_()) 