from models.document import Document
from .lamicoid_item import LamicoidItem
from typing import Optional, List
import logging
from datetime import date

logger = logging.getLogger('GDJ_App')

class LamicoidDocument(Document):
    """Modèle de données pour un document Lamicoid complet.
    Contient une liste d'items Lamicoid.
    """
    
    def __init__(self, 
                 file_name: str, 
                 title: Optional[str] = "Nouveau Document Lamicoid", 
                 items: Optional[List[LamicoidItem]] = None,
                 date_creation_doc: Optional[date] = None,
                 profile_name: Optional[str] = None
                 ):
        super().__init__(title=title, content="")
        
        self.file_name: str = file_name
        self.type_document: str = "Lamicoid" 
        self.date_creation_doc: date = date_creation_doc if date_creation_doc else date.today()
        self.items: List[LamicoidItem] = items if items is not None else []
        self.profile_name: Optional[str] = profile_name
        
        if self.profile_name is None:
            try:
                from models.preference import Preference
                prefs = Preference.get_instance()
                default_profile = prefs.get_default_profile()
                if default_profile and isinstance(default_profile, dict):
                    nom = default_profile.get('nom', '')
                    prenom = default_profile.get('prenom', '')
                    if nom or prenom:
                        self.profile_name = f"{nom} {prenom}".strip()
                    else:
                        self.profile_name = "Profil par défaut"
                else:
                    self.profile_name = "Profil inconnu"
            except Exception as e:
                logger.error(f"Erreur lors de la récupération du profil par défaut pour LamicoidDocument: {e}")
                self.profile_name = "Erreur Profil"

        logger.debug(f"LamicoidDocument initialisé: {self.title} (Fichier: {self.file_name}, Profil: {self.profile_name}), {len(self.items)} items.")

    def add_item(self, item: LamicoidItem):
        """Ajoute un LamicoidItem à la liste des items du document."""
        self.items.append(item)

    def remove_item(self, item_id: str):
        """Supprime un LamicoidItem de la liste basé sur son ID."""
        initial_len = len(self.items)
        self.items = [it for it in self.items if it.id_item != item_id]
        if len(self.items) < initial_len:
            return True
        return False

    def get_item_by_id(self, item_id: str) -> Optional[LamicoidItem]:
        """Récupère un LamicoidItem par son ID."""
        for item in self.items:
            if item.id_item == item_id:
                return item
        return None

    def update_item(self, item_id: str, updated_data: dict) -> bool:
        """Met à jour un LamicoidItem existant."""
        item = self.get_item_by_id(item_id)
        if item:
            if 'date_item' in updated_data and isinstance(updated_data['date_item'], date):
                item.date = updated_data['date_item']
            if 'numero_reference' in updated_data:
                item.numero_reference = str(updated_data['numero_reference'])
            if 'description' in updated_data:
                item.description = str(updated_data['description'])
            if 'quantite' in updated_data:
                item.quantite = int(updated_data['quantite'])
            if 'materiel' in updated_data:
                item.materiel = str(updated_data['materiel'])
            return True
        return False

    @property
    def content(self) -> str:
        """Génère une représentation textuelle du contenu (liste des items)."""
        return f"Document Lamicoid contenant {len(self.items)} item(s)."
    
    @content.setter
    def content(self, value: str):
        pass 

    def save(self):
        """Prépare les données du document Lamicoid pour la sauvegarde."""
        document_data = {
            'version_format': '1.0',
            'type_document': self.type_document,
            'title': self.title,
            'date_creation_doc': self.date_creation_doc.isoformat() if self.date_creation_doc else None,
            'nom_fichier_origine': self.file_name,
            'profile_name': self.profile_name,
            'items': [item.to_dict() for item in self.items]
        }
        logger.debug(f"LamicoidDocument.save() appelé pour: {self.title}, {len(self.items)} items.")
        return document_data, [] 

    @classmethod
    def from_dict(cls, data: dict, base_path_for_factures: str, original_rdj_filepath: str) -> 'LamicoidDocument':
        """
        Crée une instance de LamicoidDocument à partir d'un dictionnaire.
        base_path_for_factures n'est pas utilisé ici, mais gardé pour compatibilité d'API.
        """
        title = data.get('title', "Lamicoid importé sans titre")
        file_name_loaded = original_rdj_filepath
        profile_name = data.get('profile_name', None)
        
        date_creation_obj = None
        if data.get('date_creation_doc'):
            try:
                date_creation_obj = date.fromisoformat(data['date_creation_doc'])
            except (ValueError, TypeError):
                logger.warning(f"Date de création du document Lamicoid invalide: {data['date_creation_doc']}")

        items_data = data.get('items', [])
        loaded_items = [LamicoidItem.from_dict(item_data) for item_data in items_data]
        
        logger.debug(f"LamicoidDocument.from_dict() appelé pour: {title} (Fichier: {file_name_loaded}), {len(loaded_items)} items.")
        
        return cls(
            file_name=file_name_loaded,
            title=title,
            items=loaded_items,
            date_creation_doc=date_creation_obj,
            profile_name=profile_name
        )

    def validate(self):
        """Valide que le document Lamicoid est correct."""
        if not self.title or not self.title.strip():
            logger.warning(f"Validation échouée pour LamicoidDocument ({self.file_name}): Le titre est manquant.")
            return False
        return True

    def __repr__(self):
        return (f"<LamicoidDocument Titre: '{self.title}', Fichier: '{self.file_name}', Items: {len(self.items)}>") 