import datetime

import streamlit as st
from sqlalchemy import text

import audit
import auth
import availability
import notifications
from db import get_connection
from navbar import render_navbar

st.set_page_config(page_title="IcamTrack - Équipements", layout="wide", page_icon="🧰")
user = auth.require_login()
render_navbar(user)

conn = get_connection()

st.title("Matériel disponible")
st.caption("Choisissez une période pour voir le matériel réellement disponible sur ces dates.")

col_debut, col_fin, col_recherche = st.columns([1, 1, 2])
date_debut = col_debut.date_input("Du", value=datetime.date.today(), min_value=datetime.date.today())
date_fin = col_fin.date_input(
    "Au", value=datetime.date.today() + datetime.timedelta(days=7), min_value=date_debut
)
recherche = col_recherche.text_input("Rechercher", placeholder="Nom ou catégorie…")

equipements = availability.list_availability(conn, date_debut, date_fin)

if recherche:
    masque = (
        equipements["name"].str.contains(recherche, case=False, na=False, regex=False)
        | equipements["category"].str.contains(recherche, case=False, na=False, regex=False)
    )
    equipements = equipements[masque]

if equipements.empty:
    st.info("Aucun équipement ne correspond à cette recherche.")
else:
    st.dataframe(
        equipements[["name", "category", "description", "quantite_disponible", "quantity_total"]].rename(
            columns={
                "name": "Nom",
                "category": "Catégorie",
                "description": "Description",
                "quantite_disponible": "Disponible sur la période",
                "quantity_total": "Quantité totale",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Nouvelle demande")

disponibles = equipements[equipements["quantite_disponible"] > 0]

if disponibles.empty:
    st.warning("Aucun équipement n'est disponible en quantité suffisante sur cette période.")
else:
    with st.form("form_demande"):
        options = dict(zip(disponibles["id_equipment"], disponibles["name"]))
        id_equipment = st.selectbox(
            "Équipement", options=list(options.keys()), format_func=lambda eid: options[eid]
        )
        max_dispo = int(disponibles.loc[disponibles["id_equipment"] == id_equipment, "quantite_disponible"].iloc[0])
        quantity = st.number_input("Quantité", min_value=1, max_value=max_dispo, value=1, step=1)
        st.caption(f"Période sélectionnée : du {date_debut:%d/%m/%Y} au {date_fin:%d/%m/%Y}.")
        submitted = st.form_submit_button("Envoyer la demande", type="primary")

    if submitted:
        with conn.session as s:
            dispo = availability.get_available_quantity(s, id_equipment, date_debut, date_fin, for_update=True)
            if dispo is None or dispo < quantity:
                s.rollback()
                st.error("Le stock disponible a changé entre-temps, veuillez réessayer.")
            else:
                result = s.execute(
                    text(
                        "INSERT INTO emprunt (id_user, id_equipment, quantity, date_debut_prevue, date_retour_prevue) "
                        "VALUES (:id_user, :id_equipment, :quantity, :date_debut, :date_fin)"
                    ),
                    {
                        "id_user": user["id_user"],
                        "id_equipment": id_equipment,
                        "quantity": quantity,
                        "date_debut": date_debut,
                        "date_fin": date_fin,
                    },
                )
                id_emprunt = result.lastrowid
                nom_equipement = options[id_equipment]
                notifications.notify_validators(
                    s,
                    "nouvelle_demande",
                    f"{user['first_name']} {user['last_name']} demande {quantity}x {nom_equipement} "
                    f"du {date_debut:%d/%m/%Y} au {date_fin:%d/%m/%Y}.",
                    id_emprunt=id_emprunt,
                    exclude_id_user=user["id_user"],
                )
                audit.log_action(
                    s, user["id_user"], "demande_emprunt",
                    f"équipement #{id_equipment} ({nom_equipement}), quantité {quantity}",
                )
                s.commit()
                st.success("Demande envoyée. Vous serez notifié une fois qu'elle aura été traitée.")
                st.rerun()

st.subheader("Mes demandes en cours")
mes_demandes = conn.query(
    """
    SELECT e.name AS equipement, em.quantity, em.date_debut_prevue, em.date_retour_prevue, em.statut_validation
    FROM emprunt em
    JOIN equipment e ON e.id_equipment = em.id_equipment
    WHERE em.id_user = :id_user AND em.date_retour_reelle IS NULL AND em.statut_validation != 'annule'
    ORDER BY em.date_debut_prevue
    """,
    params={"id_user": user["id_user"]},
    ttl=5,
)
if mes_demandes.empty:
    st.caption("Vous n'avez aucune demande en cours.")
else:
    st.dataframe(mes_demandes, use_container_width=True, hide_index=True)
