import streamlit as st

from auth import require_admin
from db import get_connection
from navbar import render_navbar

st.set_page_config(page_title="IcamTrac - Administration", layout="wide")
render_navbar()
require_admin()

conn = get_connection()

st.title("Administration")

onglet_tables, onglet_analyses = st.tabs(["Tables", "Analyses"])

with onglet_tables:
    st.subheader("Utilisateurs")
    st.dataframe(conn.query("SELECT * FROM user ORDER BY id_user", ttl=30), use_container_width=True)

    st.subheader("Équipements")
    st.dataframe(conn.query("SELECT * FROM equipment ORDER BY id_equipment", ttl=30), use_container_width=True)

    st.subheader("Emprunts")
    st.dataframe(conn.query("SELECT * FROM emprunt ORDER BY id_emprunt DESC", ttl=30), use_container_width=True)

with onglet_analyses:
    emprunts_en_cours = conn.query(
        "SELECT COUNT(*) AS n FROM emprunt WHERE date_retour_reelle IS NULL", ttl=30
    )["n"].iloc[0]
    total_equipements = conn.query("SELECT COUNT(*) AS n FROM equipment", ttl=30)["n"].iloc[0]
    equipements_disponibles = conn.query(
        "SELECT COUNT(*) AS n FROM equipment WHERE disponibility = TRUE", ttl=30
    )["n"].iloc[0]
    en_retard = conn.query("SELECT COUNT(*) AS n FROM v_retard", ttl=30)["n"].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Équipements", int(total_equipements))
    col2.metric("Dont disponibles", int(equipements_disponibles))
    col3.metric("Emprunts en cours", int(emprunts_en_cours))
    col4.metric("Emprunts en retard", int(en_retard))

    st.subheader("Équipements par catégorie")
    par_categorie = conn.query(
        "SELECT category, COUNT(*) AS nombre FROM equipment GROUP BY category ORDER BY nombre DESC",
        ttl=30,
    )
    st.bar_chart(par_categorie.set_index("category"))

    st.subheader("Équipements les plus empruntés")
    plus_empruntes = conn.query(
        """
        SELECT eq.name AS equipement, COUNT(*) AS nombre_emprunts
        FROM emprunt em
        JOIN equipment eq ON eq.id_equipment = em.id_equipment
        GROUP BY eq.name
        ORDER BY nombre_emprunts DESC
        LIMIT 10
        """,
        ttl=30,
    )
    st.bar_chart(plus_empruntes.set_index("equipement"))

    st.subheader("Emprunts en retard")
    retards = conn.query(
        """
        SELECT u.first_name, u.last_name, eq.name AS equipement,
               v.date_retour_prevue, v.jours_de_retard
        FROM v_retard v
        JOIN user u ON u.id_user = v.id_user
        JOIN equipment eq ON eq.id_equipment = v.id_equipment
        ORDER BY v.jours_de_retard DESC
        """,
        ttl=30,
    )
    if retards.empty:
        st.write("Aucun emprunt en retard.")
    else:
        st.dataframe(retards, use_container_width=True, hide_index=True)
