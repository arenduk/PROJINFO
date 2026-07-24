import datetime

import streamlit as st
from sqlalchemy import text

import audit
import auth
import availability
import notifications
from db import get_connection
from navbar import render_navbar


def _as_date(value):
    """Normalise une valeur DATE renvoyee par la requete (parfois un
    datetime.date, parfois un pandas.Timestamp selon le driver) en
    datetime.date pur, pour pouvoir la soustraire a datetime.date.today() :
    Python refuse de melanger date et datetime dans une soustraction."""
    return value.date() if isinstance(value, datetime.datetime) else value

st.set_page_config(page_title="IcamTrack - Validation", layout="wide", page_icon="🧰")
user = auth.require_role("stock_manager")
render_navbar(user)

conn = get_connection()

st.title("Validation des emprunts")


def traiter_demande(id_emprunt, id_equipment, quantity, date_debut, date_fin, id_demandeur, equip_name, decision, commentaire):
    with conn.session as s:
        if decision == "valide":
            dispo = availability.get_available_quantity(
                s, id_equipment, date_debut, date_fin, exclude_emprunt_id=id_emprunt, for_update=True
            )
            if dispo is None or dispo < quantity:
                s.rollback()
                st.error("Stock insuffisant pour valider : la disponibilité a changé depuis la demande.")
                return
        s.execute(
            text(
                "UPDATE emprunt SET statut_validation = :decision, commentaire_validation = :commentaire, "
                "id_validateur = :validateur, date_validation = CURRENT_TIMESTAMP "
                "WHERE id_emprunt = :id AND statut_validation = 'en_attente'"
            ),
            {
                "decision": decision,
                "commentaire": commentaire or None,
                "validateur": user["id_user"],
                "id": id_emprunt,
            },
        )
        verbe = "validé" if decision == "valide" else "refusé"
        message = f"Votre emprunt de {equip_name} a été {verbe}."
        if commentaire:
            message += f" Commentaire : {commentaire}"
        notifications.notify(s, id_demandeur, f"emprunt_{decision}", message, id_emprunt=id_emprunt)
        audit.log_action(s, user["id_user"], f"{decision}_emprunt", f"emprunt #{id_emprunt} ({equip_name})")
        s.commit()
    st.success("Décision enregistrée.")
    st.rerun()


def marquer_retourne(id_emprunt, equip_name):
    with conn.session as s:
        s.execute(
            text("UPDATE emprunt SET date_retour_reelle = CURRENT_TIMESTAMP WHERE id_emprunt = :id"),
            {"id": id_emprunt},
        )
        audit.log_action(s, user["id_user"], "retour_materiel", f"emprunt #{id_emprunt} ({equip_name})")
        s.commit()
    st.success("Retour enregistré.")
    st.rerun()


onglet_demandes, onglet_retours = st.tabs(["Demandes en attente", "Emprunts en cours (retours)"])

with onglet_demandes:
    demandes = conn.query(
        """
        SELECT em.id_emprunt, em.id_equipment, em.quantity, em.date_debut_prevue, em.date_retour_prevue,
               em.date_demande, e.name AS equipement, u.id_user, u.first_name, u.last_name, u.email
        FROM emprunt em
        JOIN equipment e ON e.id_equipment = em.id_equipment
        JOIN user u ON u.id_user = em.id_user
        WHERE em.statut_validation = 'en_attente'
        ORDER BY em.date_demande
        """,
        ttl=5,
    )

    if demandes.empty:
        st.info("Aucune demande en attente.")
    else:
        for row in demandes.itertuples():
            with st.container(border=True):
                st.markdown(
                    f"**{row.equipement}** × {row.quantity} — demandé par {row.first_name} {row.last_name} "
                    f"({row.email})  \n"
                    f"Période souhaitée : du {row.date_debut_prevue:%d/%m/%Y} au {row.date_retour_prevue:%d/%m/%Y} "
                    f"— demande soumise le {row.date_demande:%d/%m/%Y %H:%M}"
                )
                commentaire = st.text_input(
                    "Commentaire (optionnel)", key=f"commentaire_{row.id_emprunt}"
                )
                bcol1, bcol2, _ = st.columns([1, 1, 4])
                if bcol1.button("Valider", key=f"valider_{row.id_emprunt}", type="primary"):
                    traiter_demande(
                        row.id_emprunt, row.id_equipment, row.quantity,
                        row.date_debut_prevue, row.date_retour_prevue,
                        row.id_user, row.equipement, "valide", commentaire,
                    )
                if bcol2.button("Refuser", key=f"refuser_{row.id_emprunt}"):
                    traiter_demande(
                        row.id_emprunt, row.id_equipment, row.quantity,
                        row.date_debut_prevue, row.date_retour_prevue,
                        row.id_user, row.equipement, "refuse", commentaire,
                    )

with onglet_retours:
    en_cours = conn.query(
        """
        SELECT em.id_emprunt, em.quantity, em.date_debut_prevue, em.date_retour_prevue,
               e.name AS equipement, u.first_name, u.last_name
        FROM emprunt em
        JOIN equipment e ON e.id_equipment = em.id_equipment
        JOIN user u ON u.id_user = em.id_user
        WHERE em.statut_validation = 'valide' AND em.date_retour_reelle IS NULL
        ORDER BY em.date_retour_prevue
        """,
        ttl=5,
    )

    if en_cours.empty:
        st.info("Aucun emprunt en cours.")
    else:
        aujourdhui = datetime.date.today()
        for row in en_cours.itertuples():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                retard = (aujourdhui - _as_date(row.date_retour_prevue)).days
                ligne = (
                    f"**{row.equipement}** × {row.quantity} — emprunté par {row.first_name} {row.last_name}  \n"
                    f"Retour prévu le {row.date_retour_prevue:%d/%m/%Y}"
                )
                if retard > 0:
                    ligne += f"  \n:red[⚠️ En retard de {retard} jour(s)]"
                c1.markdown(ligne)
                if c2.button("Marquer rendu", key=f"retour_{row.id_emprunt}", use_container_width=True):
                    marquer_retourne(row.id_emprunt, row.equipement)
