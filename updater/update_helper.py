import sys
import requests
import os
import subprocess
import time


def download_installer(installer_url, output_path):
    """Télécharge l'installateur en affichant une barre de progression."""
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
    print("\nTéléchargement terminé : {}".format(output_path))


def launch_installer(installer_path):
    """Lance l'installateur."""
    print("Lancement de l'installateur...")
    # Lancer l'installateur. Selon votre installateur, vous pourriez avoir besoin de droits élevés.
    subprocess.run([installer_path])
    print("Installation terminée.")


def main():
    if len(sys.argv) < 2:
        print("Usage : update_helper.exe <installer_url>")
        sys.exit(1)

    installer_url = sys.argv[1]
    # Définir le chemin temporaire pour le fichier téléchargé.
    output_installer = os.path.join(os.path.abspath(os.path.dirname(__file__)), "installer_setup.exe")

    print("Téléchargement de l'installateur depuis :")
    print(installer_url)
    download_installer(installer_url, output_installer)

    # Petite pause pour être certain que le téléchargement est terminé
    time.sleep(1)
    launch_installer(output_installer)

    # Optionnel : supprimer le fichier téléchargé après l'installation
    # os.remove(output_installer)


if __name__ == '__main__':
    main()
