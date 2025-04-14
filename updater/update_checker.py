# updater/update_checker.py

import os
import json
import requests
import subprocess
import sys
from packaging import version  # Pour comparer les versions
from config import CONFIG
from PyQt5.QtWidgets import QMessageBox

# Paramètres de votre dépôt GitHub (à adapter)
REPO_OWNER = "3M6PR0"  # Remplacez par le nom de votre compte ou organisation
REPO_NAME = "GDJ_App"      # Remplacez par le nom de votre repository

# URL de l'API GitHub pour la dernière release
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

# Chemin local pour stocker la version (ex. data/version.txt)
VERSION_FILE = os.path.join(CONFIG.get("DATA_PATH", "data"), "version.txt")

# Chemin vers l'exécutable update helper (à générer et placer dans un dossier dédié, par exemple "updater")
UPDATER_EXECUTABLE = os.path.join("updater", "updater.exe")


def get_local_version():
    """Lit la version locale depuis le fichier version.txt."""
    if not os.path.exists(VERSION_FILE):
        return "0.0.0"
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        ver = f.read().strip()
    return ver


def get_remote_release_info():
    """Interroge l'API GitHub pour récupérer les informations de la dernière release."""
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print("Erreur lors de la récupération des informations de release :", response.status_code)
    except Exception as e:
        print("Exception lors de la récupération de la release :", e)
    return None


def is_new_version_available(local_ver, remote_ver):
    """Compare les versions locales et distantes en utilisant packaging.version."""
    try:
        return version.parse(remote_ver) > version.parse(local_ver)
    except Exception as e:
        print("Erreur lors de la comparaison des versions :", e)
        return False


def prompt_update(remote_version):
    """Affiche une boîte de dialogue pour demander à l'utilisateur s'il souhaite mettre à jour."""
    message = f"Une nouvelle version ({remote_version}) est disponible. Voulez-vous mettre à jour maintenant ?"
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Question)
    msg_box.setWindowTitle("Mise à jour disponible")
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    result = msg_box.exec_()
    return result == QMessageBox.Yes


def launch_updater(installer_url):
    """Lance l'update helper en lui passant l'URL de l'installateur en paramètre."""
    try:
        # Lancer l'exécutable updater avec l'URL comme argument
        subprocess.Popen([UPDATER_EXECUTABLE, installer_url])
        # Fermer l'application principale
        sys.exit(0)
    except Exception as e:
        print("Erreur lors du lancement de l'updater :", e)


def check_for_updates():
    """Fonction principale à appeler au démarrage pour vérifier et proposer une mise à jour."""
    local_version = get_local_version()
    release_info = get_remote_release_info()
    if not release_info:
        return

    remote_version = release_info.get("tag_name", "0.0.0")
    print(f"Version locale : {local_version} | Version distante : {remote_version}")

    if is_new_version_available(local_version, remote_version):
        if prompt_update(remote_version):
            # Recherche dans les assets de la release l'installateur (setup.exe ou MSI)
            assets = release_info.get("assets", [])
            installer_url = None
            for asset in assets:
                name = asset.get("name", "").lower()
                if "setup" in name or "installer" in name or name.endswith(".msi") or name.endswith(".exe"):
                    installer_url = asset.get("browser_download_url")
                    break
            if installer_url:
                launch_updater(installer_url)
            else:
                print("Aucun installateur trouvé dans les assets de la release.")
    else:
        print("Aucune mise à jour disponible.")
