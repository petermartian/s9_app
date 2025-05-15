import streamlit as st
from utils.auth import check_access, logout

# --- AUTH FOR FINANCE PAGE ---
if not check_access("finance"):
    st.stop()

# --- LOGOUT BUTTON ---
logout("finance")

# --- FINANCE PAGE CONTENT ---
st.title("💰 Finance Dashboard")
st.markdown("""
This section is for the **Finance Team** to:

- 📊 Review financial summaries
- 🧾 Manage budgets and forecasts
- 📄 Export financial reports

### Coming Soon
- Financial KPIs
- Budget tracking charts
- Report generation tools
""")
