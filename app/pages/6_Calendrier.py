import calendar
import datetime
import html

import streamlit as st

import auth
import theme
from db import get_connection
from navbar import render_navbar

st.set_page_config(page_title="IcamTrack - Calendrier", layout="wide")
user = auth.require_login()
render_navbar(user)

conn = get_connection()

st.title("Mon calendrier d'emprunts")

NOMS_MOIS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]
NOMS_JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

today = datetime.date.today()
st.session_state.setdefault("calendrier_annee", today.year)
st.session_state.setdefault("calendrier_mois", today.month)
st.session_state.setdefault("calendrier_jour_selectionne", None)

col_prev, col_titre, col_next = st.columns([1, 3, 1])
if col_prev.button("<- Mois précédent"):
    mois, annee = st.session_state["calendrier_mois"] - 1, st.session_state["calendrier_annee"]
    if mois < 1:
        mois, annee = 12, annee - 1
    st.session_state["calendrier_mois"], st.session_state["calendrier_annee"] = mois, annee
    st.rerun()
if col_next.button("Mois suivant ->"):
    mois, annee = st.session_state["calendrier_mois"] + 1, st.session_state["calendrier_annee"]
    if mois > 12:
        mois, annee = 1, annee + 1
    st.session_state["calendrier_mois"], st.session_state["calendrier_annee"] = mois, annee
    st.rerun()

annee = st.session_state["calendrier_annee"]
mois = st.session_state["calendrier_mois"]
col_titre.markdown(f"### {NOMS_MOIS[mois - 1]} {annee}")

premier_jour = datetime.date(annee, mois, 1)
dernier_jour = datetime.date(annee, mois, calendar.monthrange(annee, mois)[1])

mes_emprunts = conn.query(
    """
    SELECT em.id_emprunt, em.date_debut_prevue, em.date_retour_prevue, em.statut_validation,
           em.quantity, e.name AS equipement
    FROM emprunt em
    JOIN equipment e ON e.id_equipment = em.id_equipment
    WHERE em.id_user = :id_user
      AND em.statut_validation IN ('en_attente', 'valide')
      AND em.date_debut_prevue <= :dernier_jour
      AND em.date_retour_prevue >= :premier_jour
    """,
    params={"id_user": user["id_user"], "premier_jour": premier_jour, "dernier_jour": dernier_jour},
    ttl=5,
)

# Normalise en datetime.date pur (le driver peut renvoyer un pandas.Timestamp
# pour une colonne DATE) : Python refuse de comparer date et datetime entre eux.
for _col in ("date_debut_prevue", "date_retour_prevue"):
    mes_emprunts[_col] = mes_emprunts[_col].apply(
        lambda v: v.date() if isinstance(v, datetime.datetime) else v
    )


def emprunts_du_jour(jour):
    return mes_emprunts[
        (mes_emprunts["date_debut_prevue"] <= jour) & (mes_emprunts["date_retour_prevue"] >= jour)
    ]


header_cols = st.columns(7)
for c, nom in zip(header_cols, NOMS_JOURS):
    c.markdown(f"**{nom}**")

for semaine in calendar.monthcalendar(annee, mois):
    cols = st.columns(7)
    for c, jour_num in zip(cols, semaine):
        if jour_num == 0:
            c.write("")
            continue
        jour = datetime.date(annee, mois, jour_num)
        du_jour = emprunts_du_jour(jour)
        badges = ""
        if (du_jour["statut_validation"] == "en_attente").any():
            badges += " 🟠"
        if (du_jour["statut_validation"] == "valide").any():
            badges += " 🟢"
        type_bouton = "primary" if jour == today else "secondary"
        if c.button(f"{jour_num}{badges}", key=f"jour_{jour.isoformat()}", use_container_width=True, type=type_bouton):
            st.session_state["calendrier_jour_selectionne"] = jour.isoformat()
            st.rerun()

st.caption("🟠 en attente de validation · 🟢 validé")
st.divider()

jour_selectionne = st.session_state["calendrier_jour_selectionne"]
if jour_selectionne:
    jour = datetime.date.fromisoformat(jour_selectionne)
    st.subheader(f"Emprunts du {jour:%d/%m/%Y}")
    du_jour = emprunts_du_jour(jour)
    if du_jour.empty:
        st.caption("Aucun emprunt ce jour-là.")
    else:
        for row in du_jour.itertuples():
            st.markdown(
                f"{theme.status_badge(row.statut_validation)}&nbsp;&nbsp;**{html.escape(row.equipement)}** × "
                f"{row.quantity} (du {row.date_debut_prevue:%d/%m/%Y} au {row.date_retour_prevue:%d/%m/%Y})",
                unsafe_allow_html=True,
            )
else:
    st.caption("Cliquez sur un jour pour voir le détail des emprunts.")
