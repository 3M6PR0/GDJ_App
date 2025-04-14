import sys
import os
import requests
import subprocess
import time
from packaging import version  # Pour comparer les versions
import win32api
import win32con


def download_installer(installer_url, output_path):
    """
    Télécharge l'installateur depuis installer_url et l'enregistre dans output_path.
    Affiche une barre de progression.
    """
    response = requests.get(installer_url, stream=True)
    total_length = response.headers.get('content-length')
    with open(output_path, 'wb') as f:
        if total_length is None:
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write('\r[{}{}]'.format('=' * done, ' ' * (50 - done)))
                sys.stdout.flush()
    print("\nTéléchargement terminé :", output_path)


def launch_installer(installer_path):
    """
    Lance l'installateur téléchargé.
    """
    print("Lancement de l'installateur...")
    try:
        # Utilisation de subprocess.run pour attendre la fin de l'installation
        subprocess.run([installer_path], check=True)
        print("Installation terminée.")
    except Exception as e:
        print("Erreur lors du lancement de l'installateur :", e)


def schedule_update_helper_replace(current_path, new_path):
    """
    Planifie le remplacement de current_path par new_path lors du prochain redémarrage.
    Utilise MoveFileEx avec le flag MOVEFILE_DELAY_UNTIL_REBOOT.
    """
    if not os.path.exists(new_path):
        print("Le nouveau fichier n'existe pas :", new_path)
        return False
    try:
        win32api.MoveFileEx(new_path, current_path,
                            win32con.MOVEFILE_REPLACE_EXISTING | win32con.MOVEFILE_DELAY_UNTIL_REBOOT)
        print("Remplacement planifié pour le prochain redémarrage.")
        return True
    except Exception as e:
        print("Erreur lors de la planification du remplacement :", e)
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage : update_helper.exe <installer_url>")
        sys.exit(1)

    installer_url = sys.argv[1]
    print("Téléchargement de l'installateur depuis :")
    print(installer_url)

    # Définir le dossier temporaire (on utilise la variable d'environnement TEMP ou le répertoire courant)
    temp_directory = os.environ.get("TEMP", os.getcwd())
    output_installer = os.path.join(temp_directory, "installer_setup.exe")

    download_installer(installer_url, output_installer)
    time.sleep(1)
    launch_installer(output_installer)

    # Optionnel : Si une nouvelle version de update_helper.exe est téléchargée,
    # planifiez le remplacement pour le prochain redémarrage.
    # Ici, on vérifie l'existence d'un fichier "update_helper_new.exe" dans le dossier temporaire.
    new_helper_path = os.path.join(temp_directory, "update_helper_new.exe")
    if os.path.exists(new_helper_path):
        # Récupère le dossier de l'exécutable installé.
        # On suppose que update_helper.exe se trouve dans le sous-dossier "updater" de l'application installée.
        app_dir = os.path.dirname(sys.executable)
        current_helper_path = os.path.join(app_dir, "updater", "update_helper.exe")
        if schedule_update_helper_replace(current_helper_path, new_helper_path):
            print(
                "La mise à jour de l'update helper sera effectuée au prochain redémarrage.\nVeuillez redémarrer pour finaliser la mise à jour.")

    sys.exit(0)


if __name__ == '__main__':
    main()
