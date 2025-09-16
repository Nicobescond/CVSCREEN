def run():
    import streamlit as st
    import json
    from pathlib import Path
    from datetime import datetime
    import re
    import os
    import groq

    st.header("🛠️ Administration des référentiels")

    tab1, tab2 = st.tabs(["📥 Importer JSON", "✨ Créer via IA"])

    with tab1:
        st.subheader("Importer un fichier JSON")
        uploaded = st.file_uploader("Choisissez un fichier .json", type="json")
        if uploaded:
            try:
                data = json.load(uploaded)
                st.success("JSON valide ✅")
                st.json(data)
                filename = st.text_input("Nom de fichier (sans .json)", value=Path(uploaded.name).stem)
                if st.button("💾 Sauvegarder dans /referentiels"):
                    ref_dir = Path("referentiels")
                    ref_dir.mkdir(exist_ok=True)
                    filepath = ref_dir / f"{filename}.json"
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    st.success(f"Fichier sauvegardé : {filepath}")
            except Exception as e:
                st.error(f"Erreur de parsing : {e}")

    with tab2:
        st.subheader("Créer un référentiel à partir de texte brut")
        exigences_text = st.text_area("Collez ici les exigences...", height=300, placeholder="Ex: Le candidat doit avoir...")
        nom_fichier = st.text_input("Nom du fichier (sans .json)", value="nouveau_referentiel")
        api_key = st.text_input("Clé API Groq", type="password")

        if exigences_text and api_key and st.button("🧠 Générer avec IA"):
            with st.spinner("Génération IA en cours..."):
                client = groq.Client(api_key=api_key)
                prompt = f"""
Structure these requirements into hierarchical JSON with categories/subcategories, weights summing to 1.0, references and minimums. Respond with STRICT JSON only.
Date: {datetime.now().date()}
Text:
{exigences_text}
"""
                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": "You are an expert in structuring compliance referentials."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=4000,
                        temperature=0.1
                    )
                    content = response.choices[0].message.content or ""
                    match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
                    raw_json = match.group(1) if match else content
                    gen = json.loads(raw_json)
                    st.success("Référentiel généré ✅")
                    st.json(gen)

                    if st.button("💾 Sauvegarder ce référentiel"):
                        ref_dir = Path("referentiels")
                        ref_dir.mkdir(exist_ok=True)
                        filepath = ref_dir / f"{nom_fichier}.json"
                        with open(filepath, "w", encoding="utf-8") as f:
                            json.dump(gen, f, ensure_ascii=False, indent=2)
                        st.success(f"Fichier sauvegardé : {filepath}")

                except Exception as e:
                    st.error(f"Erreur IA : {e}")
