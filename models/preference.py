"""Définit la structure des données de préférences de l'application."""

import json
import os

# Importation optionnelle pour Path, mais utilisons str pour l'instant pour simplifier
# from pathlib import Path

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

class Profile:
    """Préférences relatives au profil utilisateur."""
    def __init__(self,
                 nom: str = "",
                 prenom: str = "",
                 telephone: str = "",
                 courriel: str = "",
                 signature_path: str = ""): # Utilisation de str pour le chemin
        self.nom = nom
        self.prenom = prenom
        self.telephone = telephone
        self.courriel = courriel
        self.signature_path = signature_path

    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet."""
        return self.__dict__

    def update_from_dict(self, data: dict):
        """Met à jour les attributs depuis un dictionnaire."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Jacmar:
    """Préférences spécifiques à Jacmar."""
    def __init__(self,
                 emplacement: str = "",
                 departement: str = "",
                 titre: str = "",
                 superviseur: str = "",
                 plafond: str = ""):
        self.emplacement = emplacement
        self.departement = departement
        self.titre = titre
        self.superviseur = superviseur
        self.plafond = plafond

    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet."""
        return self.__dict__

    def update_from_dict(self, data: dict):
        """Met à jour les attributs depuis un dictionnaire."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Application:
    """Préférences relatives à l'application elle-même."""
    def __init__(self,
                 theme: str = "Sombre",
                 auto_update: bool = True,
                 show_note: bool = True):
        self.theme = theme
        self.auto_update = auto_update
        self.show_note = show_note

    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet."""
        return self.__dict__

    def update_from_dict(self, data: dict):
        """Met à jour les attributs depuis un dictionnaire."""
        for key, value in data.items():
            if hasattr(self, key):
                # Assurer la conversion en bool pour les booléens
                if key in ['auto_update', 'show_note']:
                    setattr(self, key, bool(value))
                else:
                    setattr(self, key, value)

class Preference:
    """Classe principale contenant toutes les préférences."""
    # --- Chemin par défaut relatif --- 
    DEFAULT_PREF_FILENAME = "data/preference.json"

    def __init__(self,
                 profile: Profile = None,
                 jacmar: Jacmar = None,
                 application: Application = None):
        self.profile = profile if profile is not None else Profile()
        self.jacmar = jacmar if jacmar is not None else Jacmar()
        self.application = application if application is not None else Application()

    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet Preference complet."""
        return {
            "profile": self.profile.to_dict(),
            "jacmar": self.jacmar.to_dict(),
            "application": self.application.to_dict()
        }

    def save(self, relative_filepath=DEFAULT_PREF_FILENAME):
        """Sauvegarde les préférences actuelles via get_resource_path."""
        # Construire le chemin absolu
        absolute_filepath = get_resource_path(relative_filepath)
        print(f"DEBUG: Chemin sauvegarde prefs calculé: {absolute_filepath}") # Ajout debug
        try:
            # S'assurer que le répertoire existe
            dir_path = os.path.dirname(absolute_filepath)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            data_to_save = self.to_dict()
            
            # Écrire dans le fichier JSON en utilisant le chemin absolu
            with open(absolute_filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            print(f"Préférences sauvegardées avec succès dans {absolute_filepath}")
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des préférences dans {absolute_filepath}: {e}")

    def load(self, relative_filepath=DEFAULT_PREF_FILENAME):
        """Charge les préférences via get_resource_path."""
        # Construire le chemin absolu
        absolute_filepath = get_resource_path(relative_filepath)
        print(f"DEBUG: Chemin chargement prefs calculé: {absolute_filepath}") # Ajout debug

        if not os.path.exists(absolute_filepath):
            print(f"Fichier de préférences non trouvé: {absolute_filepath}. Utilisation des valeurs par défaut.")
            # Initialiser avec les valeurs par défaut (déjà fait dans __init__)
            # self.__init__() # Réinitialiser explicitement ?
            return False
            
        try:
            # Lire depuis le chemin absolu
            with open(absolute_filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # Mettre à jour les sous-objets avec les données chargées
            if 'profile' in loaded_data and isinstance(loaded_data['profile'], dict):
                self.profile.update_from_dict(loaded_data['profile'])
            if 'jacmar' in loaded_data and isinstance(loaded_data['jacmar'], dict):
                self.jacmar.update_from_dict(loaded_data['jacmar'])
            if 'application' in loaded_data and isinstance(loaded_data['application'], dict):
                self.application.update_from_dict(loaded_data['application'])
                
            print(f"Préférences chargées avec succès depuis {absolute_filepath}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"Erreur JSON dans {absolute_filepath}: {e}...")
            return False
        except Exception as e:
            print(f"Erreur chargement {absolute_filepath}: {e}...")
            return False

# Exemple d'utilisation:
if __name__ == '__main__':
    # Créer des préférences initiales et sauvegarder
    prefs_to_save = Preference()
    prefs_to_save.profile.nom = "Sauvegardé"
    prefs_to_save.application.theme = "Noir"
    prefs_to_save.save("data/test_prefs.json")
    print("-----")
    
    # Créer une nouvelle instance vide et charger
    prefs_to_load = Preference() # Commence avec les valeurs par défaut
    print(f"Avant chargement - Nom: {prefs_to_load.profile.nom}, Thème: {prefs_to_load.application.theme}")
    loaded_ok = prefs_to_load.load("data/test_prefs.json")
    if loaded_ok:
        print(f"Après chargement - Nom: {prefs_to_load.profile.nom}, Thème: {prefs_to_load.application.theme}")
    else:
        print("Chargement échoué.")
