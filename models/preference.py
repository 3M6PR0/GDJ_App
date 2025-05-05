"""Définit la structure des données de préférences de l'application."""

import json
import os
import logging # AJOUT

# Importation optionnelle pour Path, mais utilisons str pour l'instant pour simplifier
# from pathlib import Path

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

# --- AJOUT Logger --- 
# logger = logging.getLogger(__name__) # <- Commenté
logger = logging.getLogger('GDJ_App') # <- Utiliser le logger configuré
# ------------------

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

# --- MODIFICATION: Transformer Preference en Singleton --- 
class Preference:
    """Classe Singleton contenant toutes les préférences."""
    # --- Singleton Implementation --- 
    _instance = None
    _initialized = False
    _preference_file_path = "data/preference.json" # Chemin relatif par défaut

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            logger.debug("Creating new Preference Singleton instance.")
        return cls._instance

    def __init__(self):
        """
        Initializes the Singleton. Creates default sub-objects and loads 
        data from file only on the first call.
        """
        if Preference._initialized: # Utiliser le nom de la classe ici
             return

        # Initialiser les sous-objets SEULEMENT lors de la première initialisation
        self.profile = Profile()
        self.jacmar = Jacmar()
        self.application = Application()
        
        # Charger les données depuis le fichier
        self.load() # Appelle la méthode load de CETTE instance
        
        Preference._initialized = True # Marquer comme initialisé
        logger.info("Preference Singleton initialized.")

    @classmethod
    def get_instance(cls):
        """
        Returns the single instance of the Preference class.
        Creates and initializes it (including loading data) if it doesn't exist yet.
        """
        return cls() # Appelle __new__ et __init__

    # --- Fin Singleton Implementation ---

    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet Preference complet."""
        return {
            "profile": self.profile.to_dict(),
            "jacmar": self.jacmar.to_dict(),
            "application": self.application.to_dict()
        }

    def save(self, relative_filepath=None):
        """Sauvegarde les préférences actuelles via get_resource_path.
           Utilise le chemin par défaut de la classe si non fourni.
        """
        # Utiliser le chemin par défaut de la classe si aucun n'est fourni
        filepath_to_use = relative_filepath or Preference._preference_file_path
        absolute_filepath = get_resource_path(filepath_to_use)
        logger.debug(f"Chemin sauvegarde prefs calculé: {absolute_filepath}")
        try:
            dir_path = os.path.dirname(absolute_filepath)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            data_to_save = self.to_dict()
            
            with open(absolute_filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            logger.info(f"Préférences sauvegardées avec succès dans {absolute_filepath}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des préférences dans {absolute_filepath}: {e}", exc_info=True)

    def load(self, relative_filepath=None):
        """Charge les préférences via get_resource_path.
           Utilise le chemin par défaut de la classe si non fourni.
        """
        # Utiliser le chemin par défaut de la classe si aucun n'est fourni
        filepath_to_use = relative_filepath or Preference._preference_file_path
        absolute_filepath = get_resource_path(filepath_to_use)
        logger.debug(f"Chemin chargement prefs calculé: {absolute_filepath}")

        if not os.path.exists(absolute_filepath):
            logger.warning(f"Fichier de préférences non trouvé: {absolute_filepath}. Utilisation des valeurs par défaut.")
            # Les valeurs par défaut sont déjà définies lors de la création des sous-objets
            # S'assurer de sauvegarder ces valeurs par défaut pour la prochaine fois
            self.save(filepath_to_use)
            return False
            
        try:
            with open(absolute_filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # Mettre à jour les sous-objets existants
            if 'profile' in loaded_data and isinstance(loaded_data['profile'], dict):
                self.profile.update_from_dict(loaded_data['profile'])
            if 'jacmar' in loaded_data and isinstance(loaded_data['jacmar'], dict):
                self.jacmar.update_from_dict(loaded_data['jacmar'])
            if 'application' in loaded_data and isinstance(loaded_data['application'], dict):
                self.application.update_from_dict(loaded_data['application'])
                
            logger.info(f"Préférences chargées avec succès depuis {absolute_filepath}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur JSON dans {absolute_filepath}: {e}. Utilisation des valeurs par défaut inchangées.")
            return False
        except Exception as e:
            logger.error(f"Erreur chargement {absolute_filepath}: {e}. Utilisation des valeurs par défaut inchangées.", exc_info=True)
            return False

    def update_from_dict(self, data: dict):
         """Met à jour les préférences complètes depuis un dictionnaire (utile pour import).""" 
         if 'profile' in data and isinstance(data['profile'], dict):
             self.profile.update_from_dict(data['profile'])
         if 'jacmar' in data and isinstance(data['jacmar'], dict):
             self.jacmar.update_from_dict(data['jacmar'])
         if 'application' in data and isinstance(data['application'], dict):
             self.application.update_from_dict(data['application'])

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
