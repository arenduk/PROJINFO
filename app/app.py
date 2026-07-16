import streamlit as st

from auth import current_user, is_admin, login
from db import get_connection
from navbar import render_navbar

st.set_page_config(page_title="IcamTrac - Connexion", layout="wide")
render_navbar()

st.title("Connexion")

user = current_user()
if user is not None:
    st.success(f"Vous êtes déjà connecté en tant que {user['first_name']} {user['last_name']}.")
    if is_admin(user):
        st.page_link("pages/2_Administration.py", label="Aller à l'administration ➜")
    st.page_link("pages/1_Emprunt.py", label="Aller à mes emprunts ➜")
    st.stop()

conn = get_connection()

st.info(
    "La connexion via un compte Google Icam sera disponible prochainement. "
    "En attendant, sélectionnez votre compte ci-dessous."
)

users = conn.query(
    "SELECT id_user, last_name, first_name, email, user_status FROM user "
    "ORDER BY last_name, first_name",
    ttl=60,
)

if users.empty:
    st.warning("Aucun utilisateur n'est enregistré dans la base de données.")
    st.stop()

options = {
    row.id_user: f"{row.first_name} {row.last_name} ({row.email})"
    for row in users.itertuples()
}

with st.form("login_form"):
    id_user = st.selectbox(
        "Votre compte",
        options=list(options.keys()),
        format_func=lambda uid: options[uid],
    )
    submitted = st.form_submit_button("Se connecter")

st.button("Se connecter avec Google", disabled=True, help="Bientôt disponible")

if submitted:
    row = users.loc[users["id_user"] == id_user].iloc[0]
    login(
        id_user=int(row["id_user"]),
        first_name=row["first_name"],
        last_name=row["last_name"],
        user_status=row["user_status"],
    )
    if row["user_status"] == "admin":
        st.switch_page("pages/2_Administration.py")
    else:
        st.switch_page("pages/1_Emprunt.py")
