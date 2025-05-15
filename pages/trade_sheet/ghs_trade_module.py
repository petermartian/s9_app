
import streamlit as st
import pandas as pd
from datetime import date
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from utils.auth import get_gspread_client

def render_ghs_trade():
    TRADE_SHEET_KEY = "1eQS-LZLfsGmhySVHS6ETaKNmBP6bRngtDUiy-Nq0YXw"
    TRADE_TAB = "GHS Trade"
    DATABASE_SHEET_KEY = "1j_D2QiaS3IEJuNI27OA56l8nWWatzxidLKuqV4Dfet4"
    CLIENT_TAB = "Client List"
    SELLER_TAB = "Seller List"

    @st.cache_data(ttl=60)
    def load_clients():
        client = get_gspread_client()
        sheet = client.open_by_key(DATABASE_SHEET_KEY)
        return pd.DataFrame(sheet.worksheet(CLIENT_TAB).get_all_records()).iloc[:, 0].dropna().tolist()

    @st.cache_data(ttl=60)
    def load_sellers():
        client = get_gspread_client()
        sheet = client.open_by_key(DATABASE_SHEET_KEY)
        return pd.DataFrame(sheet.worksheet(SELLER_TAB).get_all_records()).iloc[:, 0].dropna().tolist()

    @st.cache_data(ttl=60)
    def load_trades():
        client = get_gspread_client()
        sheet = client.open_by_key(TRADE_SHEET_KEY)
        ws = sheet.worksheet(TRADE_TAB)
        df = pd.DataFrame(ws.get_all_records())
        return df, ws

    clients = load_clients()
    sellers = load_sellers()
    df, worksheet = load_trades()

    st.markdown("### 🇬🇭 GHS Trade Entry")

    with st.form("ghs_trade_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            trade_date = st.date_input("Date", value=date.today())
            side = st.selectbox("Buy/Sell", ["Buy", "Sell"])
            customer = st.selectbox("Trade Customer", clients)
            currency = st.text_input("Trade Currency", value="GHS")
            trade_size = st.number_input("Trade Size", min_value=0.0)
            sell_rate = st.number_input("Sell Rate", min_value=0.01)
            amount_ghs = trade_size * sell_rate
            st.markdown(f"**Amount GHS (auto):** ₵{amount_ghs:,.2f}")
            received = st.number_input("Received", min_value=0.0)
            paid_out = st.number_input("Paid Out", min_value=0.0)
            commission = st.number_input("Commission", min_value=0.0)
        with col2:
            amount_ghs2 = st.number_input("Amount GHS 2", min_value=0.0)
            buy_rate = st.number_input("Buy Rate", min_value=0.01)
            trade_size2 = amount_ghs2 / buy_rate if buy_rate != 0 else 0
            st.markdown(f"**Trade Size 2 (auto):** {trade_size2:,.2f}")
            income = trade_size2 - trade_size
            st.markdown(f"**Income (auto):** ₵{income:,.2f}")
            customer2 = st.selectbox("Trade Customer 2", sellers)

        submitted = st.form_submit_button("✅ Submit GHS Trade")

    if submitted:
        new_row = {
            "Date": trade_date.strftime("%Y-%m-%d"),
            "Buy/Sell": side,
            "Trade Customer": customer,
            "Trade Currency": currency,
            "Trade Size": round(trade_size, 2),
            "Sell Rate": round(sell_rate, 2),
            "Amount GHS": round(amount_ghs, 2),
            "Received": round(received, 2),
            "Paid Out": round(paid_out, 2),
            "Commission": round(commission, 2),
            "Income": round(income, 2),
            "Buy Rate": round(buy_rate, 2),
            "Amount GHS 2": round(amount_ghs2, 2),
            "Trade Customer 2": customer2,
            "Trade Size 2": round(trade_size2, 2)
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.success("✅ GHS trade submitted successfully!")
        st.rerun()

    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["Date"].notna()]
        start = st.date_input("📅 Start Date", df["Date"].min().date())
        end = st.date_input("📅 End Date", df["Date"].max().date())
        df_filtered = df[(df["Date"] >= pd.to_datetime(start)) & (df["Date"] <= pd.to_datetime(end))]

        st.markdown("### 📋 Editable Table")
        gb = GridOptionsBuilder.from_dataframe(df_filtered)
        gb.configure_pagination()
        gb.configure_default_column(editable=True, filter=True, resizable=True)
        grid_response = AgGrid(
            df_filtered,
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.VALUE_CHANGED,
            fit_columns_on_grid_load=True,
            height=350
        )

        updated_df = grid_response["data"]
        if not updated_df.equals(df_filtered):
            worksheet.update([updated_df.columns.values.tolist()] + updated_df.values.tolist())
            st.success("✅ Table updates saved!")
    else:
        st.info("ℹ️ No data available in GHS Trade sheet.")
