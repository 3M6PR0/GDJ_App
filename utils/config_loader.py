# utils/config_loader.py
import json
import os
from config import CONFIG

def load_config_data(filename="config_data.json"):
    data_path = "data"
    if isinstance(CONFIG, dict):
        data_path = CONFIG.get("DATA_PATH", "data")
    else:
        print("Avertissement: CONFIG n'est pas un dictionnaire, utilise data/ par défaut")

    filepath = os.path.join(data_path, filename)
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erreur: Fichier de données JSON non trouvé: {filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"Erreur: Impossible de décoder le JSON dans {filepath}")
        return {}
    except Exception as e:
        print(f"Erreur inattendue lors du chargement de {filepath}: {e}")
        return {}

print("utils/config_loader.py défini")
