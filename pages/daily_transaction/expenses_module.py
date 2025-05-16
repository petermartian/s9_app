import streamlit as st
import pandas as pd
from datetime import date
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from utils.auth import get_gspread_client

def render_expenses():
    EXPENSE_SHEET_KEY = "1PqngUtZTmt0c_CV8uq--3HHMx40SvBE3yB-FICcLpiA"
    EXPENSE_TAB = "expenses"
    BANK_SHEET_KEY = "1RJPEK_ye59vA8ngWiTUYkJZ-xOc815TyKsQ3-f6u4kk"
    BANK_TAB = "List of A/C"

    @st.cache_data(ttl=60)
    def load_expenses():
        client = get_gspread_client()
        sheet = client.open_by_key(EXPENSE_SHEET_KEY)
        ws = sheet.worksheet(EXPENSE_TAB)
        df = pd.DataFrame(ws.get_all_records())
        return df, ws

    @st.cache_data(ttl=60)
    def load_bank_details():
        client = get_gspread_client()
        sheet = client.open_by_key(BANK_SHEET_KEY)
        df = pd.DataFrame(sheet.worksheet(BANK_TAB).get_all_records())
        if "Bank Details" in df.columns:
            return df["Bank Details"].dropna().unique().tolist()
        return []

    df, worksheet = load_expenses()
    df.columns = [str(col).strip().title() for col in df.columns]
    bank_options = load_bank_details()

    st.subheader("💸 Expenses Entry")

    with st.form("expense_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            expense_date = st.date_input("Date", value=date.today())
            description = st.text_input("Expense Description")
        with col2:
            amount_ngn = st.number_input("Amount NGN", min_value=0.0)
            amount_usd = st.number_input("Amount USD", min_value=0.0)
            bank = st.selectbox("Bank", options=bank_options)
        submitted = st.form_submit_button("✅ Submit Expense")

    if submitted:
        new_row = {
            "Date": expense_date.strftime("%Y-%m-%d"),
            "Expense Description": description,
            "Amount NGN": round(amount_ngn, 2),
            "Amount USD": round(amount_usd, 2),
            "Bank": bank
        }
        safe_row = [[str(v) if pd.isna(v) else v for v in new_row.values()]]
        worksheet.append_rows(safe_row)
        st.success("✅ Expense recorded successfully!")
        st.rerun()

    st.markdown("### 📋 Expenses Table")
    col_refresh, _ = st.columns([1, 9])
    with col_refresh:
        if st.button("🔄 Refresh Data", key="expense_refresh_btn"):
            st.cache_data.clear()
            st.rerun()

    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["Date"].notna()]
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination()
        gb.configure_default_column(editable=True, filter=True, resizable=True)
        grid_response = AgGrid(
            df,
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.VALUE_CHANGED,
            fit_columns_on_grid_load=True,
            height=350
        )

        updated_df = grid_response["data"]
        if not updated_df.equals(df):
            worksheet.update([updated_df.columns.values.tolist()] + updated_df.values.tolist())
            st.success("✅ Table updates saved!")
    else:
        st.info("ℹ️ No data available in Expenses sheet.")
