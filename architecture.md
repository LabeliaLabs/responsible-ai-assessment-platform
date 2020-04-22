# Premières réflexions sur l'architecture de l'application

## Composants principaux

- Assets :
  - L'assessment en lui-même
  - Le modèle de scoring
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
  - Calculer le score
  - Authent/Ident
- Emailings transactionnels :
  - Templates dans Mailchimp
  - Déclenchement et instructions côté backend
