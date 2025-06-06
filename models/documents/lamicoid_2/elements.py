"""Définit les différents types d'éléments pouvant composer un TemplateLamicoid."""

from dataclasses import dataclass, field
from typing import Literal

@dataclass
class ElementTemplateBase:
    """Classe de base pour tous les éléments d'un template."""
    element_id: str
    x_mm: float
    y_mm: float
    # Le champ 'type' est retiré de la base et géré directement par chaque 
    # classe enfant pour résoudre le conflit d'initialisation des dataclasses.

@dataclass
class ElementTexte(ElementTemplateBase):
    """Représente un élément de texte dans un template."""
    contenu: str = "Nouveau Texte"
    nom_police: str = "Arial"
    taille_police_pt: int = 12
    est_variable: bool = False
    nom_variable: str = ""
    # En déplaçant 'type' à la fin, on s'assure qu'il ne précède
    # aucun champ non-défaut dans d'éventuelles futures classes enfants.
    type: Literal["texte"] = "texte"

@dataclass
class ElementImage(ElementTemplateBase):
    """Un conteneur pour une image."""
    chemin_fichier: str
    largeur_mm: float
    hauteur_mm: float
    type: Literal["image"] = "image"

@dataclass
class ElementVariable(ElementTexte):
    """
    Un bloc de texte spécial dont le contenu est une variable.
    Hérite des propriétés de ElementTexte pour le style.
    """
    label_descriptif: str = "Description manquante"
    valeur_par_defaut: str = ""
    type_element: str = field(init=False, default="Variable")

# D'autres éléments (Image, CodeBarres, etc.) pourront être ajoutés ici plus tard. 