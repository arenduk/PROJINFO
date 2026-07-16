import streamlit as st
from navbar import render_navbar

st.set_page_config(layout="wide")
render_navbar()

st.title("Mes cours")
st.write("Contenu des cours à venir.")
