import streamlit as st
from sqlalchemy import text

import audit
import auth
import notifications
import settings
from db import get_connection
from navbar import render_navbar

st.set_page_config(page_title="IcamTrack - Administration", layout="wide")
user = auth.require_role("admin")
render_navbar(user)

conn = get_connection()

st.title("Administration du site")
st.caption(
    "Rôles des utilisateurs, journal d'activité et paramètres applicatifs. La gestion du nom "
    "de domaine, du certificat HTTPS et de l'infrastructure se fait en dehors de l'application "
    "(Caddy / Docker)."
)


def changer_role(id_cible: int, nouveau_role: str, nom_cible: str):
    with conn.session as s:
        ancien_role = s.execute(text("SELECT role FROM user WHERE id_user = :id"), {"id": id_cible}).scalar()
        if ancien_role == "admin" and nouveau_role != "admin":
            nb_admins = s.execute(
                text("SELECT COUNT(*) FROM user WHERE role = 'admin' AND is_active = TRUE")
            ).scalar()
            if nb_admins <= 1:
                s.rollback()
                st.error("Impossible : il doit rester au moins un administrateur actif.")
                return
        s.execute(text("UPDATE user SET role = :role WHERE id_user = :id"), {"role": nouveau_role, "id": id_cible})
        notifications.notify(
            s, id_cible, "changement_role", f"Votre rôle est désormais : {auth.ROLE_LABELS[nouveau_role]}."
        )
        audit.log_action(
            s, user["id_user"], "changement_role", f"utilisateur #{id_cible} ({nom_cible}) : {ancien_role} → {nouveau_role}"
        )
        s.commit()
    st.success("Rôle mis à jour.")
    st.rerun()


def changer_statut_actif(id_cible: int, nouveau_statut: bool, nom_cible: str):
    with conn.session as s:
        if not nouveau_statut:
            role_cible = s.execute(text("SELECT role FROM user WHERE id_user = :id"), {"id": id_cible}).scalar()
            if role_cible == "admin":
                nb_admins = s.execute(
                    text("SELECT COUNT(*) FROM user WHERE role = 'admin' AND is_active = TRUE")
                ).scalar()
                if nb_admins <= 1:
                    s.rollback()
                    st.error("Impossible : il doit rester au moins un administrateur actif.")
                    return
        s.execute(text("UPDATE user SET is_active = :actif WHERE id_user = :id"), {"actif": nouveau_statut, "id": id_cible})
        action = "activation_compte" if nouveau_statut else "desactivation_compte"
        audit.log_action(s, user["id_user"], action, f"utilisateur #{id_cible} ({nom_cible})")
        s.commit()
    st.rerun()


onglet_users, onglet_journal, onglet_parametres = st.tabs(
    ["Utilisateurs & rôles", "Journal d'activité", "Paramètres du site"]
)

with onglet_users:
    tous_users = conn.query("SELECT * FROM user ORDER BY last_name, first_name", ttl=5)

    st.subheader("Utilisateurs")
    affichage = tous_users.copy()
    affichage["Rôle"] = affichage["role"].map(auth.ROLE_LABELS)
    affichage["Statut"] = affichage["is_active"].map({True: "Actif", False: "Désactivé", 1: "Actif", 0: "Désactivé"})
    st.dataframe(
        affichage.rename(
            columns={
                "first_name": "Prénom", "last_name": "Nom", "email": "Email",
                "created_at": "Créé le", "last_login_at": "Dernière connexion",
            }
        )[["Prénom", "Nom", "Email", "Rôle", "Statut", "Créé le", "Dernière connexion"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Modifier un utilisateur")
    autres = tous_users[tous_users["id_user"] != user["id_user"]]
    if autres.empty:
        st.caption("Aucun autre utilisateur à gérer pour le moment.")
    else:
        options = dict(
            zip(autres["id_user"], (autres["first_name"] + " " + autres["last_name"] + " (" + autres["email"] + ")"))
        )
        id_cible = st.selectbox("Utilisateur", options=list(options.keys()), format_func=lambda i: options[i])
        ligne = autres[autres["id_user"] == id_cible].iloc[0]
        nom_cible = f"{ligne['first_name']} {ligne['last_name']}"

        col_role, col_actif = st.columns(2)
        with col_role:
            roles_disponibles = list(auth.ROLE_RANK.keys())
            nouveau_role = st.selectbox(
                "Rôle", options=roles_disponibles, format_func=lambda r: auth.ROLE_LABELS[r],
                index=roles_disponibles.index(ligne["role"]),
            )
            if st.button("Mettre à jour le rôle", type="primary"):
                changer_role(int(id_cible), nouveau_role, nom_cible)

        with col_actif:
            est_actif = bool(ligne["is_active"])
            st.write(f"Statut actuel : **{'Actif' if est_actif else 'Désactivé'}**")
            label_toggle = "Désactiver ce compte" if est_actif else "Réactiver ce compte"
            if st.button(label_toggle):
                changer_statut_actif(int(id_cible), not est_actif, nom_cible)

with onglet_journal:
    st.subheader("Journal d'activité")
    logs = audit.list_recent(conn, limit=300)
    if logs.empty:
        st.caption("Aucune activité enregistrée pour le moment.")
    else:
        logs = logs.copy()
        logs["first_name"] = logs["first_name"].fillna("")
        logs["last_name"] = logs["last_name"].fillna("")
        logs["Utilisateur"] = (logs["first_name"] + " " + logs["last_name"]).str.strip()
        logs.loc[logs["Utilisateur"] == "", "Utilisateur"] = "Système"

        recherche = st.text_input("Filtrer", placeholder="Action, détail ou utilisateur…")
        if recherche:
            masque = (
                logs["action"].str.contains(recherche, case=False, na=False)
                | logs["details"].str.contains(recherche, case=False, na=False)
                | logs["Utilisateur"].str.contains(recherche, case=False, na=False)
            )
            logs = logs[masque]

        st.dataframe(
            logs.rename(columns={"created_at": "Date", "action": "Action", "details": "Détails"})[
                ["Date", "Utilisateur", "Action", "Détails"]
            ],
            use_container_width=True,
            hide_index=True,
        )

with onglet_parametres:
    st.subheader("Paramètres du site")
    valeurs = settings.get_all(conn)
    with st.form("form_parametres"):
        site_name = st.text_input("Nom du site", value=valeurs.get("site_name", "IcamTrack"))
        contact_email = st.text_input("Email de contact", value=valeurs.get("contact_email", ""))
        maintenance_mode = st.checkbox(
            "Afficher un bandeau de maintenance à tous les utilisateurs",
            value=valeurs.get("maintenance_mode", "false") == "true",
        )
        maintenance_message = st.text_area("Message de maintenance", value=valeurs.get("maintenance_message", ""))
        save = st.form_submit_button("Enregistrer", type="primary")

    if save:
        with conn.session as s:
            settings.set_setting(s, "site_name", site_name.strip())
            settings.set_setting(s, "contact_email", contact_email.strip())
            settings.set_setting(s, "maintenance_mode", "true" if maintenance_mode else "false")
            settings.set_setting(s, "maintenance_message", maintenance_message.strip())
            audit.log_action(s, user["id_user"], "modification_parametres_site", "mise à jour des paramètres du site")
            s.commit()
        st.success("Paramètres enregistrés.")
        st.rerun()
