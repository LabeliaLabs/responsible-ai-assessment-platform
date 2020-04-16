# Plateforme d'assessment data science responsable et de confiance (DSRC)

## Contexte et ambition

Dans le prolongement des travaux participatifs démarrés en 2019 sur la définition de la data science responsable et de confiance qui peuvent être consultés sur le [repo dédié](https://github.com/SubstraFoundation/referentiel-ds-responsable-confiance), Substra Foundation a orienté l'initiative vers une évaluation de maturité, un _assessment_, à destination des organisations qui ont une activité data science.

La suite du projet recouvre :

- la conception et le développement d'une **plateforme d'assessment** (ce repo)
- l'élaboration d'une méthode et d'un service de **certification**
- la création d'un **réseau de partenaires experts**

## Accès rapide aux ressources-clés

Voici les liens permettant un accès rapide aux ressources-clés du projet :

- Le [board Asana](https://app.asana.com/0/1159203738319657/1159203738319657) récapitulatif du projet
- Le [story mapping](https://www.featuremap.co/m/ddC0Rj/plateforme-dsrc) de la plateforme d'assessment
- Le [dossier de candidature Innov'up](https://docs.google.com/document/d/1JLyWI4lTz5Jo0UCx5WLj_7bB5Eqo-q-iOWZOuyrv5-U/edit?usp=sharing)
- L'[assessment DSRC](https://github.com/SubstraFoundation/referentiel-evaluation-dsrc/blob/master/referentiel_evaluation.md#restructuration-en-un-r%C3%A9f%C3%A9rentiel-d%C3%A9valuation-de-la-maturit%C3%A9-dune-organisation) sur le repo public
- Le [parser "jsonize-dsrc-assessment"](https://framagit.org/substra-foundation/jsonize-dsrc-assessment) pour convertir l'assessment de son format texte à un objet JSON
- Le [modèle de scoring](https://docs.google.com/spreadsheets/d/1QhvOTsPpNhNcLlt7z_-vL3EBCRAxhjrhy_ybYKcDuFM/edit?usp=sharing)

## Conventions et choix techniques

Pour assurer une cohérence et une homogénéité entre les contributeurs à ce repo, il est important de suivre les pratiques décrites dans les sections qui suivent.

### Commit messages

On définit rarement des conventions pour les messages de commits, alors que cela apporte une clarté et une facilité de lecture qui fait une vraie différence. Pour s'en rendre compte il faut regarder l'historique de `master` dans un projet où les 4 dernières PR mergées proviennent de 4 contributeurs différents... ça n'est pas facile de s'y retrouver !

Une approche qui est devenue une référence au fil des ans est celle décrite dans cet article [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/). Voici les principes-clés à avoir en tête :

- Par souci d'homogénéité et pour préserver les futures collaborations possibles, les commits messages doivent être **en anglais**
- Ils démarrent par une majuscule, un verbe à l'impératif, et finissent sans point. Exemple :
    > `Populate README with context and quick links to key resources`
- Ils ne doivent pas être trop longs (72 caractères est une bonne limite : les commits messages plus longs sont tronqués sur Github). Si besoin, utiliser la possibilité d'ajouter un _body_ en plus du _subject_ du commit message.

### Branching model

Le modèle de branches dit "[git-flow](https://nvie.com/posts/a-successful-git-branching-model/)" est devenu une référence au cours des années écoulées. On choisit donc d'en appliquer les principes-clés :

- `develop` est la branche par défaut. Toutes les MR doivent être créées par rapport à elle. C'est une branche protégée sur laquelle on n'est pas censé commiter et pousser directement
- `master` est l'état de ce qui est en production à l'instant t, alors que `develop` est l'état de ce qui est testé et prêt à être déployé en pré-production puis en production
- pour déployer en production, une fois tous les tests réalisés y compris sur la pré-production, on crée une MR de `develop` sur `master` décrivant les changements principaux (note : lorsque l'historique de commits est propre et clair cela aide grandement !). Une fois la fusion réalisée, on pousse un tag de version sur `master` selon les principes du versionnage sémantique
