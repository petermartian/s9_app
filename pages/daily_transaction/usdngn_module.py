import streamlit as st
import pandas as pd
from datetime import date
from calendar import month_name
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from utils.auth import get_gspread_client

def render_usdngn():
    SHEET_KEY = "1PqngUtZTmt0c_CV8uq--3HHMx40SvBE3yB-FICcLpiA"
    TAB_NAME = "usdngn"
    DATABASE_KEY = "1j_D2QiaS3IEJuNI27OA56l8nWWatzxidLKuqV4Dfet4"
    SELLER_TAB = "Seller List"
    CLIENT_TAB = "Client List"
    TXN_TYPE_TAB = "Transaction type"

    @st.cache_data(ttl=3600)
    def get_dropdown_list(tab):
        client = get_gspread_client()
        sheet = client.open_by_key(DATABASE_KEY)
        try:
            ws = sheet.worksheet(tab)
            df = pd.DataFrame(ws.get_all_values())
            if not df.empty:
                return df.iloc[1:, 0].dropna().tolist()
            return []
        except Exception as e:
            st.warning(f"Tab '{tab}' not found in the database sheet. Please check spelling/casing.")
            return []

    seller_list = get_dropdown_list(SELLER_TAB)
    client_list = get_dropdown_list(CLIENT_TAB)
    txn_type_list = get_dropdown_list(TXN_TYPE_TAB)

    @st.cache_data(ttl=60)
    def load_data():
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_KEY)
        ws = sheet.worksheet(TAB_NAME)
        df = pd.DataFrame(ws.get_all_records())
        return df, ws

    df, worksheet = load_data()
    df.columns = [str(col).strip() for col in df.columns]

    st.subheader("💱 USD/NGN Tracker")

    with st.form("usdngn_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            record_date = st.date_input("Date", value=date.today())
            month = month_name[record_date.month]
            selling_client = st.selectbox("Selling Client", seller_list)
            bank_paid_from = st.text_input("Bank Paid From")
            buy_rate = st.number_input("Buy Rate", min_value=0.0, format="%.2f")
        with col2:
            buying_client = st.selectbox("Buying Client", client_list)
            txn_type = st.selectbox("Transaction Type", txn_type_list)
            sell_rate = st.number_input("Sell Rate", min_value=0.0, format="%.2f")
            fcy_total_value = st.number_input("Fcy Total Value", min_value=0.0, format="%.2f")
            total_fcy_paid_to_client = st.number_input("Total Fcy Paid To Client", min_value=0.0, format="%.2f")
            lcy_payments = st.number_input("Lcy Payments", min_value=0.0, format="%.2f")
        
        # --- Computed Fields ---
        lcy_value = fcy_total_value * sell_rate
        fcy_outstanding = round(fcy_total_value - total_fcy_paid_to_client, 0)
        lcy_outstanding = round(max(lcy_value - lcy_payments, 0), 0)
        spread = (lcy_payments / fcy_total_value - sell_rate) if fcy_total_value != 0 else 0
        commission = spread * fcy_total_value
        profit_ngn = (sell_rate - buy_rate) * fcy_total_value

        our_obli_status = "OUTSTANDING" if (txn_type and txn_type.lower() == "sales" and fcy_outstanding > 0) or lcy_outstanding > 0 else "COMPLETED"
        customer_obli_status = "OUTSTANDING" if lcy_outstanding > 0 else "COMPLETED"
        status = "EXCESS PAYMENT PLEASE REVIEW" if fcy_outstanding < 0 else ""

        st.markdown("#### 🧮 Computed Fields Preview")
        preview_dict = {
            "profit (ngn)": profit_ngn,
            "spread": spread,
            "lcy value": lcy_value,
            "fcy outstanding": fcy_outstanding,
            "lcy outstanding": lcy_outstanding,
            "commission": commission,
            "our obli. status": our_obli_status,
            "customer obli status": customer_obli_status,
            "status": status
        }
        st.json(preview_dict)

        submitted = st.form_submit_button("✅ Submit Transaction")

    def sanitize(val):
        try:
            import numpy as np
            if isinstance(val, (np.generic,)):
                return float(val)
        except ImportError:
            pass
        if isinstance(val, (float, int)):
            return float(val)
        return str(val)

    if submitted:
        new_row = {
            "Date": record_date.strftime("%Y-%m-%d"),
            "Month": month,
            "Selling Client": selling_client,
            "Bank Paid From": bank_paid_from,
            "Buy Rate": buy_rate,
            "Buying Client": buying_client,
            "Transaction Type": txn_type,
            "Sell Rate": sell_rate,
            "Fcy Total Value": fcy_total_value,
            "Total Fcy Paid To Client": total_fcy_paid_to_client,
            "Lcy Payments": lcy_payments,
            "Profit (Ngn)": profit_ngn,
            "Spread": spread,
            "Lcy Value": lcy_value,
            "Fcy Outstanding": fcy_outstanding,
            "Lcy Outstanding": lcy_outstanding,
            "Commission": commission,
            "Our Obli. Status": our_obli_status,
            "Customer Obli Status": customer_obli_status,
            "Status": status,
        }
        worksheet.append_row([sanitize(v) for v in new_row.values()])
        st.success("✅ USD/NGN transaction added successfully!")
        st.rerun()

    # --- Display Table ---
    st.markdown("### 📋 USD/NGN Transactions Table")
    col_refresh, _ = st.columns([1, 9])
    with col_refresh:
        if st.button("🔄 Refresh Data", key="usdngn_refresh_btn"):
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
            st.success("✅ Table updates saved!")
    else:
        st.info("ℹ️ No data available in USD/NGN sheet.")

    # ---- SUMMARY TABLES SECTION WITH DATE FILTER ----
    st.markdown("## 📅 Filter Summaries by Date Range")

    # Always show the filter if df has a Date column and is not empty
    if not df.empty and "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["Date"].notna()]

        min_date = df["Date"].min().date()
        max_date = df["Date"].max().date()
        default_start = max_date.replace(day=1)
        start_date, end_date = st.date_input(
            "Select date range:",
            value=(default_start, max_date),
            min_value=min_date,
            max_value=max_date
        )

        mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
        filtered_df = df.loc[mask].copy()
    else:
        st.info("No data to filter.")
        filtered_df = pd.DataFrame()

    if not filtered_df.empty:
        # Only sales
        sales_df = filtered_df[filtered_df["Transaction Type"].str.lower() == "sales"].copy()

        for col in ["Profit (Ngn)", "Lcy Value", "Fcy Total Value"]:
            sales_df[col] = pd.to_numeric(sales_df[col], errors="coerce").fillna(0)

        if not sales_df.empty:
            # Daily
            daily_summary = sales_df.groupby("Date")[["Profit (Ngn)", "Lcy Value", "Fcy Total Value"]].sum().reset_index()
            st.markdown("### 📈 Daily Summary (Sales Only)")
            st.dataframe(daily_summary, hide_index=True)

            # Weekly
            sales_df["Year"] = sales_df["Date"].dt.year
            sales_df["Week"] = sales_df["Date"].dt.isocalendar().week
            weekly_summary = sales_df.groupby(["Year", "Week"])[["Profit (Ngn)", "Lcy Value", "Fcy Total Value"]].sum().reset_index()
            st.markdown("### 📈 Weekly Summary (Sales Only)")
            st.dataframe(weekly_summary, hide_index=True)

            # Monthly
            sales_df["MonthStr"] = sales_df["Date"].dt.strftime('%Y-%m')
            monthly_summary = sales_df.groupby("MonthStr")[["Profit (Ngn)", "Lcy Value", "Fcy Total Value"]].sum().reset_index()
            st.markdown("### 📈 Monthly Summary (Sales Only)")
            st.dataframe(monthly_summary, hide_index=True)
        else:
            st.info("No sales data found in the selected date range.")
    else:
        st.info("No data found in the selected date range.")

