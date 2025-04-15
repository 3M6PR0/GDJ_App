import os
import sys
import subprocess
import requests
import json

# ---------- Configuration ----------
REPO_OWNER = "3M6PR0"  # Propriétaire du repository
REPO_NAME = "GDJ_App"  # Nom de votre repository
TARGET_BRANCH = "main"  # Branche cible pour la release (à partir de laquelle la nouvelle branche sera créée)
TAG_NAME = "v1.0.13"  # Tag de la nouvelle release
BRANCH_NAME = f"pack-{TAG_NAME}"  # Nom de la nouvelle branche (ex: "pack v1.0.2")
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

# Chemin de l'exécutable Inno Setup (à adapter à votre installation)
ISCC_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
# Chemin vers le script Inno Setup
ISS_SCRIPT = os.path.join("installer", "GDJ_Installer.iss")
# Chemin de l'artefact compilé par Inno Setup (sortie du script .iss)
INSTALLER_OUTPUT = os.path.join("installer", "Output", "GDJ_Installer.exe")


# ---------- Fonctions ----------

def compile_gdj():
    """
    Compile GDJ.exe avec PyInstaller en mode onefile, windowed.
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


def git_commit_push_new_branch(commit_message, branch_name):
    """
    Crée une nouvelle branche (basée sur TARGET_BRANCH), y commit et pousse le commit.
    """
    try:
        print(f"Création de la branche '{branch_name}' basée sur {TARGET_BRANCH}...")
        subprocess.run(["git", "checkout", TARGET_BRANCH], check=True)
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
        print(f"Branche '{branch_name}' créée et poussée avec succès.")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de la création ou du push de la branche :", e)
        sys.exit(1)


def update_branch_config_file(branch_name):
    """
    Met à jour (ou crée) le fichier data/branch.txt avec le nom de la branche.
    Ce fichier peut être utilisé par l'installateur pour pointer vers la branche appropriée.
    """
    config_path = os.path.join("data", "branch.txt")
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(branch_name)
        print(f"Le fichier de configuration de branche '{config_path}' a été mis à jour.")
    except Exception as e:
        print("Erreur lors de la mise à jour du fichier branch.txt :", e)
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
    Crée une release sur GitHub via l'API.
    """
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "tag_name": TAG_NAME,
        "target_commitish": BRANCH_NAME,  # On pointe la release vers la nouvelle branche
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

    # Vérifier que GDJ.exe existe dans le dossier dist.
    gdj_path = os.path.join("dist", "GDJ.exe")
    if not os.path.exists(gdj_path):
        print("Erreur : GDJ.exe n'a pas été trouvé dans le dossier 'dist'.")
        sys.exit(1)

    # Étape 2 : Créer une nouvelle branche pour le packaging.
    git_commit_push_new_branch(f"Build release {TAG_NAME} - Mise à jour de GDJ.exe", BRANCH_NAME)

    # Étape 3 : Mettre à jour le fichier de configuration de branche.
    update_branch_config_file(BRANCH_NAME)

    # Étape 4 : Compiler l'installateur via Inno Setup.
    compile_innosetup()

    # Vérifier que l'installateur existe.
    if not os.path.exists(INSTALLER_OUTPUT):
        print("Erreur : L'installateur n'a pas été trouvé à", INSTALLER_OUTPUT)
        sys.exit(1)

    # Étape 5 : Créer la release GitHub, en pointant vers la nouvelle branche.
    release_info = create_release()

    # Étape 6 : Uploader l'installateur sur la release.
    upload_url = release_info["upload_url"]
    upload_asset(upload_url, INSTALLER_OUTPUT, asset_label="Installateur GDJ")

    print("Processus de création de release terminé avec succès.")


if __name__ == '__main__':
    main()
