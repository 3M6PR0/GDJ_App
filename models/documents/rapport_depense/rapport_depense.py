from models.document import Document
from datetime import date
from typing import List, Optional

# --- Imports relatifs --- 
from .deplacement import Deplacement
from .repas import Repas
from .depense import Depense
# ----------------------

class RapportDepense(Document):
    """Modèle de données pour un rapport de dépenses complet."""
    
    # --- Modifier le constructeur --- 
    def __init__(self, 
                 nom_fichier: str, # Nom du fichier de sauvegarde/origine
                 date_rapport: date, # Mois/Année du rapport
                 nom_employe: str,
                 prenom_employe: str,
                 emplacement: str,
                 departement: str,
                 superviseur: str,
                 plafond_deplacement: str, # Ex: 'Cap 1'
                 title: Optional[str] = None, # Titre optionnel, peut être généré
                 content: str = "" # Content hérité de Document, usage? 
                 ):
        
        # Générer un titre par défaut si non fourni
        if title is None:
            title = f"Rapport {date_rapport.strftime('%Y-%m')} - {prenom_employe} {nom_employe}"
            
        super().__init__(title, content) # Appeler le parent
        
        # --- Nouveaux attributs d'en-tête --- 
        if not isinstance(date_rapport, date):
            raise TypeError("date_rapport doit être un objet date.")
        self.nom_fichier: str = nom_fichier
        self.date_rapport: date = date_rapport
        self.nom_employe: str = nom_employe
        self.prenom_employe: str = prenom_employe
        self.emplacement: str = emplacement
        self.departement: str = departement
        self.superviseur: str = superviseur
        self.plafond_deplacement: str = plafond_deplacement
        # -----------------------------------

        # --- Remplacer l'ancienne liste par les nouvelles --- 
        # self.depenses = depenses if depenses is not None else []
        self.deplacements: List[Deplacement] = []
        self.repas: List[Repas] = []
        self.depenses_diverses: List[Depense] = []
        # ----------------------------------------------------

    # --- Méthodes pour ajouter des items --- 
    def ajouter_deplacement(self, deplacement: Deplacement):
        if not isinstance(deplacement, Deplacement):
            raise TypeError("L'objet ajouté doit être une instance de Deplacement.")
        self.deplacements.append(deplacement)

    def ajouter_repas(self, repas: Repas):
        if not isinstance(repas, Repas):
            raise TypeError("L'objet ajouté doit être une instance de Repas.")
        self.repas.append(repas)

    def ajouter_depense(self, depense: Depense):
        if not isinstance(depense, Depense):
            raise TypeError("L'objet ajouté doit être une instance de Depense.")
        self.depenses_diverses.append(depense)
    # -------------------------------------

    # --- Adapter la validation --- 
    def validate(self):
        """Valide que le rapport contient au moins une dépense de n'importe quel type."""
        return bool(self.deplacements or self.repas or self.depenses_diverses)
    # ---------------------------
    
    # --- Adapter __repr__ (simplifié) --- 
    def __repr__(self):
        return (f"RapportDepense(titre='{self.title}', date='{self.date_rapport.isoformat()}', "
                f"employe='{self.prenom_employe} {self.nom_employe}', "
                f"{len(self.deplacements)} déplacements, {len(self.repas)} repas, "
                f"{len(self.depenses_diverses)} dépenses diverses)")
    # -----------------------------------

    # --- NOUVELLE MÉTHODE D'EXPORTATION PDF UTILISANT DocumentPDFPrinter ---
    def export_to_pdf(self, output_path: str):
        """Exporte ce rapport de dépenses en PDF en utilisant DocumentPDFPrinter."""
        # Importation locale pour éviter les dépendances circulaires au niveau du module
        # et parce que DocumentPDFPrinter n'est utilisé que par cette méthode ici.
        from utils.document_printer import DocumentPDFPrinter
        
        printer = DocumentPDFPrinter()
        try:
            printer.generate(self, output_path)
        except Exception as e:
            # Il est généralement préférable de logger l'erreur ici plutôt que juste print
            # et potentiellement remonter l'exception ou la gérer d'une manière spécifique à l'application.
            print(f"Erreur lors de l'exportation du rapport en PDF: {e}")
            # raise # Décommenter pour remonter l'exception si nécessaire
    # -------------------------------------------------------------------- 

    def save(self):
        """
        Prépare les données du rapport pour la sauvegarde.

        Retourne un tuple contenant:
            - Un dictionnaire avec toutes les données du rapport sérialisables en JSON.
            - Une liste des chemins absolus des dossiers de factures sources à inclure dans l'archive.
        """
        rapport_data = {
            'version_format': '1.0', # Pour une éventuelle gestion de versions futures
            'type_document': 'RapportDepense',
            # Attributs de Document (classe parente)
            'title': self.title,
            'content': self.content, 
            # Attributs de RapportDepense
            'nom_fichier_origine': self.nom_fichier, # nom_fichier est déjà utilisé par QFileDialog
            'date_rapport': self.date_rapport.isoformat() if self.date_rapport else None,
            'nom_employe': self.nom_employe,
            'prenom_employe': self.prenom_employe,
            'emplacement': self.emplacement,
            'departement': self.departement,
            'superviseur': self.superviseur,
            'plafond_deplacement': self.plafond_deplacement,
            'deplacements': [d.to_dict() for d in self.deplacements],
            'repas': [r.to_dict() for r in self.repas],
            'depenses_diverses': [dd.to_dict() for dd in self.depenses_diverses],
        }

        facture_dossiers_sources = []
        for item_list in [self.repas, self.depenses_diverses]:
            for item in item_list:
                if item.facture and item.facture.folder_path:
                    # S'assurer de ne pas ajouter de doublons si plusieurs factures partagent un dossier (peu probable)
                    if item.facture.folder_path not in facture_dossiers_sources:
                        facture_dossiers_sources.append(item.facture.folder_path)
        
        return rapport_data, list(set(facture_dossiers_sources)) # Utiliser set pour garantir l'unicité
    # -------------------------------------------------------------------- 