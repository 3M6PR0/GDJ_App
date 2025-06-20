"""Définit la classe pour le modèle TemplateLamicoid."""

from dataclasses import dataclass, field
from typing import List, Literal
import json
import os
import shutil
import tempfile
from pathlib import Path
from .elements import ElementTemplateBase, ElementImage, ElementTexte

def _create_element_from_dict(elem_data: dict) -> ElementTemplateBase | None:
    """Crée une instance d'élément à partir d'un dictionnaire de données."""
    from .elements import ELEMENT_TYPE_MAP
    import inspect

    elem_type = elem_data.get('type')
    if not elem_type:
        return None
        
    element_class = ELEMENT_TYPE_MAP.get(elem_type)
    if not element_class:
        return None
    
    # Filtre les clés du dictionnaire pour ne garder que celles qui
    # correspondent aux paramètres du constructeur de la classe.
    sig = inspect.signature(element_class.__init__)
    known_args = {k: v for k, v in elem_data.items() if k in sig.parameters}
    
    try:
        return element_class(**known_args)
    except (TypeError, KeyError) as e:
        print(f"Erreur à la création de l'élément '{elem_type}': {e}")
        return None

@dataclass
class TemplateLamicoid:
    """Représente un modèle (blueprint) réutilisable pour créer des Lamicoids."""
    template_id: str
    nom_template: str
    largeur_mm: float = 100.0
    hauteur_mm: float = 50.0
    rayon_coin_mm: float = 2.0
    marge_mm: float = 2.0
    espacement_grille_mm: float = 1.0
    elements: List[ElementTemplateBase] = field(default_factory=list) 

    @classmethod
    def from_dict(cls, data: dict):
        """Crée une instance de TemplateLamicoid à partir d'un dictionnaire."""
        elements_data = data.pop('elements', [])
        elements = [_create_element_from_dict(elem_data) for elem_data in elements_data if elem_data]
        
        # Filtre les None au cas où certains éléments n'aient pas pu être créés
        valid_elements = [elem for elem in elements if elem is not None]
        
        return cls(elements=valid_elements, **data)

    def to_dict(self):
        """Convertit l'objet TemplateLamicoid en dictionnaire."""
        return {
            "template_id": self.template_id,
            "nom_template": self.nom_template,
            "largeur_mm": self.largeur_mm,
            "hauteur_mm": self.hauteur_mm,
            "rayon_coin_mm": self.rayon_coin_mm,
            "marge_mm": self.marge_mm,
            "espacement_grille_mm": self.espacement_grille_mm,
            "elements": [elem.to_dict() for elem in self.elements]
        }

    def save(self, directory: str, template_name: str):
        """
        Sauvegarde le template sous forme de package .tlj (un fichier zip).
        Le package contient le fichier JSON du template et une copie de toutes les images utilisées.
        """
        dest_dir = Path(directory)
        # S'assurer que le répertoire de destination existe
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Nettoyer le nom du fichier pour éviter les caractères invalides
        safe_filename = "".join(c for c in template_name if c.isalnum() or c in (' ', '_')).rstrip()
        final_tlj_path = dest_dir / f"{safe_filename}.tlj"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            images_dir = tmpdir_path / 'images'
            images_dir.mkdir()

            template_data_for_json = self.to_dict()
            template_data_for_json['nom_template'] = template_name # S'assurer que le nom est à jour
            
            for i, element in enumerate(self.elements):
                if isinstance(element, ElementImage):
                    original_image_path = Path(element.chemin_fichier)
                    if original_image_path.exists():
                        destination_image_path = images_dir / original_image_path.name
                        shutil.copy(original_image_path, destination_image_path)
                        
                        relative_path = Path('images') / original_image_path.name
                        template_data_for_json['elements'][i]['chemin_fichier'] = relative_path.as_posix()

            json_path = tmpdir_path / "template.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(template_data_for_json, f, indent=4, ensure_ascii=False)
            
            # Créer l'archive dans le même dossier temporaire pour éviter les problèmes de droits
            archive_base_path = tmpdir_path / safe_filename
            shutil.make_archive(str(archive_base_path), 'zip', str(tmpdir_path))
            
            zip_file = archive_base_path.with_suffix('.zip')
            
            if final_tlj_path.exists():
                final_tlj_path.unlink()
                
            shutil.move(str(zip_file), str(final_tlj_path))
            
        print(f"Template sauvegardé avec succès sous : {final_tlj_path}") 