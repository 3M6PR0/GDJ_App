import sys
import os

def get_base_path():
    """ 
    Retourne le chemin de base absolu de l'application.
    
    Fonctionne que l'application soit exécutée depuis les sources
    ou compilée avec PyInstaller (en mode one-file ou one-folder).
    """
    if getattr(sys, 'frozen', False):
        # Si l'application est compilée (frozen)
        # Le chemin de base est le dossier contenant l'exécutable
        return os.path.dirname(sys.executable)
    else:
        # Si exécuté depuis les sources.
        # On suppose que ce fichier (paths.py) est dans utils/
        # et que la racine du projet est un niveau au-dessus.
        # Si la structure est différente, ce chemin doit être ajusté.
        # Alternative: utiliser le chemin du script principal (main.py)
        # return os.path.dirname(os.path.abspath(sys.argv[0]))
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- NOUVELLE FONCTION ---
def get_resource_path(relative_path):
    """
    Construit le chemin absolu vers une ressource à partir du chemin de base.

    Args:
        relative_path (str): Le chemin relatif depuis la racine du projet/application
                             (ex: "resources/icons/icon.png" ou "data/config.json").
                             Utiliser des slashes (/) pour la portabilité.

    Returns:
        str: Le chemin absolu complet vers la ressource.
    """
    base = get_base_path()
    # os.path.join gère les séparateurs corrects pour l'OS
    return os.path.join(base, relative_path.replace('/', os.sep))

# Exemple d'utilisation (à ne pas laisser dans le code final ici) :
# if __name__ == '__main__':
#     BASE_PATH = get_base_path()
#     print(f"Chemin de base détecté : {BASE_PATH}")
#     # Test d'accès à un fichier de ressources
#     icon_test_path = os.path.join(BASE_PATH, "resources", "icons", "clear", "round_settings.png")
#     print(f"Tentative d'accès à : {icon_test_path}")
#     print(f"Existe : {os.path.exists(icon_test_path)}")
#     # Test d'accès à un fichier de données
#     data_test_path = os.path.join(BASE_PATH, "data", "config_data.json")
#     print(f"Tentative d'accès à : {data_test_path}")
#     print(f"Existe : {os.path.exists(data_test_path)}")
#     # Test avec un chemin de ressource
#     icon_path = get_resource_path("resources/icons/clear/round_settings.png")
#     print(f"Chemin ressource calculé : {icon_path}")
#     print(f"Existe : {os.path.exists(icon_path)}")
#     # Test avec un chemin de donnée
#     data_path = get_resource_path("data/config_data.json")
#     print(f"Chemin donnée calculé : {data_path}")
#     print(f"Existe : {os.path.exists(data_path)}") 