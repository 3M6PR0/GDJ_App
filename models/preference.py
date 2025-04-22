"""Définit la structure des données de préférences de l'application."""

import json
import os

# Importation optionnelle pour Path, mais utilisons str pour l'instant pour simplifier
# from pathlib import Path

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

class Jacmar:
    """Préférences spécifiques à Jacmar."""
    def __init__(self,
                 emplacement: str = "",
                 departement: str = "",
                 titre: str = "",
                 superviseur: str = "",
                 plafond: int = 0):
        self.emplacement = emplacement
        self.departement = departement
        self.titre = titre
        self.superviseur = superviseur
        self.plafond = plafond

    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet."""
        return self.__dict__

class Application:
    """Préférences relatives à l'application elle-même."""
    def __init__(self,
                 theme: str = "Default", # Exemple de valeur par défaut
                 auto_update: bool = True,
                 show_note: bool = True): # Nom d'attribut corrigé
        self.theme = theme
        self.auto_update = auto_update
        self.show_note = show_note

    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet."""
        return self.__dict__

class Preference:
    """Classe principale contenant toutes les préférences."""
    def __init__(self,
                 profile: Profile = None,
                 jacmar: Jacmar = None,
                 application: Application = None):
        # Initialise avec des instances par défaut si aucune n'est fournie
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

    def save(self, filepath="data/preference.json"):
        """Sauvegarde les préférences actuelles dans un fichier JSON."""
        try:
            # S'assurer que le répertoire existe
            dir_path = os.path.dirname(filepath)
            if dir_path: # S'assurer qu'il y a un chemin de dossier (pas juste un nom de fichier)
                os.makedirs(dir_path, exist_ok=True)
            
            # Convertir l'objet en dictionnaire
            data_to_save = self.to_dict()
            
            # Écrire dans le fichier JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            print(f"Préférences sauvegardées avec succès dans {filepath}")
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des préférences dans {filepath}: {e}")

    # def load(self, filepath):
    #     # ... logique de chargement
    #     pass

# Exemple d'utilisation:
if __name__ == '__main__':
    prefs = Preference()

    # Modifier quelques préférences pour le test
    prefs.profile.nom = "Dupont"
    prefs.profile.prenom = "Jean"
    prefs.application.theme = "Dark"
    prefs.jacmar.plafond = 500

    # Sauvegarder les préférences
    prefs.save() # Sauvegarde dans data/preference.json par défaut

    # Vous pouvez vérifier le contenu du fichier data/preference.json généré
