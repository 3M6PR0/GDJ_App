from datetime import date
from typing import Optional, List
from .facture import Facture

class Repas:
    """Représente une dépense de type repas."""

    def __init__(self,
                 date_repas: date,
                 restaurant: str,
                 client: str,
                 payeur: bool, # True = Employé, False = Jacmar?
                 refacturer: bool,
                 numero_commande: str, # Peut être vide si non refacturé
                 totale_avant_taxes: float,
                 pourboire: float,
                 tps: float,
                 tvq: float,
                 tvh: float,
                 totale_apres_taxes: float,
                 facture: Optional[Facture] = None # <-- RESTAURATION
                 ):

        if not isinstance(date_repas, date):
            raise TypeError("date_repas doit être un objet date.")
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
        # --- Assigner l'attribut facture --- 
        self.facture: Optional[Facture] = facture
        # -----------------------------------
        
    def __repr__(self):
        # --- Adapter repr pour inclure facture --- 
        facture_repr = f", facture={self.facture}" if self.facture else ""
        return (f"Repas(date={self.date.isoformat()}, restaurant='{self.restaurant}', "
                f"client='{self.client}', payeur_employe={self.payeur}, refacturer={self.refacturer}, "
                f"num_cmd='{self.numero_commande}', avant_tx={self.totale_avant_taxes:.2f}, "
                f"pourboire={self.pourboire:.2f}, tps={self.tps:.2f}, tvq={self.tvq:.2f}, "
                f"tvh={self.tvh:.2f}, total={self.totale_apres_taxes:.2f}, "
                f"{facture_repr})")
        # ---------------------------------------

    @property
    def total(self) -> float:
        """Retourne le montant total après taxes."""
        return self.totale_apres_taxes

    def to_dict(self):
        """Retourne une représentation dictionnaire de l'objet Repas pour la sérialisation JSON."""
        return {
            'date': self.date.isoformat() if self.date else None,
            'restaurant': self.restaurant,
            'client': self.client,
            'payeur': self.payeur,
            'refacturer': self.refacturer,
            'numero_commande': self.numero_commande,
            'totale_avant_taxes': self.totale_avant_taxes,
            'pourboire': self.pourboire,
            'tps': self.tps,
            'tvq': self.tvq,
            'tvh': self.tvh,
            'totale_apres_taxes': self.totale_apres_taxes,
            'facture': self.facture.to_dict() if self.facture else None
        }

    @classmethod
    def from_dict(cls, data: dict, base_path_for_factures_in_zip: str) -> 'Repas':
        """
        Crée une instance de Repas à partir d'un dictionnaire.

        Args:
            data: Dictionnaire contenant les attributs du repas.
            base_path_for_factures_in_zip: Le chemin du répertoire 'factures'
                                             où les dossiers de factures individuels (nommés par folder_name)
                                             ont été copiés après extraction du .rdj.
        
        Returns:
            Une instance de Repas.
        """
        date_str = data.get('date')
        facture_data = data.get('facture')
        
        # Valider les champs essentiels
        if date_str is None:
            raise ValueError("La date est manquante pour le repas.")
        # Ajouter d'autres validations si nécessaire pour les champs obligatoires

        facture_obj = None
        if facture_data:
            try:
                facture_obj = Facture.from_dict(facture_data, base_path_for_factures_in_zip)
            except Exception as e:
                # Log l'erreur et continuer sans facture, ou remonter l'erreur
                # selon la politique de gestion des erreurs souhaitée.
                # Pour l'instant, on log et on continue sans la facture.
                # logger.error(f"Erreur lors de la création de la facture pour un repas: {e}")
                print(f"AVERTISSEMENT: Erreur lors de la reconstruction de la facture pour un repas: {e}. Le repas sera chargé sans facture.")
                # Ou, si une facture est essentielle et que l'erreur est fatale:
                # raise ValueError(f"Impossible de reconstruire la facture pour le repas: {e}") from e

        return cls(
            date_repas=date.fromisoformat(date_str),
            restaurant=str(data.get('restaurant', '')),
            client=str(data.get('client', '')),
            payeur=bool(data.get('payeur', True)), # True par défaut si manquant?
            refacturer=bool(data.get('refacturer', False)),
            numero_commande=str(data.get('numero_commande', '')),
            totale_avant_taxes=float(data.get('totale_avant_taxes', 0.0)),
            pourboire=float(data.get('pourboire', 0.0)),
            tps=float(data.get('tps', 0.0)),
            tvq=float(data.get('tvq', 0.0)),
            tvh=float(data.get('tvh', 0.0)),
            totale_apres_taxes=float(data.get('totale_apres_taxes', 0.0)),
            facture=facture_obj
        )

    # Ajouter d'autres méthodes si nécessaire (ex: calcul total, validation) 