# Remplir une évaluation

## Objectif

L'objectif de cette section est d'expliquer comment l'utilisateur va pouvoir répondre aux différentes questions de l'évaluation.

## Création d'une évaluation

Lorsque l'utilisateur [créé une évaluation](./evaluation-user.md), il arrive sur la première section de l'évaluation.
(_à discuter : prévoir une page "de garde" ?_)

## Navigation entre sections

En haut ou en colonne (_à définir_), l'utilisateur a accès à la liste des différentes sections.
Pour chaque section, un pourcentage d'avancement est indiqué corrrespondant au nombre de questions répondues / le nombre de questions de la section.
Un indicateur est mis pour indiquer qu'une section est complétée.
L'utilisateur peut cliquer sur une section pour avoir accès aux questions de la section.

## Soumission d'une évaluation

L'utilisateur ne peut soumettre une évaluation que si 100% des questions ont été remplies.
Un bouton se trouve en bas de la page en permanence. Il est grisé tant que 100% des questions ne sont pas remplies.
Lorsque l'utilisateur a complété toutes les questions, il peut alors cliquer sur le bouton "Soumettre mon évaluation".
Une popin apparait pour lui demander de valider.
L'utilisateur arrive alors sur la page de [consultation des résultats](./results-user.md).

## Répondre à une évaluation

Pour chaque section, une liste de questions est proposée.
(_à discuter : soit une liste, soit chaque question fait l'objet d'un écran spécifique et on bascule d'une question à une autre_)

Une question est composée de 4 éléments :
- La question adressée à l'utilisateur (obligatoire)
- Une explication de la question et / ou des réponses proposées (facultatif)
- Une liste de réponses possibles à la question (obligatoire)
- Des ressources en lien avec la question posée (facultatif _mettre plutôt un lien vers le centre de ressources avec les ressources liées à la question ?_ )

En terme d'affichage, lorsque l'utilisateur arrive dans la section, l'utilisateur peut voir la question, ainsi que les réponses proposées.
Dans le bloc de réponse, une partie commentaire / justification est disponible.
Les explications sont fournies via une infobulle (_ou l'ouverture d'un bloc dédié ?_).
Les ressources sont fournies via un bloc dédié qui est fermé (_ou uniquement lien vers centre de ressources_).
L'utilisateur peut "fermer" le bloc dédié aux réponses.

L'utilisateur pour chaque question peut :
- Répondre à la question selon le type de réponse requis :
  - multi-select
  - choix unique - l'utilisateur doit pouvoir déselectionner son choix
- Ajouter une justification, sous forme de textes libres (_définir un nombre de caractères maximum ? champs WYSIWYG ?_)

## Sauvegarde d'une réponse

Deux possibilités :
- Sauvegarde via un bouton. L'utilisateur doit cliquer sur un bouton pour sauvegarder ses données. S'il souhaite voir une autre section sans avoir sauvegardé (ou clique sur n'importe quel lien en dehors), une popin l'informe qu'il n'a pas sauvegardé et lui propose de :
  - Sauvegarder et continuer
  - Ne pas sauvegarder et continuer
  - Annuler
- Une sauvegarde au fil de l'eau dès que l'utilisateur entre des informations.

(_A priori, la sauvegarde automatique semble plus UX friendly. Cependant, si on prévoit que les justifications prennent une place importante, un utilisateur qui perds par mégarde ce qu'il a complété est plus fréquent et risqué en sauvegarde automatique... Il faut aussi prendre en compote la complexité technique des deux solutions._)

_Work in progress_
