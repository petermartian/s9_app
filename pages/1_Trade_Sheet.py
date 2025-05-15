import streamlit as st
from utils.auth import app_login, check_access, logout

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

with tab1:
    from pages.trade_sheet.purchase_trade_module import *
    st.markdown("### 🛒 Purchase Trade")

with tab2:
    from pages.trade_sheet.usd_trade_module import *
    st.markdown("### 💵 USD Trade")

with tab3:
    from pages.trade_sheet.ghs_trade_module import *
    st.markdown("### 🇬🇭 GHS Trade")

with tab4:
    from pages.trade_sheet.swap_trade_module import *
    st.markdown("### 🔁 Swap Trade")