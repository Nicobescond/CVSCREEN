def run():
    import streamlit as st
    from datetime import datetime
    import json, io
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    st.header("📄 Analyse comparative de CV")

    uploaded = st.file_uploader("Uploader un CV PDF", type="pdf")
    if uploaded:
        st.success("CV reçu. Simulation d'analyse...")
        synthese = "Le candidat possède une expérience intéressante en audit IFS."
        score = 0.75

        def generate_pdf_report(cv_name, synthese, score):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer)
            styles = getSampleStyleSheet()
            story = [
                Paragraph("Rapport IA - Analyse de CV", styles["Title"]),
                Paragraph(f"Candidat : {cv_name}", styles["Normal"]),
                Paragraph(f"Score : {score*100:.0f}%", styles["Normal"]),
                Paragraph("Synthèse IA :", styles["Heading2"]),
                Paragraph(synthese, styles["Normal"])
            ]
            doc.build(story)
            buffer.seek(0)
            return buffer

        pdf_buffer = generate_pdf_report(uploaded.name, synthese, score)
        st.download_button("📄 Télécharger le rapport PDF", data=pdf_buffer, file_name="rapport_cv.pdf", mime="application/pdf")
