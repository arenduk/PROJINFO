import streamlit as st

from auth import current_user, is_admin, logout


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

    user = current_user()

    with st.container(key="topbar"):
        col_logo, col1, col2, col_spacer, col_notif, col_user = st.columns(
            [1.2, 1.5, 1.5, 4, 0.8, 2]
        )

        col_logo.markdown("### IcamTrac")

        if user is not None:
            col1.page_link("pages/1_Emprunt.py", label="Mes emprunts")
            if is_admin(user):
                col2.page_link("pages/2_Administration.py", label="Administration")

            with col_notif:
                with st.popover("🔔"):
                    st.write("Vos notifications...")

            with col_user:
                with st.popover(f"{user['first_name']} {user['last_name']}"):
                    st.write(f"Statut : {user['user_status']}")
                    if st.button("Déconnexion"):
                        logout()
                        st.switch_page("app.py")
        else:
            with col_user:
                col_user.page_link("app.py", label="Connexion")
