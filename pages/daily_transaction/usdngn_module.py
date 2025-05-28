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
    TXN_TYPE_TAB = "Transaction Type"

    # Helper to get dropdown lists from DB sheet
    @st.cache_data(ttl=3600)
    def get_dropdown_list(tab):
        client = get_gspread_client()
        sheet = client.open_by_key(DATABASE_KEY)
        ws = sheet.worksheet(tab)
        df = pd.DataFrame(ws.get_all_values())
        if not df.empty:
            return df.iloc[1:, 0].tolist()  # Skip header row
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
    df.columns = [str(col).strip().title() for col in df.columns]

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
            fcy_total_value = st.number_input("FCY Total Value", min_value=0.0, format="%.2f")
            total_fcy_paid_to_client = st.number_input("Total FCY Paid To Client", min_value=0.0, format="%.2f")
            lcy_payments = st.number_input("LCY Payments", min_value=0.0, format="%.2f")
        
        # ==== COMPUTED FIELDS ====
        # All calculations as per your formulas (update if your logic changes!)
        lcy_total_value = fcy_total_value * sell_rate
        fcy_outstanding = round(fcy_total_value - total_fcy_paid_to_client, 0)
        lcy_outstanding = round(max(lcy_total_value - lcy_payments, 0), 0)
        spread = (lcy_payments / fcy_total_value - sell_rate) if fcy_total_value != 0 else 0
        commission = spread * fcy_total_value

        # For profit (ngn), more details would be needed, but let's use a basic spread
        # Placeholder formula (adjust as needed!):
        profit_ngn = (sell_rate - buy_rate) * fcy_total_value

        # Obligation Status logic
        our_obli_status = "OUTSTANDING" if (txn_type.lower() == "sales" and fcy_outstanding > 0) or lcy_outstanding > 0 else "COMPLETED"
        customer_obli_status = "OUTSTANDING" if lcy_outstanding > 0 else "COMPLETED"
        status = "EXCESS PAYMENT PLEASE REVIEW" if fcy_outstanding < 0 else ""

        # ==== LIVE PREVIEW ====
        st.markdown("#### 🧮 Computed Fields Preview")
        preview_dict = {
            "profit (ngn)": profit_ngn,
            "spread": spread,
            "lcy total value": lcy_total_value,
            "fcy outstanding": fcy_outstanding,
            "lcy outstanding": lcy_outstanding,
            "commission": commission,
            "our obli. status": our_obli_status,
            "customer obli status": customer_obli_status,
            "status": status
        }
        st.json(preview_dict)

        submitted = st.form_submit_button("✅ Submit Transaction")

    if submitted:
        new_row = {
            "date": record_date.strftime("%Y-%m-%d"),
            "month": month,
            "selling client": selling_client,
            "bank paid from": bank_paid_from,
            "buy rate": buy_rate,
            "buying client": buying_client,
            "transaction type": txn_type,
            "sell rate": sell_rate,
            "fcy total value": fcy_total_value,
            "total fcy paid to client": total_fcy_paid_to_client,
            "lcy payments": lcy_payments,
            "profit (ngn)": profit_ngn,
            "spread": spread,
            "lcy total value": lcy_total_value,
            "fcy outstanding": fcy_outstanding,
            "lcy outstanding": lcy_outstanding,
            "commission": commission,
            "our obli. status": our_obli_status,
            "customer obli status": customer_obli_status,
            "status": status,
        }
        worksheet.append_row(list(new_row.values()))
        st.success("✅ USD/NGN transaction added successfully!")
        st.rerun()

    # ---- Display Table ----
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
