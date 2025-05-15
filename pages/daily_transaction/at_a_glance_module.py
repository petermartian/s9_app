import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io
import xlsxwriter
from datetime import date
import plotly.io as pio

# --- Excel File Setup ---
EXCEL_FILE = "Daily Transaction.xlsx"
USDNGN_TAB = "usdngn"
EXPENSES_TAB = "expenses"

# --- Cache Excel File Loading for Performance ---
@st.cache_data
def load_excel_file(file_path, sheet_name):
    try:
        return pd.read_excel(file_path, sheet_name=sheet_name)
    except (FileNotFoundError, ValueError) as e:
        st.error(f"❌ Failed to load {sheet_name}: {e}")
        return pd.DataFrame()

# --- Paginated Data Table ---
def paginate_dataframe(df, page_size, page_number):
    start_idx = (page_number - 1) * page_size
    end_idx = start_idx + page_size
    return df.iloc[start_idx:end_idx]

def run_page():
    st.subheader("📘 At a Glance Overview")

    # --- Load Data from usdngn and expenses tabs ---
    df_usdngn = load_excel_file(EXCEL_FILE, USDNGN_TAB)
    df_expenses = load_excel_file(EXCEL_FILE, EXPENSES_TAB)

    # --- Process usdngn Data ---
    if not df_usdngn.empty:
        df_usdngn.columns = [col.strip().title() for col in df_usdngn.columns]
        df_usdngn["Date"] = pd.to_datetime(df_usdngn["Date"], errors="coerce")
        df_usdngn = df_usdngn[df_usdngn["Date"].notna()]
        df_usdngn["Profit"] = pd.to_numeric(df_usdngn["Profit"], errors="coerce")
        df_usdngn["Fcy Val"] = pd.to_numeric(df_usdngn["Fcy Val"], errors="coerce")
    else:
        df_usdngn = pd.DataFrame()

    # --- Process expenses Data ---
    if not df_expenses.empty:
        df_expenses.columns = [col.strip().title() for col in df_expenses.columns]
        df_expenses["Date"] = pd.to_datetime(df_expenses["Date"], errors="coerce")
        df_expenses = df_expenses[df_expenses["Date"].notna()]
        df_expenses["Amount Ngn"] = pd.to_numeric(df_expenses["Amount Ngn"], errors="coerce")
        df_expenses["Amount Usd"] = pd.to_numeric(df_expenses["Amount Usd"], errors="coerce")
    else:
        df_expenses = pd.DataFrame()

    # --- Date Range Filter ---
    if not df_usdngn.empty and not df_expenses.empty:
        min_date = min(df_usdngn["Date"].min(), df_expenses["Date"].min()).date()
        max_date = max(df_usdngn["Date"].max(), df_expenses["Date"].max()).date()
    elif not df_usdngn.empty:
        min_date, max_date = df_usdngn["Date"].min().date(), df_usdngn["Date"].max().date()
    elif not df_expenses.empty:
        min_date, max_date = df_expenses["Date"].min().date(), df_expenses["Date"].max().date()
    else:
        min_date, max_date = date.today(), date.today()

    start = st.date_input("📅 Start Date", min_date, key="start_at_a_glance")
    end = st.date_input("📅 End Date", max_date, key="end_at_a_glance")

    # Filter data based on on date range
    df_usdngn_filtered = df_usdngn[(df_usdngn["Date"] >= pd.to_datetime(start)) & (df_usdngn["Date"] <= pd.to_datetime(end))] if not df_usdngn.empty else pd.DataFrame()
    df_expenses_filtered = df_expenses[(df_expenses["Date"] >= pd.to_datetime(start)) & (df_expenses["Date"] <= pd.to_datetime(end))] if not df_expenses.empty else pd.DataFrame()

    # --- Summary Calculations ---
    st.markdown("### 📊 Summary Metrics")
    today = pd.to_datetime(date.today())
    if not df_usdngn_filtered.empty:
        df_usdngn_filtered["Week"] = df_usdngn_filtered["Date"].dt.isocalendar().week
        df_usdngn_filtered["Month"] = df_usdngn_filtered["Date"].dt.month
    if not df_expenses_filtered.empty:
        df_expenses_filtered["Week"] = df_expenses_filtered["Date"].dt.isocalendar().week
        df_expenses_filtered["Month"] = df_expenses_filtered["Date"].dt.month

    summary = {
        "Period": ["Daily", "Weekly", "Monthly"],
        "Total Profit (USD/NGN)": [
            df_usdngn_filtered[df_usdngn_filtered["Date"].dt.date == today.date()]["Profit"].sum() if not df_usdngn_filtered.empty else 0,
            df_usdngn_filtered[df_usdngn_filtered["Week"] == today.isocalendar().week]["Profit"].sum() if not df_usdngn_filtered.empty else 0,
            df_usdngn_filtered[df_usdngn_filtered["Month"] == today.month]["Profit"].sum() if not df_usdngn_filtered.empty else 0
        ],
        "Total FCY Amount (USD/NGN)": [
            df_usdngn_filtered[df_usdngn_filtered["Date"].dt.date == today.date()]["Fcy Val"].sum() if not df_usdngn_filtered.empty else 0,
            df_usdngn_filtered[df_usdngn_filtered["Week"] == today.isocalendar().week]["Fcy Val"].sum() if not df_usdngn_filtered.empty else 0,
            df_usdngn_filtered[df_usdngn_filtered["Month"] == today.month]["Fcy Val"].sum() if not df_usdngn_filtered.empty else 0
        ],
        "Total Expenses NGN": [
            df_expenses_filtered[df_expenses_filtered["Date"].dt.date == today.date()]["Amount Ngn"].sum() if not df_expenses_filtered.empty else 0,
            df_expenses_filtered[df_expenses_filtered["Week"] == today.isocalendar().week]["Amount Ngn"].sum() if not df_expenses_filtered.empty else 0,
            df_expenses_filtered[df_expenses_filtered["Month"] == today.month]["Amount Ngn"].sum() if not df_expenses_filtered.empty else 0
        ],
        "Total Expenses USD": [
            df_expenses_filtered[df_expenses_filtered["Date"].dt.date == today.date()]["Amount Usd"].sum() if not df_expenses_filtered.empty else 0,
            df_expenses_filtered[df_expenses_filtered["Week"] == today.isocalendar().week]["Amount Usd"].sum() if not df_expenses_filtered.empty else 0,
            df_expenses_filtered[df_expenses_filtered["Month"] == today.month]["Amount Usd"].sum() if not df_expenses_filtered.empty else 0
        ]
    }
    df_summary = pd.DataFrame(summary)
    st.dataframe(df_summary.style.set_properties(**{
        'font-weight': 'bold', 'background-color': '#e3f2fd', 'color': '#000'
    }), use_container_width=True)

    # --- Combined Data Table (Optional) ---
    st.markdown("### 📊 Recent Transactions")
    if not df_usdngn_filtered.empty or not df_expenses_filtered.empty:
        # Combine data for display
        if not df_usdngn_filtered.empty:
            df_usdngn_filtered["Source"] = "USD/NGN"
            df_usdngn_display = df_usdngn_filtered[["Date", "Source", "Buying Client", "Selling Client", "Transaction Type", "Profit", "Fcy Val"]]
        else:
            df_usdngn_display = pd.DataFrame()

        if not df_expenses_filtered.empty:
            df_expenses_filtered["Source"] = "Expenses"
            df_expenses_display = df_expenses_filtered[["Date", "Source", "Expense Description", "Amount Ngn", "Amount Usd"]]
            df_expenses_display = df_expenses_display.rename(columns={"Expense Description": "Description"})
        else:
            df_expenses_display = pd.DataFrame()

        # Combine and sort by date
        combined_df = pd.concat([df_usdngn_display, df_expenses_display], ignore_index=True, sort=False)
        combined_df = combined_df.sort_values(by="Date", ascending=False)

        # Pagination
        page_size = 10
        total_rows = len(combined_df)
        total_pages = (total_rows + page_size - 1) // page_size if total_rows > 0 else 1

        if "at_a_glance_page_number" not in st.session_state:
            st.session_state.at_a_glance_page_number = 1

        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Previous", key="at_a_glance_prev"):
                if st.session_state.at_a_glance_page_number > 1:
                    st.session_state.at_a_glance_page_number -= 1
        with col2:
            st.write(f"Page {st.session_state.at_a_glance_page_number} of {total_pages}")
        with col3:
            if st.button("Next ➡️", key="at_a_glance_next"):
                if st.session_state.at_a_glance_page_number < total_pages:
                    st.session_state.at_a_glance_page_number += 1

        paginated_df = paginate_dataframe(combined_df, page_size, st.session_state.at_a_glance_page_number)
        st.dataframe(paginated_df, use_container_width=True)
    else:
        st.info("ℹ️ No transactions available in the selected date range.")

    # --- Charts ---
    st.markdown("### 📈 Trends Over Time")
    col1, col2 = st.columns(2)
    
    profit_chart_data = None
    expenses_chart_data = None

    with col1:
        if not df_usdngn_filtered.empty:
            st.markdown("#### Profit Over Time (USD/NGN)")
            profit_chart_data = df_usdngn_filtered.groupby(df_usdngn_filtered["Date"].dt.date)["Profit"].sum().reset_index()
            fig_profit = px.line(profit_chart_data, x="Date", y="Profit", title="Profit Over Time",
                                 color_discrete_sequence=px.colors.qualitative.Bold)
            st.plotly_chart(fig_profit, use_container_width=True)

    with col2:
        if not df_expenses_filtered.empty:
            st.markdown("#### Expenses Over Time (NGN)")
            expenses_chart_data = df_expenses_filtered.groupby(df_expenses_filtered["Date"].dt.date)["Amount Ngn"].sum().reset_index()
            fig_expenses = px.line(expenses_chart_data, x="Date", y="Amount Ngn", title="Expenses Over Time",
                                   color_discrete_sequence=px.colors.sequential.Reds)
            st.plotly_chart(fig_expenses, use_container_width=True)

    # --- Export: Excel ---
    st.markdown("### 📤 Export Summary")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_summary.to_excel(writer, index=False, sheet_name="Summary")
        if not combined_df.empty:
            combined_df.to_excel(writer, index=False, sheet_name="Transactions")
        if profit_chart_data is not None:
            profit_chart_data.to_excel(writer, index=False, sheet_name="Profit Chart Data")
        if expenses_chart_data is not None:
            expenses_chart_data.to_excel(writer, index=False, sheet_name="Expenses Chart Data")
    excel_data = output.getvalue()
    st.download_button("⬇️ Download Excel", data=excel_data,
                       file_name="at_a_glance_summary.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # --- Export: PDF ---
    if st.button("⬇️ Download PDF", key="pdf_at_a_glance"):
        pdf = FPDF()
        pdf.add_page()
        pdf.image("assets/salmnine_logo.png", x=10, y=8, w=30)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Salmnine Investment Ltd", ln=True, align="C")
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "At a Glance Summary Report", ln=True, align="C")
        pdf.ln(10)

        # Add Summary Metrics
        if not df_summary.empty:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 10, "Summary Metrics", ln=True, align="L")
            pdf.set_font("Arial", size=10)
            for i, row in df_summary.iterrows():
                pdf.cell(0, 8, f"{row['Period']}: Profit = {row['Total Profit (USD/NGN)']:,.2f}, FCY = {row['Total FCY Amount (USD/NGN)']:,.2f}, Expenses NGN = {row['Total Expenses NGN']:,.2f}, Expenses USD = {row['Total Expenses USD']:,.2f}", ln=True)
            pdf.ln(5)
        else:
            pdf.cell(100, 10, txt="No summary data available.", ln=True)

        # Add Charts to PDF
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 10, "Trends Over Time", ln=True, align="L")
        pdf.ln(5)

        # Save Profit Chart as Image in Memory
        if profit_chart_data is not None:
            try:
                fig_profit = px.line(profit_chart_data, x="Date", y="Profit", title="Profit Over Time",
                                     color_discrete_sequence=px.colors.qualitative.Bold)
                img_buffer_profit = io.BytesIO()
                pio.write_image(fig_profit, img_buffer_profit, format="png", width=600, height=400)
                img_buffer_profit.seek(0)
                pdf.image(img_buffer_profit, x=10, y=None, w=190)
                pdf.ln(5)
            except Exception as e:
                pdf.set_font("Arial", size=10)
                pdf.cell(0, 10, f"Error generating Profit Chart: {str(e)}", ln=True)

        # Save Expenses Chart as Image in Memory
        if expenses_chart_data is not None:
            try:
                fig_expenses = px.line(expenses_chart_data, x="Date", y="Amount Ngn", title="Expenses Over Time",
                                       color_discrete_sequence=px.colors.sequential.Reds)
                img_buffer_expenses = io.BytesIO()
                pio.write_image(fig_expenses, img_buffer_expenses, format="png", width=600, height=400)
                img_buffer_expenses.seek(0)
                pdf.image(img_buffer_expenses, x=10, y=None, w=190)
                pdf.ln(5)
            except Exception as e:
                pdf.set_font("Arial", size=10)
                pdf.cell(0, 10, f"Error generating Expenses Chart: {str(e)}", ln=True)

        pdf.set_y(-20)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, "Generated by Salmnine Daily Transactions Suite", 0, 0, "C")

        # Write PDF to BytesIO
        pdf_output = io.BytesIO()
        pdf_output.write(pdf.output(dest='S').encode('latin1'))  # Use dest='S' to get a string, then encode
        pdf_data = pdf_output.getvalue()
        st.download_button("📄 Download PDF", data=pdf_data,
                           file_name="at_a_glance_summary.pdf", mime="application/pdf")