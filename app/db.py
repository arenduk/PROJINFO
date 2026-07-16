"""Connexion centralisee a la base de donnees MySQL."""

import os

import streamlit as st


@st.cache_resource
def get_connection():
    """Retourne la connexion SQL partagee, configuree via les variables
    d'environnement fournies par docker-compose (DB_HOST, DB_PORT, ...)."""
    return st.connection(
        "sql",
        type="sql",
        dialect="mysql",
        driver="pymysql",
        host=os.environ.get("DB_HOST", "mysql_db"),
        port=int(os.environ.get("DB_PORT", "3306")),
        database=os.environ.get("DB_NAME", "SAP_bis"),
        username=os.environ.get("DB_USER", "appuser"),
        password=os.environ.get("DB_PASSWORD", "FLef289*33"),
    )
