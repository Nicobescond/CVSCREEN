import streamlit as st
import plotly.graph_objects as go

def afficher_jauge(titre, valeur):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valeur * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': titre},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "green" if valeur >= 0.75 else "orange" if valeur >= 0.5 else "red"},
            'steps': [
                {'range': [0, 50], 'color': "#f8d7da"},
                {'range': [50, 75], 'color': "#fff3cd"},
                {'range': [75, 100], 'color': "#d4edda"}
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)
