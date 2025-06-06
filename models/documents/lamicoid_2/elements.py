"""Définit les classes pour les éléments de contenu d'un TemplateLamicoid."""

from dataclasses import dataclass, field
from typing import Literal

@dataclass
class ElementTemplateBase:
    """Classe de base pour tous les éléments d'un template."""
    # Note: L'utilisation de dataclasses simplifie la déclaration des classes de données.
    element_id: str
    position_x_mm: float
    position_y_mm: float
    largeur_mm: float
    hauteur_mm: float
    type_element: str = field(init=False)

@dataclass
class ElementTexte(ElementTemplateBase):
    """Un bloc de texte avec des propriétés de police."""
    contenu_texte: str
    nom_police: str = "Arial"
    taille_police: int = 12
    alignement: Literal['gauche', 'centre', 'droite'] = 'gauche'
    type_element: str = field(init=False, default="Texte")

@dataclass
class ElementImage(ElementTemplateBase):
    """Un conteneur pour une image."""
    chemin_image_defaut: str
    type_element: str = field(init=False, default="Image")

@dataclass
class ElementVariable(ElementTexte):
    """
    Un bloc de texte spécial dont le contenu est une variable.
    Hérite des propriétés de ElementTexte pour le style.
    """
    nom_variable: str = "variable_sans_nom"
    label_descriptif: str = "Description manquante"
    valeur_par_defaut: str = ""
    type_element: str = field(init=False, default="Variable") 