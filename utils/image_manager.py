"""
Gestionnaire d'images pour les templates lamicoid.
Gère l'importation, le stockage et la récupération des images réutilisables.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from PyQt5.QtGui import QPixmap

logger = logging.getLogger('GDJ_App')

class ImageManager:
    """Gestionnaire centralisé pour les images des templates lamicoid."""
    
    _instance = None
    
    def __init__(self):
        self.images_dir = Path("data/lamicoid/images")
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self._supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.svg'}
        
    @classmethod
    def get_instance(cls):
        """Retourne l'instance singleton du gestionnaire d'images."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_images_directory(self) -> Path:
        """Retourne le chemin du dossier des images."""
        return self.images_dir
    
    def get_all_images(self) -> List[str]:
        """Retourne la liste de tous les chemins d'images disponibles."""
        images = []
        if self.images_dir.exists():
            for file_path in self.images_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in self._supported_formats:
                    images.append(str(file_path))
        return sorted(images)
    
    def import_image(self, source_path: str) -> Optional[str]:
        """
        Importe une image depuis un chemin externe vers le dossier des images.
        Retourne le chemin de destination ou None en cas d'erreur.
        """
        try:
            source_path = Path(source_path)
            if not source_path.exists():
                logger.error(f"Fichier source introuvable : {source_path}")
                return None
                
            if source_path.suffix.lower() not in self._supported_formats:
                logger.error(f"Format d'image non supporté : {source_path.suffix}")
                return None
            
            # Générer un nom de fichier unique
            dest_filename = self._generate_unique_filename(source_path.name)
            dest_path = self.images_dir / dest_filename
            
            # Copier le fichier
            shutil.copy2(source_path, dest_path)
            logger.info(f"Image importée : {source_path} -> {dest_path}")
            
            return str(dest_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation de l'image {source_path}: {e}")
            return None
    
    def _generate_unique_filename(self, original_name: str) -> str:
        """Génère un nom de fichier unique pour éviter les conflits."""
        base_name = Path(original_name).stem
        extension = Path(original_name).suffix
        
        counter = 1
        new_name = original_name
        
        while (self.images_dir / new_name).exists():
            new_name = f"{base_name}_{counter}{extension}"
            counter += 1
            
        return new_name
    
    def delete_image(self, image_path: str) -> bool:
        """Supprime une image du dossier des images."""
        try:
            image_path = Path(image_path)
            if image_path.exists() and image_path.parent == self.images_dir:
                image_path.unlink()
                logger.info(f"Image supprimée : {image_path}")
                return True
            else:
                logger.warning(f"Impossible de supprimer l'image : {image_path}")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'image {image_path}: {e}")
            return False
    
    def is_valid_image(self, image_path: str) -> bool:
        """Vérifie si un fichier est une image valide."""
        try:
            pixmap = QPixmap(image_path)
            return not pixmap.isNull()
        except Exception:
            return False
    
    def get_image_info(self, image_path: str) -> Optional[dict]:
        """Retourne les informations d'une image (taille, format, etc.)."""
        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                return None
                
            return {
                'path': image_path,
                'name': Path(image_path).name,
                'width': pixmap.width(),
                'height': pixmap.height(),
                'format': Path(image_path).suffix.lower(),
                'size_bytes': Path(image_path).stat().st_size
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos de l'image {image_path}: {e}")
            return None 