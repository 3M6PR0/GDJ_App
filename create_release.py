import os
import sys
import subprocess
import requests
import json

# ---------- Configuration ----------
REPO_OWNER = "3M6PR0"          # Propriétaire du repository
REPO_NAME = "GDJ_App"          # Nom du repository
TARGET_BRANCH = "main"         # Branche cible de la release
TAG_NAME = "v1.0.11"            # Tag de la nouvelle release
RELEASE_NAME = "Version 1.0.11 - Release automatique"
RELEASE_BODY = "Ceci est une release générée automatiquement avec l'installateur compilé."
DRAFT = False
PRERELEASE = False


# Récupération du token GitHub
GITHUB_TOKEN = os.getenv("GH_TOKEN")
if not GITHUB_TOKEN:
    print("Erreur: Le token GitHub n'est pas défini dans la variable d'environnement GH_TOKEN.")
    sys.exit(1)

# URL de l'API GitHub pour les releases
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"

# Chemin de l'exécutable Inno Setup (adapté à votre installation)
ISCC_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
# Chemin vers votre script Inno Setup
ISS_SCRIPT = os.path.join("installer", "GDJ_Installer.iss")
# Chemin de l'artefact compilé (la sortie de Inno Setup)
INSTALLER_OUTPUT = os.path.join("installer", "Output", "GDJ_Installer.exe")

# ---------- Fonctions ----------

def compile_innosetup():
    """Compile l'installateur avec Inno Setup."""
    print("Compilation de l'installateur avec Inno Setup...")
    try:
        result = subprocess.run([ISCC_PATH, ISS_SCRIPT], check=True)
        print("Compilation réussie.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de la compilation de l'installateur :", e)
        sys.exit(1)

def create_release():
    """Crée une nouvelle release sur GitHub via l'API."""
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
    print("Création de la release...")
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
    """Upload un asset vers la release via l'API GitHub."""
    # L'URL d'upload contient une partie templatisée ; on l'extrait :
    upload_url = upload_url.split("{")[0]
    filename = os.path.basename(asset_path)
    params = {"name": filename}
    if asset_label:
        params["label"] = asset_label
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/octet-stream",
    }
    with open(asset_path, "rb") as f:
        print(f"Upload de l'asset {filename}...")
        response = requests.post(upload_url, headers=headers, params=params, data=f)
    if response.status_code == 201:
        print(f"L'asset {filename} a été uploadé avec succès.")
        return response.json()
    else:
        print("Erreur lors de l'upload de l'asset :", response.status_code)
        print(response.text)
        sys.exit(1)

# ---------- Main ----------
def main():
    # Étape 1 : Compiler l'installateur Inno Setup
    compile_innosetup()

    # Vérifier que l'artefact de l'installateur a bien été généré
    if not os.path.exists(INSTALLER_OUTPUT):
        print("Erreur : l'artefact installateur n'a pas été trouvé à", INSTALLER_OUTPUT)
        sys.exit(1)

    # Étape 2 : Créer la release GitHub
    release_info = create_release()

    # Étape 3 : Uploader l'artefact (installateur) sur la release
    upload_url = release_info["upload_url"]
    upload_asset(upload_url, INSTALLER_OUTPUT, asset_label="Installateur GDJ")

    print("Processus de création de release terminé avec succès.")

if __name__ == '__main__':
    main()
