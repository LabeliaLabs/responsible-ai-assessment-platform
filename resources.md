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

1. Quelle(s) interface(s) pour les admins pour agir sur ces ressources ? (ajout, modification, suppression)

   Ces ressources complémentaires peuvent toutes être ramenées à du texte formatté. En effet les articles et outils seront fournis naturellement sous forme de liens (*note : dans un second temps il pourrait être intéressant de pouvoir fournir des images*).

   Toute interface permettant d'interagir avec du texte ferait donc l'affaire. Les candidats sont donc naturellement :

   - le backoffice de la plateforme
   - le repo GitLab pour les assets complexes

1. Comment gérer les sorties de nouvelles versions du référentiel d'évaluation ?

   Régulièrement le référentiel d'évaluation évoluera en une nouvelle version. La question que cela pose est celle de l'évolution des ressources complémentaires. Une approche serait de calquer cela sur la logique de migration des évaluations vers une version plus récente :

   - L'app s'appuie sur le mapping de migration de version qui est fourni avec la nouvelle version
   - Pour chaque élément d'évaluation ancien mappé vers un nouveau elle récupère les ressources complémentaires qui étaient renseignées
   - Pour chaque élément d'évaluation qui n'est pas mappé vers un nouveau, et pour chaque élément d'évaluation nouveau qui n'a pas de mappage depuis un ancien, elle ne fait rien
   - Pour ces derniers, c'est aux administrateurs de renseigner des ressources complémentaires

## Questions produit

*À compléter*

- Comment capitaliser sur et marketer ces ressources ? En fait-on quelque chose "d'important" ou "d'accessoire" du produit ?
- Faut-il imaginer une logique de notifications des inscrits quand de nouvelles ressources sont ajoutées ? Auquel cas il faudrait en ajouter avec précaution, par petits paquets et pas au fil de l'eau ?
- Imagine-t-on de les regrouper en complément ailleurs que dans les éléments d'évaluation. Par exemple tous les outils ensemble ?
- ...
