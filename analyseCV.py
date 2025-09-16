import streamlit as st
import PyPDF2
import json
from datetime import datetime
from pathlib import Path
import groq
import pandas as pd
import plotly.graph_objects as go
import hashlib
import io
import os
import re
import unicodedata

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ===================== i18n =====================
LANGS = {
    "fr": "🇫🇷 Français",
    "en": "🇬🇧 English",
    "es": "🇪🇸 Español",
}

T = {
    "app_title": {
        "fr": "📄 Analyse comparative de CV - Auditeurs GFSI",
        "en": "📄 Comparative CV Analysis – GFSI Auditors",
        "es": "📄 Análisis comparativo de CV – Auditores GFSI",
    },
    "config": {"fr": "🔧 Configuration", "en": "🔧 Settings", "es": "🔧 Configuración"},
    "api_key": {
        "fr": "🔑 Clé API Groq :",
        "en": "🔑 Groq API key:",
        "es": "🔑 Clave API de Groq:",
    },
    "need_api": {
        "fr": "Veuillez saisir une clé API valide.",
        "en": "Please enter a valid API key.",
        "es": "Por favor, introduce una clave API válida.",
    },
    "admin": {"fr": "🔒 Administration", "en": "🔒 Administration", "es": "🔒 Administración"},
    "admin_ok": {"fr": "Accès admin validé ✅", "en": "Admin access granted ✅", "es": "Acceso de administrador concedido ✅"},
    "no_refs": {
        "fr": "Aucun référentiel valide trouvé.",
        "en": "No valid referentials found.",
        "es": "No se encontraron referenciales válidos.",
    },
    "select_ref": {
        "fr": "📚 Référentiel GFSI :",
        "en": "📚 GFSI Referential:",
        "es": "📚 Referencial GFSI:",
    },
    "meta_version": {"fr": "Version", "en": "Version", "es": "Versión"},
    "meta_date": {"fr": "Date", "en": "Date", "es": "Fecha"},
    "model": {"fr": "🧠 Modèle IA :", "en": "🧠 AI Model:", "es": "🧠 Modelo de IA:"},
    "uploader": {
        "fr": "📄 Chargez un ou plusieurs CV (PDF uniquement)",
        "en": "📄 Upload one or more CVs (PDF only)",
        "es": "📄 Sube uno o varios CV (solo PDF)",
    },
    "run": {"fr": "🔍 Lancer l'analyse IA", "en": "🔍 Run AI analysis", "es": "🔍 Ejecutar análisis con IA"},
    "analyzing": {
        "fr": "Analyse des CV en cours...",
        "en": "Analyzing CVs...",
        "es": "Analizando CV...",
    },
    "invalid_json": {
        "fr": "JSON invalide pour",
        "en": "Invalid JSON for",
        "es": "JSON inválido para",
    },
    "compare": {
        "fr": "📊 Comparaison des candidats",
        "en": "📊 Candidates comparison",
        "es": "📊 Comparación de candidatos",
    },
    "candidate": {"fr": "Candidat", "en": "Candidate", "es": "Candidato"},
    "score_global": {"fr": "Score Global", "en": "Overall Score", "es": "Puntuación Global"},
    "ok_count": {"fr": "✅ Conformes", "en": "✅ Compliant", "es": "✅ Cumple"},
    "challenge_count": {"fr": "⚠️ À challenger", "en": "⚠️ To review", "es": "⚠️ A revisar"},
    "ko_count": {"fr": "❌ Non conformes", "en": "❌ Non compliant", "es": "❌ No cumple"},
    "detail_title": {
        "fr": "📄 Analyse détaillée :",
        "en": "📄 Detailed analysis:",
        "es": "📄 Análisis detallado:",
    },
    "synth": {"fr": "### 🧠 Synthèse IA", "en": "### 🧠 AI Summary", "es": "### 🧠 Resumen de IA"},
    "gauge": {"fr": "Score Global", "en": "Overall Score", "es": "Puntuación Global"},
    "justif": {"fr": "*Justification:*", "en": "*Justification:*", "es": "*Justificación:*"},
    "elements_cv": {"fr": "*Éléments du CV:*", "en": "*CV Evidence:*", "es": "*Evidencias del CV:*"},
    "confidence": {"fr": "*Confiance:*", "en": "*Confidence:*", "es": "*Confianza:*"},
    "export": {
        "fr": "💾 Télécharger CSV",
        "en": "💾 Download CSV",
        "es": "💾 Descargar CSV",
    },
    "export_pdf": {
        "fr": "📄 Télécharger Rapport PDF",
        "en": "📄 Download PDF Report",
        "es": "📄 Descargar Informe PDF",
    },
    "refresh_refs": {
        "fr": "🔄 Actualiser les référentiels",
        "en": "🔄 Refresh referentials",
        "es": "🔄 Actualizar referenciales",
    },
    "admin_header": {
        "fr": "🛠️ Administration des référentiels",
        "en": "🛠️ Referentials Administration",
        "es": "🛠️ Administración de referenciales",
    },
    "admin_need": {
        "fr": "🔐 Connectez-vous avec un compte 'admin' pour gérer les référentiels.",
        "en": "🔐 Login with an 'admin' account to manage referentials.",
        "es": "🔐 Inicia sesión con una cuenta 'admin' para gestionar referenciales.",
    },
    "tabs": {
        "fr": ["✨ Créer via IA", "📥 Importer JSON", "✏️ Éditer existant", "📄 Dupliquer"],
        "en": ["✨ Create via AI", "📥 Import JSON", "✏️ Edit existing", "📄 Duplicate"],
        "es": ["✨ Crear con IA", "📥 Importar JSON", "✏️ Editar existente", "📄 Duplicar"],
    },
    "create_from_text": {
        "fr": "Créer un référentiel à partir d'un texte brut",
        "en": "Create a referential from raw text",
        "es": "Crear un referencial desde texto libre",
    },
    "paste_here": {
        "fr": "Collez ici les exigences (texte libre)...",
        "en": "Paste requirements here (free text)...",
        "es": "Pega aquí los requisitos (texto libre)...",
    },
    "filename": {
        "fr": "Nom de fichier (sans .json)",
        "en": "Filename (without .json)",
        "es": "Nombre de archivo (sin .json)",
    },
    "preview_only": {
        "fr": "Prévisualiser seulement",
        "en": "Preview only",
        "es": "Solo previsualizar",
    },
    "gen_ai": {"fr": "🧠 Générer avec l'IA", "en": "🧠 Generate with AI", "es": "🧠 Generar con IA"},
    "gen_fail": {
        "fr": "Impossible de générer un JSON valide.",
        "en": "Unable to generate valid JSON.",
        "es": "No se pudo generar un JSON válido.",
    },
    "gen_ok": {"fr": "Référentiel généré ✅", "en": "Referential generated ✅", "es": "Referencial generado ✅"},
    "saved_under": {
        "fr": "Enregistré sous",
        "en": "Saved under",
        "es": "Guardado en",
    },
    "import_json": {
        "fr": "Importer un fichier JSON",
        "en": "Import a JSON file",
        "es": "Importar un archivo JSON",
    },
    "choose_json": {
        "fr": "Sélectionnez un fichier .json",
        "en": "Select a .json file",
        "es": "Selecciona un archivo .json",
    },
    "json_valid": {"fr": "JSON valide ✅", "en": "Valid JSON ✅", "es": "JSON válido ✅"},
    "json_invalid": {
        "fr": "Structure invalide:",
        "en": "Invalid structure:",
        "es": "Estructura inválida:",
    },
    "save_import": {
        "fr": "💾 Sauvegarder l'import",
        "en": "💾 Save import",
        "es": "💾 Guardar importación",
    },
    "copy_json": {
        "fr": "📋 Copier le JSON",
        "en": "📋 Copy JSON",
        "es": "📋 Copiar JSON",
    },
    "edit_ref": {
        "fr": "Éditer un référentiel existant",
        "en": "Edit an existing referential",
        "es": "Editar un referencial existente",
    },
    "which_ref": {
        "fr": "Référentiel à éditer",
        "en": "Referential to edit",
        "es": "Referencial a editar",
    },
    "edit_here": {
        "fr": "Éditez le JSON ci-dessous :",
        "en": "Edit the JSON below:",
        "es": "Edita el JSON a continuación:",
    },
    "new_name": {
        "fr": "Nom de fichier (sans .json)",
        "en": "Filename (without .json)",
        "es": "Nombre de archivo (sin .json)",
    },
    "backup": {
        "fr": "Créer une sauvegarde .bak",
        "en": "Create a .bak backup",
        "es": "Crear copia .bak",
    },
    "save_changes": {
        "fr": "💾 Sauvegarder les modifications",
        "en": "💾 Save changes",
        "es": "💾 Guardar cambios",
    },
    "dup": {"fr": "Dupliquer un référentiel", "en": "Duplicate a referential", "es": "Duplicar un referencial"},
    "source": {"fr": "Source", "en": "Source", "es": "Origen"},
    "target": {"fr": "Nom de fichier cible (sans .json)", "en": "Target filename (without .json)", "es": "Nombre de archivo destino (sin .json)"},
    "duplicate": {"fr": "📄 Dupliquer", "en": "📄 Duplicate", "es": "📄 Duplicar"},
    "guide_admin": {
        "fr": "Guide rapide",
        "en": "Quick guide",
        "es": "Guía rápida",
    },
    "guide_steps": {
        "fr": """1) Choisissez la méthode (Créer / Importer / Éditer / Dupliquer)
2) Validez la structure JSON (un schéma minimal est exigé)
3) Sauvegardez pour rendre le référentiel disponible
4) Cliquez sur 'Actualiser' pour mettre à jour la liste
5) Revenez en haut pour le sélectionner et lancer une analyse""",
        "en": """1) Choose method (Create / Import / Edit / Duplicate)
2) Validate JSON structure (minimal schema required)
3) Save to make the referential available
4) Click 'Refresh' to update the list
5) Scroll up to select it and run an analysis""",
        "es": """1) Elige método (Crear / Importar / Editar / Duplicar)
2) Valida la estructura JSON (se exige un esquema mínimo)
3) Guarda para hacerlo disponible
4) Haz clic en 'Actualizar' para actualizar la lista
5) Vuelve arriba para seleccionarlo y lanzar el análisis""",
    },
    "explain_more": {
        "fr": "🔎 Explications détaillées",
        "en": "🔎 Detailed explanations",
        "es": "🔎 Explicaciones detalladas",
    },
    "what_we_checked": {
        "fr": "Ce que nous avons cherché",
        "en": "What we looked for",
        "es": "Lo que buscamos",
    },
    "found_in_cv": {"fr": "Détection dans le CV", "en": "Detection in CV", "es": "Detección en el CV"},
    "scoring_details": {"fr": "Détails du scoring", "en": "Scoring details", "es": "Detalles de la puntuación"},
    "top_missing": {"fr": "Principaux manques", "en": "Top missing items", "es": "Principales ausencias"},
    "download_json": {"fr": "📥 Télécharger le JSON détaillé", "en": "📥 Download detailed JSON", "es": "📥 Descargar JSON detallado"},
    "login_title": {"fr": "🔒 Connexion", "en": "🔒 Login", "es": "🔒 Iniciar sesión"},
    "username": {"fr": "Nom d'utilisateur", "en": "Username", "es": "Nombre de usuario"},
    "password": {"fr": "Mot de passe", "en": "Password", "es": "Contraseña"},
    "login_btn": {"fr": "Se connecter", "en": "Login", "es": "Iniciar sesión"},
    "login_success": {"fr": "Connexion réussie ✅", "en": "Login successful ✅", "es": "Conexión exitosa ✅"},
    "login_failed": {"fr": "Identifiants incorrects ❌", "en": "Invalid credentials ❌", "es": "Credenciales incorrectas ❌"},
    "logout_btn": {"fr": "Se déconnecter", "en": "Logout", "es": "Cerrar sesión"},
    "connected_as": {"fr": "Connecté", "en": "Connected", "es": "Conectado"},
    "role": {"fr": "rôle", "en": "role", "es": "rol"},
    "need_admin_role": {"fr": "Connectez-vous avec un compte 'admin' pour accéder aux fonctions avancées.", "en": "Login with an 'admin' account to access advanced features.", "es": "Inicia sesión con una cuenta 'admin' para acceder a funciones avanzadas."},
}

def tr(key, lang):
    return T.get(key, {}).get(lang, T.get(key, {}).get("en", key))

# ===================== Helpers =====================
def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")

def normalize_status(raw):
    if not raw:
        return "CHALLENGE"
    s = strip_accents(str(raw)).upper().strip()
    mapping = {
        "CONFORME": "OK",
        "COMPLIANT": "OK",
        "CUMPLE": "OK",
        "OK": "OK",
        "A CHALLENGER": "CHALLENGE",
        "A REVOIR": "CHALLENGE",
        "A VERIFIER": "CHALLENGE",
        "TO REVIEW": "CHALLENGE",
        "REVIEW": "CHALLENGE",
        "TO CHALLENGE": "CHALLENGE",
        "A REVISAR": "CHALLENGE",
        "POR REVISAR": "CHALLENGE",
        "NON CONFORME": "KO",
        "NON-COMPLIANT": "KO",
        "NON COMPLIANT": "KO",
        "NOT COMPLIANT": "KO",
        "NO CUMPLE": "KO",
        "INCUMPLE": "KO",
    }
    return mapping.get(s, "CHALLENGE")

def jauge(label, value, lang):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': label},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "green" if value >= 0.75 else "orange" if value >= 0.5 else "red"},
            'steps': [
                {'range': [0, 50], 'color': "#f8d7da"}, 
                {'range': [50, 75], 'color': "#fff3cd"}, 
                {'range': [75, 100], 'color': "#d4edda"}
            ]
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

def extract_json_strict(text):
    s = (text or "").strip()
    a, b = s.find("{"), s.rfind("}")
    if a == -1 or b == -1 or b <= a:
        return None
    try:
        return json.loads(s[a:b+1])
    except Exception:
        pass
    stack, start = 0, None
    for i, ch in enumerate(s):
        if ch == "{":
            if stack == 0:
                start = i
            stack += 1
        elif ch == "}":
            stack -= 1
            if stack == 0 and start is not None:
                try:
                    return json.loads(s[start:i+1])
                except Exception:
                    continue
    return None

def validate_analysis(obj):
    if not isinstance(obj, dict):
        return False, "root-not-dict"
    if "analysis" not in obj or not isinstance(obj["analysis"], list):
        return False, "no-analysis"
    ok_items = []
    for it in obj["analysis"]:
        if not isinstance(it, dict):
            continue
        need = ["exigence_id", "exigence_titre", "statut", "justification", "confiance", "ponderation", "niveau_requis"]
        if not all(k in it for k in need):
            continue
        it["statut"] = normalize_status(it.get("statut"))
        if "category_id" not in it:
            it["category_id"] = ""
        ok_items.append(it)
    obj["analysis"] = ok_items
    if "score_global" not in obj:
        obj["score_global"] = 0
    if "synthese" not in obj:
        obj["synthese"] = ""
    return True, obj

@st.cache_data
def pdf_to_text(file_bytes: bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    return " ".join([(page.extract_text() or "") for page in reader.pages])

def file_digest(uploaded_file):
    uploaded_file.seek(0)
    data = uploaded_file.read()
    uploaded_file.seek(0)
    return hashlib.sha256(data).hexdigest(), data

def validate_referential_structure(data: dict):
    if not isinstance(data, dict):
        return False, "root must be object"
    if "exigences" not in data and "categories" not in data:
        return False, "missing 'exigences' or 'categories'"
    if "exigences" in data and not isinstance(data["exigences"], dict):
        return False, "'exigences' must be object"
    if "categories" in data and not isinstance(data["categories"], dict):
        return False, "'categories' must be object"
    return True, "OK"

def save_referential_to_json(referential_data: dict, filename: str) -> bool:
    try:
        ref_dir = Path("referentiels")
        ref_dir.mkdir(exist_ok=True)
        safe = filename.strip().replace(" ", "_").replace("/", "_")
        if not safe.endswith(".json"):
            safe += ".json"
        with open(ref_dir / safe, "w", encoding="utf-8") as f:
            json.dump(referential_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Erreur de sauvegarde: {e}")
        st.info("ℹ️ Les fichiers peuvent ne pas persister après redémarrage sur certaines plateformes.")
        return False

# ===================== PDF Generation =====================
def generate_pdf_report(results_all, selected_ref, ref_name, lang):
    """Generate a comprehensive PDF report"""
    if not PDF_AVAILABLE:
        raise ImportError("ReportLab n'est pas installé")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], alignment=1, fontSize=18, spaceAfter=30)
    story.append(Paragraph(tr("app_title", lang), title_style))
    story.append(Spacer(1, 20))
    
    # Summary section
    story.append(Paragraph(tr("compare", lang), styles['Heading2']))
    
    # Create comparison table
    table_data = [[
        tr("candidate", lang),
        tr("score_global", lang),
        tr("ok_count", lang),
        tr("challenge_count", lang),
        tr("ko_count", lang)
    ]]
    
    for result in results_all:
        table_data.append([
            result["nom"],
            f"{result['score']:.0%}",
            str(result["conformes"]),
            str(result["challengers"]),
            str(result["non_conformes"])
        ])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(PageBreak())
    
    # Detailed analysis for each candidate
    for result in results_all:
        story.append(Paragraph(f"{tr('detail_title', lang)} {result['nom']}", styles['Heading2']))
        
        # AI Summary
        story.append(Paragraph(tr("synth", lang)[4:], styles['Heading3']))
        story.append(Paragraph(result["synthese"], styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Requirements details
        story.append(Paragraph("Détail par exigence:", styles['Heading3']))
        
        for item in result["details"]:
            norm = normalize_status(item.get("statut"))
            status_symbol = {"OK": "✅", "CHALLENGE": "⚠️", "KO": "❌"}.get(norm, "❓")
            
            req_title = f"{status_symbol} {item.get('exigence_titre', '')}"
            story.append(Paragraph(req_title, styles['Heading4']))
            
            justif_text = f"<b>{tr('justif', lang)[1:-1]}</b> {item.get('justification', '')}"
            story.append(Paragraph(justif_text, styles['Normal']))
            
            if item.get('elements_cv'):
                evidence_text = f"<b>{tr('elements_cv', lang)[1:-1]}</b> {item.get('elements_cv')}"
                story.append(Paragraph(evidence_text, styles['Normal']))
            
            conf_text = f"<b>{tr('confidence', lang)[1:-1]}</b> {float(item.get('confiance', 0)):.0%}"
            story.append(Paragraph(conf_text, styles['Normal']))
            story.append(Spacer(1, 10))
        
        story.append(PageBreak())
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ===================== Auth System =====================
def load_users_config():
    users = {}
    
    if "users" in st.secrets:
        for username, user_data in st.secrets["users"].items():
            users[username] = {
                "password_hash": user_data.get("password_hash", ""),
                "role": user_data.get("role", "user")
            }
    elif "users_plain" in st.secrets:
        for username, user_data in st.secrets["users_plain"].items():
            plain_password = user_data.get("password", "")
            users[username] = {
                "password_hash": hashlib.sha256(plain_password.encode()).hexdigest(),
                "role": user_data.get("role", "user")
            }
    else:
        legacy_password = st.secrets.get("ADMIN_PASSWORD", os.environ.get("ADMIN_PASSWORD", ""))
        if legacy_password:
            users["admin"] = {
                "password_hash": hashlib.sha256(legacy_password.encode()).hexdigest(),
                "role": "admin"
            }
        else:
            st.error("❌ Aucune configuration d'utilisateur trouvée dans les secrets Streamlit.")
            st.info("""
            **Configuration requise dans .streamlit/secrets.toml :**
            
            ```toml
            [users_plain]
            admin = { password = "votre_mot_de_passe", role = "admin" }
            user1 = { password = "autre_mot_de_passe", role = "user" }
            ```
            
            **OU avec mots de passe hashés (recommandé) :**
            
            ```toml
            [users]
            admin = { password_hash = "sha256_hash", role = "admin" }
            ```
            """)
            st.stop()
    
    return users

def check_credentials(username: str, password: str):
    users = load_users_config()
    user_data = users.get(username)
    
    if not user_data:
        return False, None
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash == user_data.get("password_hash", ""):
        return True, user_data.get("role", "user")
    
    return False, None

# ===================== PAGE CONFIG =====================
st.set_page_config(page_title="GFSI CV", layout="wide")

# ===================== Session State Init =====================
if "authenticated" not in st.session_state:
    st.session_state.update({
        "authenticated": False,
        "role": None,
        "username": None
    })

if "ref_cache_key" not in st.session_state:
    st.session_state.ref_cache_key = 0

# ===================== Login Screen =====================
if not st.session_state["authenticated"]:
    if "lang" not in st.session_state:
        st.session_state["lang"] = lang

st.title(tr("app_title", lang))
st.caption(f"👤 {st.session_state['username']} • {tr('role', lang)}: {st.session_state['role']}")

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header(tr("config", lang))
    api_key = st.text_input(tr("api_key", lang), type="password", help="Get a key at console.groq.com")

    st.divider()
    st.subheader(tr("admin", lang))
    st.caption(f"{tr('connected_as', lang)}: {st.session_state['username']} ({st.session_state['role']})")
    
    if st.button(tr("logout_btn", lang)):
        for key in ("authenticated", "role", "username"):
            st.session_state.pop(key, None)
        st.rerun()

    admin_ok = (st.session_state["role"] == "admin")
    if admin_ok:
        st.success(tr("admin_ok", lang))
    else:
        st.caption(tr("need_admin_role", lang))

    if not api_key:
        st.warning(tr("need_api", lang))
        st.stop()
    
    client = groq.Client(api_key=api_key)

    # Improved referential loading with manual cache management
    def load_referentials(cache_key=None):
        out = {}
        ref_dir = Path("referentiels")
        if ref_dir.exists():
            for file in ref_dir.glob("*.json"):
                try:
                    with open(file, encoding="utf-8") as f:
                        data = json.load(f)
                    if "exigences" in data or "categories" in data:
                        out[file.stem] = data
                except Exception as e:
                    st.error(f"❌ Erreur de chargement {file.name}: {e}")
        return out

    # Refresh button for referentials
    if st.button(tr("refresh_refs", lang), help="Actualise la liste des référentiels"):
        st.session_state.ref_cache_key += 1
        st.rerun()
    
    referentials = load_referentials(st.session_state.ref_cache_key)
    if not referentials:
        st.error(tr("no_refs", lang))
        st.stop()

    ref_name = st.selectbox(tr("select_ref", lang), list(referentials.keys()))
    selected_ref = referentials[ref_name]

    if "metadata" in selected_ref:
        md = selected_ref["metadata"]
        meta_line = f"**{md.get('name','')}**\n\n{md.get('description','')}"
        st.info(meta_line)
        st.caption(f"{tr('meta_version', lang)}: {md.get('version','N/A')} | {tr('meta_date', lang)}: {md.get('date_creation', md.get('last_updated','N/A'))}")

    model = st.selectbox(tr("model", lang), [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile", 
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ])

# ===================== Prompt builder =====================
def build_prompt(selected_ref, cv_text, lang):
    if "exigences" in selected_ref and isinstance(selected_ref["exigences"], dict) and selected_ref["exigences"]:
        lines = []
        for req_id, req in selected_ref["exigences"].items():
            lines.append(
                f"REQUIREMENT {req_id}: {req.get('title','')}\n"
                f"Description: {req.get('description','')}\n"
                f"Level: {req.get('niveau_requis','')}\n"
                f"Weight: {req.get('ponderation',1.0)}\n"
                "Criteria:\n" + "\n".join(["• "+c for c in req.get("criteres", [])])
            )
            lines.append("Conform examples:\n" + "\n".join(["• "+e for e in req.get("exemples_conformes", [])]))
            lines.append("Non-conform examples:\n" + "\n".join(["• "+e for e in req.get("exemples_non_conformes", [])]) + "\n---")
        exigences_detail = "\n".join(lines)
    else:
        lines = []
        for cat, cat_data in selected_ref.get("categories", {}).items():
            lines.append(f"== CATEGORY {cat} (weight {cat_data.get('weight',0)}) ==")
            lines.append(cat_data.get("description",""))
            for sub, sub_data in cat_data.get("subcategories", {}).items():
                lines.append(f"-- Subcategory {sub} (weight {sub_data.get('weight',0)}) --")
                for req in sub_data.get("requirements", []):
                    lines.append(
                        f"REQUIREMENT {req.get('id','N/A')}\n"
                        f"Text: {req.get('text','')}\n"
                        f"Minimum acceptable: {req.get('minimum_acceptable','')}\n"
                        f"References: {', '.join(req.get('references', []))}\n---"
                    )
        exigences_detail = "\n".join(lines)

    lang_text = {
        "fr": "Français",
        "en": "English", 
        "es": "Español",
    }[lang]

    schema = {
        "analysis": [{
            "exigence_id": "ID exact",
            "exigence_titre": "Title",
            "category_id": "Category/Subcategory",
            "statut": "COMPLIANT | TO_REVIEW | NON_COMPLIANT",
            "justification": "Evidence and reasoning",
            "elements_cv": "CV quotes",
            "confiance": 0.0,
            "niveau_requis": "obligatoire|recommande|souhaitable",
            "ponderation": 1.0
        }],
        "score_global": 0.0,
        "synthese": "Summary and recommendations"
    }

    return f"""
You are a senior GFSI conformity expert.
Respond ONLY with STRICTLY VALID JSON using EXACTLY the following keys/schema (keys in English). All texts (justification, synthese) must be written in {lang_text}.

Schema:
{json.dumps(schema, ensure_ascii=False, indent=2)}

REFERENTIAL:
{exigences_detail}

CANDIDATE CV:
{cv_text}

Method:
1) Match CV evidence against each requirement criteria and examples
2) Decide status: COMPLIANT / TO_REVIEW / NON_COMPLIANT
3) Provide precise justification with CV evidence quotes
4) Provide confidence 0..1
"""

# ===================== Main: Upload & Analyse =====================
uploaded_files = st.file_uploader(tr("uploader", lang), type=["pdf"], accept_multiple_files=True)

if uploaded_files and st.button(tr("run", lang)):
    results_all, details_export = [], []
    with st.spinner(tr("analyzing", lang)):
        for up in uploaded_files:
            try:
                digest, data = file_digest(up)
                cv_text = pdf_to_text(data)
                prompt = build_prompt(selected_ref, cv_text, lang)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=4000
                )
                raw = response.choices[0].message.content or ""
                parsed = extract_json_strict(raw)
                if not parsed:
                    st.error(f"{tr('invalid_json', lang)} {up.name}")
                    continue
                ok, res = validate_analysis(parsed)
                if not ok:
                    st.error(f"{tr('invalid_json', lang)} {up.name}")
                    continue
                analysis = res["analysis"]
                for a in analysis:
                    a["cv"] = up.name
                    details_export.append(a)
                score_pondere, poids_total = 0.0, 0.0
                ok_c = ch_c = ko_c = 0
                for item in analysis:
                    statut = item.get("statut", "")
                    norm = normalize_status(statut)
                    ponderation = float(item.get("ponderation", 1.0) or 1.0)
                    confiance = float(item.get("confiance", 0) or 0)
                    if norm == "OK":
                        ok_c += 1
                        score_pondere += confiance * ponderation
                    elif norm == "CHALLENGE":
                        ch_c += 1
                        score_pondere += (confiance * 0.5) * ponderation
                    else:
                        ko_c += 1
                    poids_total += ponderation
                score_final = (score_pondere / poids_total) if poids_total > 0 else 0.0
                results_all.append({
                    "nom": up.name,
                    "conformes": ok_c,
                    "challengers": ch_c,
                    "non_conformes": ko_c,
                    "score": round(score_final, 2),
                    "score_global": res.get("score_global", score_final),
                    "details": analysis,
                    "synthese": res.get("synthese", ""),
                    "cv_text": cv_text
                })
            except Exception as e:
                st.error(f"❌ Erreur pour {up.name}: {e}")

    if results_all:
        st.subheader(tr("compare", lang))
        comparison_df = pd.DataFrame([{
            tr("candidate", lang): r["nom"],
            tr("score_global", lang): f"{r['score']:.0%}",
            tr("ok_count", lang): r["conformes"],
            tr("challenge_count", lang): r["challengers"],
            tr("ko_count", lang): r["non_conformes"]
        } for r in results_all])
        st.dataframe(comparison_df, use_container_width=True)

        # Export buttons
        col1, col2 = st.columns(2)
        
        with col1:
            export_df = pd.DataFrame([d for d in details_export])
            csv = export_df.to_csv(index=False, encoding="utf-8")
            st.download_button(
                label=tr("export", lang), 
                data=csv, 
                file_name=f"analyse_cv_gfsi_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", 
                mime="text/csv"
            )
        
        with col2:
            # PDF Report generation
            if PDF_AVAILABLE:
                try:
                    pdf_buffer = generate_pdf_report(results_all, selected_ref, ref_name, lang)
                    st.download_button(
                        label=tr("export_pdf", lang),
                        data=pdf_buffer,
                        file_name=f"rapport_cv_gfsi_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Erreur génération PDF: {e}")
            else:
                st.info("📄 PDF non disponible - installez reportlab: pip install reportlab")

        for result in results_all:
            st.subheader(f"{tr('detail_title', lang)} {result['nom']}")
            col1, col2 = st.columns([1, 2])
            with col1:
                jauge(tr("gauge", lang), result["score"], lang)
            with col2:
                st.markdown(tr("synth", lang))
                st.info(result["synthese"])

            # === Explications détaillées ===
            with st.expander(tr("explain_more", lang), expanded=False):
                df = pd.DataFrame(result["details"])
                status_emoji = {"OK": "✅", "CHALLENGE": "⚠️", "KO": "❌"}

                # Ce que nous avons cherché + détection naïve dans le CV
                st.markdown(f"**{tr('what_we_checked', lang)}**")
                if "exigences" in selected_ref and isinstance(selected_ref["exigences"], dict):
                    for req_id, req in selected_ref["exigences"].items():
                        keywords = [w for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", " ".join(req.get("criteres", [])))][:10]
                        presence = [k for k in keywords if strip_accents(k).lower() in strip_accents(result["cv_text"]).lower()]
                        st.write(f"• {req_id} – {req.get('title','')}")
                        st.caption(f"{tr('found_in_cv', lang)}: {', '.join(presence) if presence else '—'}")

                # Détails par exigence
                for _, row in df.iterrows():
                    norm = normalize_status(row.get("statut"))
                    emoji = status_emoji.get(norm, "❓")
                    st.write(f"{emoji} **{row.get('exigence_titre','')}**")
                    st.write(f"{tr('justif', lang)} {row.get('justification','')}")
                    if row.get('elements_cv'):
                        st.write(f"{tr('elements_cv', lang)} {row.get('elements_cv')}")
                    st.write(f"{tr('confidence', lang)} {float(row.get('confiance',0)):.0%}")
                    st.divider()

                # Détails de scoring
                st.markdown(f"**{tr('scoring_details', lang)}**")
                st.write({
                    tr("ok_count", lang): result["conformes"],
                    tr("challenge_count", lang): result["challengers"],
                    tr("ko_count", lang): result["non_conformes"],
                    tr("score_global", lang): f"{result['score']:.0%}"
                })

                # Top manques
                st.markdown(f"**{tr('top_missing', lang)}**")
                missing = [d for d in result["details"] if normalize_status(d.get("statut")) == "KO"]
                for m in missing[:5]:
                    st.write(f"• {m.get('exigence_titre','')}")

                # Export JSON détaillé
                detailed_json = json.dumps(result, ensure_ascii=False, indent=2)
                st.download_button(
                    tr("download_json", lang), 
                    data=detailed_json.encode("utf-8"), 
                    file_name=f"detailed_{result['nom']}.json", 
                    mime="application/json"
                )

# ===================== Admin: CRUD Référentiels =====================
st.divider()
st.header(tr("admin_header", lang))
st.caption(tr("guide_admin", lang))
st.info(tr("guide_steps", lang))

if not admin_ok:
    st.info(tr("admin_need", lang))
else:
    tab_names = tr("tabs", lang)
    tab_creer, tab_import, tab_editer, tab_dupliquer = st.tabs(tab_names)

    # Créer via IA
    with tab_creer:
        st.subheader(tr("create_from_text", lang))
        exigences_text = st.text_area(
            tr("paste_here", lang), 
            height=220, 
            placeholder="Ex: The auditor shall ...", 
            help="Collez le texte brut du standard à structurer"
        )
        colA, colB = st.columns(2)
        with colA:
            ref_filename = st.text_input(
                tr("filename", lang), 
                value="nouveau_referentiel", 
                help="Nom du fichier à créer dans /referentiels"
            )
        with colB:
            ref_preview = st.checkbox(tr("preview_only", lang), value=False)
        
        if st.button(tr("gen_ai", lang)) and exigences_text.strip():
            with st.spinner("Génération IA en cours..."):
                gen = None
                try:
                    prompt = f"""
Structure these requirements into hierarchical JSON. Use EXACTLY this structure and respond with STRICT JSON only:

{{
  "metadata": {{
    "name": "Référentiel Généré IA",
    "description": "Référentiel créé automatiquement à partir du texte fourni",
    "version": "1.0",
    "date_creation": "{datetime.now().strftime('%Y-%m-%d')}"
  }},
  "categories": {{
    "cat1": {{
      "name": "category_name",
      "description": "category description",
      "weight": 0.5,
      "subcategories": {{
        "sub1": {{
          "name": "subcategory_name", 
          "description": "subcategory description",
          "weight": 0.5,
          "requirements": [
            {{
              "id": "req_id",
              "text": "requirement text",
              "minimum_acceptable": "minimum level required",
              "references": ["reference1", "reference2"]
            }}
          ]
        }}
      }}
    }}
  }}
}}

Requirements text to structure:
{exigences_text}

IMPORTANT: 
- Respond ONLY with valid JSON matching the exact structure above
- No markdown, no explanations, no code blocks
- Ensure all weights sum to 1.0 within each level
- Create logical categories and subcategories from the text
- Extract specific requirements with clear IDs
"""
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are an expert in structuring compliance referentials. Respond only with valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        model=model,
                        max_tokens=4000,
                        temperature=0.1
                    )
                    content = response.choices[0].message.content or ""
                    
                    # Clean the response
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    gen = extract_json_strict(content)
                    
                except Exception as e:
                    st.error(f"Erreur IA: {e}")

                if not gen:
                    st.error(tr("gen_fail", lang))
                    if 'content' in locals() and content:
                        st.text_area("Réponse brute de l'IA:", value=content, height=200)
                else:
                    ok, msg = validate_referential_structure(gen)
                    if not ok:
                        st.error(f"{tr('json_invalid', lang)} {msg}")
                        st.json(gen)
                    else:
                        st.success(tr("gen_ok", lang))
                        
                        # Display JSON
                        json_str = json.dumps(gen, ensure_ascii=False, indent=2)
                        st.json(gen)
                        
                        # Copy button
                        if st.button(tr("copy_json", lang), key="copy_generated"):
                            st.text_area(
                                "JSON généré (sélectionnez tout et copiez):", 
                                value=json_str, 
                                height=300,
                                key="json_to_copy"
                            )
                        
                        if not ref_preview:
                            if save_referential_to_json(gen, ref_filename):
                                st.success(f"{tr('saved_under', lang)} referentiels/{ref_filename}.json")
                                st.info(f"💡 Cliquez sur '{tr('refresh_refs', lang)}' dans la barre latérale pour voir le nouveau référentiel")
                                st.session_state.ref_cache_key += 1

    # Import JSON
    with tab_import:
        st.subheader(tr("import_json", lang))
        uploaded_json = st.file_uploader(
            tr("choose_json", lang), 
            type=["json"], 
            accept_multiple_files=False, 
            key="imp_json"
        )
        if uploaded_json is not None:
            try:
                data = json.loads(uploaded_json.read().decode("utf-8"))
                ok, msg = validate_referential_structure(data)
                if not ok:
                    st.error(f"{tr('json_invalid', lang)} {msg}")
                    st.json(data)
                else:
                    st.success(tr("json_valid", lang))
                    st.json(data)
                    filename = st.text_input(tr("filename", lang), value=Path(uploaded_json.name).stem)
                    if st.button(tr("save_import", lang)):
                        if save_referential_to_json(data, filename):
                            st.success(f"{tr('saved_under', lang)} referentiels/{filename}.json")
                            st.session_state.ref_cache_key += 1
                            st.info(f"💡 Cliquez sur '{tr('refresh_refs', lang)}' dans la barre latérale")
            except Exception as e:
                st.error(f"Erreur JSON: {e}")

    # Éditer existant
    with tab_editer:
        st.subheader(tr("edit_ref", lang))
        edit_key = st.selectbox(tr("which_ref", lang), list(referentials.keys()))
        current = referentials[edit_key]
        raw = st.text_area(
            tr("edit_here", lang), 
            value=json.dumps(current, ensure_ascii=False, indent=2), 
            height=400
        )
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input(tr("new_name", lang), value=edit_key)
        with col2:
            keep_backup = st.checkbox(tr("backup", lang), value=True)
        if st.button(tr("save_changes", lang)):
            try:
                data = json.loads(raw)
                ok, msg = validate_referential_structure(data)
                if not ok:
                    st.error(f"{tr('json_invalid', lang)} {msg}")
                else:
                    if keep_backup:
                        save_referential_to_json(
                            current, 
                            f"{edit_key}.bak_{datetime.now().strftime('%Y%m%d_%H%M')}"
                        )
                    if save_referential_to_json(data, new_name):
                        st.success(f"{tr('saved_under', lang)} referentiels/{new_name}.json")
                        st.session_state.ref_cache_key += 1
                        st.info(f"💡 Cliquez sur '{tr('refresh_refs', lang)}' dans la barre latérale")
            except Exception as e:
                st.error(f"Erreur JSON: {e}")

    # Dupliquer
    with tab_dupliquer:
        st.subheader(tr("dup", lang))
        src = st.selectbox(tr("source", lang), list(referentials.keys()), key="dup_src")
        target = st.text_input(tr("target", lang), value=f"{src}_copy")
        if st.button(tr("duplicate", lang)):
            if save_referential_to_json(referentials[src], target):
                st.success(f"{tr('saved_under', lang)} referentiels/{target}.json")
                st.session_state.ref_cache_key += 1
                st.info(f"💡 Cliquez sur '{tr('refresh_refs', lang)}' dans la barre latérale") "fr"
    
    lang = st.selectbox(
        "Language / Langue / Idioma",
        options=list(LANGS.keys()),
        format_func=lambda c: LANGS[c],
        index=list(LANGS.keys()).index(st.session_state["lang"])
    )
    st.session_state["lang"] = lang
    
    st.title(tr("login_title", lang))
    
    with st.form("login_form"):
        username = st.text_input(tr("username", lang))
        password = st.text_input(tr("password", lang), type="password")
        submitted = st.form_submit_button(tr("login_btn", lang))
        
        if submitted:
            if username and password:
                is_valid, role = check_credentials(username, password)
                if is_valid:
                    st.session_state.update({
                        "authenticated": True,
                        "role": role,
                        "username": username
                    })
                    st.success(f"{tr('login_success', lang)} ({tr('role', lang)}: {role})")
                    st.rerun()
                else:
                    st.error(tr("login_failed", lang))
            else:
                st.warning("Veuillez saisir un nom d'utilisateur et un mot de passe.")
    
    with st.expander("ℹ️ Configuration des secrets"):
        st.code("""
# Dans .streamlit/secrets.toml

[users_plain]
admin = { password = "mon_mot_de_passe_admin", role = "admin" }
user1 = { password = "mot_de_passe_utilisateur", role = "user" }

# OU avec hashes (plus sécurisé)
[users]
admin = { password_hash = "votre_hash_sha256", role = "admin" }
        """)
    
    st.stop()

# ===================== Main Interface =====================
if "lang" not in st.session_state:
    st.session_state["lang"] = "fr"

lang = st.sidebar.selectbox(
    "Language / Langue / Idioma",
    options=list(LANGS.keys()),
    format_func=lambda c: LANGS[c],
    index=list(LANGS.keys()).index(st.session_state["lang"])
)
st.session_state["lang"] =
