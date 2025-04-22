# controllers/about/about_release_notes_controller.py # <- Nouveau nom
# Contient la logique pour charger et afficher le fichier RELEASE_NOTES.md.

import os
from PyQt5.QtCore import QObject

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

# Import de la vue correspondante (ajuster si nécessaire)
# from pages.about.about_release_notes_page import AboutReleaseNotesPage

# --- Constante pour le chemin relatif ---
RELEASE_NOTES_PATH = "RELEASE_NOTES.md" 

class AboutReleaseNotesController(QObject): # <- Nom de classe mis à jour
    def __init__(self, view: 'QWidget'): # ou AboutReleaseNotesPage
        super().__init__()
        self.view = view
        self.load_notes()

    def load_notes(self):
        """Charge RELEASE_NOTES.md via get_resource_path."""
        content = "Impossible de charger le fichier RELEASE_NOTES.md"
        try:
            # --- Utiliser get_resource_path --- 
            notes_full_path = get_resource_path(RELEASE_NOTES_PATH)
            print(f"DEBUG: Chemin RELEASE_NOTES calculé: {notes_full_path}") # Ajout debug
            
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