import os
import sys
import requests

# Configuration à personnaliser
REPO_OWNER = "3M6PR0"  # Le propriétaire du repository
REPO_NAME = "GDJ_App"  # Le nom de votre repository
TARGET_BRANCH = "main"  # La branche cible pour la release
TAG_NAME = "v1.0.8"  # Le tag de la nouvelle release (doit être unique)
RELEASE_NAME = "Version 1.0.8 - Release automatique"
RELEASE_BODY = "Ceci est une release générée automatiquement par un script."
DRAFT = False
PRERELEASE = False

# Récupération du token depuis les variables d'environnement
GITHUB_TOKEN = os.getenv("GH_TOKEN")
if not GITHUB_TOKEN:
    print("Erreur: Le token GitHub n'est pas défini dans la variable d'environnement GH_TOKEN.")
    sys.exit(1)

API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"


def create_release():
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


if __name__ == '__main__':
    release = create_release()
