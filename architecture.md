# Premières réflexions sur l'architecture de l'application

## Composants principaux

- Assets :
  - L'assessment en lui-même (les assessements en réalité, cf. [Gestion des multiples versions de référentiels d'évaluation](#gestion-des-multiples-versions-de-référentiels-dévaluation))
  - Le(s) modèle(s) de scoring attaché(s) à un référentiel d'évaluation
  - Contenus textuels additionnels : textes de page d'accueil, FAQ, CGU, mentions légales
- Frontend :
  - Page d'accueil
  - Affichage des éléments de l'assessment pour que l'utilisateur interagisse
  - Synthèse de la progression dans l'assessment
  - Synthèse des résultats de l'assessment
  - Faire un feedback sur un élément de l'assessment
  - Page de profil / réglages
- Backend :
  - Créer un assessment vierge pour un utilisateur, enregistrer son état / ses changements d'état
  - Créer un assessment nouveau à partir d'un assessment existant dans une précédente version ("en cours" ou "terminé")
  - Calculer le score
  - Authent/Ident
- Emailings transactionnels :
  - Templates dans Mailchimp
  - Déclenchement et instructions côté backend

## Gestion des multiples versions de référentiels d'évaluation

Le référentiel d'évaluation est amené à évoluer, avec l'évolution de l'état de l'art, les retours d'expérience des organisations qui s'évaluent, etc. Il est donc crucial de savoir gérer le plus proprement possible ces évolutions. D'autant plus que :

- le référentiel d'évaluation est open source et participatif. Son évolution est donc soumise à une gouvernance ouverte, elle ne peut se faire de manière discrétionnaire (sauf pour des modifications très mineures, de type fautes d'orthographe ou de ponctuation)
- une fois la plateforme lancée publiquement, il existera des évaluations terminées et des évaluations en cours. L'évolution du référentiel d'évaluation a donc immédiatement des impacts à prendre en compte

On peut envisager l'approche suivante lorsqu'une nouvelle version du référentiel d'évaluation est disponible :

1. Les évaluations déjà existantes (en statut "en cours" ou "terminé") **restent telles quelles**
1. Il est proposé à l'utilisateur disposant d'évaluations existantes de **les migrer dans une version plus récente**
1. Une migration d'une évaluation existante vers une version plus récente consiste à :
   - instancier une nouvelle évaluation dans la version plus récente choisie
   - récupérer en base la liste des éléments d'évaluation inchangés entre la version de l'évaluation existante et la version cible
   - pour chaque élément inchangé, récupérer la réponse d'alors (_note : cela pourrait être laissé au choix de l'utilisateur ; dans certains cas il peut vouloir redémarrer une évaluation vierge_). Pour les éléments qui ont changé, laisser vierge

Conséquences à retenir :

- les référentiels d'évaluation existent en plusieurs versions qui coexistent en base de données
- une "évaluation" est donc l'instanciation d'un certain référentiel d'évaluation (une certaine version)
- la coexistence de plusieurs référentiels d'évaluation est une notion distincte de la coexistence de plusieurs modèles de scoring des évaluations. Il peut y avoir plusieurs modèles de scoring pour un même référentiel d'évaluation
- les évaluations ont un statut d'avancement, dont une valeur est "terminé"
