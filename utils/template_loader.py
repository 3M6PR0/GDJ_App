import zipfile
import json
import tempfile
import os
from pathlib import Path
import shutil
import logging

from models.documents.lamicoid_2.template_lamicoid import TemplateLamicoid
from models.documents.lamicoid_2.elements import ElementImage

logger = logging.getLogger('GDJ_App')

def load_template_from_tlj(file_path: str) -> TemplateLamicoid | None:
    """
    Charge un template de lamicoid à partir d'un fichier .tlj.
    Extrait l'archive dans un répertoire temporaire, charge les données
    et met à jour les chemins des images pour qu'ils soient absolus.
    """
    try:
        # Utiliser un répertoire temporaire qui persiste le temps de l'utilisation des données.
        # Il est important que les QPixmap soient chargés avant que ce dossier ne soit potentiellement nettoyé.
        temp_dir = tempfile.mkdtemp(prefix="gjd_tlj_")

        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        json_path = Path(temp_dir) / 'template.json'
        if not json_path.exists():
            logger.error(f"template.json non trouvé dans l'archive {file_path}")
            shutil.rmtree(temp_dir) # Nettoyer
            return None

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Utiliser la nouvelle méthode de classe pour créer l'objet
        template = TemplateLamicoid.from_dict(data)

        # Mettre à jour les chemins des images pour qu'ils soient absolus
        for element in template.elements:
            if isinstance(element, ElementImage):
                relative_image_path = Path(element.chemin_fichier)
                # Le chemin absolu pointe vers le fichier dans le dossier temporaire
                absolute_image_path = Path(temp_dir) / relative_image_path
                element.chemin_fichier = str(absolute_image_path)
        
        return template

    except Exception as e:
        logger.error(f"Erreur lors du chargement du template {file_path}: {e}", exc_info=True)
        return None 