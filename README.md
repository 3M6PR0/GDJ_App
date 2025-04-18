# GDJ - Générateur de Document Jacmar

<!-- Optionnel: Ajouter un logo/bannière ici -->
[![Logo GDJ](resources/images/logo-gdj.png)]()

[![Version](https://img.shields.io/badge/Version-v0.02-blue.svg)]() 
<!-- Optionnel: Ajouter d'autres badges (Build, Licence, etc.) -->
<!-- [![Build Status](URL_Badge_Build)](URL_Lien_Build) -->
<!-- [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) -->

## Introduction

**GDJ (Générateur de Document Jacmar)** est une application de bureau conçue pour rationaliser et automatiser la création de divers documents standardisés utilisés au sein de Jacmar. L'objectif principal est de fournir un outil centralisé, efficace et convivial pour réduire les erreurs manuelles et accélérer les flux de travail administratifs.

Cette version initiale (v0.01) se concentre sur la génération de deux types de documents essentiels :

1.  **Rapports de Dépense (.rdj)**
2.  **Dépenses pour Écritures Comptables (.dec)**

Le projet est conçu avec une architecture modulaire pour faciliter l'ajout futur de nouveaux types de documents Jacmar.

## Fonctionnalités Clés (Mises à jour)

*   **Génération de Documents Standardisés**: Crée des fichiers `.rdj` (Rapport de Dépense) et `.ecj` (Écriture Comptable) avec une structure de données JSON cohérente.
*   **Interface Graphique Intuitive**: Utilise PyQt5 pour une expérience utilisateur claire.
*   **Gestion des Rapports de Dépense (.rdj)**: 
    *   Saisie détaillée des déplacements (kilométrage, coût), repas (taxes, pourboire, refacturation) et dépenses diverses.
    *   Gestion des profils utilisateurs pour pré-remplir les informations.
    *   Association de factures (images, PDF) aux dépenses et repas, avec prévisualisation.
    *   Calcul automatique des totaux remboursables avec gestion du plafond de déplacement.
    *   Vue Résumé/Remboursement détaillée.
*   **Gestion des Écritures Comptables (.ecj)**: 
    *   Interface dédiée pour associer des Rapports de Dépense (`.rdj`) existants.
    *   Extraction et affichage des informations pertinentes des RDJ associés :
        *   **Rapport de dépense**: Liste des RDJ avec détails profil (Nom, Emplacement, Département, Cap modifiable).
        *   **Carte de crédit**: Tableau récapitulatif des transactions (import à implémenter).
        *   **Taxes**: Récapitulatif des taxes par type et par RDJ (avec gestion du plafond KM).
        *   **Fidelio**: Agrégation des montants par code GL pour une vue comptable.
        *   **Factures**: Affichage centralisé de toutes les factures issues des RDJ associés, avec options de téléchargement individuel (incluant nom personne) et global (sous-dossiers par personne).
    *   Fonctionnalités d'export Excel pour plusieurs onglets (Carte de Crédit, Taxes, Fidelio).
*   **Gestionnaire de Documents**: 
    *   Panneau d'accueil listant les documents récents.
    *   Création, chargement, et sauvegarde des documents `.rdj` et `.ecj`.
    *   Navigation facile entre les documents ouverts.
*   **Persistance des Données**: Sauvegarde dans des fichiers JSON structurés et `.rdj`/`.ecj` (archives zip).

## Aperçu

<!-- Ajouter des captures d'écran de l'interface ici pour illustrer -->
<!-- 
![Capture d'écran Accueil](path/to/screenshot_home.png)
![Capture d'écran Onglet Dépenses](path/to/screenshot_depenses.png)
![Capture d'écran Onglet Factures](path/to/screenshot_factures.png) 
-->

## Stack Technique

*   **Langage**: Python 3.x
*   **Interface Graphique (GUI)**: PyQt5
*   **Stockage des Données**: JSON
*   **Manipulation PDF (pour miniatures)**: PyMuPDF (fitz)

## Installation

Assurez-vous d'avoir Python 3 installé sur votre système.

1.  **Cloner le dépôt** (si applicable) :
    ```bash
    git clone URL_DU_DEPOT
    cd GDJ 
    ```
2.  **Créer un environnement virtuel** (recommandé) :
    ```bash
    python -m venv venv
    # Sur Linux/macOS:
    source venv/bin/activate
    # Sur Windows (cmd/powershell):
    venv\Scripts\activate
    ```
3.  **Installer les dépendances** :
    *(Assurez-vous d'avoir un fichier `requirements.txt` à jour)*
    ```bash
    pip install -r requirements.txt 
    ```
    Les dépendances principales incluent `PyQt5` et `PyMuPDF`.

## Utilisation

1.  Lancez l'application en exécutant le script principal (probablement `main.py`) :
    ```bash
    python main.py 
    ```
2.  **Configuration Initiale**: Si c'est la première utilisation, configurez votre profil via l'onglet ou la section appropriée.
3.  **Créer ou Charger**: Utilisez les boutons sur la page d'accueil pour créer un nouveau document (`.rdj` ou `.dec`) ou charger un document existant (`.rdj` ou `.dec`).
4.  **Saisie des Données**: Naviguez entre les différents onglets (Déplacement, Repas, Dépense, Facture, etc. pour les `.rdj` ; interface spécifique pour les `.dec`) pour entrer les informations requises.
5.  **Sauvegarde**: Les données sont généralement sauvegardées automatiquement lors des modifications ou à la fermeture (vérifier le comportement exact).
6.  **Accès Rapide**: Les documents ouverts ou créés récemment apparaîtront dans la barre latérale et/ou la liste des documents récents sur la page d'accueil.

## État Actuel

*   **Version**: 0.01 (Alpha/Beta)
*   **Fonctionnalités Implémentées**: Génération et gestion de base des documents `.rdj` (Rapport de Dépense) et `.dec` (Dépenses Écriture Comptable).
*   L'application est en cours de développement actif. Des bugs peuvent être présents et des fonctionnalités sont sujettes à évolution.

## Feuille de Route (Roadmap)

Les développements futurs envisagés incluent :

*   ✅ **Support pour de Nouveaux Types de Documents Jacmar**: Intégration progressive d'autres modèles de documents selon les besoins.
*   **Amélioration UI/UX**: Raffinement de l'interface utilisateur, optimisation des workflows.
*   **Fonctionnalités Avancées**: 
    *   Options d'export (PDF, CSV ?).
    *   Recherche et filtrage plus poussés dans les listes.
    *   Validation des données plus robuste.
*   **Intégrations**: Potentielle intégration avec d'autres systèmes ou bases de données Jacmar (si pertinent).
*   **Tests et Fiabilisation**: Ajout de tests unitaires et amélioration de la robustesse générale.

## Contribuer

Ce projet est actuellement développé pour un usage interne à Jacmar. Pour toute suggestion, rapport de bug ou demande de fonctionnalité, veuillez contacter Etienne Manseau-Godin.

<!-- Ou, si ouvert aux contributions externes :
Les contributions sont les bienvenues ! Veuillez lire le fichier CONTRIBUTING.md (à créer) pour plus de détails sur le processus de contribution et les normes de codage. -->

## Licence et Conditions d'Utilisation

Ce logiciel est la propriété de Jacmar et est destiné à un **usage interne exclusif**.

Les conditions d'utilisation, incluant l'avis de copyright et les limitations de responsabilité, sont détaillées dans le fichier `NOTICE.txt` à la racine du projet.

---

*Générateur de Document Jacmar (GDJ) - Simplifions la paperasse.* 