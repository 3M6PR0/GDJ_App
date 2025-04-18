# controllers/about/about_release_notes_controller.py # <- Nouveau nom
# Contient la logique pour charger et afficher le fichier RELEASE_NOTES.md.

import os
from PyQt5.QtCore import QObject

# Import de la vue correspondante (ajuster si nécessaire)
# from pages.about.about_release_notes_page import AboutReleaseNotesPage

RELEASE_NOTES_PATH = "RELEASE_NOTES.md" # Chemin relatif depuis la racine du projet

class AboutReleaseNotesController(QObject): # <- Nom de classe mis à jour
    def __init__(self, view: 'QWidget'): # ou AboutReleaseNotesPage
        super().__init__()
        self.view = view
        self.load_notes()

    def load_notes(self):
        """Charge le contenu du fichier RELEASE_NOTES.md."""
        content = "Impossible de charger le fichier RELEASE_NOTES.md"
        try:
            # Construire le chemin absolu en remontant de deux niveaux
            # controllers/about -> controllers -> racine
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            notes_full_path = os.path.join(script_dir, RELEASE_NOTES_PATH)
            
            if os.path.exists(notes_full_path):
                with open(notes_full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = f"Fichier non trouvé: {notes_full_path}"
        except Exception as e:
            content = f"Erreur lors du chargement de RELEASE_NOTES.md: {e}"
        
        # Assurez-vous que la vue a la méthode set_content
        if hasattr(self.view, 'set_content'):
            self.view.set_content(content)
        else:
            print("Erreur: La vue associée n'a pas de méthode set_content")

    print("AboutReleaseNotesController initialized") # Debug 