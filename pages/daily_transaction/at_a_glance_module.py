
import streamlit as st
import pandas as pd
from datetime import date
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from utils.auth import get_gspread_client

def render_at_a_glance():
    SHEET_KEY = "1PqngUtZTmt0c_CV8uq--3HHMx40SvBE3yB-FICcLpiA"
    TAB_NAME = "at_a_glance"

    @st.cache_data(ttl=60)
    def load_data():
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_KEY)
        ws = sheet.worksheet(TAB_NAME)
        df = pd.DataFrame(ws.get_all_records())
        return df, ws

    df, worksheet = load_data()
    df.columns = [str(col).strip().title() for col in df.columns]  # safer handling

    st.subheader("📌 At a Glance Summary")

    with st.form("glance_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            record_date = st.date_input("Date", value=date.today())
            account_name = st.text_input("Account Name")
            opening_balance = st.number_input("Opening Balance", format="%.2f")
        with col2:
            closing_balance = st.number_input("Closing Balance", format="%.2f")
            inflow = st.number_input("Inflow", format="%.2f")
            outflow = st.number_input("Outflow", format="%.2f")

        submitted = st.form_submit_button("✅ Submit Summary")

    if submitted:
        new_row = {
            "Date": record_date.strftime("%Y-%m-%d"),
            "Account Name": account_name,
            "Opening Balance": round(opening_balance, 2),
            "Closing Balance": round(closing_balance, 2),
            "Inflow": round(inflow, 2),
            "Outflow": round(outflow, 2)
        }
        safe_row = [[str(v) if pd.isna(v) else v for v in new_row.values()]]
        worksheet.append_rows(safe_row)
        st.success("✅ Summary recorded successfully!")
        st.rerun()

    st.markdown("### 📋 Daily Balances Table")
    col_refresh, _ = st.columns([1, 9])
    with col_refresh:
        if st.button("🔄 Refresh Data", key="glance_refresh_btn"):
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
        st.info("ℹ️ No data available in At a Glance sheet.")
