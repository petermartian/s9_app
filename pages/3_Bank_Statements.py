import streamlit as st
from bank_statements_tab import render_bank_statement


st.set_page_config(page_title="Bank Statements", layout="wide")
st.title("🏦 Bank Statement Module")

tab1, tab2 = st.tabs(["📄 Bank Statements", "💰 Bank Balance"])

with tab1:
    render_bank_statements()

with tab2:
    st.info("💡 Bank Balance tab coming soon...")
