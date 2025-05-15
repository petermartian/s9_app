
import streamlit as st
import pandas as pd
import time
from datetime import date
import plotly.express as px
import io
import xlsxwriter
from utils.auth import get_gspread_client

def render_usd_trade():
    # --- CONFIG ---
    TRADE_SHEET_KEY = "1eQS-LZLfsGmhySVHS6ETaKNmBP6bRngtDUiy-Nq0YXw"
    TRADE_TAB = "USD Trade"
    DATABASE_SHEET_KEY = "1j_D2QiaS3IEJuNI27OA56l8nWWatzxidLKuqV4Dfet4"
    CLIENT_TAB = "Client List"

    @st.cache_data(ttl=60)
    def load_clients():
        client = get_gspread_client()
        sheet = client.open_by_key(DATABASE_SHEET_KEY)
        df = pd.DataFrame(sheet.worksheet(CLIENT_TAB).get_all_records())
        return df.iloc[:, 0].dropna().tolist()

    @st.cache_data(ttl=60)
    def load_usd_trades():
        client = get_gspread_client()
        sheet = client.open_by_key(TRADE_SHEET_KEY)
        ws = sheet.worksheet(TRADE_TAB)
        df = pd.DataFrame(ws.get_all_records())
        return df, ws

    # --- Load Data ---
    client_list = load_clients()
    df, worksheet = load_usd_trades()
    df.columns = df.columns.str.strip().str.title()

    st.subheader("💵 USD Trade Entry")
    with st.form("usd_trade_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            trade_date = st.date_input("Date", value=date.today())
            side = st.selectbox("Buy/Sell", ["Buy", "Sell"])
            customer = st.selectbox("Trade Customer", client_list)
            currency = st.text_input("Trade Currency", value="USD")
            trade_size = st.number_input("Trade Size", min_value=0.0)
            sell_rate = st.number_input("Sell Rate", min_value=0.0)
            buy_rate = st.number_input("Buy Rate", min_value=0.0)
        with col2:
            amount = trade_size * sell_rate if trade_size and sell_rate else 0.0
            st.markdown(f"**Amount (auto):** ₦{amount:,.2f}")
            usd_received = st.number_input("USD Received", min_value=0.0)
            usd_paid_out = st.number_input("USD Paid Out", min_value=0.0)
            commission = st.number_input("Commission", min_value=0.0)
            ngn_income = (sell_rate - buy_rate) * trade_size if trade_size and buy_rate else 0.0
            st.markdown(f"**NGN Income (auto):** ₦{ngn_income:,.2f}")
        submitted = st.form_submit_button("✅ Submit USD Trade")

    if submitted:
        new_row = {
            "Date": trade_date.strftime("%Y-%m-%d"),
            "Buy/Sell": side,
            "Trade Customer": customer,
            "Trade Currency": currency,
            "Trade Size": round(trade_size, 2),
            "Sell Rate": round(sell_rate, 2),
            "Amount": round(amount, 2),
            "USD Received": round(usd_received, 2),
            "USD Paid Out": round(usd_paid_out, 2),
            "Commission": round(commission, 2),
            "NGN Income": round(ngn_income, 2),
            "Buy Rate": round(buy_rate, 2)
        }
        safe_row = [[str(v) if pd.isna(v) else v for v in new_row.values()]]
        worksheet.append_rows(safe_row)
        st.success("✅ Trade submitted successfully!")
        st.rerun()

    if not df.empty and "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["Date"].notna()]
        start = st.date_input("📅 Start Date", df["Date"].min().date())
        end = st.date_input("📅 End Date", df["Date"].max().date())
        df_filtered = df[(df["Date"] >= pd.to_datetime(start)) & (df["Date"] <= pd.to_datetime(end))]

        for col in ["Trade Size", "Amount", "NGN Income"]:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors="coerce")

        df_filtered["Week"] = df_filtered["Date"].dt.isocalendar().week
        df_filtered["Month"] = df_filtered["Date"].dt.month

        summary = {
            "Period": ["Daily", "Weekly", "Monthly"],
            "Trade Size": [
                df_filtered[df_filtered["Date"] == pd.to_datetime(date.today())]["Trade Size"].sum(),
                df_filtered[df_filtered["Week"] == date.today().isocalendar().week]["Trade Size"].sum(),
                df_filtered[df_filtered["Month"] == date.today().month]["Trade Size"].sum()
            ],
            "Amount": [
                df_filtered[df_filtered["Date"] == pd.to_datetime(date.today())]["Amount"].sum(),
                df_filtered[df_filtered["Week"] == date.today().isocalendar().week]["Amount"].sum(),
                df_filtered[df_filtered["Month"] == date.today().month]["Amount"].sum()
            ],
            "NGN Income": [
                df_filtered[df_filtered["Date"] == pd.to_datetime(date.today())]["NGN Income"].sum(),
                df_filtered[df_filtered["Week"] == date.today().isocalendar().week]["NGN Income"].sum(),
                df_filtered[df_filtered["Month"] == date.today().month]["NGN Income"].sum()
            ]
        }
        df_summary = pd.DataFrame(summary)
        st.dataframe(df_summary.style.set_properties(**{
            'font-weight': 'bold', 'background-color': '#f0f4c3', 'color': '#000'
        }), use_container_width=True)

        st.markdown("### 📈 Weekly Trade Size")
        chart = df_filtered.groupby("Week")["Trade Size"].sum().reset_index()
        fig = px.bar(chart, x="Week", y="Trade Size", title="Weekly Trade Volume")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📤 Export Summary")
        excel_out = io.BytesIO()
        with pd.ExcelWriter(excel_out, engine="xlsxwriter") as writer:
            df_summary.to_excel(writer, index=False, sheet_name="Summary")
            chart.to_excel(writer, index=False, sheet_name="Chart")
        st.download_button("⬇️ Download Excel", data=excel_out.getvalue(),
                           file_name="usd_trade_summary.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("No trades found for the selected date range.")
