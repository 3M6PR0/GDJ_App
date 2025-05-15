from models.document import Document
from typing import Optional
import logging

logger = logging.getLogger('GDJ_App')

class LamicoidDocument(Document):
    """Modèle de données pour un document Lamicoid."""
    
    def __init__(self, 
                 nom_fichier: str, 
                 title: Optional[str] = "Nouveau Lamicoid", 
                 content: str = "Contenu initial du Lamicoid"
                 ):
        super().__init__(title, content)
        self.nom_fichier: str = nom_fichier
        # Le type de document est important pour l'identification et la gestion
        self.type_document: str = "Lamicoid" 
        logger.debug(f"LamicoidDocument initialisé: {title} (Fichier: {nom_fichier})")

    def save(self):
        """Prépare les données du document Lamicoid pour la sauvegarde.
        
        Retourne un tuple contenant:
            - Un dictionnaire avec toutes les données du document sérialisables en JSON.
            - Une liste vide (pas de factures pour Lamicoid pour l'instant).
        """
        lamicoid_data = {
            'version_format': '1.0',
            'type_document': self.type_document,
            'title': self.title,
            'content': self.content,
            'nom_fichier_origine': self.nom_fichier 
        }
        logger.debug(f"LamicoidDocument.save() appelé pour: {self.title}")
        return lamicoid_data, [] # Pas de dossiers de factures pour Lamicoid

    @classmethod
    def from_dict(cls, data: dict, base_path_for_factures: str, original_rdj_filepath: str) -> 'LamicoidDocument':
        """
        Crée une instance de LamicoidDocument à partir d'un dictionnaire.
        Les arguments base_path_for_factures sont présents pour la compatibilité de l'API 
        avec RapportDepense mais ne sont pas utilisés ici.
        """
        title = data.get('title', "Lamicoid importé")
        content = data.get('content', "")
        # nom_fichier_origine = data.get('nom_fichier_origine') # Sera remplacé par original_rdj_filepath
        
        logger.debug(f"LamicoidDocument.from_dict() appelé pour: {title} (Fichier origine: {original_rdj_filepath})")
        
        return cls(
            nom_fichier=original_rdj_filepath, 
            title=title,
            content=content
        )

    def validate(self):
        """Valide que le document Lamicoid est correct (peut être étendu)."""
        return True # Pour l'instant, toujours valide

    def __repr__(self):
        return (f"LamicoidDocument(titre='{self.title}', fichier='{self.nom_fichier}')") 