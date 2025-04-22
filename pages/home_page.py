import os
import configparser
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

def get_version_from_file():
    # --- Utiliser get_resource_path --- 
    version_file = get_resource_path("data/version.txt")
    config = configparser.ConfigParser()
    try:
        # Utiliser le chemin absolu
        config.read(version_file, encoding='utf-8') # Ajouter encoding pour être sûr
        ver = config.get("Version", "value")
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier version ({version_file}) :", e)
        ver = "0.0.0"
    # Si la version ne commence pas par "v", on l'ajoute.
    if not ver.startswith("v"):
        ver = "v" + ver
    return ver

class HomePage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        version = get_version_from_file()  # Récupère la version depuis data/version.txt (ex: "v1.0.16")
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
