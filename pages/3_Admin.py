import streamlit as st
from components.login import check_admin_auth
from components.i18n import t
import json
from pathlib import Path

if not check_admin_auth():
    st.stop()

st.title(t("admin.title"))

uploaded = st.file_uploader(t("admin.upload_ref"), type=["json"])

if uploaded:
    try:
        ref_data = json.load(uploaded)
        name = uploaded.name.replace(".json", "")
        referentials_dir = Path("referentiels")
        referentials_dir.mkdir(exist_ok=True)
        with open(referentials_dir / f"{name}.json", "w", encoding="utf-8") as f:
            json.dump(ref_data, f, indent=2, ensure_ascii=False)
        st.success(t("admin.upload_success"))
    except Exception as e:
        st.error(f"{t('admin.upload_fail')} : {e}")
