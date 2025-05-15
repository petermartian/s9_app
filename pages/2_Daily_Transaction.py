import streamlit as st
from utils.auth import app_login, check_access, logout

# --- CONFIG ---
st.set_page_config(page_title="Daily Transactions", layout="wide")
st.title("💼 Daily Transaction Dashboard")

# --- AUTH ---
if not app_login():
    st.stop()
if not check_access("daily_transaction"):
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.image("assets/salmnine_logo.png", width=150)
    st.markdown("---")
    st.markdown("📞 Support: operations@salmnine.com")
    st.markdown("_v1.0 - Salmnine Internal_")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 At a Glance", "💵 USD/NGN Transactions", "🧾 Expense Report"])

# --- ROUTE TO SUBMODULES ---
with tab1:
    from pages.daily_transaction import at_a_glance_module
    at_a_glance_module.run_page()

with tab2:
    from pages.daily_transaction import usdngn_module
    usdngn_module.run_page()

with tab3:
    from pages.daily_transaction import expenses_module
    expenses_module.run_page()

# --- LOGOUT ---
logout("daily_transaction")