import datetime
import os
import sqlite3
import base64
import streamlit as st

DB_FILE = "rifas_v4.db"

st.set_page_config(
    page_title="Rifas Sirio RD",
    page_icon="logo.png" if os.path.exists("logo.png") else "🎲",
    layout="wide"
)

# =========================================================
# GESTIÓN DE TEMA (CLARO / OSCURO)
# =========================================================
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"

def toggle_theme():
    st.session_state["theme_mode"] = "light" if st.session_state["theme_mode"] == "dark" else "dark"

is_dark = st.session_state["theme_mode"] == "dark"

bg_style = """
    background-color: #0b0f17;
    background-image: 
        radial-gradient(#d4af37 0.75px, transparent 0.75px), 
        repeating-linear-gradient(45deg, rgba(212, 175, 55, 0.05) 0, rgba(212, 175, 55, 0.05) 10px, transparent 0, transparent 20px);
    background-size: 15px 15px, 40px 40px;
    color: #FFFFFF;
""" if is_dark else """
    background-color: #f8fafc;
    background-image: 
        radial-gradient(#c0a028 0.85px, transparent 0.85px), 
        repeating-linear-gradient(45deg, rgba(212, 175, 55, 0.08) 0, rgba(212, 175, 55, 0.08) 10px, transparent 0, transparent 20px);
    background-size: 15px 15px, 40px 40px;
    color: #0f172a;
"""

text_color = "#FFFFFF" if is_dark else "#0f172a"

# =========================================================
# ESTILOS CSS PERSONALIZADOS (BANCOS Y BARRA)
# =========================================================
st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    .stApp {{
        {bg_style}
    }}
    
    .logo-hero-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 15px 0;
    }}

    .bank-card-container {{
        position: relative;
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 2px solid #38bdf8;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        color: #ffffff;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }}

    .badge-pop {{
        background: linear-gradient(90deg, #f5c518, #ff8c00);
        color: #000;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
    }}

    /* Contenedor interactivo para los botones de banco */
    .bank-card-wrapper {{
        position: relative;
        width: 135px;
        height: 110px;
        margin: 0 auto;
    }}

    /* Superposición transparente táctil y de clic sobre el 100% de la tarjeta */
    .bank-card-wrapper div[data-testid="stButton"] {{
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
