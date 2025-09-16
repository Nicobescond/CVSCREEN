import streamlit as st
import json
from pathlib import Path
from components.i18n import t
from components.login import require_login

require_login(admin_only=True)

st.title("👤 Gestion des utilisateurs (admin uniquement)")

USERS_FILE = Path("users.json")

# Charger les utilisateurs
if USERS_FILE.exists():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {"admin": "adminpass"}

# Afficher la liste
st.subheader("📋 Utilisateurs actuels")
for username in users:
    if username == "admin":
        st.text(f"👑 {username} (admin)")
    else:
        col1, col2 = st.columns([3, 1])
        col1.write(f"👤 {username}")
        if col2.button("🗑️ Supprimer", key=f"delete_{username}"):
            del users[username]
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=2)
            st.success(f"Utilisateur '{username}' supprimé.")
            st.experimental_rerun()

st.markdown("---")

# Formulaire d'ajout/modification
st.subheader("➕ Ajouter / Modifier un utilisateur")
new_username = st.text_input("Nom d'utilisateur")
new_password = st.text_input("Mot de passe", type="password")

if st.button("💾 Enregistrer utilisateur"):
    if not new_username or not new_password:
        st.warning("Merci de remplir tous les champs.")
    else:
        users[new_username] = new_password
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
        st.success(f"Utilisateur '{new_username}' enregistré / mis à jour.")
        st.experimental_rerun()
