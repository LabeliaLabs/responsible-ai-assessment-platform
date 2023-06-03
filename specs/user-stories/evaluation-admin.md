# Gestion des évaluations

## Objectifs de la section

_Work in progress_

## Liste des évaluations

L'administrateur accède à la liste des évaluations.

Cette liste comprend :

- Un numéro d'identification
- L'organisation rattachée à l'évaluation
- Le statut de l'évaluation (En cours ou Terminée)
- La date de création de l'évaluation
- La date de soumissions de l'évaluation (si l'évaluation est terminée)
- La version de l'évaluation
- La note globale reçue par l'organisation (si l'évaluation est terminée)

Par défault, 50 évaluations sont affichées.
Il est possible de naviguer entre les évaluations :

- Voir la page suivante
- Voir la dernière page
- Entrer un numéro de page

Il est possible de cliquer sur l'intitulé des colonnes pour changer le tri.
Par défaut, le tri appliqué est par date de création de l'évaluation, du plus récent au plus ancien.

## Accès à une évaluation

L'administrateur peut cliquer sur une évaluation en cours ou terminé.
Il accède alors aux réponses de l'évaluation et les justifications données.
Si l'évaluation est terminée, il accède aux résultats par section.

## Filtres de recherche

Sur la page de liste des évaluations, l'administrateur peut effectuer une recherche :

- Possibilité de voir uniquement les évaluations en cours ou terminée
- Possibilité de rechercher une organisation
- Possibilité de rechercher un utilisateur
- Possibilité d'appliquer des filtres par :
  - Secteur d'activité
  - Secteur géographique
  - Taille d'entreprises
  - Possibilité de filtrer par date de création de l'utilisateur :
    - Avant une date donnée
    - Après une date donnée
    - Entre deux périodes
  - Possibilité de filtrer par date de création de l'évaluation :
    - Avant une date donnée
    - Après une date donnée
    - Entre deux périodes
  - Possibilité de filtrer par date de soumission de l'évaluation :
    - Avant une date donnée
    - Après une date donnée
    - Entre deux périodes

Si l'utilisateur applique plusieurs filtres, un "ET" est appliqué entre les différents filtres.
Si l'utilisateur sélectionne plusieurs valeurs dans un critère (exemple : sélection de deux secteurs d'activité), un "OU" est appliqué à l'interieur de ce filtre (toutes les organisation de l'un ou de l'autre secteur s'affiche).

## Extraction

Possibilité d'extraire au format CSV la liste sur un clic, avec application des filtres indiqués.

_Work in progress_
