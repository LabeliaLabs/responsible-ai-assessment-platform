# Gestion des organisations

# Objectif de cette section

L'objectif est de permettre à un administrateur de gérer les organisations de la plateforme.

## Liste des organisations

L'administrateur accède à la liste des organisations de la plateforme.

Cette liste comprend :
- Un numéro d'identification
- Le nom de l'organisation
- Le prénom / nom de l'utilisateur qui a créé l'organisation
- Le mail de l'utilisateur qui a créé l'organisation
- La liste des utilisateurs rattachés à son organisation
- La date de création de l'organisation
- Les évaluations liées à l'organisation
- Le secteur d'activité
- La taille de l'organisation
- La zone géographique

Par défault, 50 organisations sont affichérs.
Il est possible de naviguer entre les organisations :

- Voir la page suivante
- Voir la dernière page
- Entrer un numéro de page

Il est possible de cliquer sur l'intitulé des colonnes pour changer le tri.
Par défaut, le tri appliqué est par numéro d'identification.

## Action sur une organisation

L'administrateur peut cliquer sur un bouton d'action pour une organisation pour la supprimer
Lorsque l'organisation est supprimée, les évaluations rattachées à l'organisation sont supprimées.

## Accès aux utilisateurs

L'administrateur peut, dans la liste, avoir accès aux utilisateurs de l'organisation en cliquant dessus. Cela le mène dans la liste des utilisateurs avec un filtre appliqué sur l'organisation.

## Filtres de recherche

Sur la page de liste des organisation, l'administrateur peut effectuer une recherche :

- Possibilité de rechercher une organisation
- Possibilité de rechercher par utilisateur (prénom, nom, mail)
- Filtre par secteur géographique
- Filtre par secteur d'activité
- Filtre par taille d'organisation
- Possibilité de filtrer par date de création de l'organisation :
  - Avant une date donnée
  - Après une date donnée
  - Entre deux périodes

Si l'utilisateur applique plusieurs filtres, un "ET" est appliqué entre les différents filtres.
Si l'utilisateur sélectionne plusieurs valeurs dans un critère (exemple : sélection de deux secteurs d'activité), un "OU" est appliqué à l'interieur de ce filtre (toutes les organisation de l'un ou de l'autre secteur s'affiche).

## Extraction

Possibilité d'extraire au format CSV la liste sur un clic, avec application des filtres indiqués.

_Work in progress_
