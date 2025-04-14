from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget

class HomePage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("GDJ - v1.0.5")
        layout.addWidget(title)

        # Boutons pour créer ou ouvrir un document
        btn_new = QPushButton("Nouveau Document")
        btn_open = QPushButton("Ouvrir Document")
        layout.addWidget(btn_new)
        layout.addWidget(btn_open)

        btn_new.clicked.connect(self.controller.create_new_document)
        btn_open.clicked.connect(self.controller.open_document)

        # Section récents (exemple statique)
        recents = QListWidget()
        recents.addItem("Document1.doc")
        recents.addItem("Document2.doc")
        layout.addWidget(recents)
