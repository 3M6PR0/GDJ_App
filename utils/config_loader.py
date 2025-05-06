# utils/config_loader.py
import json
import os
# Retirer: from config import CONFIG
import logging # Ajout pour le logger

# Initialisation du logger
logger = logging.getLogger('GDJ_App')

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

def load_config_data(filename="config_data.json"):
    """Charge un fichier de config JSON depuis le dossier data via get_resource_path."""
    # Construire le chemin relatif dans data
    relative_path = os.path.join("data", filename)
    # Obtenir le chemin absolu
    absolute_filepath = get_resource_path(relative_path)
    logger.debug(f"DEBUG: Chemin {filename} calculé par config_loader: {absolute_filepath}") # Remplacement
    
    try:
        # Lire depuis le chemin absolu
        with open(absolute_filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Erreur: Fichier de données JSON non trouvé: {absolute_filepath}") # Remplacement
        return {}
    except json.JSONDecodeError:
        logger.error(f"Erreur: Impossible de décoder le JSON dans {absolute_filepath}") # Remplacement
        return {}
    except Exception as e:
        logger.error(f"Erreur inattendue lors du chargement de {absolute_filepath}: {e}") # Remplacement
        return {}

logger.info("utils/config_loader.py défini") # Remplacement
