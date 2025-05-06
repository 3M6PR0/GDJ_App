import sys
import os
import requests # Import restauré
import subprocess # Import restauré
import time # Import restauré
from packaging import version # Import restauré
# import win32api # Commenté - Suppression dépendance
# import win32con # Commenté - Suppression dépendance
import logging

# Initialisation du logger
logger = logging.getLogger('GDJ_App')

# print("Imports win32api et win32con réussis !") # Commenté
# print("Ceci est un test simplifié de update_helper.") # Commenté
# sys.exit(0) # Commenté

# --- Restauration du code fonctionnel (sauf partie win32) ---

def download_installer(installer_url, output_path):
    """
    Télécharge l'installateur depuis installer_url et l'enregistre dans output_path.
    Affiche une barre de progression.
    """
    logger.info(f"Téléchargement depuis: {installer_url}")
    try:
        response = requests.get(installer_url, stream=True, timeout=30) # Ajout timeout
        response.raise_for_status() # Vérifie les erreurs HTTP
        total_length = response.headers.get('content-length')

        with open(output_path, 'wb') as f:
            if total_length is None:
                f.write(response.content)
                logger.info("Téléchargement terminé (taille inconnue).")
            else:
                dl = 0
                total_length = int(total_length)
                logger.info(f"Taille totale : {total_length / 1024 / 1024:.2f} Mo")
                for data in response.iter_content(chunk_size=8192): # Augmentation chunk size
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    percent = (dl / total_length) * 100
                    logger.info(f"[{'=' * done}{' ' * (50 - done)}] {percent:.1f}% ")
        logger.info(f"\nTéléchargement terminé : {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"\nErreur de téléchargement : {e}")
        return False
    except IOError as e:
        logger.error(f"\nErreur d'écriture du fichier : {e}")
        return False

def launch_installer(installer_path):
    """
    Lance l'installateur téléchargé SANS attendre sa fin.
    """
    logger.info(f"Lancement de l'installateur (sans attente) : {installer_path}")
    try:
        # Utilisation de Popen pour lancer et ne pas attendre
        subprocess.Popen([installer_path])
        logger.info("Installeur lancé (Popen retourné). L'helper va se terminer.")
        return True # Succès du lancement
    except Exception as e:
        # Erreur si Popen ne peut même pas lancer le processus
        logger.error(f"Erreur imprévue lors du lancement (Popen) de l'installateur : {e}")
        return False

# def schedule_update_helper_replace(current_path, new_path):
#     """
#     Fonction commentée - dépendance pywin32 supprimée
#     """
#     pass # Ne fait rien

def main():
    if len(sys.argv) < 2:
        logger.error("Usage : update_helper.exe <installer_url>")
        input("Appuyez sur Entrée pour quitter...") # Pause si lancé manuellement
        sys.exit(1)

    installer_url = sys.argv[1]
    logger.info("-- Update Helper Démarré --")
    logger.info(f"URL de l'installeur reçue : {installer_url}")

    temp_directory = os.environ.get("TEMP", os.getcwd())
    output_installer = os.path.join(temp_directory, "GDJ_downloaded_setup.exe") # Nom de fichier plus clair
    logger.info(f"Téléchargement vers : {output_installer}")

    if download_installer(installer_url, output_installer):
        time.sleep(1) # Petite pause après le téléchargement
        if launch_installer(output_installer):
             logger.info("Mise à jour terminée (lancement de l'installeur réussi).")
        else:
             logger.error("Échec du lancement de l'installeur téléchargé.")
             input("Appuyez sur Entrée pour quitter...") # Pause
             sys.exit(1)
    else:
        logger.error("Échec du téléchargement de l'installeur.")
        input("Appuyez sur Entrée pour quitter...") # Pause
        sys.exit(1)

    # Section pour l'auto-update de l'helper commentée car dépendance pywin32 supprimée
    # new_helper_path = os.path.join(temp_directory, "update_helper_new.exe")
    # if os.path.exists(new_helper_path):
    #     app_dir = os.path.dirname(sys.executable)
    #     current_helper_path = os.path.join(app_dir, "updater", "update_helper.exe")
    #     if schedule_update_helper_replace(current_helper_path, new_helper_path):
    #         logger.info(
    #             "La mise à jour de l'update helper sera effectuée au prochain redémarrage.\nVeuillez redémarrer pour finaliser la mise à jour.")

    logger.info("-- Update Helper Terminé --")
    sys.exit(0)

if __name__ == '__main__':
    main()
