import streamlit as st


def render_navbar():
    st.markdown(
        """
        <style>
        .stApp {
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        }

        .st-key-topbar {
            background-color: #1c8adb;
            padding: 10px 24px;
            border-radius: 0 0 12px 12px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.18);
            margin-bottom: 1.5rem;
        }
        .st-key-topbar button, .st-key-topbar a {
            color: white !important;
            background: transparent !important;
            border: none !important;
            font-weight: 500;
            transition: opacity 0.15s ease;
        }
        .st-key-topbar button:hover, .st-key-topbar a:hover {
            opacity: 0.75;
        }

        h1, h2, h3 {
            color: var(--text-color);
        }

        div[data-testid="stForm"] {
            background-color: var(--secondary-background-color);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(128, 128, 128, 0.2);
        }

        div[data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid rgba(128, 128, 128, 0.2);
        }

        .stButton button {
            border-radius: 8px;
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="topbar"):
        col_logo, col1, col2, col3, col_spacer, col_notif, col_user, col_toggle = st.columns(
            [1.2, 1, 1.5, 1, 4, 0.8, 1.4, 2.5]
        )

        col_logo.markdown("### Icam")
        col1.page_link("test.py", label="Accueil")
        col2.page_link("pages/1_Tableau_de_bord.py", label="Tableau de bord")
        col3.page_link("pages/2_Mes_cours.py", label="Mes cours")

        with col_notif:
            with st.popover("🔔"):
                st.write("Vos notifications etc...")

        with col_user:
            with st.popover("user"):
                st.write("Profil")
                st.button("Déconnexion")

        col_toggle.toggle("Mode administrateur")
