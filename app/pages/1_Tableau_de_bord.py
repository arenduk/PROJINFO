import streamlit as st
from navbar import render_navbar

st.set_page_config(layout="wide")
render_navbar()

st.title("Tableau de bord")
st.write("Contenu du tableau de bord à venir.")
