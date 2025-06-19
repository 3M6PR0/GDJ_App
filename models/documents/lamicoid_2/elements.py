"""Définit les différents types d'éléments pouvant composer un TemplateLamicoid."""

from dataclasses import dataclass, field, asdict
from typing import Literal
from PyQt5.QtCore import Qt

@dataclass
class ElementTemplateBase:
    """Classe de base pour tous les éléments d'un template."""
    element_id: str
    x_mm: float
    y_mm: float
    largeur_mm: float
    hauteur_mm: float
    rotation: float = 0.0

    def to_dict(self):
        """Sérialise l'objet en dictionnaire."""
        return asdict(self)

@dataclass
class ElementTexte(ElementTemplateBase):
    """Représente un élément de texte dans un template."""
    contenu: str = "Nouveau Texte"
    nom_police: str = "Arial"
    taille_police_pt: int = 12
    est_variable: bool = False
    nom_variable: str = ""
    bold: bool = False
    italic: bool = False
    underline: bool = False
    align: int = Qt.AlignHCenter
    type: Literal["texte"] = "texte"

    def to_dict(self):
        """Sérialise l'objet en dictionnaire."""
        return asdict(self)

@dataclass
class ElementImage(ElementTemplateBase):
    """Un conteneur pour une image."""
    chemin_fichier: str = field(kw_only=True)
    type: Literal["image"] = "image"

    def to_dict(self):
        """Sérialise l'objet en dictionnaire."""
        return asdict(self)

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