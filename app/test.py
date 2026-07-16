import streamlit as st
import datetime

def convert_date(text):
    return datetime.datetime.fromisoformat(text)

ajd = datetime.date.today()

conn = st.connection(
    "sql",
    dialect="mysql",
    driver="pymysql",
    host="mysql_db",
    database="SAP_bis",
    username="appuser",
    password="FLef289*33",
    port=3306
)
def demande_emprunt(id_user,id_equip,date_retour_prev):
    if date_retour_prev < ajd :
        st.warning("Entrer une date de retour > aujourd'hui")
        exit
    else:
        conn.query("insert into emprunt(ajd,date_retour_prev,NULL,id_user,id_equip)")

def affichage_tables():

    st.write("Liste des équipements")
    df = conn.query("SELECT * FROM equipment")
    st.dataframe(df)

    st.write("Liste des utilisateurs")
    list_user = conn.query("SELECT * FROM user")
    st.dataframe(list_user)

    st.write("Liste des emprunts")
    list_emprunt = conn.query("SELECT * FROM emprunt")
    st.dataframe(list_emprunt)

def add_new_user(vlast_name, vfirst_name, vemail, vuser_status):
    conn.query("INSERT INTO user (last_name, first_name, email, user_status)" \
    "values(vlast_name, vfirst_name, vemail, vuser_status)")

with st.form("my_form"):
    st.write("Add new user form")
    admin_checkbox = st.checkbox("Admin ?")
    st.write("Name")


    # Every form must have a submit button.
    submitted = st.form_submit_button("add emprunt")
    if submitted:
        demande_emprunt(1,2,'2026-08-08')
        st.write("New user not added you bitch :)")


affichage_tables()
