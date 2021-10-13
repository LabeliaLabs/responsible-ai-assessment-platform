# Approche de notation (_scoring_) des évaluations

Liens rapides :

- La réflexion sur le(s) [modèle(s) de scoring](https://docs.google.com/spreadsheets/d/1QhvOTsPpNhNcLlt7z_-vL3EBCRAxhjrhy_ybYKcDuFM/edit?usp=sharing)
- [Issue sur le scoring](https://github.com/LabeliaLabs/referentiel-evaluation-dsrc/issues/38) sur le repo public

## Positionnement du problème

Pour donner corps à une évaluation il faut lui associer une notation. Cela permet de synthétiser une note globale (pour l'ensemble de l'évaluation mais aussi pour chaque section). Cette note globale est très utile par exemple pour :

- mesurer une évolution dans le temps et voir les progrès d'une organisation
- positionner une organisation par rapport à la moyenne des autres
- fixer un ou plusieurs seuils qui peuvent servir à déterminer une note minimale pour prétendre à être certifié
- ...

Cela n'est pas sans difficulté, et on peut énoncer les grands principes suivants :

1. l'approche de notation doit être **compréhensible**. Elle peut être relativement élaborée, mais ne doit pas dépasser un certain degré de sophistication au-delà duquel elle deviendrait incompréhensible pour le public concerné
1. l'approche de notation doit **permettre de comparer les évaluations de différentes organisations**. Il est important que les notes globales de différentes organisations puissent être lues et comparées sur une même échelle. Elle doit donc tenir compte des cas des situations et perspectives différentes pour certaines organisations (e.g. les cas où une organisation n'est pas concerné par un sujet de l'évaluation)
1. l'approche de notation doit **permettre de comparer les évaluations d'une organisation sur différentes versions du référentiel d'évaluation**

## Mécanismes à mettre en oeuvre

Les mécanismes suivants semblent pertinents pour répondre aux problématiques mentionnées :

1. Pour chaque élément d'évaluation **chaque réponse apporte un certain nombre de points**, plus ou moins élevé selon le niveau de maturité que la réponse traduit pour l'élément d'évaluation. Les points s'additionnent

1. Les éléments d'évaluation et/ou les sections se voient affecter une **pondération d'importance**, c'est-à-dire des poids multiplicateurs qui permettent de donner une plus ou moins grande importance à certains éléments d'évaluation et/ou sections

1. La pondération d'importance est calibrée **pour que la note globale maximale soit toujours identique** (quel que soit le nombre d'éléments d'évaluation, qui évolue au fil des versions du référentiel d'évaluation). Par exemple 100 ou 200 points

1. La notation des éléments d'évaluation où les organisations peuvent ne pas être concernées est traitée de la manière suivante :

   1. **la moitié des points de l'élément d'évaluation est attribuée automatiquement** à l'organisation non concernée. Cela traduit le fait qu'elle n'est pas soumise au risque sous-jacent

   1. l'autre moitié des points **ne** lui est **pas** attribuée automatiquement, afin qu'elle ne se voit pas attribuer automatiquement un score d'office trop élevé sans avoir à faire ses preuves

   1. pour que la note globale de l'organisation soit comparable aux notes des autres organisations et donc pour assurer le principe de comparabilité, **cette seconde moitié des points est redistribuée sur l'ensemble des autres éléments d'évaluation par lesquels l'organisation est concernée**. Les points de ceux-ci sont donc "dilatés" d'autant. Cela est effectué en pratique par une **pondération d'équilibre** (qui vient en combinaison de la pondération d'importance)

1. On peut résumer ces mécanismes avec les formules suivantes :

   Notations :  

   - points(EdEc) : points possibles pour les **E**léments **d**'**E**valuation par lequel l'organisation est **c**oncernée
   - points_auto(EdEnc) : points automatiquement attribués pour les **E**léments **d**'**E**valuation par lesquels l'organisation **n**'est pas **c**oncernée
   - pond_eq : **pond**ération d'**éq**uilibre
   - pond_imp : **pond**ération d'**imp**ortance

   Formules :

   - points_auto(EdEnc) = 1/2 x (points(EdEc) x pond_imp)
   - note globale max = (pond_eq x points(EdEc) x pond_imp) + points_auto(EdEnc)

1. Qu'est-ce qui défini donc une grille de notation ?

   - un nombre de points pour chaque élément de réponse à un élément d'évaluation
   - une pondération d'importance comportant des poids pour chaque élément d'évaluation et section thématique
   - _note : la pondération d'équilibre peut être calculée simplement à partir du reste_

## Pour démarrer vs. à la cible

À la cible on peut imaginer s'inspirer du fonctionnement du _Business Impact Assessment_ de B-Corp et appliquer des grilles de notation comportant des pondérations d'importance différentes selon un certain nombre de critères (géographies, typologies d'organisation...).

Dans un premier temps cela semble trop sophistiqué et on pourra se contenter d'une grille de notation. Cependant celle-ci pourra être amenée à évoluer :

- au fil des retours d'expériences
- au fil de l'évolution du référentiel d'évaluation (nouveau éléments d'évaluation etc.)

Il est donc crucial de savoir faire coexister dans la plateforme plusieurs versions de la grille de notation.

## Coexistence de plusieurs versions de la grille de notation

- Lorsque qu'une évaluation est initiée (vierge ou par migration), la grille de notation actuellement en vigueur est référencée
- Par la suite, si une nouvelle version de la grille de notation est intégrée, les évaluations déjà initiées en sont donc pas modifiées ni impactées
- Pour chaque évaluation, on garde en mémoire le numéro de version du référentiel d'évaluation lui correspondant, et le numéro de version de la grille de notation lui correspondant