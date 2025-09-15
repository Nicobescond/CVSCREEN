import streamlit as st
from components.i18n import set_language

st.set_page_config(page_title="Évaluation GFSI Multilingue", layout="wide")

# Sélection de la langue
lang = set_language()

st.switch_page("pages/1_Home.py")
