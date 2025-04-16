Cette version marque une étape importante avec l'introduction d'un système de mise à jour entièrement fonctionnel et plusieurs améliorations du processus de build et de déploiement.

## ✨ Nouvelles fonctionnalités

*   **Affichage des notes de version :** L'application intègre désormais un système complet pour afficher les notes de version.
    *   Un fichier `RELEASE_NOTES.md` centralise le contenu.
    *   Les notes sont montrées automatiquement après une mise à jour.
    *   Une option "Notes de version" est disponible dans le menu "Aide".
    *   Une boîte de dialogue dédiée affiche les notes (format Markdown).

## 🚀 Améliorations

*   **Processus de build et déploiement :**
    *   Le script `create_release.py` utilise `RELEASE_NOTES.md` pour la description de la release GitHub (ajoute titre/version).
    *   L'installeur Inno Setup (`GDJ_Installer.iss`) inclut le fichier `RELEASE_NOTES.md`.
*   **Intégration :**
    *   L'interface graphique (`ui/main_window.py`) contient l'action "Notes de version".
    *   Le contrôleur (`controllers/main_controller.py`) gère la logique d'affichage (post-mise à jour et via le menu).

## 🐛 Corrections de bugs

*   Correction du titre qui apparaissait en double dans la boîte de dialogue des notes de version.

---
*Équipe de développement GDJ* 