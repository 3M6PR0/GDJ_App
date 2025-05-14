from typing import List
import os

# --- Imports relatifs supprimés car plus nécessaires --- 
# from .repas import Repas
# from .depense import Depense
# ---------------------------------------------------

class Facture:
    """Représente une ou plusieurs factures associées à une dépense."""

    def __init__(self,
                 folder_path: str,
                 filenames: List[str]):
        """
        Initialise l'objet Facture.

        Args:
            folder_path: Le chemin d'accès au dossier contenant les fichiers de facture.
            filenames: Une liste des noms de fichiers de facture dans le dossier.
        """
        if not isinstance(folder_path, str):
            raise TypeError("folder_path doit être une chaîne de caractères.")
        if not isinstance(filenames, list) or not all(isinstance(f, str) for f in filenames):
            raise TypeError("filenames doit être une liste de chaînes de caractères.")
        if not filenames:
            raise ValueError("La liste filenames ne peut pas être vide.")

        self.folder_path: str = folder_path
        self.filenames: List[str] = filenames

    def get_full_paths(self) -> List[str]:
        """Retourne la liste complète des chemins d'accès aux fichiers de facture."""
        return [os.path.join(self.folder_path, f) for f in self.filenames]

    def __repr__(self):
        return (f"Facture(folder='{self.folder_path}', files={self.filenames})")

    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet Facture pour la sérialisation JSON."""
        # Pour la sauvegarde, nous voulons stocker uniquement le nom du dossier (basename)
        # car il sera copié dans un sous-dossier 'factures' dans l'archive ZIP.
        # Le chemin complet sera reconstruit lors du chargement par rapport à ce sous-dossier.
        return {
            'folder_name': os.path.basename(self.folder_path),
            'filenames': self.filenames
        }

    # Ajouter d'autres méthodes si nécessaire 