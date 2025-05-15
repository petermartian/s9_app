import streamlit as st
import pandas as pd
import time
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from utils.auth import get_gspread_client

# --- CONFIG ---
SHEET_KEY = "1j_D2QiaS3IEJuNI27OA56l8nWWatzxidLKuqV4Dfet4"
TAB_NAME = "Seller List"

def render_seller_list():
    st.markdown("<div style='background-color:#FDEBD0;padding:10px;border-radius:5px'><h4>➕ Add Seller</h4></div>", unsafe_allow_html=True)

    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_KEY)
    worksheet = sheet.worksheet(TAB_NAME)

    # --- Load data from Google Sheet ---
    @st.cache_data(ttl=60)
    def load_data():
        records = worksheet.get_all_records()
        return pd.DataFrame(records)

    df = load_data()

    # --- Add Seller Form ---
    with st.form("add_form_seller_list", clear_on_submit=False):
        inputs = [st.text_input(label) for label in ["Seller Name", "Contact Person", "Phone Number"]]
        submitted = st.form_submit_button("Add")
        if submitted and inputs[0].strip():
            if inputs[0].strip().lower() in df["Seller Name"].str.lower().str.strip().values:
                st.error(f"Seller '{inputs[0]}' already exists.")
            else:
                new_row = pd.DataFrame([inputs], columns=["Seller Name", "Contact Person", "Phone Number"])
                df = pd.concat([df, new_row], ignore_index=True)
                worksheet.update([df.columns.values.tolist()] + df.values.tolist())
                st.success("Seller added.")
                st.rerun()

    # --- Table Title and Refresh ---
    st.markdown("### 📋 Seller Table")

    if st.button("🔄 Refresh Seller List"):
        st.cache_data.clear()
        st.rerun()

    # --- AgGrid Table Display ---
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination()
    gb.configure_default_column(editable=True)

    grid_response = AgGrid(
        df,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=True,
        height=400,
        reload_data=False
    )

    updated_df = grid_response["data"]

    # --- Save edits from AgGrid ---
    if not updated_df.equals(df):
        st.success("Changes detected. Saving...")
        time.sleep(0.5)
        worksheet.update([updated_df.columns.values.tolist()] + updated_df.values.tolist())
        st.rerun()

