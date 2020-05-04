# Création de compte et gestion de profil

## Objectif

L'objectif de cette section est de documenter les fonctionnalités utilisateurs de :
- Création d'un compte
- Connexion à un compte
- Modification d'un compte
- Suppression d'un compte

## Principes

- Le principe de minimisation de collecte des données personnelles sera appliqué.
- Nous utiliserons les fonctionnalités d'autentification fournies par Django.  

### Création / connexion à un compte

L'utilisateur peut, depuis le site vitrine, se connecter ou créer son compte en cliquant :

- Dans le header de la plateforme;
- Dans différents boutons situés dans le site vitrine.

Lorsque l'utilisateur clique dessus, une popin apparait.
Par défaut, il est considéré comme déjà utilisateur de la plateforme. On lui demande son email et son mot de passe.
Il dispose d'un bouton "Je n'ai pas de compte" qui lui permettra de créer son compte.

#### Connexion à son compte

L'utilisateur non connecté entre son mail et son mot de passe. Si celui-ci est bon, il accède à la plateforme.
Si le mot de passe et / ou l'identifiant ne sont pas reconnus, un message d'erreur en rouge apparait : "Le mot de passe et/ou le mail entrés sont incorrects".

_Sécurité addtionnelle_ : si l'utilisateur entre 5 fois un mot de passe incorrect d'affilée, alors le compte passe en inactif pendant une durée de 1h.


#### Mot de passe oublié

L'utilisateur a la possibilité de cliquer sur mot de passe oublié. Il entre alors son email.
Un message lui indique qu'un mail pour réinitialiser son mot de passe a été envoyé sur le compte indiqué :  

- Si le compte est bien présent dans la base, un mail est envoyé contenant un lien pour réinitialiser son mot de passe.
- Si le compte n'est pas présent dans la base, aucun email est envoyé mais le message est le même (pour des questions de sécurité).

#### Création de compte

Lorsque l'utilisateur clique sur "Créer son compte", un formulaire s'ouvre.

| # | Intitulé du champs | Type de champs | Obligatoire / Facultatif | Contraintes |
|:---:|:---|:---|:---|:---|
| 1 | Prénom | Texte court | Obligatoire |  |
| 2 | Nom | Texte court | Obligatoire | |
| 3 | Email | Texte court | Obligatoire | Pas d'espace accepté, obligation d'avoir un "@" |
| 4 | Mot de passe | Texte court | Obligatoire | Le mot de passe doit être de 8 caractères minimum et contenir au moins 1 chiffre. |
| 5 | Confirmer le mot de passe | Texte court | Obligatoire | Doit être identique au champs "mot de passe" |

Lorsque l'utilisateur a entré ses informations, il clique sur "Je créé mon compte".
Un mail est alors envoyé sur son addresse email contenant un lien pour valider la création de son compte.
Lorsqu'il a cliqué sur le lien, l'utilisateur peut accéder alors à la plateforme.

Si le mail entré est déjà présent dans la base, un message apparait indiquant "Cet email est déjà rattaché à un compte" avec la proposition : "Je me connecte" ou "Mot de passe oublié". L'utilisateur peut cliquer sur un des deux et est alors ammené à la section choisie.

_Point ouvert : faut-il créer son organisation dès la création du compte ou dans une seconde étape ?_

### Déconnexion

L'utilisateur peut à tout moment se déconnecter de la plateforme en cliquant sur "Se déconnecter" présent dans le header de la plateforme.

### Gestion du profil

_Work in progress_

### Modification du profil

_Work in progress_

### Suppression du compte

_Work in progress_
