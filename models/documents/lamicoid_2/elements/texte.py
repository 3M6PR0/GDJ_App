from dataclasses import dataclass
from typing import Literal
from .base import ElementTemplateBase

@dataclass
class ElementTexte(ElementTemplateBase):
    """
    Modèle de données pour un élément texte.
    Hérite de ElementTemplateBase et utilise les dataclasses.
    """
    contenu: str = "Texte"
    nom_police: str = "Arial"
    taille_police_pt: int = 12
    alignement_horizontal: Literal["gauche", "centre", "droite"] = "gauche"
    alignement_vertical: Literal["haut", "centre", "bas"] = "haut"
    type: Literal["texte"] = "texte" 