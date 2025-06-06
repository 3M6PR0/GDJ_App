"""Définit la classe pour le modèle TemplateLamicoid."""

from dataclasses import dataclass, field
from typing import List
from .elements import ElementTemplateBase

@dataclass
class TemplateLamicoid:
    """Représente un modèle (blueprint) réutilisable pour créer des Lamicoids."""
    template_id: str
    nom_template: str
    largeur_mm: float = 50.0
    hauteur_mm: float = 20.0
    marge_mm: float = 1.0
    rayon_coin_mm: float = 0.0
    elements: List[ElementTemplateBase] = field(default_factory=list) 