import streamlit as st
from components.i18n import t
from components.gauge import afficher_jauge
from components.exporter import export_to_pdf, export_to_csv
import PyPDF2
import json
import pandas as pd
from pathlib import Path
import groq

st.set_page_config(page_title=t("analyse.title"), layout="wide")
st.title(t("analyse.title"))

# Récupérer clé API Groq
try:
    api_key = st.secrets.get("groq") or st.secrets.get("api_keys", {}).get("groq")

if not api_key:
    st.error("❌ Clé API Groq manquante. Ajoutez-la dans les secrets.")
    st.stop()


client = groq.Client(api_key=api_key)

# Chargement des référentiels
referentials_dir = Path("referentiels")
referentials = {}
for file in referentials_dir.glob("*.json"):
    with open(file, encoding="utf-8") as f:
        referentials[file.stem] = json.load(f)

selected_ref_name = st.selectbox(t("analyse.select_ref"), list(referentials.keys()))
selected_ref = referentials[selected_ref_name]

uploaded_files = st.file_uploader(t("analyse.upload_cv"), type=["pdf"], accept_multiple_files=True)

# Fonction pour parser réponse JSON tolérant
def extract_valid_json(text):
    decoder = json.JSONDecoder()
    text = text.strip()
    for i in range(len(text)):
        try:
            obj, _ = decoder.raw_decode(text[i:])
            return obj
        except json.JSONDecodeError:
            continue
    return None

if uploaded_files and st.button(t("analyse.run_analysis")):
    for file in uploaded_files:
        try:
            reader = PyPDF2.PdfReader(file)
            cv_text = " ".join([page.extract_text() or "" for page in reader.pages])

            prompt = f'''
Tu es un expert en conformité GFSI.
Analyse le CV ci-dessous en comparant CHAQUE EXIGENCE du référentiel une par une.
Pour chaque exigence :
- indique si elle est ✅ CONFORME, ⚠️ À CHALLENGER, ou ❌ NON CONFORME
- fournis une justification brève basée sur les données du CV
- indique un score de confiance (0 à 1)

RÉFÉRENTIEL GFSI :
{json.dumps(selected_ref, indent=2)}

CV DU CANDIDAT :
{cv_text}

Répond UNIQUEMENT avec un objet JSON strictement valide :
{{
  "analysis": [
    {{
      "exigence": "description de l'exigence",
      "statut": "CONFORME / À CHALLENGER / NON CONFORME",
      "justification": "justification basée sur le CV",
      "confiance": 0.85
    }}
  ],
  "synthese": "résumé clair et actionnable pour le candidat"
}}
'''

            with st.spinner(f"Analyse de {file.name}..."):
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )

                result = response.choices[0].message.content.strip()
                result_data = extract_valid_json(result)

                if not result_data:
                    st.error(f"⚠️ JSON invalide pour {file.name}")
                    continue

                analysis = result_data["analysis"]
                synthese = result_data.get("synthese", "")

                st.subheader(f"📄 Résultat : {file.name}")
                for item in analysis:
                    taux = item.get("confiance", 0)
                    afficher_jauge(item["exigence"], taux)

                st.markdown("#### 🧠 Synthèse IA")
                st.info(synthese)

                st.markdown("#### 💬 Observations manuelles")
                st.text_area(t("analyse.comment_area"), placeholder=t("analyse.comment_placeholder"))

                st.button(t("analyse.export_pdf"), on_click=export_to_pdf)
                st.button(t("analyse.export_csv"), on_click=export_to_csv)

        except Exception as e:
            st.error(f"❌ Erreur d'analyse : {e}")
