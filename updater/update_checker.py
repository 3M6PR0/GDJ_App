# updater/update_checker.py

import os
import json
import requests
import subprocess
import sys
import configparser
from packaging import version  # Pour comparer les versions
from config import CONFIG
from PyQt5.QtWidgets import QMessageBox

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

# Paramètres de votre dépôt GitHub (à adapter)
REPO_OWNER = "3M6PR0"  # Remplacez par le nom de votre compte ou organisation
REPO_NAME = "GDJ_App"      # Remplacez par le nom de votre repository

# URL de l'API GitHub pour la dernière release
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

# --- Utiliser get_resource_path --- 
VERSION_FILE = get_resource_path(os.path.join(CONFIG.get("DATA_PATH", "data"), "version.txt"))
# Chemin vers l'exécutable update helper (calculé une seule fois)
UPDATER_EXECUTABLE = get_resource_path(os.path.join("updater", "update_helper.exe"))


def get_local_version():
    """Lit la version locale depuis le fichier version.txt."""
    # VERSION_FILE est maintenant le chemin absolu
    if not os.path.exists(VERSION_FILE):
        print(f"DEBUG: {VERSION_FILE} non trouvé.") # Debug
        return "0.0.0"
    config = configparser.ConfigParser()
    try:
        config.read(VERSION_FILE, encoding="utf-8")
        return config.get("Version", "value").strip()
    except Exception as e:
        print(f"Erreur lecture {VERSION_FILE}: {e}") # Debug
        return "0.0.0"


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
    """Lance l'update helper en lui passant l'URL de l'installateur."""
    try:
        print("Tentative de lancement de l'update helper...")
        # Utiliser la constante globale UPDATER_EXECUTABLE
        print(f"Chemin updater: {UPDATER_EXECUTABLE}")

        if not os.path.exists(UPDATER_EXECUTABLE):
            print(f"Erreur : {UPDATER_EXECUTABLE} non trouvé.")
            QMessageBox.critical(None, "Erreur de mise à jour",
                                 f"Le fichier nécessaire à la mise à jour est introuvable.\nChemin attendu : {UPDATER_EXECUTABLE}")
            return

        print("Lancement de l'update helper avec l'URL :", installer_url)
        subprocess.Popen([UPDATER_EXECUTABLE, installer_url])
        print("Update helper lancé, fermeture de l'application principale.")
        sys.exit(0)

    except Exception as e:
        print("Erreur lors du lancement de l'updater :", e)
        QMessageBox.critical(None, "Erreur de mise à jour",
                             f"Une erreur est survenue lors du lancement de la mise à jour :\n{e}")


def check_for_updates(manual_check=False):
    """
    Vérifie les mises à jour sur GitHub et lance l'updater si nécessaire.
    Retourne un message de statut pour affichage.
    
    Args:
        manual_check (bool): True si la vérification est déclenchée manuellement.
                             Affecte seulement le message de retour.
                             
    Returns:
        str: Un message décrivant le résultat ("À jour", "MàJ X trouvée", "Erreur: ...")
    """
    status_message = "Statut : Inconnu"
    update_info = {"available": False, "version": None, "url": None} # Pour retourner plus d'infos
    try:
        local_version = get_local_version()
        release_info = get_remote_release_info()
        if not release_info:
            status_message = "Erreur : Impossible de contacter GitHub."
            if manual_check:
                print("Manual Check: " + status_message)
            return status_message, update_info # Sortir tôt

        remote_version = release_info.get("tag_name", "0.0.0")
        print(f"Version locale : {local_version} | Version distante : {remote_version}")

        is_new = is_new_version_available(local_version, remote_version)

        if is_new:
            status_message = f"Mise à jour trouvée : {remote_version}"
            update_info["available"] = True
            update_info["version"] = remote_version
            
            # --- Ne pas appeler prompt si manual_check est True --- 
            if not manual_check:
                print("Automatic check found update, prompting user...")
                if prompt_update(remote_version):
                    assets = release_info.get("assets", [])
                    installer_name_expected = "gdj_installer.exe"
                    print(f"Recherche de l'asset '{installer_name_expected}'...")
                    installer_url = None
                    for asset in assets:
                        name = asset.get("name", "").lower()
                        print(f"  - Asset trouvé : {name}")
                        if installer_name_expected == name:
                            installer_url = asset.get("browser_download_url")
                            print(f"    -> Correspondance trouvée ! URL : {installer_url}")
                            break
                    update_info["url"] = installer_url # Stocker l'URL trouvée
                    if installer_url:
                        launch_updater(installer_url)
                    else:
                        status_message = f"Erreur : Installateur ({installer_name_expected}) non trouvé."
                        update_info["available"] = False # Marquer comme non dispo si asset manque
                        # QMessageBox.warning(...) # Gardé car critique
                else:
                    status_message = "Mise à jour refusée par l'utilisateur."
                    update_info["available"] = False # Refusée = non dispo pour l'instant
            else:
                 # En mode manuel, on récupère juste l'URL si possible pour plus tard
                 print("Manual check found update. Storing info.")
                 assets = release_info.get("assets", [])
                 installer_name_expected = "gdj_installer.exe"
                 installer_url = None
                 for asset in assets:
                     name = asset.get("name", "").lower()
                     if installer_name_expected == name:
                         installer_url = asset.get("browser_download_url")
                         break
                 update_info["url"] = installer_url 
                 if not installer_url:
                      status_message = f"Mise à jour trouvée ({remote_version}) mais asset introuvable."
                      update_info["available"] = False # Si pas d'asset, l'update n'est pas réellement "disponible"
        else:
            status_message = "À jour"
            print("Aucune mise à jour disponible.")
            if manual_check:
                print("Manual Check: " + status_message)
                # RETIRER: QMessageBox.information(None, "Mise à jour", "Votre application est à jour.")

    except Exception as e:
        error_text = str(e)
        print(f"Erreur lors de la vérification des mises à jour: {error_text}")
        status_message = f"Erreur lors de la vérification : {error_text}"
        update_info["available"] = False
        if manual_check:
            print("Manual Check: Échec de la vérification des mises à jour.")
            # RETIRER: QMessageBox.warning(None, "Mise à jour", f"Impossible de vérifier les mises à jour.\nErreur: {e}")
    
    # Retourner un tuple: (message, info_dict)
    return status_message, update_info

print("updater/update_checker.py défini")
