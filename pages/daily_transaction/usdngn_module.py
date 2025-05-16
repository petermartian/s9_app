
import streamlit as st
import pandas as pd
from datetime import date
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from utils.auth import get_gspread_client

def render_usdngn():
    SHEET_KEY = "1PqngUtZTmt0c_CV8uq--3HHMx40SvBE3yB-FICcLpiA"
    TAB_NAME = "usdngn"

    @st.cache_data(ttl=60)
    def load_data():
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_KEY)
        ws = sheet.worksheet(TAB_NAME)
        df = pd.DataFrame(ws.get_all_records())
        return df, ws

    df, worksheet = load_data()
    df.columns = df.columns.str.strip().str.title()

    st.subheader("💱 USD/NGN Tracker")

    with st.form("usdngn_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            record_date = st.date_input("Date", value=date.today())
            source = st.text_input("Source")
            rate = st.number_input("Rate", format="%.2f")
        with col2:
            comment = st.text_area("Comment")
        submitted = st.form_submit_button("✅ Submit Rate")

    if submitted:
        new_row = {
            "Date": record_date.strftime("%Y-%m-%d"),
            "Source": source,
            "Rate": round(rate, 2),
            "Comment": comment
        }
        safe_row = [[str(v) if pd.isna(v) else v for v in new_row.values()]]
        worksheet.append_rows(safe_row)
        st.success("✅ USD/NGN rate added successfully!")
        st.rerun()

    st.markdown("### 📋 USD/NGN Rates Table")
    col_refresh, _ = st.columns([1, 9])
    with col_refresh:
        if st.button("🔄 Refresh Data", key="usdngn_refresh_btn"):
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
        st.info("ℹ️ No data available in USD/NGN sheet.")
