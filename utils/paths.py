import sys
import os
from pathlib import Path

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
def get_resource_path(relative_path: str) -> str:
    """
    Construit le chemin absolu vers une ressource à partir du chemin de base.

    Args:
        relative_path (str): Le chemin relatif depuis la racine du projet/application
                             (ex: "resources/icons/icon.png" ou "data/config.json").
                             Utiliser des slashes (/) pour la portabilité.

    Returns:
        str: Le chemin absolu complet vers la ressource.
    """
    base = Path(get_base_path())
    # Construire le chemin en utilisant Path pour une meilleure gestion des / et \
    # et s'assurer que relative_path est traité correctement même s'il commence par / ou \
    # en le décomposant et en le rejoignant.
    # Cependant, os.path.join fait déjà cela correctement.
    # Simplicité:
    # return str(base.joinpath(*relative_path.replace('\\', '/').split('/')))
    # La version originale avec os.path.join est plus directe ici si relative_path est bien formé.
    # Gardons la conversion explicite des slashes pour être sûr.
    return os.path.join(str(base), *relative_path.replace('\\', '/').split('/'))

# --- NOUVELLE FONCTION: Pour obtenir le chemin des données utilisateur ---
def get_user_data_path(subfolder: str = None) -> Path:
    """
    Retourne le chemin vers un dossier de données spécifique à l'application dans AppData.
    Crée le dossier (et le sous-dossier GDJ_App) s'il n'existe pas.

    Args:
        subfolder (str, optional): Un sous-dossier optionnel à créer/retourner 
                                   à l'intérieur du dossier de données de l'application.
                                   Ex: "FacturesEntrees", "Logs", etc.

    Returns:
        Path: Un objet Path vers le dossier de données utilisateur (ou le sous-dossier).
              Retourne Path('.') en cas d'erreur critique d'accès à APPDATA.
    """
    try:
        # Utiliser LOCALAPPDATA est souvent préférable pour les données non itinérantes
        appdata_base = os.getenv('LOCALAPPDATA')
        if not appdata_base: # Fallback sur APPDATA si LOCALAPPDATA n'est pas défini
            appdata_base = os.getenv('APPDATA')
        if not appdata_base: # Fallback ultime sur le répertoire courant si aucun n'est défini
            app_dir_base = Path('.') / 'GDJ_App_User_Data' # Pour éviter de polluer le répertoire courant directement
            # print("AVERTISSEMENT: LOCALAPPDATA et APPDATA non définis. Utilisation d'un dossier local.") # Logguer ceci serait mieux
        else:
            app_dir_base = Path(appdata_base) / 'GDJ_App'

        if subfolder:
            target_path = app_dir_base / subfolder
        else:
            target_path = app_dir_base
        
        target_path.mkdir(parents=True, exist_ok=True)
        return target_path
    except Exception as e:
        # print(f"ERREUR CRITIQUE: Impossible de créer/accéder au dossier de données utilisateur : {e}") # Logguer
        # En cas d'erreur majeure, retourner un chemin local sûr pour éviter un crash complet.
        # Mais cela indique un problème de configuration ou de permissions.
        fallback_path = Path('.') / 'GDJ_App_User_Data_Fallback'
        if subfolder:
            fallback_path = fallback_path / subfolder
        try:
            fallback_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass # Si même le fallback échoue, on ne peut plus faire grand chose ici.
        return fallback_path

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