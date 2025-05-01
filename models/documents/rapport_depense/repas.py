from datetime import date
from typing import Optional, List
from .facture import Facture

class Repas:
    """Représente une dépense de type repas."""

    def __init__(self,
                 date_repas: date,
                 description: str,
                 restaurant: str,
                 client: str, # Peut être vide si repas interne?
                 payeur: bool, # True = Employé, False = Jacmar?
                 refacturer: bool,
                 numero_commande: str, # Peut être vide?
                 totale_avant_taxes: float,
                 pourboire: float,
                 tps: float,
                 tvq: float,
                 tvh: float,
                 totale_apres_taxes: float,
                 employe: float, # Montant payé par l'employé?
                 jacmar: float, # Montant payé par Jacmar?
                 facture: Optional[Facture] = None # <-- RESTAURATION
                 ):

        if not isinstance(date_repas, date):
            raise TypeError("date_repas doit être un objet date.")
        if not isinstance(description, str):
            raise TypeError("description doit être une chaîne de caractères.")
        if not isinstance(refacturer, bool):
            raise TypeError("refacturer doit être un booléen.")
        if not isinstance(payeur, bool):
            raise TypeError("payeur doit être un booléen.")
            
        # Valider les montants numériques (y compris employe et jacmar)
        montants = {
            "totale_avant_taxes": totale_avant_taxes,
            "pourboire": pourboire,
            "tps": tps,
            "tvq": tvq,
            "tvh": tvh,
            "totale_apres_taxes": totale_apres_taxes,
            "employe": employe,
            "jacmar": jacmar
        }
        for nom, valeur in montants.items():
            if not isinstance(valeur, (int, float)) or valeur < 0:
                raise ValueError(f"Le montant '{nom}' doit être un nombre positif.")

        # TODO: Ajouter une validation pour vérifier si totale_apres_taxes correspond à la somme?
        # TODO: Valider que employe + jacmar == totale_apres_taxes ?

        # --- Valider le type de facture (si fournie) --- 
        if facture is not None and not isinstance(facture, Facture):
            raise TypeError("facture doit être une instance de Facture ou None.")
        # --------------------------------------------------

        self.date: date = date_repas
        self.description: str = description
        self.restaurant: str = str(restaurant)
        self.client: str = str(client)
        self.payeur: bool = payeur
        self.refacturer: bool = refacturer
        self.numero_commande: str = str(numero_commande)
        self.totale_avant_taxes: float = float(totale_avant_taxes)
        self.pourboire: float = float(pourboire)
        self.tps: float = float(tps)
        self.tvq: float = float(tvq)
        self.tvh: float = float(tvh)
        self.totale_apres_taxes: float = float(totale_apres_taxes)
        self.employe: float = float(employe)
        self.jacmar: float = float(jacmar)
        # --- Assigner l'attribut facture --- 
        self.facture: Optional[Facture] = facture
        # -----------------------------------
        
    def __repr__(self):
        # --- Adapter repr pour inclure facture --- 
        facture_repr = f", facture={self.facture}" if self.facture else ""
        return (f"Repas(date={self.date.isoformat()}, desc='{self.description}', restaurant='{self.restaurant}', "
                f"client='{self.client}', payeur_employe={self.payeur}, refacturer={self.refacturer}, "
                f"num_cmd='{self.numero_commande}', avant_tx={self.totale_avant_taxes:.2f}, "
                f"pourboire={self.pourboire:.2f}, tps={self.tps:.2f}, tvq={self.tvq:.2f}, "
                f"tvh={self.tvh:.2f}, total={self.totale_apres_taxes:.2f}, "
                f"montant_employe={self.employe:.2f}, montant_jacmar={self.jacmar:.2f}{facture_repr})")
        # ---------------------------------------

    @property
    def total(self) -> float:
        """Retourne le montant total après taxes."""
        return self.totale_apres_taxes

    # Ajouter d'autres méthodes si nécessaire (ex: calcul total, validation) 