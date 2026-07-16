import streamlit as st


def render_navbar():
    st.markdown(
        """
        <style>
        .st-key-topbar {
            background-color: #1c8adb;
            padding: 8px 20px;
        }
        .st-key-topbar button, .st-key-topbar a {
            color: white !important;
            background: transparent !important;
            border: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="topbar"):
        col_logo, col1, col2, col3, col_spacer, col_notif, col_user, col_toggle = st.columns(
            [1.2, 1, 1.5, 1, 4, 0.8, 0.8, 1.5]
        )

        col_logo.markdown("### 🟠 icam")
        col1.page_link("test.py", label="Accueil")
        col2.page_link("pages/1_Tableau_de_bord.py", label="Tableau de bord")
        col3.page_link("pages/2_Mes_cours.py", label="Mes cours")

        with col_notif:
            with st.popover("🔔"):
                st.write("Vos notifications...")

        with col_user:
            with st.popover("LP"):
                st.write("Profil")
                st.button("Déconnexion")

        col_toggle.toggle("Mode d'édition")
