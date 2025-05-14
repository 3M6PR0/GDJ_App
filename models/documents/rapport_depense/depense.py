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

    @classmethod
    def from_dict(cls, data: dict, base_path_for_factures_in_zip: str) -> 'Depense':
        """
        Crée une instance de Depense à partir d'un dictionnaire.

        Args:
            data: Dictionnaire contenant les attributs de la dépense.
            base_path_for_factures_in_zip: Le chemin du répertoire 'factures'
                                             où les dossiers de factures individuels.
        
        Returns:
            Une instance de Depense.
        """
        date_str = data.get('date')
        facture_data = data.get('facture')
        
        if date_str is None:
            raise ValueError("La date est manquante pour la dépense.")

        facture_obj = None
        if facture_data:
            try:
                facture_obj = Facture.from_dict(facture_data, base_path_for_factures_in_zip)
            except Exception as e:
                # logger.error(f"Erreur lors de la création de la facture pour une dépense: {e}")
                print(f"AVERTISSEMENT: Erreur lors de la reconstruction de la facture pour une dépense: {e}. La dépense sera chargée sans facture.")
                # raise ValueError(f"Impossible de reconstruire la facture pour la dépense: {e}") from e

        return cls(
            date_depense=date.fromisoformat(date_str),
            type_depense=str(data.get('type_depense', '')),
            description=str(data.get('description', '')),
            fournisseur=str(data.get('fournisseur', '')),
            payeur=bool(data.get('payeur', True)), # True par défaut?
            totale_avant_taxes=float(data.get('totale_avant_taxes', 0.0)),
            tps=float(data.get('tps', 0.0)),
            tvq=float(data.get('tvq', 0.0)),
            tvh=float(data.get('tvh', 0.0)),
            totale_apres_taxes=float(data.get('totale_apres_taxes', 0.0)),
            facture=facture_obj
        )

    # Ajouter d'autres méthodes si nécessaire 