"""Notifications utilisateur (c'est la cloche du bandeau).
"""

from sqlalchemy import text


def notify(session, id_user, type_: str, message: str, id_emprunt=None):
    session.execute(
        text(
            "INSERT INTO notification (id_user, type, message, id_emprunt) "
            "VALUES (:id_user, :type, :message, :id_emprunt)"
        ),
        {"id_user": id_user, "type": type_, "message": message, "id_emprunt": id_emprunt},
    )


def notify_many(session, id_users, type_: str, message: str, id_emprunt=None):
    for id_user in id_users:
        notify(session, id_user, type_, message, id_emprunt)


def notify_validators(session, type_: str, message: str, id_emprunt=None, exclude_id_user=None):
    """Notifie tous les gestionnaires de stock et admins actifs (sauf, en
    general, le demandeur lui-meme s'il a aussi ce role)."""
    rows = session.execute(
        text(
            "SELECT id_user FROM user "
            "WHERE role IN ('stock_manager', 'admin') AND is_active = TRUE "
            "AND id_user != :exclude"
        ),
        {"exclude": exclude_id_user or 0},
    ).fetchall()
    notify_many(session, [r.id_user for r in rows], type_, message, id_emprunt)


def list_notifications(conn, id_user, unread_only: bool = False, limit: int = 20):
    clause = "AND is_read = FALSE" if unread_only else ""
    return conn.query(
        f"""
        SELECT id_notification, type, message, id_emprunt, is_read, created_at
        FROM notification
        WHERE id_user = :id_user {clause}
        ORDER BY created_at DESC
        LIMIT :limit
        """,
        params={"id_user": id_user, "limit": limit},
        ttl=5,
    )


def count_unread(conn, id_user) -> int:
    df = conn.query(
        "SELECT COUNT(*) AS n FROM notification WHERE id_user = :id_user AND is_read = FALSE",
        params={"id_user": id_user},
        ttl=5,
    )
    return int(df["n"].iloc[0]) if not df.empty else 0


def mark_as_read(conn, id_notification, id_user):
    with conn.session as s:
        s.execute(
            text(
                "UPDATE notification SET is_read = TRUE "
                "WHERE id_notification = :id_notification AND id_user = :id_user"
            ),
            {"id_notification": id_notification, "id_user": id_user},
        )
        s.commit()


def mark_all_as_read(conn, id_user):
    with conn.session as s:
        s.execute(
            text("UPDATE notification SET is_read = TRUE WHERE id_user = :id_user"),
            {"id_user": id_user},
        )
        s.commit()
