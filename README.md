# Responsible and Trustworthy AI assessment platform - an open source project by Labelia Labs

## Structure of repositories

This repository `/responsible-ai-assessment-platform` corresponds to the web platform enabling users to conduct an assessment of their organization. It is linked to the following other repositories:

- [`/referentiel-evaluation-dsrc`](https://github.com/LabeliaLabs/referentiel-evaluation-dsrc): the "Responsible and Trustworthy AI" master framework. This is a text content
- [`/referentiel-processing-scripts`](https://github.com/LabeliaLabs/referentiel-processing-scripts): Python scripts required to process the master framework (and its associated upgrade table when processing a more recent version of a framework already uploaded in the assessment platform) into a set of `.json` files required by the assessment platform

## Assessment platform installation

Basic instructions to clone the repository and install locally the platform are given below.
For more details on platform installation, operation and maintenance, please refer to [`README_DEV.md`](./README_DEV.md).

- Clone the project:
  
  ```console
  git clone git@framagit.org:labelia-labs/pf-assessment-dsrc.git
  ```

- Create `.env.dev` from `env_dev_template`:
  
  ```console
  cp env_dev_template .env.dev
  ```

- Replace variables in the .env.dev file

- Build Docker image and start it:
  
  ```console
  docker-compose up --build
  ```

- Apply Django migrations
  
  ```console
  docker-compose exec questionnaire-grpc ./manage.py migrate
  ```

## Technical choices

*The below sections were written in French at the beginning of the project. They are kept in this README document to reflect the rationale behind technical choices made historically.*

### Commit messages

On définit rarement des conventions pour les messages de commits, alors que cela apporte une clarté et une facilité de lecture qui fait une vraie différence. Pour s'en rendre compte il faut regarder l'historique de `master` dans un projet où les 4 dernières PR mergées proviennent de 4 contributeurs différents... ça n'est pas facile de s'y retrouver !

Une approche qui est devenue une référence au fil des ans est celle décrite dans l'article [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/). Voici les principes-clés à avoir en tête :

- Par souci d'homogénéité et pour préserver les futures collaborations possibles, les commits messages doivent être **en anglais**
- Ils démarrent par une majuscule, un verbe à l'impératif, et finissent sans point. Exemple :
    > `Populate README with context and quick links to key resources`
- Ils ne doivent pas être trop longs (72 caractères est une bonne limite : les commits messages plus longs sont tronqués sur GitHub). Si besoin, utiliser la possibilité d'ajouter un *body* en plus du *subject* du commit message.

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

Les emails transactionnels sont templatés directement avec Django.

### Serveur(s) web

Comme le suggère le [tutoriel ci-dessus](https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/) sur Django x Docker, il semble être recommandé d'utiliser :

- gunicorn comme serveur web principal
- nginx comme reverse proxy pour distribuer sur les assets statiques et le serveur web principal

### Deploy

- Git flow: `develop` > `preprod` > `prod`
- Url preprod: <http://preprod.assessment.labelia.org/>
