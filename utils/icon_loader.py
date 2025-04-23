# utils/icon_loader.py
import logging
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
    Construit le chemin absolu vers une icône en fonction du thème actif.

    Args:
        icon_base_name (str): Le nom de base du fichier icône (ex: "round_update.png").

    Returns:
        str: Le chemin absolu vers le fichier icône approprié pour le thème.
             Retourne un chemin vide si le nom de base est vide.
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
        
    relative_path = f"resources/icons/{icon_subfolder}/{icon_base_name}"
    
    # Utiliser la fonction existante pour obtenir le chemin absolu (gère source/frozen)
    absolute_path = get_resource_path(relative_path)
    
    # logger.debug(f"Icon path requested for '{icon_base_name}' (Theme: '{_active_theme}' -> Folder: '{icon_subfolder}') -> '{absolute_path}'")
    return absolute_path

print("utils/icon_loader.py defined.") 