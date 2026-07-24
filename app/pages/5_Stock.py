import streamlit as st
from sqlalchemy import text

import audit
import auth
from db import get_connection
from navbar import render_navbar

st.set_page_config(page_title="IcamTrack - Stock", layout="wide")
user = auth.require_role("stock_manager")
render_navbar(user)

conn = get_connection()

st.title("Gestion du stock")

ETATS = ["OK", "NOK", "perdu"]

tout = conn.query("SELECT * FROM equipment ORDER BY is_active DESC, name", ttl=5)
categories_existantes = sorted({c for c in tout["category"].dropna().tolist() if c})
NOUVELLE_CATEGORIE = "+ Nouvelle catégorie"

st.subheader("Catalogue")
if tout.empty:
    st.caption("Aucun équipement dans le catalogue pour le moment.")
else:
    affichage = tout.copy()
    affichage["Statut"] = affichage["is_active"].map({True: "Actif", False: "Retiré", 1: "Actif", 0: "Retiré"})
    st.dataframe(
        affichage.rename(
            columns={
                "name": "Nom", "category": "Catégorie", "description": "Description",
                "quantity_total": "Quantité totale", "etat": "État",
            }
        )[["Nom", "Catégorie", "Description", "Quantité totale", "État", "Statut"]],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Ajouter un équipement")
cat_choix_ajout = st.selectbox(
    "Catégorie", options=categories_existantes + [NOUVELLE_CATEGORIE], key="cat_choix_ajout"
)
if cat_choix_ajout == NOUVELLE_CATEGORIE:
    categorie_ajout = st.text_input("Nom de la nouvelle catégorie", key="cat_libre_ajout")
else:
    categorie_ajout = cat_choix_ajout

with st.form("form_ajout", clear_on_submit=True):
    name = st.text_input("Nom")
    description = st.text_area("Description")
    quantity_total = st.number_input("Quantité totale", min_value=0, value=1, step=1)
    etat = st.selectbox("État", options=ETATS)
    submitted = st.form_submit_button("Ajouter", type="primary")

if submitted:
    if not name.strip():
        st.error("Le nom est obligatoire.")
    else:
        with conn.session as s:
            s.execute(
                text(
                    "INSERT INTO equipment (name, description, category, quantity_total, etat) "
                    "VALUES (:n, :d, :c, :q, :e)"
                ),
                {
                    "n": name.strip(),
                    "d": description.strip() or None,
                    "c": (categorie_ajout or "").strip() or None,
                    "q": quantity_total,
                    "e": etat,
                },
            )
            audit.log_action(s, user["id_user"], "creation_equipement", name.strip())
            s.commit()
        st.success(f"Équipement « {name} » ajouté.")
        st.rerun()

st.subheader("Modifier un équipement")
if tout.empty:
    st.caption("Rien à modifier pour le moment.")
else:
    options_ids = dict(zip(tout["id_equipment"], tout["name"]))
    id_selection = st.selectbox(
        "Équipement à modifier", options=list(options_ids.keys()),
        format_func=lambda i: options_ids[i], key="select_edit",
    )
    ligne = tout[tout["id_equipment"] == id_selection].iloc[0]

    options_categories_edit = categories_existantes + [NOUVELLE_CATEGORIE]
    index_categorie = (
        options_categories_edit.index(ligne["category"])
        if ligne["category"] in categories_existantes
        else len(categories_existantes)
    )
    cat_choix_edit = st.selectbox(
        "Catégorie", options=options_categories_edit, index=index_categorie, key="cat_choix_edit"
    )
    if cat_choix_edit == NOUVELLE_CATEGORIE:
        categorie_edit = st.text_input(
            "Nom de la nouvelle catégorie",
            value="" if ligne["category"] in categories_existantes else (ligne["category"] or ""),
            key="cat_libre_edit",
        )
    else:
        categorie_edit = cat_choix_edit

    with st.form("form_edit"):
        name_edit = st.text_input("Nom", value=ligne["name"])
        description_edit = st.text_area("Description", value=ligne["description"] or "")
        quantity_edit = st.number_input(
            "Quantité totale", min_value=0, value=int(ligne["quantity_total"]), step=1
        )
        etat_edit = st.selectbox("État", options=ETATS, index=ETATS.index(ligne["etat"]))
        save = st.form_submit_button("Enregistrer les modifications", type="primary")

    if save:
        with conn.session as s:
            s.execute(
                text(
                    "UPDATE equipment SET name = :n, description = :d, category = :c, "
                    "quantity_total = :q, etat = :e WHERE id_equipment = :id"
                ),
                {
                    "n": name_edit.strip(),
                    "d": description_edit.strip() or None,
                    "c": (categorie_edit or "").strip() or None,
                    "q": quantity_edit,
                    "e": etat_edit,
                    "id": int(id_selection),
                },
            )
            audit.log_action(s, user["id_user"], "modification_equipement", f"#{id_selection} ({name_edit})")
            s.commit()
        st.success("Modifications enregistrées.")
        st.rerun()

    st.divider()
    est_actif = bool(ligne["is_active"])
    label_toggle = "🗑️ Retirer cet équipement du catalogue" if est_actif else "♻️ Réactiver cet équipement"
    st.caption(
        "Un équipement retiré n'apparaît plus dans le catalogue emprunteur, mais son historique est conservé."
    )
    if st.button(label_toggle):
        with conn.session as s:
            s.execute(
                text("UPDATE equipment SET is_active = :actif WHERE id_equipment = :id"),
                {"actif": not est_actif, "id": int(id_selection)},
            )
            action = "desactivation_equipement" if est_actif else "reactivation_equipement"
            audit.log_action(s, user["id_user"], action, f"#{id_selection} ({ligne['name']})")
            s.commit()
        st.rerun()
