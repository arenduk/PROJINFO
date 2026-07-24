import pandas as pd
import streamlit as st

import auth
import theme
from db import get_connection
from navbar import render_navbar

st.set_page_config(page_title="IcamTrack - Statistiques", layout="wide", page_icon="🧰")
user = auth.require_login()
render_navbar(user)

conn = get_connection()

st.title("Statistiques")

total_actifs = int(conn.query("SELECT COUNT(*) AS n FROM equipment WHERE is_active = TRUE", ttl=30)["n"].iloc[0])
quantite_totale = int(
    conn.query("SELECT COALESCE(SUM(quantity_total), 0) AS n FROM equipment WHERE is_active = TRUE", ttl=30)["n"].iloc[0]
)
emprunts_en_cours = int(
    conn.query(
        "SELECT COUNT(*) AS n FROM emprunt WHERE statut_validation = 'valide' AND date_retour_reelle IS NULL",
        ttl=30,
    )["n"].iloc[0]
)
en_retard = int(conn.query("SELECT COUNT(*) AS n FROM v_retard", ttl=30)["n"].iloc[0])
duree_moyenne = conn.query(
    """
    SELECT AVG(DATEDIFF(date_retour_reelle, date_debut_prevue)) AS moyenne
    FROM emprunt
    WHERE statut_validation = 'valide' AND date_retour_reelle IS NOT NULL
    """,
    ttl=30,
)["moyenne"].iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Équipements référencés", total_actifs)
c2.metric("Unités en stock", quantite_totale)
c3.metric("Emprunts en cours", emprunts_en_cours)
c4.metric("Emprunts en retard", en_retard)
c5.metric("Durée moyenne d'un emprunt", "—" if pd.isna(duree_moyenne) else f"{duree_moyenne:.1f} j")

col_gauche, col_droite = st.columns(2)

with col_gauche:
    st.subheader("Équipements par catégorie")
    par_categorie = conn.query(
        """
        SELECT COALESCE(category, 'Sans catégorie') AS categorie, COUNT(*) AS nombre
        FROM equipment
        WHERE is_active = TRUE
        GROUP BY categorie
        ORDER BY nombre DESC
        """,
        ttl=30,
    )
    if par_categorie.empty:
        st.caption("Aucun équipement.")
    else:
        st.bar_chart(par_categorie.set_index("categorie"), color=theme.SECONDARY)

with col_droite:
    st.subheader("Équipements les plus empruntés")
    plus_empruntes = conn.query(
        """
        SELECT e.name AS equipement, COUNT(*) AS nombre
        FROM emprunt em
        JOIN equipment e ON e.id_equipment = em.id_equipment
        WHERE em.statut_validation = 'valide'
        GROUP BY e.name
        ORDER BY nombre DESC
        LIMIT 10
        """,
        ttl=30,
    )
    if plus_empruntes.empty:
        st.caption("Aucun emprunt validé pour le moment.")
    else:
        st.bar_chart(plus_empruntes.set_index("equipement"), color=theme.PRIMARY)

st.subheader("Demandes par mois")
par_mois_statut = conn.query(
    """
    SELECT DATE_FORMAT(date_demande, '%Y-%m') AS mois, statut_validation, COUNT(*) AS nombre
    FROM emprunt
    GROUP BY mois, statut_validation
    ORDER BY mois
    """,
    ttl=30,
)
if par_mois_statut.empty:
    st.caption("Pas encore assez de données pour ce graphique.")
else:
    pivot = par_mois_statut.pivot(index="mois", columns="statut_validation", values="nombre")
    pivot = pivot.reindex(columns=theme.STATUS_CHART_ORDER, fill_value=0).fillna(0)
    couleurs = [theme.STATUS_COLORS[s] for s in theme.STATUS_CHART_ORDER]
    pivot = pivot.rename(columns=theme.STATUS_LABELS)
    st.bar_chart(pivot, color=couleurs)

if auth.has_role(user, "stock_manager"):
    st.subheader("Détail des emprunts en retard")
    retards = conn.query(
        """
        SELECT u.first_name, u.last_name, eq.name AS equipement, v.quantity,
               v.date_retour_prevue, v.jours_de_retard
        FROM v_retard v
        JOIN user u ON u.id_user = v.id_user
        JOIN equipment eq ON eq.id_equipment = v.id_equipment
        ORDER BY v.jours_de_retard DESC
        """,
        ttl=30,
    )
    if retards.empty:
        st.caption("Aucun emprunt en retard. 🎉")
    else:
        st.dataframe(
            retards.rename(
                columns={
                    "first_name": "Prénom", "last_name": "Nom", "equipement": "Équipement",
                    "quantity": "Quantité", "date_retour_prevue": "Retour prévu",
                    "jours_de_retard": "Jours de retard",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
