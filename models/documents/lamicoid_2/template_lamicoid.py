"""Définit la classe pour le modèle TemplateLamicoid."""

from dataclasses import dataclass, field
from typing import List, Literal
import json
import os
import shutil
import tempfile
from pathlib import Path
from .elements import ElementTemplateBase, ElementImage

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

    def save(self, directory: str):
        """
        Sauvegarde le template sous forme de package .tlj (un fichier zip).
        Le package contient le fichier JSON du template et une copie de toutes les images utilisées.
        """
        if not self.nom_template:
            raise ValueError("Le nom du template ne peut pas être vide.")

        safe_filename = "".join(c for c in self.nom_template if c.isalnum() or c in (' ', '_')).rstrip()
        final_tlj_path = Path(directory) / f"{safe_filename}.tlj"
        
        # Utiliser un répertoire temporaire pour assembler le contenu du package
        with tempfile.TemporaryDirectory() as tmpdir:
            package_dir = Path(tmpdir) / "template_package"
            package_dir.mkdir()

            template_data = self.to_dict()
            images_to_copy = {}

            # 1. Identifier les images, les copier et mettre à jour leurs chemins
            for i, element in enumerate(self.elements):
                if isinstance(element, ElementImage):
                    original_image_path = Path(element.chemin_fichier)
                    if original_image_path.exists():
                        new_filename = original_image_path.name
                        # Gérer les doublons de noms de fichiers
                        if new_filename in images_to_copy.values():
                            new_filename = f"{i}_{new_filename}"
                        
                        images_to_copy[original_image_path] = new_filename
                        # Mettre à jour le chemin dans le dictionnaire qui sera sauvegardé
                        template_data['elements'][i]['chemin_fichier'] = new_filename
            
            # Copier les fichiers image dans le dossier du package
            for src, dest_filename in images_to_copy.items():
                shutil.copy(src, package_dir / dest_filename)

            # 2. Sauvegarder le fichier JSON du template dans le package
            json_path = package_dir / "template.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=4, ensure_ascii=False)
            
            # 3. Créer l'archive zip
            archive_path_no_ext = Path(tmpdir) / safe_filename
            shutil.make_archive(str(archive_path_no_ext), 'zip', str(package_dir))
            
            # 4. Renommer le .zip en .tlj et le déplacer vers la destination finale
            zip_path = archive_path_no_ext.with_suffix('.zip')
            if final_tlj_path.exists():
                final_tlj_path.unlink() # Supprimer l'ancien fichier s'il existe
            shutil.move(str(zip_path), str(final_tlj_path))

        print(f"Template sauvegardé avec succès sous : {final_tlj_path}") 