import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from sqlalchemy import text

from auth import require_login
from db import get_connection
from navbar import render_navbar

st.set_page_config(page_title="IcamTrac - Emprunt", layout="wide")
render_navbar()
user = require_login()

conn = get_connection()

st.title("Demande d'emprunt")


def demander_emprunt(id_equipment, date_retour_prevue):
    date_emprunt = datetime.datetime.now(ZoneInfo("Europe/Paris"))

    if date_retour_prevue <= date_emprunt.date():
        st.warning("La date de retour doit être postérieure à aujourd'hui.")
        return

    with conn.session as s:
        s.execute(
            text(
                "INSERT INTO emprunt "
                "(date_emprunt, date_retour_prevue, statut_validation, id_user, id_equipment) "
                "VALUES (:date_emprunt, :date_retour_prevue, 'en_attente', :id_user, :id_equipment)"
            ),
            {
                "date_emprunt": date_emprunt,
                "date_retour_prevue": date_retour_prevue,
                "id_user": user["id_user"],
                "id_equipment": id_equipment,
            },
        )
        s.execute(
            text("UPDATE equipment SET disponibility = FALSE WHERE id_equipment = :id_equipment"),
            {"id_equipment": id_equipment},
        )
        s.commit()
    st.success("Demande d'emprunt envoyée.")
    st.rerun()


equipements = conn.query(
    "SELECT id_equipment, name, category, description FROM equipment "
    "WHERE disponibility = TRUE ORDER BY name",
    ttl=10,
)

st.subheader("Nouvelle demande")

if equipements.empty:
    st.info("Aucun équipement n'est actuellement disponible.")
else:
    recherche = st.text_input("Rechercher un équipement", placeholder="Nom ou catégorie…")

    equipements_filtres = equipements
    if recherche:
        masque = (
            equipements["name"].str.contains(recherche, case=False, na=False, regex=False)
            | equipements["category"].str.contains(recherche, case=False, na=False, regex=False)
        )
        equipements_filtres = equipements[masque]

    if equipements_filtres.empty:
        st.warning("Aucun équipement ne correspond à la recherche.")
    else:
        with st.form("form_emprunt"):
            options = dict(zip(equipements_filtres["id_equipment"], equipements_filtres["name"]))
            id_equipment = st.selectbox(
                "Équipement",
                options=list(options.keys()),
                format_func=lambda eid: options[eid],
            )
            date_retour_prevue = st.date_input(
                "Date de retour prévue",
                min_value=datetime.date.today() + datetime.timedelta(days=1),
            )
            submitted = st.form_submit_button("Envoyer la demande")
            if submitted:
                demander_emprunt(id_equipment, date_retour_prevue)

st.subheader("Mes emprunts en cours")

mes_emprunts = conn.query(
    """
    SELECT e.name AS equipement, em.date_emprunt, em.date_retour_prevue, em.statut_validation
    FROM emprunt em
    JOIN equipment e ON e.id_equipment = em.id_equipment
    WHERE em.id_user = :id_user AND em.date_retour_reelle IS NULL
    ORDER BY em.date_retour_prevue
    """,
    params={"id_user": user["id_user"]},
    ttl=0,
)

if mes_emprunts.empty:
    st.write("Vous n'avez aucun emprunt en cours.")
else:
    st.dataframe(mes_emprunts, use_container_width=True, hide_index=True)
