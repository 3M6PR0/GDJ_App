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

    # Ajouter d'autres méthodes si nécessaire (ex: validation spécifique) 