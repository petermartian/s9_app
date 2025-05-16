
import streamlit as st
from utils.auth import app_login, check_access, logout

# --- PAGE CONFIG ---
st.set_page_config(page_title="Daily Transactions", layout="wide")
st.title("🧾 Daily Transaction Dashboard")

# --- AUTH ---
if not app_login():
    st.stop()
if not check_access("daily_transaction"):
    st.stop()
logout("daily_transaction")

# --- SUBMODULE TABS ---
tab1, tab2, tab3 = st.tabs([
    "📌 At a Glance",
    "💱 USD/NGN",
    "💸 Expenses"
])

with tab1:
    from pages.daily_transaction.at_a_glance_module import render_at_a_glance
    render_at_a_glance()

with tab2:
    from pages.daily_transaction.usdngn_module import render_usdngn
    render_usdngn()

with tab3:
    from pages.daily_transaction.expenses_module import render_expenses
    render_expenses()
