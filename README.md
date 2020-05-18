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
- La réflexion sur le(s) [modèle(s) de scoring](https://docs.google.com/spreadsheets/d/1QhvOTsPpNhNcLlt7z_-vL3EBCRAxhjrhy_ybYKcDuFM/edit?usp=sharing)

## Conventions et choix techniques

Pour assurer une cohérence et une homogénéité entre les contributeurs à ce repo, il est important de suivre les pratiques décrites dans les sections qui suivent.

### Commit messages

On définit rarement des conventions pour les messages de commits, alors que cela apporte une clarté et une facilité de lecture qui fait une vraie différence. Pour s'en rendre compte il faut regarder l'historique de `master` dans un projet où les 4 dernières PR mergées proviennent de 4 contributeurs différents... ça n'est pas facile de s'y retrouver !

Une approche qui est devenue une référence au fil des ans est celle décrite dans l'article [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/). Voici les principes-clés à avoir en tête :

- Par souci d'homogénéité et pour préserver les futures collaborations possibles, les commits messages doivent être **en anglais**
- Ils démarrent par une majuscule, un verbe à l'impératif, et finissent sans point. Exemple :
    > `Populate README with context and quick links to key resources`
- Ils ne doivent pas être trop longs (72 caractères est une bonne limite : les commits messages plus longs sont tronqués sur GitHub). Si besoin, utiliser la possibilité d'ajouter un _body_ en plus du _subject_ du commit message.

### Branching model

Le modèle de branches dit "[git-flow](https://nvie.com/posts/a-successful-git-branching-model/)" est devenu une référence au cours des années écoulées. On choisit donc d'en appliquer les principes-clés :

- `develop` est la branche par défaut. Toutes les MR doivent être créées par rapport à elle. C'est une branche protégée sur laquelle on n'est pas censé commiter et pousser directement
- `master` est l'état de ce qui est en production à l'instant t, alors que `develop` est l'état de ce qui est testé et prêt à être déployé en pré-production puis en production
- pour déployer en production, une fois tous les tests réalisés y compris sur la pré-production, on crée une MR de `develop` sur `master` décrivant les changements principaux (note : lorsque l'historique de commits est propre et clair cela aide grandement !). Une fois la fusion réalisée, on pousse un tag de version sur `master` selon les principes du versionnage sémantique

### Conteneurisation

Pour faciliter le déploiement sur différents environnements (dev, pre-prod, prod) et donc assurer la portabilité de l'app, on choisit de travailler sur une infra conteneurisée avec Docker :

- [Tutoriel très complet](https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/)
- [Tutoriel léger](https://docs.docker.com/compose/django/) (de la doc Docker)

### Infrastructures, tests et déploiement

#### Infrastructures

- Compte et ressources chez OVH : pre-prod et prod isolées l'une de l'autre
- Par environnement :
  - une instance s1-4 (1 vCore, 4Go RAM, 20Go SSD)
  - le backup "Storage réplica x3"
  - l'anti DdoS (fourni par défaut)

#### Build et tests

GitLab-CI pour :

1. Lancer à chaque commit des tests automatiques :
   - Unit-tests
   - Coding standards

1. Builder notre image Docker :
   - Reverse proxy et serveur web
   - App
   - DB
   - Let's Encrypt

1. Pousser nos images sur les infras et les instancier

### Prototypage

Pour le prototypage, nous utiliserons l'outil [moqups](https://moqups.com/).

### Emailings

Pour les emailings transactionnels on choisit le [module Mandrill de Mailchimp](https://mailchimp.com/fr/help/mailchimp-vs-mandrill/). On élaborera et designera les templates via l'interface Mandrill directement.

### Framework d'application

On retient Django en tant que framework de référence pour les applications en Python, langage le plus commun dans l'équipe et utilisé dans l'écosystème.
Django est très complet et on utilisera en particulier

- son ORM interne
- son système d'authentification et autorisations
- le backoffice automatique

### Framework de frontend

On retient Bootstrap 4.4.x pour ses 140k étoiles sur GitHub. On regardera dans les [thèmes officiels](https://themes.getbootstrap.com/) s'il y en a un qui se prête bien à la plateforme d'évaluation et de certification.

On réfléchira à sélectionner quelques marqueurs "low-tech" en s'inspirant par exemple de [cet article](https://graphism.fr/quel-avenir-pour-les-sites-low-tech/).

### Base de données

On retient Postgresql : open source, battle-testé...

### Serveur(s) web

Comme le suggère le [tutoriel ci-dessus](https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/) sur Django x Docker, il semble être recommandé d'utiliser :

- gunicorn comme serveur web principal
- nginx comme reverse proxy pour distribuer sur les assets statiques et le serveur web principal

### Domaines et certificats SSL

_To do :_

- _gestion des zones DNS via Gandi ou via OVH ?_
- _certificats SSL via Gandi ou via Let's Encrypt ?_
