import streamlit as st
from pages import utilisateur, admin

st.set_page_config(page_title="Analyse CV GFSI", layout="wide")
role = st.sidebar.radio("Choisissez votre mode :", ["Utilisateur", "Admin"])

if role == "Utilisateur":
    utilisateur.run()
else:
    admin.run()
