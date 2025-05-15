import streamlit as st
from utils.auth import app_login, check_access, logout

# --- Page Setup ---
st.set_page_config(page_title="Trade Sheet Menu", layout="wide")
st.title("📒 Trade Sheet Dashboard")

# --- AUTH ---
if not app_login():
    st.stop()
if not check_access("trade_sheet"):
    st.stop()
logout("trade_sheet")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🛒 Purchase Trade", 
    "💵 USD Trade", 
    "🇬🇭 GHS Trade", 
    "🔁 Swap Trade"
])

# --- Modular Imports ---
from pages.trade_sheet.purchase_trade_module import render_purchase_trade
from pages.trade_sheet.usd_trade_module import render_usd_trade
from pages.trade_sheet.ghs_trade_module import render_ghs_trade
from pages.trade_sheet.swap_trade_module import render_swap_trade

# --- Tab Views ---
with tab1:
    st.markdown("### 🛒 Purchase Trade")
    render_purchase_trade()

with tab2:
    st.markdown("### 💵 USD Trade")
    render_usd_trade()

with tab3:
    st.markdown("### 🇬🇭 GHS Trade")
    render_ghs_trade()

with tab4:
    st.markdown("### 🔁 Swap Trade")
    render_swap_trade()
