
import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import io
import xlsxwriter
from utils.auth import get_gspread_client

def render_swap_trade():
    TRADE_SHEET_KEY = "1eQS-LZLfsGmhySVHS6ETaKNmBP6bRngtDUiy-Nq0YXw"
    TRADE_TAB = "Swap Trade"
    DATABASE_SHEET_KEY = "1j_D2QiaS3IEJuNI27OA56l8nWWatzxidLKuqV4Dfet4"
    CLIENT_TAB = "Client List"

    @st.cache_data(ttl=60)
    def load_clients():
        client = get_gspread_client()
        sheet = client.open_by_key(DATABASE_SHEET_KEY)
        df = pd.DataFrame(sheet.worksheet(CLIENT_TAB).get_all_records())
        return df.iloc[:, 0].dropna().tolist()

    @st.cache_data(ttl=60)
    def load_swap_trades():
        client = get_gspread_client()
        sheet = client.open_by_key(TRADE_SHEET_KEY)
        ws = sheet.worksheet(TRADE_TAB)
        df = pd.DataFrame(ws.get_all_records())
        return df, ws

    client_list = load_clients()
    df, worksheet = load_swap_trades()
    df.columns = df.columns.str.strip().str.title()

    st.subheader("🔄 Swap Trade Entry")

    with st.form("swap_trade_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            trade_date = st.date_input("Date", value=date.today(), key="swap_date")
            client_name = st.selectbox("Client", client_list)
            usd_received = st.number_input("USD Received", min_value=0.0)
            charges_pct = st.number_input("Charges (%)", min_value=0.0, step=0.1)
            charges_usdt = (charges_pct / 100) * usd_received
            usdt_due = usd_received - charges_usdt
            st.markdown(f"**Charges (USDT):** {charges_usdt:,.2f}")
            st.markdown(f"**USDT Due:** {usdt_due:,.2f}")
        with col2:
            usdt_paid = st.number_input("USDT Paid", min_value=0.0)
            usd_status = st.selectbox("USD Status", ["Pending", "Completed"])
            usdt_status = st.selectbox("USDT Status", ["Pending", "Completed"])
            date_received = st.date_input("Date Received", value=date.today(), key="swap_date_received")
            date_sent = st.date_input("Date Sent", value=date.today(), key="swap_date_sent")
            net_profit = usd_received - usdt_due
            st.markdown(f"**Net Profit (auto):** {net_profit:,.2f}")
        submitted = st.form_submit_button("✅ Submit Swap Trade")

    if submitted:
        new_row = {
            "Date": trade_date.strftime("%Y-%m-%d"),
            "Client": client_name,
            "USD Received": round(usd_received, 2),
            "Charges %": round(charges_pct, 2),
            "Charges (Usdt)": round(charges_usdt, 2),
            "Usdt Due": round(usdt_due, 2),
            "Usdt Paid": round(usdt_paid, 2),
            "Usd Status": usd_status,
            "Usdt Status": usdt_status,
            "Date Received": date_received.strftime("%Y-%m-%d"),
            "Date Sent": date_sent.strftime("%Y-%m-%d"),
            "Net Profit": round(net_profit, 2)
        }
        safe_row = [[str(v) if pd.isna(v) else v for v in new_row.values()]]
        worksheet.append_rows(safe_row)
        st.success("✅ Swap trade submitted successfully!")
        st.rerun()

    st.markdown("### 📋 Swap Trades Table")
    col_refresh, _ = st.columns([1, 9])
    with col_refresh:
        if st.button("🔄 Refresh Data", key="swap_refresh_btn"):
            st.cache_data.clear()
            st.rerun()

    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["Date"].notna()]
        start = st.date_input("📅 Start Date", df["Date"].min().date(), key="swap_start")
        end = st.date_input("📅 End Date", df["Date"].max().date(), key="swap_end")
        df_filtered = df[(df["Date"] >= pd.to_datetime(start)) & (df["Date"] <= pd.to_datetime(end))]

        for col in ["Net Profit", "Usdt Due"]:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors="coerce")

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

        st.markdown("### 📊 Summary")
        df_filtered["Week"] = df_filtered["Date"].dt.isocalendar().week
        df_filtered["Month"] = df_filtered["Date"].dt.month

        summary = {
            "Period": ["Daily", "Weekly", "Monthly"],
            "Net Profit": [
                df_filtered[df_filtered["Date"] == pd.to_datetime(date.today())]["Net Profit"].sum(),
                df_filtered[df_filtered["Week"] == date.today().isocalendar().week]["Net Profit"].sum(),
                df_filtered[df_filtered["Month"] == date.today().month]["Net Profit"].sum()
            ],
            "USDT Due": [
                df_filtered[df_filtered["Date"] == pd.to_datetime(date.today())]["Usdt Due"].sum(),
                df_filtered[df_filtered["Week"] == date.today().isocalendar().week]["Usdt Due"].sum(),
                df_filtered[df_filtered["Month"] == date.today().month]["Usdt Due"].sum()
            ]
        }
        df_summary = pd.DataFrame(summary)
        st.dataframe(df_summary.style.set_properties(**{
            'font-weight': 'bold', 'background-color': '#fff3e0', 'color': '#000'
        }), use_container_width=True)

        st.markdown("### 📈 Weekly Net Profit")
        chart = df_filtered.groupby("Week")["Net Profit"].sum().reset_index()
        fig = px.bar(chart, x="Week", y="Net Profit", title="Weekly Net Profit")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📤 Export Summary")
        excel_out = io.BytesIO()
        with pd.ExcelWriter(excel_out, engine="xlsxwriter") as writer:
            df_summary.to_excel(writer, index=False, sheet_name="Summary")
            chart.to_excel(writer, index=False, sheet_name="Chart")
        st.download_button("⬇️ Download Excel", data=excel_out.getvalue(),
                           file_name="swap_trade_summary.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("ℹ️ No data available in Swap Trade sheet.")
