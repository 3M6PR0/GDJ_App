# Notes de version

Cette version apporte des fonctionnalités majeures très attendues, notamment l'introduction d'un thème dynamique Clair/Sombre, une page de Préférences complète pour personnaliser l'application et les informations utilisateur, ainsi qu'une nouvelle page Paramètres centralisant la gestion des mises à jour. De nombreuses améliorations visuelles et fonctionnelles accompagnent ces ajouts, comme la mise à jour dynamique des icônes et une meilleure gestion des états.

## ✨ Nouvelles fonctionnalités

*   **Thème Dynamique (Clair/Sombre)** : Possibilité de choisir entre un thème d'interface clair et sombre via les Préférences. Le thème choisi est sauvegardé et appliqué au démarrage.
*   **Page Paramètres** : Ajout d'une nouvelle section "Paramètres" pour la configuration de l'application, incluant une interface de gestion des mises à jour refondue.
*   **Interface de Mise à Jour Améliorée** : La page Paramètres affiche la version actuelle/disponible, une barre de progression pendant le téléchargement, et des boutons contextuels ("Vérifier les mises à jour", "Mettre à jour", "Arrêter").
*   **Page Préférences Complète** : Finalisation de la page Préférences permettant de gérer :
    *   Le profil utilisateur (nom, prénom, téléphone, courriel, signature numérique avec sélection de fichier et aperçu).
    *   Les informations spécifiques à Jacmar (emplacement, département, titre, superviseur, plafond de déplacement) via des listes déroulantes dynamiques.
    *   Les paramètres de l'application (Thème, option de mise à jour automatique, option d'affichage des notes de version).
    *   L'import et l'export des fichiers de préférences (`.json`).
*   **Indicateurs de Modification (Préférences)** : Les champs modifiés dans les préférences affichent un bouton permettant de réinitialiser la valeur initiale.
*   **Barre de Titre Personnalisée** : Remplacement de la barre de titre native par une barre personnalisée (style et fonctionnement ajustés au fil du développement).
*   **Composants d'Interface Réutilisables** : Création des widgets `Frame` (cadre stylisé), `SimpleToggle` (interrupteur on/off), et `SignaturePreviewWidget`.

*   **Système de mise à jour automatique :** L'application vérifie désormais au démarrage si une nouvelle version est disponible sur GitHub. Si c'est le cas, l'utilisateur est invité à lancer la mise à jour.
    *   L'assistant de mise à jour (`update_helper.exe`) gère le téléchargement et l'exécution du nouvel installeur.
    *   L'installeur met à jour l'application principale et ses composants.
    *   L'application redémarre automatiquement dans sa nouvelle version après l'installation.

## 🚀 Améliorations

*   **Mise à Jour Thématique des Icônes** : La plupart des icônes de l'application (barre latérale, liste de documents, cadres, boutons de préférences) changent désormais d'apparence en fonction du thème (Clair/Sombre) sélectionné.
*   **Gestion Centralisée des Icônes (`icon_loader`)** : Utilisation d'un module dédié pour charger les icônes, gérant automatiquement la sélection de la bonne variante (claire/sombre) et le retour à l'icône de base si une variante manque.
*   **Système de Signaux Globaux (`signals`)** : Implémentation d'un système de signaux (ex: `theme_changed_signal`) pour une meilleure communication et un découplage entre les différents composants de l'interface.
*   **Chargement Dynamique des Stylesheets (`stylesheet_loader`)** : Les fichiers QSS utilisent des placeholders de couleur (ex: `{{COLOR_PRIMARY_DARK}}`) qui sont remplacés dynamiquement par les valeurs du thème actif lors du chargement.
*   **Layout Adaptatif (Préférences)** : Les différentes sections (cadres) de la page Préférences s'étirent maintenant pour occuper l'espace disponible lorsque la taille de la fenêtre change.
*   **Modèle de Préférences Structuré (`models/preference.py`)** : Les préférences sont organisées en classes Python imbriquées (`Profile`, `Jacmar`, `Application`) facilitant leur manipulation, sauvegarde et chargement.
*   **Logique Mise à Jour (Page Paramètres)** : Amélioration de la gestion des états (vérification, téléchargement, etc.) et de l'affichage conditionnel des boutons d'action. Logique d'annulation de mise à jour ajoutée.
*   **Style des Boutons (Paramètres)** : Le style des boutons de la page Paramètres a été ajusté pour être cohérent avec le reste de l'application.
*   **Interface Mise à Jour** : Ajout d'espacement (marge) à la barre de progression des mises à jour.
*   **Barre de Titre Personnalisée** : (Logique interne) Gestion de l'état maximisé/restauré pour l'affichage de l'icône correspondante.
*   **Général** : Divers nettoyages de code, refactoring mineurs et améliorations de la gestion des erreurs et du logging.

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

*   Correction du problème où le changement de thème dans les préférences n'était pas appliqué visuellement, n'était pas sauvegardé, et ne mettait pas à jour les icônes.
*   Résolution de multiples erreurs d'importation (`Slot`, `signals`, `logging`, `QPixmap`, etc.) apparues durant le développement.
*   Correction d'erreurs `AttributeError` et `TypeError` liées à l'initialisation de composants (`is_maximized`, `_window_icon_base` dans `CustomTitleBar`), aux connexions de signaux (`_handle_maximize_restore`), et aux appels de méthodes (arguments incorrects pour `icon_loader`).
*   Correction de `NameError` lors de l'utilisation de l'objet `signals`.
*   Correction de la logique de chargement des icônes dans `icon_loader` (ajout du fallback vers l'icône de base, correction des arguments attendus).
*   Correction du chemin utilisé pour charger l'icône du logo de l'application dans la barre de titre (`resources/images` vs `resources/icons`).
*   Correction de l'oubli d'ajout du widget `CustomTitleBar` au layout principal de `WelcomePage`.
*   Correction d'une faute de frappe dans le nom du signal émis par le bouton Agrandir/Restaurer (`maximize_restore_requested`).
*   Assurance de la présence de l'icône "Restaurer" (`round_filter_none.png`) nécessaire à la barre de titre (ajout du fichier nécessaire par l'utilisateur).
*   Correction de la logique d'affichage/masquage des boutons "Réinitialiser" dans la page Préférences.

*   Correction du problème principal où la mise à jour échouait silencieusement ou relançait l'ancienne version.
*   Résolution des erreurs `ModuleNotFoundError` (en particulier pour `win32api`) dans l'assistant de mise à jour compilé.
*   Correction des erreurs liées aux permissions et à l'existence de tags/releases lors de l'interaction avec l'API GitHub.
*   Correction de diverses erreurs de compilation PyInstaller et Inno Setup.

---
*Équipe de développement GDJ* 