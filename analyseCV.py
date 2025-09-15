import streamlit as st
from components.i18n import set_language, t

st.set_page_config(page_title="Évaluation GFSI Multilingue", layout="wide")

lang = set_language()

st.title(t("home.title"))
st.markdown(t("home.description"))
st.markdown("---")
st.markdown("⬅️ Utilisez le menu à gauche pour accéder aux différentes fonctionnalités.")
