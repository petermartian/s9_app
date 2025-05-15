import streamlit as st
from utils.auth import check_access, logout  # Import logout

# --- AUTH ---
if not check_access("bank_statement"):
    st.stop()

# --- PAGE CONTENT ---
st.set_page_config(page_title="Bank Statements", layout="wide")
st.title("🏦 Bank Statement Upload")

# --- LOGOUT BUTTON ---
logout("bank_statement")  # Add logout button

# Placeholder for upload logic
st.markdown("Upload and manage your bank statements here.")
# Bank statement upload and reconciliation