# Gestion des utilisateurs

# Objectif de cette section

L'objectif est de permettre à un administrateur de gérer les utilisateurs de la plateforme.

## Liste des utilisateurs

L'administrateur accède à la liste des utilisateurs de la plateforme.

Cette liste comprend :
- Un numéro d'identification
- Le prénom de l'utilisateur
- Le nom de l'utilisateur
- Le mail de l'utilisateur
- L'organisation de l'utilisateur si il est rattaché à une organisation
- Le statut de l'utilisateur
- Date de création de l'utilisateur
- Date de dernière connexion de l'utilisateur

Par défault, 50 utilisateurs sont affichés.
Il est possible de naviguer entre les utilisateurs :

- Voir la page suivante
- Voir la dernière page
- Entrer un numéro de page

Il est possible de cliquer sur l'intitulé des colonnes pour changer le tri.
Par défaut, le tri appliqué est par numéro d'identification.

## Action sur un utilisateur

L'administrateur peut cliquer sur un bouton d'action pour un utilisateur.
Lorsque l'utilisateur est actif, il peut :

- Rendre inactif un utilisateur
- Supprimer un utilisateur

Lorsque l'utilisateur est supprimé, il n'est plus présent dans la liste _(et les évaluations sont supprimées ? - a priori non car liées à une organisation)_.

Lorsque l'utilisateur est inactif, l'adminstrateur peut :

- Rendre actif un utilisateur
- Supprimer l'utilisater.

## Différence entre inactif / suppression

Un utilisateur inactif conserve ses informations sur la plateforme. Il ne peut juste pas se connecter à la plateforme. Cela peut servir quand un utilisateur bloque son compte avec un mauvais password.

Un utilisateur supprimé n'est plus présent sur la plateforme.

## Accès à une organisation

L'administrateur peut, dans la liste, avoir accès à l'organisation de l'utilisateur en cliquant dessus. Cela le mène dans la liste des organisations avec un filtre appliqué à l'organisation cliquée.

## Filtres de recherche

Sur la page de liste des utilisateurs, l'administrateur peut effectuer une recherche :

- Possibilité de voir uniquement les utilisateurs actifs ou inactifs
- Possibilité de rechercher une organisation
- Possibilité de rechercher un utilisateur par son prénom
- Possibilité de rechercher un utilisateur par son nom
- Possibilité de rechercher un utilisateur par son email
- Possibilité de filtrer par date de création de l'utilisateur :
  - Avant une date donnée
  - Après une date donnée
  - Entre deux périodes

Si l'utilisateur applique plusieurs filtres, un "ET" est appliqué entre les différents filtres.
Si l'utilisateur sélectionne plusieurs valeurs dans un critère (exemple : sélection de deux secteurs d'activité), un "OU" est appliqué à l'interieur de ce filtre (toutes les organisation de l'un ou de l'autre secteur s'affiche).

## Extraction

Possibilité d'extraire au format CSV la liste sur un clic, avec application des filtres indiqués.

_Work in progress_
