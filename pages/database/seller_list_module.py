
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import streamlit as st
import pandas as pd
import os
import time

def render_seller_list():
    EXCEL_PATH = "database.xlsx"
    TAB_NAME = "Seller List"
    st.markdown("<div style='background-color:#FDEBD0;padding:10px;border-radius:5px'><h4>➕ Add Seller List</h4></div>", unsafe_allow_html=True)

    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=TAB_NAME)
    else:
        df = pd.DataFrame(columns=["Seller Name", "Contact Person", "Phone Number"])

    with st.form("add_form_seller_list", clear_on_submit=False):
        inputs = [st.text_input(label) for label in ["Seller Name", "Contact Person", "Phone Number"]]
        submitted = st.form_submit_button("Add")
        if submitted and inputs[0].strip():
            if inputs[0].strip().lower() in df["Seller Name"].str.lower().str.strip().values:
                st.error(f"Seller List '{inputs[0]}' already exists.")
            else:
                df = pd.concat([df, pd.DataFrame([inputs], columns=["Seller Name", "Contact Person", "Phone Number"])], ignore_index=True)
                with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                    df.to_excel(writer, sheet_name=TAB_NAME, index=False)
                st.success("Seller List added.")

    st.markdown("### 📋 Table")

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
    if not updated_df.equals(df):
        st.success("Changes detected. Saving...")
        time.sleep(0.5)
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            updated_df.to_excel(writer, sheet_name=TAB_NAME, index=False)
        st.experimental_rerun()
