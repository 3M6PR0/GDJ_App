# utils/config_loader.py
import json
import os
# Retirer: from config import CONFIG

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

def load_config_data(filename="config_data.json"):
    """Charge un fichier de config JSON depuis le dossier data via get_resource_path."""
    # Construire le chemin relatif dans data
    relative_path = os.path.join("data", filename)
    # Obtenir le chemin absolu
    absolute_filepath = get_resource_path(relative_path)
    print(f"DEBUG: Chemin {filename} calculé par config_loader: {absolute_filepath}") # Ajout debug
    
    try:
        # Lire depuis le chemin absolu
        with open(absolute_filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erreur: Fichier de données JSON non trouvé: {absolute_filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"Erreur: Impossible de décoder le JSON dans {absolute_filepath}")
        return {}
    except Exception as e:
        print(f"Erreur inattendue lors du chargement de {absolute_filepath}: {e}")
        return {}

print("utils/config_loader.py défini")
