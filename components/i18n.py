import streamlit as st
import json

@st.cache_data
def load_translations():
    translations = {}
    for lang in ["fr", "es", "en"]:
        with open(f"locales/{lang}.json", encoding="utf-8") as f:
            translations[lang] = json.load(f)
    return translations

def set_language():
    st.sidebar.title("🌍 Choix de la langue / Language")
    lang = st.sidebar.selectbox("Langue / Language", ["fr", "es", "en"])
    st.session_state.lang = lang
    return lang

def t(key):
    lang = st.session_state.get("lang", "fr")
    translations = load_translations()
    return translations.get(lang, {}).get(key, key)
