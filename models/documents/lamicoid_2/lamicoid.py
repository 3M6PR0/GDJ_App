"""Définit la classe pour un Lamicoid individuel, instancié à partir d'un template."""

from dataclasses import dataclass, field
from typing import Dict
from .template_lamicoid import TemplateLamicoid

@dataclass
class Lamicoid:
    """Représente une instance unique d'un Lamicoid."""
    instance_id: str
    template_id: str  # Référence à l'ID du TemplateLamicoid utilisé
    
    # Dictionnaire qui mappe un nom_variable à la valeur saisie par l'utilisateur.
    # ex: {"nom_employe": "Jean Dupont", "poste": "Développeur"}
    valeurs_variables: Dict[str, str] = field(default_factory=dict)

    def to_dict(self):
        """Convertit l'objet Lamicoid en dictionnaire."""
        return {
            "instance_id": self.instance_id,
            "template_id": self.template_id,
            "valeurs_variables": self.valeurs_variables,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Crée un objet Lamicoid à partir d'un dictionnaire."""
        return cls(
            instance_id=data["instance_id"],
            template_id=data["template_id"],
            valeurs_variables=data["valeurs_variables"],
        ) 