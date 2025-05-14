from datetime import date
from typing import Optional
from .facture import Facture

class Depense:
    """Représente une dépense générale."""

    def __init__(self,
                 date_depense: date,
                 type_depense: str, 
                 description: str,
                 fournisseur: str,
                 payeur: bool, # True = Employé, False = Jacmar?
                 totale_avant_taxes: float,
                 tps: float,
                 tvq: float,
                 tvh: float,
                 totale_apres_taxes: float,
                 facture: Optional[Facture] = None
                 ):

        if not isinstance(date_depense, date):
            raise TypeError("date_depense doit être un objet date.")
        if not isinstance(payeur, bool):
            raise TypeError("payeur doit être un booléen.")
        if facture is not None and not isinstance(facture, Facture):
            raise TypeError("facture doit être une instance de Facture ou None.")
            
        # Valider les montants numériques
        montants = {
            "totale_avant_taxes": totale_avant_taxes,
            "tps": tps,
            "tvq": tvq,
            "tvh": tvh,
            "totale_apres_taxes": totale_apres_taxes,
        }
        for nom, valeur in montants.items():
            if not isinstance(valeur, (int, float)) or valeur < 0:
                raise ValueError(f"Le montant '{nom}' doit être un nombre positif.")

        # TODO: Validation somme vs total?
        # TODO: Validation employe + jacmar vs total?

        self.date: date = date_depense
        self.type_depense: str = str(type_depense)
        self.description: str = str(description)
        self.fournisseur: str = str(fournisseur)
        self.payeur: bool = payeur
        self.totale_avant_taxes: float = float(totale_avant_taxes)
        self.tps: float = float(tps)
        self.tvq: float = float(tvq)
        self.tvh: float = float(tvh)
        self.totale_apres_taxes: float = float(totale_apres_taxes)
        self.facture: Optional[Facture] = facture

    def __repr__(self):
        facture_repr = f", facture={self.facture}" if self.facture else ""
        return (f"Depense(date={self.date.isoformat()}, type='{self.type_depense}', "
                f"desc='{self.description}', fournisseur='{self.fournisseur}', "
                f"payeur_employe={self.payeur}, avant_tx={self.totale_avant_taxes:.2f}, "
                f"tps={self.tps:.2f}, tvq={self.tvq:.2f}, tvh={self.tvh:.2f}, "
                f"total={self.totale_apres_taxes:.2f}{facture_repr})")

    @property
    def total(self) -> float:
        """Retourne le montant total après taxes."""
        return self.totale_apres_taxes

    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet Depense pour la sérialisation JSON."""
        return {
            'date': self.date.isoformat() if self.date else None,
            'type_depense': self.type_depense,
            'description': self.description,
            'fournisseur': self.fournisseur,
            'payeur': self.payeur,
            'totale_avant_taxes': self.totale_avant_taxes,
            'tps': self.tps,
            'tvq': self.tvq,
            'tvh': self.tvh,
            'totale_apres_taxes': self.totale_apres_taxes,
            'facture': self.facture.to_dict() if self.facture else None
        }

    # Ajouter d'autres méthodes si nécessaire 