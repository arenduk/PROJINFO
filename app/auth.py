"""Gestion de la session utilisateur.

Pour le moment la connexion se fait en choisissant son compte dans une liste
(pas encore de veritable authentification). La fonction `login` est isolee
ici pour pouvoir etre appelee plus tard depuis un callback OAuth Google sans
toucher au reste de l'application.
"""

import streamlit as st

SESSION_KEY = "utilisateur"


def login(id_user, first_name, last_name, user_status):
    st.session_state[SESSION_KEY] = {
        "id_user": id_user,
        "first_name": first_name,
        "last_name": last_name,
        "user_status": user_status,
    }


def logout():
    st.session_state.pop(SESSION_KEY, None)


def current_user():
    return st.session_state.get(SESSION_KEY)


def is_admin(user):
    return user is not None and user["user_status"] == "admin"


def require_login():
    """Bloque le rendu de la page si personne n'est connecte."""
    user = current_user()
    if user is None:
        st.warning("Vous devez vous connecter pour acceder a cette page.")
        st.page_link("app.py", label="Aller a la page de connexion")
        st.stop()
    return user


def require_admin():
    """Bloque le rendu de la page si l'utilisateur connecte n'est pas admin."""
    user = require_login()
    if not is_admin(user):
        st.error("Cette page est reservee aux administrateurs.")
        st.stop()
    return user
