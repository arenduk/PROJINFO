"""Journal d'activite (table `journal_audit`).

Chaque fonction ici prend une session SQLAlchemy deja ouverte et n'appelle
jamais `commit()` elle-meme : l'appelant compose l'ecriture principale + le
log dans une seule transaction (`with conn.session as s: ... s.commit()`).
"""

from sqlalchemy import text


def log_action(session, id_user, action: str, details: str = ""):
    """Enregistre une action dans le journal d'activite.

    id_user peut etre None (evenement systeme / echec d'authentification).
    """
    session.execute(
        text(
            "INSERT INTO journal_audit (id_user, action, details) "
            "VALUES (:id_user, :action, :details)"
        ),
        {"id_user": id_user, "action": action, "details": details},
    )


def list_recent(conn, limit: int = 200):
    """Journal recent avec nom/email de l'auteur, pour la page Administration.

    LEFT JOIN : un journal peut referencer un utilisateur supprime, et on
    veut un affichage propre meme quand la table est encore vide.
    """
    return conn.query(
        """
        SELECT j.id_journal, j.created_at, j.action, j.details,
               u.first_name, u.last_name, u.email
        FROM journal_audit j
        LEFT JOIN user u ON u.id_user = j.id_user
        ORDER BY j.created_at DESC
        LIMIT :limit
        """,
        params={"limit": limit},
        ttl=5,
    )
