import streamlit as st

def login_form():
    with st.sidebar:
        st.header("🔐 Connexion")

        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")

        if st.button("Se connecter"):
            users = st.secrets.get("users", {})
            if username in users and users[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["is_admin"] = (username == "admin")
                st.success(f"Bienvenue {username} !")
                st.rerun()
            else:
                st.error("Identifiants incorrects.")

def require_login(admin_only=False):
    if not st.session_state.get("logged_in", False):
        login_form()
        st.stop()

    if admin_only and not st.session_state.get("is_admin", False):
        st.error("Accès réservé à l'administrateur.")
        st.stop()
