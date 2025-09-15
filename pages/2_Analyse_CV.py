import streamlit as st
from components.i18n import t
from components.gauge import afficher_jauge
from components.exporter import export_to_pdf, export_to_csv
import PyPDF2
import json
import pandas as pd
from pathlib import Path

st.set_page_config(page_title=t("analyse.title"), layout="wide")
st.title(t("analyse.title"))

# Chargement du référentiel
referentials_dir = Path("referentiels")
referentials = {}
for file in referentials_dir.glob("*.json"):
    with open(file, encoding="utf-8") as f:
        referentials[file.stem] = json.load(f)

selected_ref_name = st.selectbox(t("analyse.select_ref"), list(referentials.keys()))
selected_ref = referentials[selected_ref_name]

uploaded_files = st.file_uploader(t("analyse.upload_cv"), type=["pdf"], accept_multiple_files=True)

if uploaded_files and st.button(t("analyse.run_analysis")):
    for file in uploaded_files:
        reader = PyPDF2.PdfReader(file)
        cv_text = " ".join([page.extract_text() or "" for page in reader.pages])

        st.markdown(f"### {file.name}")
        st.markdown("#### 🔍 Résultat fictif (exemple)")

        for section, exigences in selected_ref.items():
            score = 0.8  # Exemple statique
            afficher_jauge(section, score)

        st.text_area(t("analyse.comment_area"), placeholder=t("analyse.comment_placeholder"))
        st.button(t("analyse.export_pdf"), on_click=export_to_pdf)
        st.button(t("analyse.export_csv"), on_click=export_to_csv)
