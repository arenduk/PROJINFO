"""Authentification (Google OAuth natif de Streamlit) et gestion des roles.

Connexion reelle via `st.login()` / `st.user`, restreinte aux comptes Google
Workspace icam.fr. Un compte est cree automatiquement en base au premier
login (voir `_provision_new_user`) : aucune inscription manuelle necessaire.

Point important : `st.login()`/`st.logout()` redirigent toujours vers
`app.py` dans une session neuve, donc la verification (connecte ? domaine
autorise ? compte actif ?) ne peut pas etre faite une seule fois sur
`app.py` — une page de `pages/` reste directement accessible par son URL.
`require_login()`/`require_role()` doivent donc etre appelees en toute
premiere ligne de CHAQUE page.
"""

import os

import streamlit as st
from sqlalchemy import text

import audit
from db import get_connection

ALLOWED_DOMAIN = "icam.fr"
ALLOWED_EMAIL_SUFFIX = "icam.fr"

ROLE_RANK = {"user": 0, "stock_manager": 1, "admin": 2}
ROLE_LABELS = {
    "user": "Utilisateur",
    "stock_manager": "Gestionnaire de stock",
    "admin": "Administrateur",
}


def _domain_ok(claims: dict) -> bool:
    email = (claims.get("email") or "").lower()
    return claims.get("hd") == ALLOWED_DOMAIN or email.endswith(ALLOWED_EMAIL_SUFFIX)


def _provision_new_user(session, email: str, claims: dict) -> dict:
    """Cree la ligne `user` au tout premier login de cet email.

    Bootstrap admin : si la table est totalement vide, la premiere connexion
    reussie devient admin (ou, si la variable d'environnement
    BOOTSTRAP_ADMIN_EMAIL est definie, seule cette adresse-la peut le
    devenir — recommande en production pour ne pas laisser le hasard
    decider qui administre le site). Un verrou nomme MySQL serialise les
    provisionnements concurrents pour eviter que deux premieres connexions
    simultanees ne deviennent toutes les deux admin.
    """
    session.execute(text("SELECT GET_LOCK('icamtrack_provision', 10)"))
    try:
        is_first_ever = session.execute(text("SELECT COUNT(*) FROM user")).scalar() == 0
        bootstrap_email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
        role = "admin" if is_first_ever and (not bootstrap_email or bootstrap_email == email) else "user"

        result = session.execute(
            text(
                "INSERT INTO user (email, first_name, last_name, role, last_login_at) "
                "VALUES (:email, :fn, :ln, :role, CURRENT_TIMESTAMP)"
            ),
            {
                "email": email,
                "fn": claims.get("given_name") or claims.get("name") or "",
                "ln": claims.get("family_name") or "",
                "role": role,
            },
        )
        new_id = result.lastrowid
        audit.log_action(session, new_id, "provisioning", f"role initial : {role}")
    finally:
        session.execute(text("SELECT RELEASE_LOCK('icamtrack_provision')"))

    return dict(
        session.execute(text("SELECT * FROM user WHERE id_user = :id"), {"id": new_id}).mappings().first()
    )


def _fetch_or_provision(email: str, claims: dict) -> dict:
    conn = get_connection()
    with conn.session as s:
        row = s.execute(text("SELECT * FROM user WHERE email = :email"), {"email": email}).mappings().first()
        if row is None:
            user_row = _provision_new_user(s, email, claims)
        else:
            s.execute(
                text("UPDATE user SET last_login_at = CURRENT_TIMESTAMP WHERE id_user = :id"),
                {"id": row["id_user"]},
            )
            user_row = dict(row)
        s.commit()
    return user_row


def require_login() -> dict:
    """A appeler en premiere ligne de chaque page. Bloque le rendu tant que
    l'utilisateur n'est pas connecte avec un compte icam.fr actif."""
    if not st.user.is_logged_in:
        st.login()
        st.stop()

    claims = st.user.to_dict()
    email = (claims.get("email") or "").lower()
    if not email or not _domain_ok(claims):
        st.error(f"Acces refuse : seuls les comptes {ALLOWED_EMAIL_SUFFIX} peuvent utiliser IcamTrack.")
        if st.button("Se deconnecter et reessayer"):
            st.logout()
        st.stop()

    user_row = _fetch_or_provision(email, claims)

    if not user_row["is_active"]:
        st.error("Ce compte a ete desactive. Contactez un administrateur.")
        if st.button("Se deconnecter"):
            st.logout()
        st.stop()

    return user_row


def require_role(min_role: str) -> dict:
    """require_login() + verification hierarchique (user < stock_manager <
    admin, un role superieur herite des droits des roles inferieurs)."""
    user = require_login()
    if not has_role(user, min_role):
        st.error("Vous n'avez pas les droits necessaires pour acceder a cette page.")
        st.stop()
    return user


def has_role(user: dict | None, min_role: str) -> bool:
    """Verification non bloquante, pour un affichage conditionnel (ex. liens
    du bandeau, boutons d'action)."""
    if user is None:
        return False
    return ROLE_RANK.get(user["role"], -1) >= ROLE_RANK.get(min_role, 99)
