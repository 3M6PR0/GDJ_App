"""Définit la classe pour la FeuilleLamicoid, la plaque de production."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from .lamicoid import Lamicoid

@dataclass
class LamicoidPositionne:
    """Structure pour stocker un Lamicoid et sa position sur la feuille."""
    lamicoid: Lamicoid
    position_x_mm: float
    position_y_mm: float

@dataclass
class FeuilleLamicoid:
    """
    Représente la feuille de production finale.
    C'est l'objet principal qui sera sauvegardé dans un fichier de document.
    """
    largeur_feuille_mm: float = 300.0
    hauteur_feuille_mm: float = 200.0
    epaisseur_mm: float = 1.6
    
    # Liste des lamicoids placés sur la feuille.
    lamicoids_sur_feuille: List[LamicoidPositionne] = field(default_factory=list) 