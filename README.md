# GDJ - Générateur de Document Jacmar

<!-- Optionnel: Ajouter un logo/bannière ici -->
<img src="resources/images/logo-jacmar-gdj.png" alt="Logo GDJ" width="700">

[![Version](https://img.shields.io/badge/Version-v0.02-blue.svg)]() 
<!-- Optionnel: Ajouter d'autres badges (Build, Licence, etc.) -->
<!-- [![Build Status](URL_Badge_Build)](URL_Lien_Build) -->
<!-- [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) -->

## Introduction

**GDJ (Générateur de Document Jacmar)** est une application de bureau développée pour rationaliser et fiabiliser la création de documents administratifs standardisés utilisés au sein de Jacmar. L'objectif est de fournir un outil centralisé et efficace pour minimiser les erreurs de saisie manuelle et accélérer les flux de travail.

L'application est actuellement en développement actif (**Version 0.02**).

## État Actuel & Fonctionnalités Implémentées

Cette version se concentre sur la mise en place de l'architecture générale et des fonctionnalités clés suivantes :

*   **Interface Utilisateur (PyQt5)**: Une interface graphique principale avec une barre de navigation latérale permettant d'accéder aux différentes sections (Accueil, Documents, Paramètres, etc.).
*   **Gestion des Préférences Utilisateur**:
    *   Interface dédiée (`PreferencesPage`) pour gérer les informations du profil (Nom, Prénom, Téléphone, Email) et les paramètres de l'application.
    *   Prévisualisation de la signature email.
    *   Sélection du thème de l'application (Clair/Sombre) avec application dynamique.
    *   Persistance des préférences dans un fichier `data/preference.json`.
*   **Gestion des Thèmes (Clair/Sombre)**:
    *   Chargement dynamique des feuilles de style QSS en fonction du thème choisi.
    *   Mise à jour automatique des icônes et de certains éléments d'interface lors du changement de thème.
*   **Système de Mise à Jour**:
    *   Vérification des mises à jour via une source définie (détails à confirmer).
    *   Interface pour afficher l'état de la mise à jour et les notes de version.
    *   Possibilité d'annuler le processus de mise à jour.
*   **Section "Documents"**:
    *   **Navigation**: Un conteneur (`DocumentsPage`) utilise un `QStackedWidget` pour basculer entre les différentes vues de la section.
    *   **Liste des Documents Récents (`DocumentsRecentListPage`)**:
        *   Affiche les fichiers récemment ouverts ou créés.
        *   Barre d'outils avec recherche (`QLineEdit`), bouton "Nouveau" et "Ouvrir".
        *   Liste (`QListWidget`) d'éléments personnalisés (`ProjectListItemWidget`) affichant icône, nom, chemin, et un menu d'options contextuel (Ouvrir, Ouvrir dossier, Copier chemin, Retirer).
    *   **Création de Nouveau Document (`DocumentsTypeSelectionPage`)**:
        *   Accessible via le bouton "Nouveau".
        *   Permet de choisir le *type* de document via une `QComboBox`.
        *   Affiche dynamiquement un formulaire (`QFormLayout`) avec les champs requis (`QLineEdit`, `QComboBox`) pour le type sélectionné.
        *   Inclut un champ "date" spécial (mois/année) et des boutons de réinitialisation par champ.
        *   Boutons "Annuler" et "Créer" pour gérer le processus.

## Fonctionnalités Prévues ou Partiellement Implémentées

*   **Affichage/Édition de Document (`documents_detail_page.py`)**: **Non implémenté.** La vue permettant d'afficher et de modifier le contenu d'un document spécifique après sa création ou son ouverture depuis la liste des récents est manquante. C'est une étape cruciale pour la fonctionnalité complète de la section "Documents".
*   **Gestion des Fichiers `.rdj`, `.dec`, `.ecj`**: Bien que mentionnés dans des versions précédentes du README ou dans le code, la logique métier spécifique pour charger, manipuler, sauvegarder et utiliser ces formats de fichiers (Rapport de Dépense, Dépenses Écriture Comptable) nécessite une implémentation ou une finalisation détaillée dans les contrôleurs et potentiellement une vue de détail dédiée.
*   **Export (Excel, PDF, etc.)**: Fonctionnalités d'export mentionnées mais nécessitent implémentation.
*   **Logique Métier Complète**: La logique associée à certaines actions (ex: calculs spécifiques aux `.rdj`, validation des données, interaction avec Fidelio) est partiellement présente ou à implémenter.

## Stack Technique

*   **Langage**: Python 3.x
*   **Interface Graphique (GUI)**: PyQt5
*   **Stockage des Préférences**: JSON (`data/preference.json`)
*   **Format des Documents (Prévu)**: JSON encapsulé dans des archives zip (`.rdj`, `.ecj`, etc.)
*   **Manipulation PDF (Miniatures)**: PyMuPDF (fitz) - utilisé pour la prévisualisation des factures dans les versions antérieures ou prévues.

## Installation

Assurez-vous d'avoir Python 3 installé sur votre système.

1.  **Cloner le dépôt** (si applicable) :
    ```bash
    # git clone URL_DU_DEPOT # Si le code est sur un dépôt Git
    # cd GDJ
    ```
2.  **Créer un environnement virtuel** (fortement recommandé) :
    ```bash
    python -m venv venv
    # Sur Windows (cmd/powershell):
    venv\Scripts\activate
    # Sur Linux/macOS:
    # source venv/bin/activate
    ```
3.  **Installer les dépendances** :
    *(Assurez-vous d'avoir un fichier `requirements.txt` à jour)*
    ```bash
    pip install -r requirements.txt
    ```
    Les dépendances principales incluent `PyQt5`, `requests` (pour les mises à jour), et potentiellement `PyMuPDF` si la manipulation PDF est active.

## Utilisation

1.  Activez l'environnement virtuel (si créé).
2.  Lancez l'application :
    ```bash
    python main.py
    ```
3.  **Configuration Initiale**: Allez dans la section "Paramètres" (ou équivalent) pour configurer votre profil et choisir votre thème préféré.
4.  **Section Documents**:
    *   Naviguez vers la section "Documents".
    *   Utilisez "Nouveau" pour créer un document en sélectionnant son type et en remplissant les champs.
    *   La liste des récents se peuplera au fur et à mesure. (La logique de chargement/sauvegarde des documents réels reste à finaliser).

## Feuille de Route (Roadmap) - Suggestions

*   **Priorité Haute**: Implémenter la vue de détail des documents (`documents_detail_page.py` ou similaire) pour permettre l'affichage et la modification du contenu des documents créés/ouverts.
*   Finaliser la logique métier pour les types de documents cibles (`.rdj`, `.ecj`).
*   Intégrer la sauvegarde et le chargement effectifs des fichiers documents.
*   Améliorer la robustesse (validation des entrées, gestion des erreurs).
*   Ajouter des tests unitaires et d'intégration.
*   Compléter les fonctionnalités prévues (exports, recherche avancée, etc.).

## Contribuer

Ce projet est développé pour un usage interne à Jacmar. Pour toute suggestion, rapport de bug ou demande de fonctionnalité, veuillez contacter Etienne Manseau-Godin.

## Licence et Conditions d'Utilisation

Ce logiciel est la propriété de Jacmar et est destiné à un **usage interne exclusif**. Les détails sont spécifiés dans le fichier `NOTICE.txt`.

---

*GDJ - Générateur de Document Jacmar* 