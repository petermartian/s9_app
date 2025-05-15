
import streamlit as st
import pandas as pd
import time
from datetime import date
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import plotly.express as px
from utils.auth import get_gspread_client

def render_purchase_trade():
    # --- CONFIG ---
    TRADE_SHEET_KEY = "1eQS-LZLfsGmhySVHS6ETaKNmBP6bRngtDUiy-Nq0YXw"
    TRADE_TAB = "Purchase Trade"
    DATABASE_SHEET_KEY = "1j_D2QiaS3IEJuNI27OA56l8nWWatzxidLKuqV4Dfet4"
    SELLER_TAB = "Seller List"

    @st.cache_data(ttl=60)
    def load_seller_list():
        client = get_gspread_client()
        db_sheet = client.open_by_key(DATABASE_SHEET_KEY)
        seller_ws = db_sheet.worksheet(SELLER_TAB)
        df = pd.DataFrame(seller_ws.get_all_records())
        return df.iloc[:, 0].dropna().tolist()

    @st.cache_data(ttl=60)
    def load_trade_data():
        client = get_gspread_client()
        trade_sheet = client.open_by_key(TRADE_SHEET_KEY)
        ws = trade_sheet.worksheet(TRADE_TAB)
        df = pd.DataFrame(ws.get_all_records())
        return df, ws

    st.subheader("💱 Purchase Trade")

    seller_data = load_seller_list()
    df_trade, worksheet = load_trade_data()

    # --- Form ---
    with st.form("purchase_trade_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            trade_date = st.date_input("Date", value=date.today())
            trade_type = st.selectbox("Buy/Sell", ["Buy", "Sell"])
            trade_currency = st.text_input("Trade Currency")
            rate = st.number_input("Rate", format="%.2f")
        with col2:
            trade_customer = st.selectbox("Trade Customer", seller_data)
            ngn_amount = st.number_input("NGN Amount", format="%.2f")
            naira_paid = st.number_input("Naira Paid", format="%.2f")

        trade_size = ngn_amount / rate if rate else 0
        naira_balance = ngn_amount - naira_paid

        submitted = st.form_submit_button("Add Trade")
        if submitted and trade_customer:
            new_row = {
                "Date": trade_date.strftime("%Y-%m-%d"),
                "Buy/Sell": trade_type,
                "Trade Customer": trade_customer,
                "Trade Currency": trade_currency,
                "Trade Size": round(trade_size, 2),
                "Rate": rate,
                "NGN Amount": ngn_amount,
                "Naira Paid": naira_paid,
                "Naira Balance": naira_balance
            }
            worksheet.append_rows([list(new_row.values())])
            st.success("Trade added successfully.")
            st.rerun()

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("### 📋 Trade Table")
    gb = GridOptionsBuilder.from_dataframe(df_trade)
    gb.configure_pagination()
    gb.configure_default_column(editable=False)

    AgGrid(
        df_trade,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=True,
        height=400,
        reload_data=False
    )

    st.markdown("### 📊 Summary")
    required_cols = ["Buy/Sell", "Trade Size", "NGN Amount"]
    if all(col in df_trade.columns for col in required_cols):
        summary = df_trade.groupby("Buy/Sell")[["Trade Size", "NGN Amount"]].sum().round(2)
        st.dataframe(summary)
    else:
        st.warning("⚠️ Summary table not shown. Required columns are missing.")

    if "Date" in df_trade.columns and "Trade Size" in df_trade.columns:
        st.markdown("### 📈 Weekly Trade Size")
        df_trade["Week"] = pd.to_datetime(df_trade["Date"], errors="coerce").dt.to_period("W").astype(str)
        weekly_chart = df_trade.groupby("Week")["Trade Size"].sum().reset_index()
        fig = px.bar(weekly_chart, x="Week", y="Trade Size", title="Weekly Trade Size")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📆 No valid 'Date' or 'Trade Size' data available for chart.")
