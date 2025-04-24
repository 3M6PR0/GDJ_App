# utils/icon_loader.py
import logging
import os
from utils.paths import get_resource_path

logger = logging.getLogger(__name__)

# Variable globale du module pour stocker le nom du thème actif
_active_theme = "Sombre"  # Thème par défaut au démarrage

def set_active_theme(theme_name: str):
    """
    Met à jour le thème actif utilisé pour choisir les icônes.
    Doit être appelée lorsque le thème de l'application change.

    Args:
        theme_name (str): Le nom du nouveau thème actif ('Clair' ou 'Sombre').
    """
    global _active_theme
    if theme_name in ["Clair", "Sombre"]:
        if _active_theme != theme_name:
            logger.info(f"Setting active icon theme based on application theme: {theme_name}")
            _active_theme = theme_name
        # else: # Optionnel: logger.debug(f"Icon theme already set for: {theme_name}")
    else:
        logger.warning(f"Attempted to set invalid theme for icons: '{theme_name}'. Keeping '{_active_theme}'.")

def get_icon_path(icon_base_name: str) -> str:
    """
    Construit le chemin absolu vers une icône en fonction du thème actif,
    avec fallback sur l'icône de base si l'icône spécifique au thème n'est pas trouvée.

    Args:
        icon_base_name (str): Le nom de base du fichier icône (ex: "round_update.png").

    Returns:
        str: Le chemin absolu vers le fichier icône approprié, ou un chemin vide si introuvable.
    """
    if not icon_base_name:
        return ""
        
    global _active_theme
    
    # Logique inversée comme demandé:
    # Thème Clair -> Icônes 'dark'
    # Thème Sombre -> Icônes 'clear'
    if _active_theme == "Clair":
        icon_subfolder = "dark"
    else:  # Défaut sur 'clear' pour "Sombre" ou autre valeur inattendue
        icon_subfolder = "clear"
        
    # Essayer le chemin spécifique au thème D'ABORD
    relative_theme_path = f"resources/icons/{icon_subfolder}/{icon_base_name}"
    absolute_theme_path = get_resource_path(relative_theme_path)
    
    # Vérifier si le fichier existe
    if os.path.exists(absolute_theme_path):
        # logger.debug(f"Icon '{icon_base_name}' found for theme '{_active_theme}' (folder '{icon_subfolder}'): {absolute_theme_path}")
        return absolute_theme_path
    else:
        # logger.warning(f"Icon '{icon_base_name}' NOT found for theme '{_active_theme}' (folder '{icon_subfolder}'). Path tried: {absolute_theme_path}")
        # Essayer le chemin de base comme fallback
        relative_base_path = f"resources/icons/{icon_base_name}"
        absolute_base_path = get_resource_path(relative_base_path)
        if os.path.exists(absolute_base_path):
             # logger.info(f"Falling back to base icon '{icon_base_name}': {absolute_base_path}")
             return absolute_base_path
        else:
             logger.error(f"Base icon '{icon_base_name}' also NOT found. Path tried: {absolute_base_path}")
             return "" # Retourner vide si aucune icône n'est trouvée

print("utils/icon_loader.py defined with theme fallback.") 