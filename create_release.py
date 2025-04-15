import os
import sys
import subprocess
import requests
import json

# ---------- Configuration ----------
REPO_OWNER = "3M6PR0"  # Propriétaire du repository
REPO_NAME = "GDJ_App"  # Nom du repository
TARGET_BRANCH = "main"  # Branche cible de la release
TAG_NAME = "v1.0.12"  # Le tag de la nouvelle release
RELEASE_NAME = "Version 1.0.12 - Release automatique"
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

# Chemin de l'exécutable Inno Setup (adapté à votre installation)
ISCC_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
# Chemin vers le script Inno Setup (dans le dossier installer)
ISS_SCRIPT = os.path.join("installer", "GDJ_Installer.iss")
# Chemin de l'artefact compilé par Inno Setup (sortie du script .iss)
INSTALLER_OUTPUT = os.path.join("installer", "Output", "GDJ_Installer.exe")


# ---------- Fonctions ----------

def compile_gdj():
    """
    Compile l'exécutable GDJ.exe avec PyInstaller.
    L'option --onefile crée un exécutable autonome, --windowed évite l'ouverture de la console.
    """
    print("Compilation de GDJ.exe avec PyInstaller...")
    try:
        # Nettoyage préalable pour forcer la recompilation.
        subprocess.run(
            ["pyinstaller", "--onefile", "--windowed", "--clean", "--name=GDJ", "main.py"],
            check=True
        )
        print("Compilation de GDJ.exe terminée.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de la compilation de GDJ.exe :", e)
        sys.exit(1)


def git_commit_push(commit_message):
    """
    Effectue un commit et un push sur le dépôt.
    Cette étape est optionnelle, à utiliser uniquement si vous souhaitez pousser
    les modifications (par exemple, la nouvelle build) dans votre dépôt avant la release.
    """
    try:
        print("Ajout des modifications au dépôt...")
        subprocess.run(["git", "add", "."], check=True)
        print("Commit des modifications...")
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print("Poussée des modifications...")
        subprocess.run(["git", "push"], check=True)
        print("Modifications poussées avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors du commit/push :", e)
        # Selon votre besoin, vous pouvez choisir de continuer ou d'arrêter ici.
        # sys.exit(1)


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
    # Extraction de l'URL d'upload.
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
    # Étape 1 : Compiler GDJ.exe via PyInstaller.
    compile_gdj()

    # Vérifier que le nouveau GDJ.exe existe.
    gdj_path = os.path.join("dist", "GDJ.exe")
    if not os.path.exists(gdj_path):
        print("Erreur : GDJ.exe n'a pas été trouvé dans le dossier 'dist'.")
        sys.exit(1)

    # Optionnel : Pousser le build dans le dépôt si nécessaire.
    # Vous pouvez commenter la ligne suivante si vous ne souhaitez pas pousser.
    git_commit_push(f"Build release {TAG_NAME} - Mise à jour de GDJ.exe")

    # Étape 2 : Compiler l'installateur via Inno Setup.
    compile_innosetup()

    # Vérifier que l'installateur a bien été généré.
    if not os.path.exists(INSTALLER_OUTPUT):
        print("Erreur : L'installateur n'a pas été trouvé à", INSTALLER_OUTPUT)
        sys.exit(1)

    # Étape 3 : Créer la release GitHub.
    release_info = create_release()

    # Étape 4 : Uploader l'installateur sur la release.
    upload_url = release_info["upload_url"]
    upload_asset(upload_url, INSTALLER_OUTPUT, asset_label="Installateur GDJ")

    print("Processus de création de release terminé avec succès.")


if __name__ == '__main__':
    main()
