import streamlit as st
from utils.auth import check_access, logout

st.set_page_config(page_title="Database", layout="wide")

if not check_access("database"):
    st.stop()

st.title("📁 Salmnine Database")
st.write("Logged in as:", st.session_state.auth["database"]["username"])
logout("database")

tab1, tab2, tab3 = st.tabs(["👥 Client List", "🏷️ Seller List", "🔄 Transaction Types"])

with tab1:
    from pages.database.client_list_module import render_client_list
    render_client_list()

with tab2:
    from pages.database.seller_list_module import render_seller_list
    render_seller_list()

with tab3:
    from pages.database.transaction_type_module import render_transaction_type
    render_transaction_type()
