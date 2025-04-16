# Notes de version

Cette version marque une étape importante avec l'introduction d'un système de mise à jour entièrement fonctionnel et plusieurs améliorations du processus de build et de déploiement.

## ✨ Nouvelles fonctionnalités

*   **Système de mise à jour automatique :** L'application vérifie désormais au démarrage si une nouvelle version est disponible sur GitHub. Si c'est le cas, l'utilisateur est invité à lancer la mise à jour.
    *   L'assistant de mise à jour (`update_helper.exe`) gère le téléchargement et l'exécution du nouvel installeur.
    *   L'installeur met à jour l'application principale et ses composants.
    *   L'application redémarre automatiquement dans sa nouvelle version après l'installation.

## 🚀 Améliorations

*   **Processus de création de release (`create_release.py`) :**
    *   Intégration de la compilation de `update_helper.exe`.
    *   Gestion robuste des dépendances complexes (`pywin32`) pour `update_helper.exe` via modification du fichier `.spec` de PyInstaller.
    *   Compilation de `update_helper.exe` en mode "one-folder" pour une meilleure compatibilité.
    *   Lecture des notes de version depuis ce fichier (`RELEASE_NOTES.md`) pour la description sur GitHub.
    *   Amélioration de la gestion des chemins et du nettoyage post-build.
*   **Installeur Inno Setup (`GDJ_Installer.iss`) :**
    *   Inclusion directe de `GDJ.exe` et du dossier `updater` (contenant `update_helper.exe` et ses dépendances) pour une installation autonome.
    *   Configuration pour lancer l'application principale après l'installation.
    *   Corrections de diverses syntaxes et configurations Inno Setup.
*   **Vérificateur de mise à jour (`updater/update_checker.py`) :**
    *   Amélioration de la gestion des erreurs avec affichage de messages clairs à l'utilisateur en cas d'échec (ex: assistant introuvable).
    *   Utilisation de `subprocess.Popen` pour lancer l'assistant sans bloquer l'application principale, permettant sa fermeture.

## 🐛 Corrections de bugs

*   Correction du problème principal où la mise à jour échouait silencieusement ou relançait l'ancienne version.
*   Résolution des erreurs `ModuleNotFoundError` (en particulier pour `win32api`) dans l'assistant de mise à jour compilé.
*   Correction des erreurs liées aux permissions et à l'existence de tags/releases lors de l'interaction avec l'API GitHub.
*   Correction de diverses erreurs de compilation PyInstaller et Inno Setup.

---
*Équipe de développement GDJ* 