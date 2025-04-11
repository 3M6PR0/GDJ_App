# models/profile.py
import os
import json
from config import CONFIG

class Profile:
    def __init__(self, nom='', prenom='', telephone='', courriel='',
                 departement='', emplacement='', superviseur='',
                 plafond='', theme='Clair'):
        self.nom = nom
        self.prenom = prenom
        self.telephone = telephone
        self.courriel = courriel
        self.departement = departement
        self.emplacement = emplacement
        self.superviseur = superviseur
        self.plafond = plafond
        self.theme = theme

    def to_dict(self):
        return {
            "nom": self.nom,
            "prenom": self.prenom,
            "telephone": self.telephone,
            "courriel": self.courriel,
            "departement": self.departement,
            "emplacement": self.emplacement,
            "superviseur": self.superviseur,
            "plafond": self.plafond,
            "theme": self.theme
        }

    def update_from_dict(self, data):
        self.nom = data.get('nom', self.nom)
        self.prenom = data.get('prenom', self.prenom)
        self.telephone = data.get('telephone', self.telephone)
        self.courriel = data.get('courriel', self.courriel)
        self.departement = data.get('departement', self.departement)
        self.emplacement = data.get('emplacement', self.emplacement)
        self.superviseur = data.get('superviseur', self.superviseur)
        self.plafond = data.get('plafond', self.plafond)
        self.theme = data.get('theme', self.theme)

    def save_to_file(self, filename="profile.json"):
        storage_path = CONFIG.get('DATA_PATH', 'data')
        os.makedirs(storage_path, exist_ok=True)
        filepath = os.path.join(storage_path, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filename="profile.json"):
        storage_path = CONFIG.get('DATA_PATH', 'data')
        filepath = os.path.join(storage_path, filename)
        if not os.path.exists(filepath):
            return cls()  # Si le fichier n'existe pas, retourne un profil vide par défaut
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(
            nom=data.get('nom', ''),
            prenom=data.get('prenom', ''),
            telephone=data.get('telephone', ''),
            courriel=data.get('courriel', ''),
            departement=data.get('departement', ''),
            emplacement=data.get('emplacement', ''),
            superviseur=data.get('superviseur', ''),
            plafond=data.get('plafond', ''),
            theme=data.get('theme', 'Clair')
        )
