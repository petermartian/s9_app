import streamlit as st
import os
from utils.auth import app_login, check_access, logout  # Import all auth functions

st.set_page_config(page_title="Salmnine Trade Report", layout="wide")

# --- APP LOGIN ---
if not app_login():
    st.stop()

# --- AUTH FOR MAIN PAGE (if needed) ---
if not check_access("main"):
    st.stop()

# --- LOGOUT BUTTON ---
logout("main")

# --- LOGO ---
logo_path = os.path.join("assets", "salmnine_logo.png")
if os.path.exists(logo_path):
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(logo_path, width=100)
    with col2:
        st.title("Salmnine Investment Ltd")
else:
    st.title("Salmnine Investment Ltd")

# --- WELCOME ---
st.markdown("### 👋 Welcome to the **Trade Reporting Suite**")
st.markdown("""
This internal dashboard helps our **Treasury**, **Accounts**, and **Management** teams:

- 📌 Capture and track daily trades (NGN, USD, GHS, Swap)
- 📊 Visualize performance via summaries and charts
- 🧾 Upload and reconcile bank statements
- 📄 Download reports in Excel and PDF
- 💼 Gain a complete financial overview

> Start by selecting a section from the **left-hand menu**.
""")