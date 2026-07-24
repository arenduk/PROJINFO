"""Parametres du site (table `site_settings`, cle/valeur) : nom du site,
email de contact, bandeau de maintenance. Utilise par la page Administration
(edition) et par le bandeau de navigation (affichage du bandeau de maintenance
sur toutes les pages).
"""

from sqlalchemy import text


def get_all(conn) -> dict:
    df = conn.query("SELECT setting_key, setting_value FROM site_settings", ttl=15)
    return dict(zip(df["setting_key"], df["setting_value"]))


def get_setting(conn, key: str, default: str = "") -> str:
    return get_all(conn).get(key, default) or default


def set_setting(session, key: str, value: str):
    session.execute(
        text("UPDATE site_settings SET setting_value = :value WHERE setting_key = :key"),
        {"key": key, "value": value},
    )
