# models/documents/lamicoid_2/elements/base.py
import uuid
from dataclasses import dataclass, field

@dataclass
class ElementTemplateBase:
    """
    Classe de base pour les modèles de données des éléments de template.
    Utilise les dataclasses pour une gestion simplifiée des attributs.
    """
    x_mm: float
    y_mm: float
    largeur_mm: float
    hauteur_mm: float
    element_id: str = field(default_factory=lambda: str(uuid.uuid4())) 