from datetime import date
from typing import Optional
import logging
import uuid # Pour générer des IDs uniques

logger = logging.getLogger('GDJ_App')

class LamicoidItem:
    """Représente une entrée Lamicoid individuelle (un item) au sein d'un LamicoidDocument."""
    def __init__(self, 
                 id_item: Optional[str] = None,
                 date_item: date = date.today(), 
                 numero_reference: str = "",
                 description: str = "",
                 quantite: int = 1,
                 materiel: str = ""):
        
        self.id_item: str = id_item if id_item else str(uuid.uuid4())
        self.date: date = date_item
        self.numero_reference: str = numero_reference
        self.description: str = description
        self.quantite: int = quantite
        self.materiel: str = materiel
        
        # logger.debug(f"LamicoidItem créé: ID={self.id_item}, Date={self.date}, Ref={self.numero_reference}")

    def to_dict(self) -> dict:
        """Retourne une représentation dictionnaire de l'objet LamicoidItem."""
        return {
            "id_item": self.id_item,
            "date": self.date.isoformat() if self.date else None,
            "numero_reference": self.numero_reference,
            "description": self.description,
            "quantite": self.quantite,
            "materiel": self.materiel
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LamicoidItem":
        """Crée une instance de LamicoidItem à partir d'un dictionnaire."""
        date_obj = None
        if data.get("date"):
            try:
                date_obj = date.fromisoformat(data["date"])
            except (ValueError, TypeError):
                logger.warning(f"Format de date invalide pour LamicoidItem from_dict: {data['date']}. Utilisation de None.")
        
        return cls(
            id_item=data.get("id_item"), # L'ID sera généré si None
            date_item=date_obj if date_obj else date.today(),
            numero_reference=data.get("numero_reference", ""),
            description=data.get("description", ""),
            quantite=data.get("quantite", 1),
            materiel=data.get("materiel", "")
        )

    def __repr__(self):
        return f"<LamicoidItem ID: {self.id_item} Date: {self.date} Ref: {self.numero_reference}>" 