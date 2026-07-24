# IcamTrack

Plateforme de réservation et de suivi de matériel pour l'Icam Strasbourg-Europe :
demande d'emprunt pour une période donnée, validation par un gestionnaire de
stock, historique, calendrier personnel, statistiques, notifications, et une
administration du site (rôles, journal d'activité, paramètres).

## Stack

- **Streamlit** (interface) + **MySQL 8** (données), orchestrés via **Docker
  Compose**, exposés en HTTPS par **Caddy**.
- Authentification : connexion Google (comptes `icam.fr` uniquement), via
  l'authentification native de Streamlit (`st.login`).

## Démarrage

1. Copier `.env.exemple` en `.env` et renseigner de vrais mots de passe
   (+ `BOOTSTRAP_ADMIN_EMAIL`, voir *Premier admin* ci-dessous).
2. Créer un client OAuth Google (voir *Connexion Google* ci-dessous), copier
   `app/.streamlit/secrets.toml.example` en `app/.streamlit/secrets.toml` et
   le remplir avec les vraies valeurs. Ce fichier ne doit jamais être commit
   (déjà dans `.gitignore`).
3. Lancer :
   ```
   docker compose up --build
   ```
4. Ouvrir `https://arenduk.fr` (ou `http://localhost:8501` en local) et se
   connecter avec un compte Google `icam.fr`.

## Connexion Google (obligatoire)

1. Sur [Google Cloud Console](https://console.cloud.google.com/), créer ou
   choisir un projet, puis **APIs & Services → OAuth consent screen**. Si ce
   projet appartient à l'organisation Google Workspace icam.fr, choisir
   **Interne** pour restreindre nativement aux comptes `icam.fr` ; sinon
   choisir **Externe** — le contrôle de domaine est alors fait côté
   application (déjà en place dans `app/auth.py`, indépendamment de ce
   réglage).
2. **Credentials → Create credentials → OAuth client ID**, type **Application
   Web**.
3. Dans **Authorized redirect URIs**, ajouter exactement
   `https://arenduk.fr/oauth2callback` (et `http://localhost:8501/oauth2callback`
   si besoin de tester en local). Ce chemin est imposé par Streamlit, ne pas
   le modifier.
4. Récupérer le *Client ID* et le *Client secret*, les renseigner dans
   `app/.streamlit/secrets.toml`. Générer un `cookie_secret` avec :
   ```
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

## Premier admin

À la toute première connexion réussie sur une base vide, le compte devient
automatiquement administrateur ; toutes les connexions suivantes créent des
comptes "utilisateur" standards. Comme le site est sur un domaine public,
renseigne `BOOTSTRAP_ADMIN_EMAIL` dans `.env` avec ta propre adresse `icam.fr`
**avant le premier déploiement** : seule cette adresse pourra alors devenir
admin via ce mécanisme, plutôt que de laisser la course au premier arrivé.

Une fois connecté en tant qu'admin, promouvoir d'autres utilisateurs
(gestionnaire de stock / admin) se fait depuis **Administration → Utilisateurs
& rôles**.

## ⚠️ Important : le schéma a été entièrement réécrit

`DB/Init_SQL.sql` a été refait de zéro (nouvelles tables, nouvelles colonnes,
nouveaux rôles). Il ne s'exécute que sur un volume MySQL **vide**
(`docker-entrypoint-initdb.d`). Si l'ancienne version tournait déjà, purger le
volume existant avant de relancer, sans quoi l'ancien schéma reste en place :
```
docker compose down -v
docker compose up --build
```
Cela efface les données de l'ancienne base (utilisateurs/emprunts de test) —
le catalogue de matériel est reseedé automatiquement.

## Rôles

- **Utilisateur** : parcourt le matériel disponible, fait des demandes
  d'emprunt pour une période donnée, consulte son historique, son calendrier
  et ses notifications, et peut signaler lui-même le retour d'un emprunt en
  cours (même avant la date de retour prévue) depuis l'historique.
- **Gestionnaire de stock** : en plus — valide ou refuse les demandes, marque
  le matériel comme rendu, gère le catalogue (ajout/modification/retrait
  d'équipement).
- **Administrateur** : en plus — gère les rôles des utilisateurs, consulte le
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
    secrets.toml.example   # gabarit (committé)
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
