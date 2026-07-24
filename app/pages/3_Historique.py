import streamlit as st
from sqlalchemy import text

import audit
import auth
import notifications
import theme
from db import get_connection
from navbar import render_navbar

st.set_page_config(page_title="IcamTrack - Historique", layout="wide")
user = auth.require_login()
render_navbar(user)

conn = get_connection()

st.title("Historique de mes emprunts")


def annuler_demande(id_emprunt):
    with conn.session as s:
        result = s.execute(
            text(
                "UPDATE emprunt SET statut_validation = 'annule' "
                "WHERE id_emprunt = :id AND id_user = :uid AND statut_validation = 'en_attente'"
            ),
            {"id": id_emprunt, "uid": user["id_user"]},
        )
        annule = result.rowcount > 0
        if annule:
            audit.log_action(s, user["id_user"], "annulation_emprunt", f"emprunt #{id_emprunt}")
        s.commit()
    if annule:
        st.success("Demande annulée.")
    else:
        st.warning("Cette demande a déjà été traitée entre-temps.")
    st.rerun()


def declarer_retour(id_emprunt, equip_name):
    with conn.session as s:
        result = s.execute(
            text(
                "UPDATE emprunt SET date_retour_reelle = CURRENT_TIMESTAMP "
                "WHERE id_emprunt = :id AND id_user = :uid "
                "AND statut_validation = 'valide' AND date_retour_reelle IS NULL"
            ),
            {"id": id_emprunt, "uid": user["id_user"]},
        )
        marque = result.rowcount > 0
        if marque:
            notifications.notify_validators(
                s,
                "retour_anticipe",
                f"{user['first_name']} {user['last_name']} a signalé le retour de {equip_name}.",
                id_emprunt=id_emprunt,
                exclude_id_user=user["id_user"],
            )
            audit.log_action(s, user["id_user"], "retour_materiel_self", f"emprunt #{id_emprunt} ({equip_name})")
        s.commit()
    if marque:
        st.success("Retour enregistré. Pensez à restituer le matériel à un gestionnaire de stock.")
    else:
        st.warning("Cet emprunt ne peut plus être marqué comme rendu (déjà traité entre-temps).")
    st.rerun()


historique = conn.query(
    """
    SELECT em.id_emprunt, e.name AS equipement, em.quantity, em.date_demande,
           em.date_debut_prevue, em.date_retour_prevue, em.date_retour_reelle,
           em.statut_validation, em.commentaire_validation
    FROM emprunt em
    JOIN equipment e ON e.id_equipment = em.id_equipment
    WHERE em.id_user = :id_user
    ORDER BY em.date_demande DESC
    """,
    params={"id_user": user["id_user"]},
    ttl=5,
)

if historique.empty:
    st.info("Vous n'avez encore fait aucune demande d'emprunt.")
    st.stop()

statuts = st.multiselect(
    "Filtrer par statut",
    options=list(theme.STATUS_LABELS.keys()),
    default=list(theme.STATUS_LABELS.keys()),
    format_func=lambda s: theme.STATUS_LABELS[s],
)
filtre = historique[historique["statut_validation"].isin(statuts)].copy()

en_attente = filtre[filtre["statut_validation"] == "en_attente"]
if not en_attente.empty:
    st.subheader("Demandes en attente")
    st.caption("Vous pouvez annuler une demande tant qu'elle n'a pas été traitée par un gestionnaire.")
    for row in en_attente.itertuples():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(
                f"**{row.equipement}** × {row.quantity} — du {row.date_debut_prevue:%d/%m/%Y} "
                f"au {row.date_retour_prevue:%d/%m/%Y}"
            )
            if c2.button("Annuler", key=f"annuler_{row.id_emprunt}", use_container_width=True):
                annuler_demande(row.id_emprunt)

en_cours = filtre[(filtre["statut_validation"] == "valide") & (filtre["date_retour_reelle"].isna())]
if not en_cours.empty:
    st.subheader("Emprunts en cours")
    st.caption("Vous pouvez signaler vous-même un retour, même avant la date de retour prévue.")
    for row in en_cours.itertuples():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(
                f"**{row.equipement}** × {row.quantity} — retour prévu le {row.date_retour_prevue:%d/%m/%Y}"
            )
            if c2.button("J'ai rendu ce matériel", key=f"rendre_{row.id_emprunt}", use_container_width=True):
                declarer_retour(row.id_emprunt, row.equipement)

st.subheader("Détail")
affichage = filtre.copy()
affichage["Statut"] = affichage["statut_validation"].map(theme.STATUS_LABELS)
affichage = affichage.rename(
    columns={
        "equipement": "Équipement",
        "quantity": "Quantité",
        "date_demande": "Demandé le",
        "date_debut_prevue": "Début prévu",
        "date_retour_prevue": "Retour prévu",
        "date_retour_reelle": "Retourné le",
        "commentaire_validation": "Commentaire",
    }
)
st.dataframe(
    affichage[
        ["Équipement", "Quantité", "Demandé le", "Début prévu", "Retour prévu",
         "Retourné le", "Statut", "Commentaire"]
    ],
    use_container_width=True,
    hide_index=True,
)
