import uuid
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class DocumentPage(QWidget):
    def __init__(self, title="Document"):
        super().__init__()
        # Chaque document a un identifiant unique
        self.id = str(uuid.uuid4())
        self.title = title
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel(f"Contenu de {self.title}")
        layout.addWidget(label)
