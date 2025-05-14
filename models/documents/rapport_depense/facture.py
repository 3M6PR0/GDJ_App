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

    @classmethod
    def from_dict(cls, data: dict, base_path_for_factures_in_zip: str) -> 'Facture':
        """
        Crée une instance de Facture à partir d'un dictionnaire et du chemin de base
        où les dossiers de factures ont été extraits du ZIP.

        Args:
            data: Dictionnaire contenant 'folder_name' et 'filenames'.
            base_path_for_factures_in_zip: Le chemin du répertoire 'factures'
                                             extrait du fichier .rdj.
        
        Returns:
            Une instance de Facture.
        """
        folder_name = data.get('folder_name')
        filenames = data.get('filenames')

        if not folder_name or not isinstance(folder_name, str):
            raise ValueError("Clé 'folder_name' manquante ou invalide dans les données de la facture.")
        if not filenames or not isinstance(filenames, list):
            raise ValueError("Clé 'filenames' manquante ou invalide dans les données de la facture.")

        # Reconstituer le chemin complet du dossier de la facture
        # Ce chemin pointera vers l'emplacement où le dossier a été extrait (par exemple, dans FacturesEntrees).
        # Lors de l'ouverture d'un .rdj, les factures seront d'abord extraites dans un tmp,
        # puis copiées vers un nouveau dossier unique dans FacturesEntrees.
        # C'est ce NOUVEAU CHEMIN DANS FacturesEntrees qui doit être utilisé ici.
        # Le 'base_path_for_factures_in_zip' ne sera PAS le self.folder_path final.
        # La logique de copie et de détermination du chemin final sera dans MainController.
        # Pour l'instant, la méthode from_dict se contente de prendre le chemin fourni.
        # MAIS, pour que la facture soit correctement liée aux fichiers physiques,
        # `folder_path` doit être le chemin où les fichiers sont *effectivement* après extraction et copie.
        # Pour l'instant, le contrat de `base_path_for_factures_in_zip` sera le chemin *final* du dossier parent des factures uniques.
        
        # Le `folder_path` qui sera passé au constructeur de Facture est le chemin
        # où le dossier spécifique de cette facture (identifié par folder_name) se trouve DANS l'application
        # après extraction et copie.
        # Exemple: base_path_for_factures_in_zip pourrait être "C:/Users/.../FacturesEntrees"
        # et folder_name est "facture_unique_123".
        # Donc, le folder_path de l'objet Facture sera "C:/Users/.../FacturesEntrees/facture_unique_123"
        # Cependant, la méthode `save` de RapportDepense s'attend à ce que les dossiers de factures (folder_path)
        # soient des chemins absolus vers les dossiers uniques DANS FacturesEntrees.
        # Et to_dict stocke os.path.basename(self.folder_path).
        # Donc, `from_dict` doit reconstruire le chemin complet.
        # Le `base_path_for_factures_in_zip` sera le chemin vers le dossier parent où tous les dossiers de factures
        # individuels (nommés par `folder_name`) ont été copiés.
        
        reconstructed_folder_path = os.path.join(base_path_for_factures_in_zip, folder_name)

        return cls(folder_path=reconstructed_folder_path, filenames=filenames)

    # Ajouter d'autres méthodes si nécessaire 