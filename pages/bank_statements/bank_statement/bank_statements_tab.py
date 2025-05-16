
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from datetime import date
from utils.auth import get_gspread_client

def render_bank_statements():
    SHEET_KEY = "1RJPEK_ye59vA8ngWiTUYkJZ-xOc815TyKsQ3-f6u4kk"
    TAB_NAME = "List of A/C"

    @st.cache_data(ttl=60)
    def load_data():
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_KEY)
        ws = sheet.worksheet(TAB_NAME)
        df = pd.DataFrame(ws.get_all_records())
        return df, ws

    df, worksheet = load_data()
    df.columns = [str(col).strip().title() for col in df.columns]

    st.subheader("📄 Add Bank Account")

    with st.form("bank_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            account_name = st.text_input("Account Name")
            account_number = st.text_input("Account Number")
            bank = st.text_input("Bank")
        with col2:
            bank_details = st.text_input("Bank Details")
            concession_usd = st.number_input("Concession USD", min_value=0.0, format="%.2f")
            concession_ngn = st.number_input("Concession NGN", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("✅ Submit")

    if submitted:
        new_row = {
            "Account Name": account_name,
            "Account Number": account_number,
            "Bank": bank,
            "Bank Details": bank_details,
            "Concession USD": round(concession_usd, 2),
            "Concession NGN": round(concession_ngn, 2)
        }
        safe_row = [[str(v) if pd.isna(v) else v for v in new_row.values()]]
        worksheet.append_rows(safe_row)
        st.success("✅ Bank record submitted!")
        st.rerun()

    st.markdown("### 📋 Bank Account Table")
    col_refresh, _ = st.columns([1, 9])
    with col_refresh:
        if st.button("🔄 Refresh Data", key="bank_refresh_btn"):
            st.cache_data.clear()
            st.rerun()

    if not df.empty:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination()
        gb.configure_default_column(editable=True, filter=True, resizable=True)
        grid_response = AgGrid(
            df,
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.VALUE_CHANGED,
            fit_columns_on_grid_load=True,
            height=400
        )

        updated_df = grid_response["data"]
        if not updated_df.equals(df):
            worksheet.update([updated_df.columns.values.tolist()] + updated_df.values.tolist())
            st.success("✅ Table updates saved.")
    else:
        st.info("ℹ️ No data found in Bank Statements sheet.")

