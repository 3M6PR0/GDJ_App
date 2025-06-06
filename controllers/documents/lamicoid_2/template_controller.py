import json
import os
import logging
import uuid
from dataclasses import asdict
from typing import List, Dict, Optional, Type

from utils.paths import get_user_data_path
from models.documents.lamicoid_2 import (
    ElementTemplateBase, ElementTexte, ElementImage, ElementVariable,
    TemplateLamicoid
)
from models.documents.lamicoid_2.elements import ElementTemplateBase, ElementTexte, ElementImage, ElementVariable

logger = logging.getLogger('GDJ_App')

# Mapper les noms de type aux classes pour la désérialisation
ELEMENT_TYPE_MAP: Dict[str, Type[ElementTemplateBase]] = {
    "Texte": ElementTexte,
    "Image": ElementImage,
    "Variable": ElementVariable,
}

def create_demo_template() -> TemplateLamicoid:
    """Crée un template de démonstration pré-rempli."""
    template_id = str(uuid.uuid4())
    demo_template = TemplateLamicoid(
        template_id=template_id,
        nom_template="Template de Démonstration",
        largeur_mm=85,
        hauteur_mm=55,
        rayon_coin_mm=3.5
    )
    
    # Ajout des éléments
    logo_element = ElementImage(
        element_id=str(uuid.uuid4()),
        position_x_mm=5,
        position_y_mm=5,
        largeur_mm=20,
        hauteur_mm=10,
        chemin_image_defaut="resources/images/logo-jacmar-gdj.png"
    )
    
    nom_employe_element = ElementVariable(
        element_id=str(uuid.uuid4()),
        position_x_mm=5,
        position_y_mm=25,
        largeur_mm=75,
        hauteur_mm=10,
        nom_variable="nom_employe",
        label_descriptif="Nom de l'employé",
        contenu_texte="<Nom de l'employé>", # Texte affiché dans l'éditeur
        taille_police=12
    )
    
    poste_element = ElementVariable(
        element_id=str(uuid.uuid4()),
        position_x_mm=5,
        position_y_mm=38,
        largeur_mm=75,
        hauteur_mm=8,
        nom_variable="poste",
        label_descriptif="Poste occupé",
        contenu_texte="<Poste>",
        taille_police=8
    )

    demo_template.elements = [logo_element, nom_employe_element, poste_element]
    return demo_template

class TemplateController:
    """
    Contrôleur responsable de la gestion (chargement, sauvegarde, accès)
    des TemplateLamicoid globaux.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TemplateController, cls).__new__(cls)
        return cls._instance

    def __init__(self, templates_filename: str = "lamicoid_templates.json"):
        # Évite la ré-initialisation sur les appels multiples
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.templates_file_path = os.path.join(get_user_data_path(), templates_filename)
        self.templates: Dict[str, TemplateLamicoid] = {}
        self.load_templates()
        self._initialized = True
        logger.info(f"TemplateController initialisé. {len(self.templates)} templates chargés.")

    @classmethod
    def get_instance(cls):
        """Méthode pour accéder à l'instance unique du contrôleur."""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def load_templates(self):
        """Charge les templates depuis le fichier JSON, ou en crée un de démo."""
        if not os.path.exists(self.templates_file_path):
            logger.warning(f"Fichier de templates non trouvé. Création d'un fichier de démo.")
            demo = create_demo_template()
            self.templates = {demo.template_id: demo}
            self.save_templates() # Sauvegarder immédiatement le fichier de démo
            return

        try:
            with open(self.templates_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data: # Si le fichier est vide
                    logger.warning("Le fichier de templates est vide. Création d'un template de démo.")
                    demo = create_demo_template()
                    self.templates = {demo.template_id: demo}
                    self.save_templates()
                    return

            loaded_templates = {}
            for template_data in data:
                elements_data = template_data.pop('elements', [])
                elements = [self._create_element_from_dict(elem_data) for elem_data in elements_data]
                template = TemplateLamicoid(elements=elements, **template_data)
                loaded_templates[template.template_id] = template
            
            self.templates = loaded_templates
            logger.info(f"{len(self.templates)} templates chargés depuis {self.templates_file_path}")

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error(f"Erreur lors du chargement ou de la désérialisation de {self.templates_file_path}: {e}", exc_info=True)
            self.templates = {}

    def _create_element_from_dict(self, elem_data: dict) -> ElementTemplateBase | None:
        """Crée une instance d'élément à partir d'un dictionnaire de données."""
        elem_type = elem_data.pop('type', None)
        if not elem_type:
            return None

        # --- Remappage des clés pour la compatibilité ---
        if 'position_x_mm' in elem_data:
            elem_data['x_mm'] = elem_data.pop('position_x_mm')
        if 'position_y_mm' in elem_data:
            elem_data['y_mm'] = elem_data.pop('position_y_mm')
        if 'contenu_texte' in elem_data:
            elem_data['contenu'] = elem_data.pop('contenu_texte')
        # ... (ajoutez d'autres remappages si nécessaire) ...

        element_class_map = {
            "texte": ElementTexte,
            "image": ElementImage,
            "variable": ElementVariable,
        }
        
        element_class = element_class_map.get(elem_type)
        if not element_class:
            logger.warning(f"Type d'élément inconnu lors du chargement: {elem_type}")
            return None
        
        try:
            # On ne passe que les arguments que la classe connaît
            import inspect
            sig = inspect.signature(element_class.__init__)
            known_args = {k: v for k, v in elem_data.items() if k in sig.parameters}
            return element_class(**known_args)
        except (TypeError, KeyError) as e:
            logger.error(f"Erreur lors de la création de l'élément '{elem_type}': {e}. Données: {elem_data}")
            return None

    def save_templates(self):
        """Sauvegarde tous les templates en mémoire vers le fichier JSON."""
        try:
            # Convertit la liste des objets TemplateLamicoid en une liste de dictionnaires
            data_to_save = [asdict(template) for template in self.templates.values()]
            
            with open(self.templates_file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            logger.info(f"{len(self.templates)} templates sauvegardés dans {self.templates_file_path}")
        except TypeError as e:
            logger.error(f"Erreur de sérialisation lors de la sauvegarde des templates: {e}", exc_info=True)
        except IOError as e:
            logger.error(f"Erreur d'écriture dans le fichier {self.templates_file_path}: {e}", exc_info=True)

    def get_all_templates(self) -> List[TemplateLamicoid]:
        """Retourne une liste de tous les templates chargés."""
        return list(self.templates.values())

    def get_template_by_id(self, template_id: str) -> Optional[TemplateLamicoid]:
        """Récupère un template par son ID unique."""
        return self.templates.get(template_id)

    def add_or_update_template(self, template: TemplateLamicoid):
        """Ajoute un nouveau template ou met à jour un existant."""
        if not template.template_id:
            template.template_id = str(uuid.uuid4())
        self.templates[template.template_id] = template
        self.save_templates()
        logger.info(f"Template '{template.nom_template}' (ID: {template.template_id}) ajouté/mis à jour.")

    def delete_template(self, template_id: str):
        """Supprime un template par son ID."""
        if template_id in self.templates:
            del self.templates[template_id]
            self.save_templates()
            logger.info(f"Template ID: {template_id} supprimé.")
            return True
        logger.warning(f"Tentative de suppression d'un template non trouvé. ID: {template_id}")
        return False 