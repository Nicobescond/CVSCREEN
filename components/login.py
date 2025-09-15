import streamlit as st

def check_admin_auth():
    st.sidebar.header("🔒 Authentification Admin")
    username = st.sidebar.text_input("Nom d'utilisateur")
    password = st.sidebar.text_input("Mot de passe", type="password")

    secrets = st.secrets.get("users", {})
    return secrets.get(username) == password
