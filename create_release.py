import os
import sys
import subprocess
import requests
import configparser
import json


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
TAG_NAME = get_version_from_file()  # Ex. "v1.0.14" ou "1.0.14", selon ce que contient le fichier
# Si le fichier contient seulement la version sans "v", on peut l'ajouter automatiquement :
if not TAG_NAME.startswith("v"):
    TAG_NAME = "v" + TAG_NAME

RELEASE_NAME = f"Version {TAG_NAME} - Release automatique"
RELEASE_BODY = "Ceci est une release générée automatiquement avec l'installateur compilé."
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
            check=True
        )
        print("Compilation de GDJ.exe terminée.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de la compilation de GDJ.exe :", e)
        sys.exit(1)


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
    # Étape 1 : Compiler GDJ.exe avec PyInstaller.
    compile_gdj()
    gdj_path = os.path.join("dist", "GDJ.exe")
    if not os.path.exists(gdj_path):
        print("Erreur : GDJ.exe n'a pas été trouvé dans le dossier 'dist'.")
        sys.exit(1)

    # Étape 2 : Compiler l'installateur via Inno Setup.
    compile_innosetup()
    if not os.path.exists(INSTALLER_OUTPUT):
        print("Erreur : L'installateur n'a pas été trouvé à", INSTALLER_OUTPUT)
        sys.exit(1)

    # Étape 3 : Créer la release GitHub à partir de la branche main.
    release_info = create_release()

    # Étape 4 : Uploader l'installateur sur la release.
    upload_url = release_info["upload_url"]
    upload_asset(upload_url, INSTALLER_OUTPUT, asset_label="Installateur GDJ")

    # Étape 5 : Uploader GDJ.exe dans la release.
    upload_asset(upload_url, gdj_path, asset_label="GDJ.exe")

    print("Processus de création de release terminé avec succès.")


if __name__ == '__main__':
    main()
