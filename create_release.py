import os
import sys
import subprocess
import requests
import configparser
import json
import shutil


# ---------- Fonction pour lire la version depuis data/version.txt ----------
def get_version_from_file():
    version_file = os.path.join("data", "version.txt")
    if not os.path.exists(version_file):
        print(f"Erreur : Le fichier {version_file} n'existe pas.")
        sys.exit(1)
    config = configparser.ConfigParser()
    try:
        config.read(version_file, encoding="utf-8")
        ver = config.get("Version", "value").strip()
    except Exception as e:
        print("Erreur lors de la lecture du fichier version.txt :", e)
        sys.exit(1)
    if not ver.startswith("v"):
        ver = "v" + ver
    return ver


# ---------- Configuration ----------
REPO_OWNER = "3M6PR0"  # Propriétaire du repository sur GitHub
REPO_NAME = "GDJ_App"  # Nom de votre repository
TARGET_BRANCH = "main"  # On travaille directement sur la branche principale

# Récupération de la version depuis data/version.txt
TAG_NAME = get_version_from_file()  # Ex. "v1.1.0"
if not TAG_NAME.startswith("v"):
    TAG_NAME = "v" + TAG_NAME

RELEASE_NAME = f"Version {TAG_NAME} - Release automatique"

# Lire le contenu brut des notes depuis le fichier externe
RELEASE_NOTES_FILE = "RELEASE_NOTES.md"
release_notes_content = ""
try:
    with open(RELEASE_NOTES_FILE, 'r', encoding='utf-8') as f:
        release_notes_content = f.read()
    print(f"Contenu des notes lu depuis {RELEASE_NOTES_FILE}")
except FileNotFoundError:
    print(f"Avertissement : Le fichier {RELEASE_NOTES_FILE} est introuvable. Le corps de la release sera générique.")
    release_notes_content = "Publication automatique de cette version."
except Exception as e:
    print(f"Erreur lors de la lecture de {RELEASE_NOTES_FILE} : {e}. Le corps de la release sera générique.")
    release_notes_content = f"Publication automatique de cette version. Erreur lecture notes: {e}"

# Construire le corps final de la release avec le titre dynamique
RELEASE_BODY = f"# Notes de version - {TAG_NAME}\n\n{release_notes_content}"

DRAFT = False
PRERELEASE = False

# Récupération du token GitHub depuis la variable d'environnement
GITHUB_TOKEN = os.getenv("GH_TOKEN")
if not GITHUB_TOKEN:
    print("Erreur: Le token GitHub n'est pas défini dans la variable d'environnement GH_TOKEN.")
    sys.exit(1)

# URL de l'API GitHub pour les releases
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"

# Chemins utilisés
ISCC_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"  # Chemin vers Inno Setup Compiler
ISS_SCRIPT = os.path.join("installer", "GDJ_Installer.iss")  # Script Inno Setup
INSTALLER_OUTPUT = os.path.join("installer", "Output", "GDJ_Installer.exe")  # Sortie du script .iss


# ---------- Fonctions ----------
def compile_gdj():
    """
    Compile GDJ.exe avec PyInstaller en mode onefile et windowed.
    """
    print("Compilation de GDJ.exe avec PyInstaller...")
    try:
        subprocess.run(
            ["pyinstaller", "--onefile", "--windowed", "--clean", "--name=GDJ", "main.py"],
            check=True,
            capture_output=True, # Capturer stdout/stderr pour ne pas polluer la sortie principale
            text=True
        )
        print("Compilation de GDJ.exe terminée.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de la compilation de GDJ.exe :", e)
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        sys.exit(1)


def compile_update_helper():
    """
    Compile update_helper avec PyInstaller en mode one-folder (simple).
    """
    print("Compilation de update_helper (one-folder, simple) avec PyInstaller...")
    script_path = os.path.join("updater", "update_helper.py")
    helper_name = "update_helper"
    try:
        cmd = [
            "pyinstaller",
            "--noconfirm", # Gardé pour écraser la sortie
            "--clean",
            f"--name={helper_name}",
            # Mode dossier par défaut (pas de --onefile)
            # Imports cachés pour les dépendances restantes
            "--hidden-import=requests",
            "--hidden-import=packaging",
            script_path,
        ]
        print("Commande PyInstaller pour update_helper:", cmd)
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print("Compilation de update_helper (one-folder, simple) terminée.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la compilation de update_helper : {e}")
        print("stdout:", e.stdout); print("stderr:", e.stderr); sys.exit(1)
    except FileNotFoundError:
        print("Erreur : PyInstaller introuvable..."); sys.exit(1)


def compile_innosetup():
    """
    Compile l'installateur via Inno Setup.
    """
    print("Compilation de l'installateur avec Inno Setup...")
    try:
        subprocess.run([ISCC_PATH, ISS_SCRIPT], check=True)
        print("Compilation de l'installateur réussie.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de la compilation de l'installateur :", e)
        sys.exit(1)


def create_release():
    """
    Crée une nouvelle release sur GitHub via l'API.
    """
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "tag_name": TAG_NAME,
        "target_commitish": TARGET_BRANCH,
        "name": RELEASE_NAME,
        "body": RELEASE_BODY,
        "draft": DRAFT,
        "prerelease": PRERELEASE
    }

    print("Création de la release sur GitHub...")
    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 201:
        data = response.json()
        print("Release créée avec succès !")
        print(f"URL de la release : {data.get('html_url')}")
        return data
    else:
        print("Erreur lors de la création de la release :", response.status_code)
        print(response.text)
        sys.exit(1)


def upload_asset(upload_url, asset_path, asset_label=None):
    """
    Upload un asset vers la release via l'API GitHub.
    """
    upload_url = upload_url.split("{")[0]
    filename = os.path.basename(asset_path)
    params = {"name": filename}
    if asset_label:
        params["label"] = asset_label
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/octet-stream",
    }

    with open(asset_path, "rb") as asset_file:
        print(f"Upload de l'asset {filename}...")
        response = requests.post(upload_url, headers=headers, params=params, data=asset_file)

    if response.status_code == 201:
        print(f"L'asset {filename} a été uploadé avec succès.")
        return response.json()
    else:
        print("Erreur lors de l'upload de l'asset :", response.status_code)
        print(response.text)
        sys.exit(1)


# ---------- Main ----------
def main():
    # Étape 1 : Compiler GDJ.exe avec PyInstaller (onefile).
    compile_gdj()
    gdj_path_dist = os.path.join("dist", "GDJ.exe")
    gdj_path_installer_src = os.path.join("installer", "GDJ.exe")
    if not os.path.exists(gdj_path_dist):
        print("Erreur : GDJ.exe n'a pas été trouvé...")
        sys.exit(1)

    # Étape 1.5 : Compiler update_helper (one-folder) avec PyInstaller.
    compile_update_helper()
    # Le résultat est maintenant un dossier dist/update_helper
    updater_folder_dist = os.path.join("dist", "update_helper")
    updater_dest_folder_installer = os.path.join("installer", "updater") # Dossier cible pour Inno Setup
    if not os.path.exists(updater_folder_dist):
        print("Erreur : Le dossier de l'updater n'a pas été trouvé dans 'dist'.")
        sys.exit(1)

    # Supprimer l'ancien dossier de destination s'il existe et le recréer
    if os.path.exists(updater_dest_folder_installer):
        shutil.rmtree(updater_dest_folder_installer)
    # os.makedirs(updater_dest_folder_installer, exist_ok=True) # copytree le crée

    # Copier GDJ.exe et le dossier update_helper dans le dossier installer
    try:
        print(f"Copie de {gdj_path_dist} vers {gdj_path_installer_src}...")
        shutil.copy(gdj_path_dist, gdj_path_installer_src)
        print("Copie GDJ.exe réussie.")
        print(f"Copie du dossier {updater_folder_dist} vers {updater_dest_folder_installer}...")
        shutil.copytree(updater_folder_dist, updater_dest_folder_installer)
        print("Copie du dossier update_helper réussie.")
    except Exception as e:
        print(f"Erreur lors de la copie des exécutables/dossiers vers le dossier installer : {e}")
        sys.exit(1)

    # Étape 2 : Compiler l'installateur via Inno Setup.
    compile_innosetup()
    if not os.path.exists(INSTALLER_OUTPUT):
        print("Erreur : L'installateur n'a pas été trouvé...")
        # Nettoyage si l'installeur échoue
        if os.path.exists(gdj_path_installer_src):
            os.remove(gdj_path_installer_src)
        if os.path.exists(updater_dest_folder_installer):
            shutil.rmtree(updater_dest_folder_installer)
        sys.exit(1)

    # Étape 3 : Créer la release GitHub à partir de la branche main.
    release_info = create_release()

    # Étape 4 : Uploader l'installateur sur la release.
    upload_url = release_info["upload_url"]
    upload_asset(upload_url, INSTALLER_OUTPUT, asset_label="Installateur GDJ")

    # Étape 5 : Supprimée - GDJ.exe n'est plus uploadé séparément

    # Nettoyage : Supprimer GDJ.exe et le dossier updater du dossier installer
    if os.path.exists(gdj_path_installer_src):
        try:
            os.remove(gdj_path_installer_src)
            print(f"Nettoyage : {gdj_path_installer_src} supprimé.")
        except Exception as e:
            print(f"Avertissement : Échec suppression {gdj_path_installer_src}: {e}")
    if os.path.exists(updater_dest_folder_installer):
        try:
            shutil.rmtree(updater_dest_folder_installer)
            print(f"Nettoyage : Dossier {updater_dest_folder_installer} supprimé.")
        except Exception as e:
            print(f"Avertissement : Échec suppression dossier {updater_dest_folder_installer}: {e}")

    print("Processus de création de release terminé avec succès.")


if __name__ == '__main__':
    main()
