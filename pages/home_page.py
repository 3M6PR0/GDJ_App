import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget

def get_version_from_file():
    version_file = os.path.join("data", "version.txt")
    try:
        with open(version_file, "r", encoding="utf-8") as f:
            ver = f.read().strip()
        # Si la version ne commence pas par "v", vous pouvez l'ajouter ici ou la laisser telle quelle.
        if not ver.startswith("v"):
            ver = "v" + ver
        return ver
    except Exception as e:
        print("Erreur lors de la lecture du fichier version :", e)
        return "v0.0.0"  # Version par défaut en cas d'erreur

class HomePage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        version = get_version_from_file()  # Récupère la version depuis data/version.txt
        title = QLabel(f"GDJ - {version}")
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
