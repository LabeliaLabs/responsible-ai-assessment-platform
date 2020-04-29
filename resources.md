# Ressources complémentaires au référentiel d'évaluation

Le référentiel d'évaluation est constitué d'éléments d'évaluation, avec leurs éléments de réponse, regroupés par sections thématiques.

À chaque éléments d'évaluation ou groupe d'élément, on veut pouvoir rattacher des ressources complémentaires. Elles peuvent être de natures variées :

- Articles techniques et scientifiques de référence
- Articles média d'illustration
- Outils techniques ou méthodologiques
- Explications, textes descriptifs
- ...

Ces ressources sont des contenus statiques (les utilisateurs n'interagissent pas avec sur la plateforme), mais qui sont amenés à évoluer assez régulièrement. En effet on veut pouvoir en ajouter, en supprimer, les modifier facilement.

Cela soulève plusieurs [questions d'architecture](#questions-darchitecture) et [questions produit](#questions-produit) traitées dans les sections suivantes.

## Questions d'architecture

1. Comment / à quoi les rattacher dans le modèle de données : aux éléments d'évaluation ?

   D'un point de vue utilisateur, cela fait plus sens d'être invité à les consulter au niveau des éléments d'évaluation. C'est le point d'entrée naturel pour s'interroger et s'intéresser à des ressources supplémentaires sur un sujet donné en lien avec l'évaluation.
   Il faut toutefois considérer différents éléments :

   - Certaines ressources pourront potentiellement s'appliquer à plusieurs questions d'une même section. En cas de modification, il faudra trouver un moyen de lier les ressources entre elles (ou bien s'assurer que la modification soit faite aux différents endroits d'un point de vue processus)
   - Un utilisateur va potentiellement vouloir retrouver des ressources plusieurs temps après avoir réalisé son questionnaire. Il ne vas pas forcément vouloir explorer chaque question pour retrouver la ressource en question. Il serait intéssant de les avoir au niveau des sections potentiellement, ou bien utiliser un système de tags.
   - En fait, il semble naturel pour l'évaluateur d'apporter des ressources à travers un élément d'évaluation. Par contre, l'utilisateur peut s'interroger et s'intéresser à différents moments à un sujet. Le moment où la question est posée est un de ces moments. Mais le point d'entrée peut être une recherche sur un sujet, comme par exemple _"les biais"_, _"les fairness metrics"_, ...

1. Quelle(s) interface(s) pour les admins pour agir sur ces ressources ? (ajout, modification, suppression)

   Ces ressources complémentaires peuvent toutes être ramenées à du texte formatté. En effet les articles et outils seront fournis naturellement sous forme de liens (*note : dans un second temps il pourrait être intéressant de pouvoir fournir des images*).

   Toute interface permettant d'interagir avec du texte ferait donc l'affaire. Les candidats sont donc naturellement :

   - le backoffice de la plateforme
   - le repo GitLab pour les assets complexes

   Il faudra réfléchir à ajouter des attributs à ces ressources, comme des catégories / tags

1. Comment gérer les sorties de nouvelles versions du référentiel d'évaluation ?

   Régulièrement le référentiel d'évaluation évoluera en une nouvelle version. La question que cela pose est celle de l'évolution des ressources complémentaires. Une approche serait de calquer cela sur la logique de migration des évaluations vers une version plus récente :

   - L'app s'appuie sur le mapping de migration de version qui est fourni avec la nouvelle version
   - Pour chaque élément d'évaluation ancien mappé vers un nouveau elle récupère les ressources complémentaires qui étaient renseignées
   - Pour chaque élément d'évaluation qui n'est pas mappé vers un nouveau, et pour chaque élément d'évaluation nouveau qui n'a pas de mappage depuis un ancien, elle ne fait rien
   - Pour ces derniers, c'est aux administrateurs de renseigner des ressources complémentaires

## Questions produit

*À compléter*

- Comment capitaliser sur et marketer ces ressources ? En fait-on quelque chose "d'important" ou "d'accessoire" du produit ?

  Il faut distinguer deux types de ressources :
    - Les ressources externes "trouvées" et apportées par la communauté : ces ressources viennent aider l'utilisateur à réfléchir sur un point en particulier et lui apporter des clés pour le résoudre. Elle montre que le questionnaire est dans une démarche positive et apporte des éléments de réponses.
    - Les ressources créées pour la plateforme : on peut imaginer que Substra ou ses partenaires crééent du contenus dédiés et exclusives sur certains sujets. Le but étant de renforcer la crédibilité des partenaires sur certains sujets en vu d'être reconnus comme experts (et vendre des prestations de services).

  Il faudrait probablement marketer les ressources que si un vrai travail de fond est réalisé sur les ressources     
    - Si on ne produit pas de contenu, le risque de trop marketer les ressources est de se voir reprocher leur qualité : _"Je suis venu parce qu'on m'a promis des ressources et vous ne parlez pas de cela / vous faites la promotion de tel outil qui est dépassé"_. On peut tout à fait être d'accord mais cela demande alors que l'on prenne vraiment le temps sur chaque contenu pour s'assurer de sa qualité. Ou décider que notre valeur ajoutée est sur le questionnaire et scoring et que cela est donc accessoire.
    - Entre les deux approches, on peut imaginer le faire que pour une partie des ressources et avoir une petite cocarde "ressource de choix". Une sélection de la sélection, qui représenterait moins de travail.   
    - Si on produit du contenu, pour le coup cela sera un vrai plus et il faudra le marketer : "retrouver du contenu exclusive".



- Faut-il imaginer une logique de notifications des inscrits quand de nouvelles ressources sont ajoutées ? Auquel cas il faudrait en ajouter avec précaution, par petits paquets et pas au fil de l'eau ?

  On peut distinguer deux types de notification :

    - Par mail : on peut se dire peut être que plutôt que d'envoyer un mail à chaque update, un mail est envoyé une fois par mois (fréquence à définir) aggrégeant et présentant les nouvelles ressources qui ont été ajoutées.
    - Si on mets un système de notification dans la plateforme (certains outils gèrent cela), il n'y a pas de problème à faire apparaitre une nouvelle information à chaque nouvel update.

- Imagine-t-on de les regrouper en complément ailleurs que dans les éléments d'évaluation. Par exemple tous les outils ensemble ?


  - Si cela n'est pas nécessaire d'avoir dans un premier temps le regroupement des ressources, cela semble nécessaire d'un point de vue utilisateur. Les utilisateurs ne vont pas vouloir nécessairement se replonger dans l'intégralité du questionnaire pour retrouver une ressource qu'ils avaient identifiée.
  - Sans centre de ressources, l'utilisateur est obligé d'initialiser / modifier / consulter une évaluation pour avoir accès aux ressources. Avoir un regroupement pour trouver une ressource semble approprié.
  - Il faudrait pouvoir effectuer de la recherche sur ces ressources, et / ou les catégoriser.
- ...
