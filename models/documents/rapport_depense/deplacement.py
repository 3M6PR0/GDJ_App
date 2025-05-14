from datetime import date

class Deplacement:
    """Représente une dépense de type déplacement."""
    
    def __init__(self, 
                 date_deplacement: date, 
                 client: str, 
                 ville: str, 
                 numero_commande: str, 
                 kilometrage: float, 
                 montant: float):
        
        if not isinstance(date_deplacement, date):
            raise TypeError("date_deplacement doit être un objet date.")
        if not isinstance(kilometrage, (int, float)) or kilometrage < 0:
            raise ValueError("Le kilométrage doit être un nombre positif.")
        if not isinstance(montant, (int, float)) or montant < 0:
            raise ValueError("Le montant doit être un nombre positif.")
            
        self.date: date = date_deplacement
        self.client: str = str(client) # Assurer str
        self.ville: str = str(ville)
        self.numero_commande: str = str(numero_commande)
        self.kilometrage: float = float(kilometrage) # Assurer float
        self.montant: float = float(montant)

    def __repr__(self):
        return (f"Deplacement(date={self.date.isoformat()}, client='{self.client}', "
                f"ville='{self.ville}', numero_commande='{self.numero_commande}', "
                f"kilometrage={self.kilometrage}, montant={self.montant:.2f})")

    @property
    def total(self) -> float:
        """Retourne le montant total du déplacement."""
        return self.montant

    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet Deplacement pour la sérialisation JSON."""
        return {
            'date': self.date.isoformat() if self.date else None,
            'client': self.client,
            'ville': self.ville,
            'numero_commande': self.numero_commande,
            'kilometrage': self.kilometrage,
            'montant': self.montant
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Deplacement':
        """
        Crée une instance de Deplacement à partir d'un dictionnaire.

        Args:
            data: Dictionnaire contenant les attributs du déplacement.
        
        Returns:
            Une instance de Deplacement.
        """
        date_str = data.get('date')
        client = data.get('client')
        ville = data.get('ville')
        numero_commande = data.get('numero_commande')
        kilometrage = data.get('kilometrage')
        montant = data.get('montant')

        if date_str is None:
            raise ValueError("La date est manquante pour le déplacement.")
        # Validation de base pour les autres champs si nécessaire (ex: type)
        if kilometrage is None or not isinstance(kilometrage, (int, float)):
            raise ValueError("Kilométrage manquant ou invalide.")
        if montant is None or not isinstance(montant, (int, float)):
            raise ValueError("Montant manquant ou invalide.")

        return cls(
            date_deplacement=date.fromisoformat(date_str),
            client=str(client) if client is not None else "",
            ville=str(ville) if ville is not None else "",
            numero_commande=str(numero_commande) if numero_commande is not None else "",
            kilometrage=float(kilometrage),
            montant=float(montant)
        )

    # Ajouter d'autres méthodes si nécessaire (ex: validation spécifique) 