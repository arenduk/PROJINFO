import streamlit as st

import auth
import theme

st.set_page_config(page_title="IcamTrack - Connexion", layout="wide")

if st.user.is_logged_in:
    user = auth.require_login()
    theme.inject_base_style()
    st.success(f"Vous êtes déjà connecté en tant que {user['first_name']} {user['last_name']}.")
    st.page_link("pages/1_Accueil.py", label="Aller à l'accueil ➜")
    st.stop()

theme.inject_base_style()

col_visual, col_form = st.columns([1.3, 1], gap="large")

with col_visual:
    theme.render_hero(
        "IcamTrack",
        "La plateforme de réservation et de suivi du matériel de l'Icam Strasbourg-Europe. "
        "Empruntez du matériel pour vos projets, suivez vos demandes et retrouvez tout "
        "votre historique au même endroit.",
    )
    st.caption(
        "Matériel disponible en temps réel · Calendrier de vos emprunts · "
        "Notifications de validation · Statistiques d'utilisation"
    )

with col_form:
    with st.container(border=True):
        st.markdown('<div class="icamtrack-logo">Icam<span>Track</span></div>', unsafe_allow_html=True)
        st.subheader("Bienvenue,")
        st.write("Connexion avec votre compte Google Icam (**icam.fr**).")
        if st.button("SE CONNECTER", type="primary", use_container_width=True):
            st.login()
        st.caption("Seuls les comptes icam.fr sont autorisés à utiliser IcamTrack.")
