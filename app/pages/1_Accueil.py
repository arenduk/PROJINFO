import pandas as pd
import streamlit as st

import auth
import notifications
import theme
from db import get_connection
from navbar import render_navbar

st.set_page_config(page_title="IcamTrack - Accueil", layout="wide")
user = auth.require_login()
render_navbar(user)

conn = get_connection()

theme.render_hero(
    f"Bonjour {user['first_name']}",
    "Retrouvez ici un aperçu de vos emprunts, vos dernières notifications et un accès "
    "rapide aux principales fonctionnalités d'IcamTrack.",
)

mes_stats = conn.query(
    """
    SELECT
        COALESCE(SUM(CASE WHEN statut_validation = 'valide' AND date_retour_reelle IS NULL THEN 1 ELSE 0 END), 0) AS en_cours,
        COALESCE(SUM(CASE WHEN statut_validation = 'en_attente' THEN 1 ELSE 0 END), 0) AS en_attente,
        MIN(CASE WHEN statut_validation = 'valide' AND date_retour_reelle IS NULL THEN date_retour_prevue END) AS prochain_retour
    FROM emprunt
    WHERE id_user = :id_user
    """,
    params={"id_user": user["id_user"]},
    ttl=5,
).iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Emprunts en cours", int(mes_stats["en_cours"]))
col2.metric("Demandes en attente", int(mes_stats["en_attente"]))
prochain_retour = mes_stats["prochain_retour"]
col3.metric(
    "Prochain retour prévu",
    "—" if pd.isna(prochain_retour) else prochain_retour.strftime("%d/%m/%Y"),
)
col4.metric("Notifications non lues", notifications.count_unread(conn, user["id_user"]))

if auth.has_role(user, "stock_manager"):
    st.subheader("Vue gestionnaire")
    demandes_en_attente = conn.query(
        "SELECT COUNT(*) AS n FROM emprunt WHERE statut_validation = 'en_attente'", ttl=5
    )["n"].iloc[0]
    en_retard = conn.query("SELECT COUNT(*) AS n FROM v_retard", ttl=5)["n"].iloc[0]
    gcol1, gcol2 = st.columns(2)
    gcol1.metric("Demandes de tous les utilisateurs en attente", int(demandes_en_attente))
    gcol2.metric("Emprunts en retard", int(en_retard))
    if int(demandes_en_attente) > 0:
        st.page_link("pages/4_Validation.py", label="➜ Traiter les demandes en attente")

st.subheader("Accès rapide")
qcol1, qcol2, qcol3 = st.columns(3)
with qcol1:
    with st.container(border=True):
        st.markdown("**Emprunter du matériel**")
        st.caption("Parcourir le matériel disponible et faire une demande.")
        st.page_link("pages/2_Equipements.py", label="Voir les équipements ➜")
with qcol2:
    with st.container(border=True):
        st.markdown("**Mon historique**")
        st.caption("Suivre mes demandes passées et en cours.")
        st.page_link("pages/3_Historique.py", label="Voir l'historique ➜")
with qcol3:
    with st.container(border=True):
        st.markdown("**Mon calendrier**")
        st.caption("Visualiser mes emprunts sur un calendrier mensuel.")
        st.page_link("pages/6_Calendrier.py", label="Voir le calendrier ➜")

st.subheader("Dernières notifications")
recentes = notifications.list_notifications(conn, user["id_user"], limit=5)
if recentes.empty:
    st.caption("Aucune notification pour le moment.")
else:
    for row in recentes.itertuples():
        prefix = "🟠" if not row.is_read else "⚪"
        st.write(f"{prefix} {row.message}  \n:gray[{row.created_at.strftime('%d/%m/%Y %H:%M')}]")
