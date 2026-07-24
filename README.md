# IcamTrack

Plateforme de réservation et de suivi de matériel pour l'Icam :
demande d'emprunt pour une période donnée, validation par un gestionnaire de
stock, historique, calendrier personnel, statistiques, notifications, et une
administration du site.

## Stack

- **Streamlit** (interface) + **MySQL 8** (données), controllée via **Docker
  Compose**, le tout publiée en HTTPS par **Caddy**.
- Authentification : connexion Google (comptes `icam.fr` uniquement), via
  l'authentification native de Streamlit (`st.login`).

## Démarrage

1. Renomer `.env.exemple` en `.env` et renseigner de vrais mots de passe
   (+ `BOOTSTRAP_ADMIN_EMAIL`, voir *Premier admin* ci-dessous).
2. Créer un client OAuth Google (voir *Connexion Google* ci-dessous), copier
   `app/.streamlit/secrets.toml.example` en `app/.streamlit/secrets.toml` et
   le remplir avec les vraies valeurs.
3. Lancer :
   ```
   docker compose up --build
   ```
4. Ouvrir `https://adresseip.fr` (ou `http://localhost:8501` en local) et se
   connecter avec un compte Google `icam.fr`.

## Connexion Google (obligatoire)

1. Sur [Google Cloud Console](https://console.cloud.google.com/), créer ou
   choisir un projet, puis **APIs & Services → OAuth consent screen**. Comme ce
   projet appartient à l'organisation Google Workspace icam.fr, choisir
   **Interne** pour restreindre nativement aux comptes `icam.fr` ; sinon
   choisir **Externe** — le contrôle de domaine est alors fait côté
   application (une vérif est déjà en place dans `app/auth.py`, et elle fonctionne
   indépendamment de ce réglage).
3. **Credentials → Create credentials → OAuth client ID**, type **Application
   Web**.
4. Dans **Authorized redirect URIs**, ajouter exactement
   `https://nomdedomaine.fr/oauth2callback` (et `http://localhost:8501/oauth2callback`
   si besoin de tester en local). Ce chemin est imposé par Streamlit, ne pas
   le modifier.
5. Récupérer le *Client ID* et le *Client secret*, les renseigner dans
   `app/.streamlit/secrets.toml`. Générer un `cookie_secret` avec par exemple :
   ```
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

## Premier admin

À la toute première connexion réussie sur une base vide, le compte devient
automatiquement administrateur ; toutes les connexions suivantes créent des
comptes "utilisateur" standards. Comme le site est sur un domaine public,
il faut renseigner `BOOTSTRAP_ADMIN_EMAIL` dans `.env` avec une  adresse `icam.fr`
propre a cet utilisation.
**avant le premier déploiement** : seule cette adresse pourra alors devenir
admin via ce mécanisme, il vaut mieux utiliser ce système pour eviter tout problème.

Une fois connecté en tant qu'admin, on peut promouvoir d'autres utilisateurs
(gestionnaire de stock / admin) se fait depuis **Administration → Utilisateurs
& rôles**.

## Rôles

- **Utilisateur** : parcourt le matériel disponible, fait des demandes
  d'emprunt pour une période donnée, consulte son historique, son calendrier
  et ses notifications, et peut signaler lui-même le retour d'un emprunt en
  cours avant la date de retour prévue depuis l'historique.
- **Gestionnaire de stock** : en plus il valide ou refuse les demandes, marque
  le matériel comme rendu, gère le catalogue (ajout/modification/retrait
  d'équipement).
- **Administrateur** : en plus il gère les rôles des utilisateurs, consulte le
  journal d'activité, modifie les paramètres du site (nom, contact, bandeau de
  maintenance).

## Structure

```
app/
  app.py                 # écran de connexion Google
  db.py                  # connexion MySQL partagée
  auth.py                # st.login/st.user, rôles, provisioning, bootstrap admin
  navbar.py              # bandeau : navigation, notifications, menu utilisateur
  theme.py                # palette + CSS partagé (charte Icam)
  notifications.py       # notifications utilisateur
  audit.py                # journal d'activité
  availability.py         # disponibilité du matériel par plage de dates
  settings.py             # paramètres du site (clé/valeur)
  .streamlit/
    config.toml            # thème (committé)
    secrets.toml            # réel, jamais commit
  pages/
    1_Accueil.py, 2_Equipements.py, 3_Historique.py, 4_Validation.py,
    5_Stock.py, 6_Calendrier.py, 7_Statistiques.py, 8_Administration.py
DB/
  Init_SQL.sql            # schéma + données de démarrage (catalogue matériel)
Dockerfile / docker-compose.yml / Caddyfile
```

## Usage au quotidien

- Modifier du code dans `app/` → Streamlit recharge automatiquement (bind
  mount + file watcher), pas besoin de relancer quoi que ce soit.
- Modifier `requirements.txt` ou le `Dockerfile` → relancer avec
  `docker compose up --build` pour reconstruire l'image.
- Arrêter sans perdre les données MySQL : `docker compose down`.
- Tout réinitialiser (efface aussi les données MySQL) : `docker compose down -v`.
