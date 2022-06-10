# Readme 

## Installation

- Clone the project:

  ```console
  git clone git@framagit.org:labelia-labs/pf-assessment-dsrc.git
  ```

- Create `.env.dev` from `env_dev_template`:

  ```console
  cp env_dev_template .env.dev
  ```
>>>>>>> README.md

- Replace variables in the .env.dev file

- Build Docker image and start it:

  ```console
  docker-compose up --build
  ```

- Migrations

  ```
  docker-compose exec questionnaire-grpc ./manage.py migrate
  ```

## Contexte et ambition

Dans le prolongement des travaux participatifs démarrés en 2019 sur la définition de la data science responsable et de confiance qui peuvent être consultés sur le [repo dédié](https://github.com/LabeliaLabs/referentiel-ds-responsable-confiance), l'initiative s'est petit à petit orientée vers une évaluation de maturité, un _assessment_, à destination des organisations qui ont une activité data science / IA.

- L'[assessment DSRC](https://github.com/LabeliaLabs/referentiel-evaluation-dsrc/blob/master/referentiel_evaluation.md)
- Le [story mapping](https://www.featuremap.co/m/ddC0Rj/plateforme-dsrc) de la plateforme d'assessment
- Les scripts [jsonize-dsrc-assessment](https://framagit.org/labelia-labs/jsonize-dsrc-assessment) pour convertir l'assessment de son format texte à un objet JSON et pour implémenter la grille de scoring

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

- `develop` est la branche par défaut. Toutes les MR doivent être créées par rapport à elle. C'est une branche protégée sur laquelle on n'est pas censé commiter et pousser directement.
- Les Merges Request de la branche feature vers la branche `develop` doivent être validées par au moins une autre personne que le développeur en charge de la feature.
- Les releases se font d'abord en fusionnant `develop` sur `preprod` qui est ensuite déployée sur le serveur de préprod pour que les tests fonctionnels soient réalisés.
- Une fois les tests fonctionnels validés, les releases sont ensuite ajoutées à la branche `prod` qui sera déployée sur le serveur de production.
- `prod` est en effet l'état de ce qui est en production à l'instant t, alors que `develop` est l'état de ce qui est testé et prêt à être déployé en pré-production (`preprod`) puis en production
- pour déployer en production, une fois tous les tests réalisés y compris sur la pré-production, on crée une MR de `develop` sur `prod` décrivant les changements principaux (note : lorsque l'historique de commits est propre et clair cela aide grandement !). Une fois la fusion réalisée, on pousse un tag de version sur `prod` selon les principes du versionnage sémantique

> Les branches `develop`, `preprod` et `prod` sont des branches réservées. Seuls les membres du groupe `maintainer` peuvent les manipuler (avec prudence !).
> Les développements par les membres du groupe `developer` se font sur des branches spécifiques, crées à partir de la branche `develop`.

### Conteneurisation

Pour faciliter le déploiement sur différents environnements (dev, preprod, prod) et donc assurer la portabilité de l'app, on choisit de travailler sur une infra conteneurisée avec Docker :

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

1. Pousser nos images sur les infras et les instancier

### Prototypage

Pour le prototypage, nous utilisons l'outil [moqups](https://moqups.com/).

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

### Emailings

Pour les emailings transactionnels on choisit le [module Mandrill de Mailchimp](https://mailchimp.com/fr/help/mailchimp-vs-mandrill/). On élaborera et designera les templates via l'interface Mandrill directement.

> Cela n'est pas encore implémenté - à ce stade les emails transactionnels sont templatés directement avec Django.

### Serveur(s) web

Comme le suggère le [tutoriel ci-dessus](https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/) sur Django x Docker, il semble être recommandé d'utiliser :

- gunicorn comme serveur web principal
- nginx comme reverse proxy pour distribuer sur les assets statiques et le serveur web principal

### Deploy

- Git flow: `develop` > `preprod` > `prod`
- Url preprod: <http://preprod.assessment.labelia.org/>

See the [dedicated document](./README_DEPLOY.md).
