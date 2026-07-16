# Template Streamlit + MySQL en Docker

## Structure

```
streamlit-mysql-docker/
├── app/
│   └── app.py            # ton code Streamlit
├── db/
│   └── init.sql          # schema/dump charge au 1er demarrage de MySQL
├── Dockerfile             # construit l'image Streamlit
├── docker-compose.yml     # orchestre Streamlit + MySQL
├── requirements.txt       # dependances Python
├── .env.example           # variables a copier dans .env
└── .dockerignore
```

## Mise en place

1. Copie tout ce dossier a la racine de ton vrai projet (ou remplace
   `app/app.py` par ton code existant, et `requirements.txt` par tes
   vraies dependances).

2. Remplace `db/init.sql` par ton propre schema/dump SQL.

3. Cree ton fichier de config reel :
   ```
   cp .env.example .env
   ```
   puis edite `.env` avec de vrais mots de passe. Ce fichier ne doit
   jamais etre commit dans git (ajoute-le a ton .gitignore).

4. Lance tout :
   ```
   docker compose up --build
   ```
   Premier lancement : construit l'image Streamlit, telecharge MySQL,
   cree la base et execute `init.sql`.

5. Ouvre http://localhost:8501 pour voir l'app, et verifie la connexion
   MySQL avec le bouton de test dans `app.py`.

## Usage au quotidien

- Modifier du code dans `app/` -> Streamlit recharge automatiquement
  (bind mount + file watcher), pas besoin de relancer quoi que ce soit.
- Modifier `requirements.txt` ou le `Dockerfile` -> il faut relancer
  avec `docker compose up --build` pour reconstruire l'image.
- Arreter sans perdre les donnees MySQL : `docker compose down`.
- Tout reinitialiser (efface aussi les donnees MySQL) :
  `docker compose down -v`.

## Partager le projet

La personne qui recupere le projet n'a besoin que de :
- Docker installe
- copier `.env.example` en `.env` et renseigner ses propres valeurs
- lancer `docker compose up --build`

Aucune installation manuelle de Python, MySQL ou de dependances n'est
necessaire de son cote.
