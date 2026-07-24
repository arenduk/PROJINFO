"""Bandeau de navigation : logo, liens filtres par role, cloche de
notifications, menu utilisateur. Ne fait AUCUNE verification d'auth elle-meme
— chaque page appelle `auth.require_login()`/`require_role()` avant de
rendre le bandeau et lui passe l'utilisateur deja valide.
"""

import streamlit as st

import auth
import notifications
import settings
import theme
from db import get_connection


def render_navbar(user: dict):
    theme.inject_base_style()
    conn = get_connection()

    unread = notifications.count_unread(conn, user["id_user"])

    with st.container(key="topbar"):
        (col_logo, col_accueil, col_equip, col_hist, col_cal, col_stats,
         col_spacer, col_gestion, col_notif, col_user) = st.columns(
            [1.3, 1, 1.1, 1, 1.1, 1.1, 2.2, 1.3, 0.7, 1.6]
        )

        col_logo.markdown(
            '<div class="icamtrack-logo">Icam<span>Track</span></div>',
            unsafe_allow_html=True,
        )
        col_accueil.page_link("pages/1_Accueil.py", label="Accueil")
        col_equip.page_link("pages/2_Equipements.py", label="Équipements")
        col_hist.page_link("pages/3_Historique.py", label="Historique")
        col_cal.page_link("pages/6_Calendrier.py", label="Calendrier")
        col_stats.page_link("pages/7_Statistiques.py", label="Statistiques")

        if auth.has_role(user, "stock_manager"):
            with col_gestion:
                with st.popover("Gestion"):
                    st.page_link("pages/4_Validation.py", label="Validation des emprunts")
                    st.page_link("pages/5_Stock.py", label="Gestion du stock")
                    if auth.has_role(user, "admin"):
                        st.page_link("pages/8_Administration.py", label="Administration du site")

        with col_notif:
            with st.popover(f"🔔 {unread}" if unread else "🔔"):
                _render_notifications(conn, user)

        with col_user:
            with st.popover(f"{user['first_name']} {user['last_name']}"):
                st.caption(auth.ROLE_LABELS.get(user["role"], user["role"]))
                st.caption(user["email"])
                if st.button("Déconnexion", use_container_width=True):
                    st.logout()

    maintenance = settings.get_setting(conn, "maintenance_mode", "false")
    if maintenance.lower() == "true":
        message = settings.get_setting(conn, "maintenance_message") or "Maintenance en cours."
        st.warning(f"🚧 {message}")


def _render_notifications(conn, user):
    notifs = notifications.list_notifications(conn, user["id_user"], limit=10)
    if notifs.empty:
        st.caption("Aucune notification.")
        return

    if (notifs["is_read"] == 0).any():
        if st.button("Tout marquer comme lu", key="notif_mark_all", use_container_width=True):
            notifications.mark_all_as_read(conn, user["id_user"])
            st.rerun()

    for row in notifs.itertuples():
        col_texte, col_action = st.columns([5, 1])
        prefix = "🟠 " if not row.is_read else "⚪ "
        col_texte.markdown(f"{prefix}{row.message}")
        col_texte.caption(row.created_at.strftime("%d/%m/%Y %H:%M"))
        if not row.is_read:
            if col_action.button("✓", key=f"notif_read_{row.id_notification}", help="Marquer comme lu"):
                notifications.mark_as_read(conn, row.id_notification, user["id_user"])
                st.rerun()
        st.divider()
