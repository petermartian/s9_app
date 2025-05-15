# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF  # Using fpdf with NGN replacement
from io import BytesIO
import re
import plotly.express as px
import plotly.io as pio  # For exporting charts
import kaleido  # Required for saving Plotly charts as images

# Set page configuration
st.set_page_config(page_title="Salmnine Report", layout="wide")

# Title with fixed emoji
try:
    st.markdown("<h2 style='color:#2E8B57;'>📊 SALMNINE REPORT SUMMARY</h2>", unsafe_allow_html=True)
except UnicodeEncodeError:
    st.markdown("<h2 style='color:#2E8B57;'>[Chart] SALMNINE REPORT SUMMARY</h2>", unsafe_allow_html=True)

# --- Excel File Setup ---
TRADE_FILE = "Trade sheet.xlsx"
DAILY_FILE = "Daily Transaction.xlsx"

# --- Cache Excel File Loading for Performance ---
@st.cache_data(ttl=3600)
def load_excel_file(file_path, sheet_name):
    try:
        return pd.read_excel(file_path, sheet_name=sheet_name)
    except FileNotFoundError:
        st.error(f"❌ File not found: {file_path}")
        return pd.DataFrame()
    except ValueError as e:
        st.error(f"❌ Error loading sheet '{sheet_name}' from {file_path}: {e}")
        return pd.DataFrame()

# Load data from Excel files
df_purchase = load_excel_file(TRADE_FILE, "Purchase Trade")
df_ghs = load_excel_file(TRADE_FILE, "GHS Trade")
df_swap = load_excel_file(TRADE_FILE, "Swap Trade")
df_usdngn = load_excel_file(DAILY_FILE, "usdngn")
df_expense = load_excel_file(DAILY_FILE, "expenses")

# Check if critical files are missing and provide guidance
missing_files = []
if df_purchase.empty and TRADE_FILE not in missing_files:
    missing_files.append(TRADE_FILE)

if missing_files:
    st.error("The following required files are missing: " + ", ".join(missing_files) + ".")
    st.markdown("""
        Please ensure these files are present in the same directory as the script or update the file paths accordingly.
    """)
    st.stop()

# Check if sheets are loaded correctly
if df_purchase.empty:
    st.error("❌ Failed to load 'Purchase Trade' sheet from Trade sheet.xlsx. Please ensure the sheet exists.")
    st.stop()
if df_ghs.empty:
    st.error("❌ Failed to load 'GHS Trade' sheet from Trade sheet.xlsx. Please ensure the sheet exists.")
    st.stop()
if df_swap.empty:
    st.error("❌ Failed to load 'Swap Trade' sheet from Trade sheet.xlsx. Please ensure the sheet exists.")
    st.stop()
if df_usdngn.empty:
    st.error("❌ Failed to load 'usdngn' sheet from Daily Transaction.xlsx. Please ensure the sheet exists.")
    st.stop()
if df_expense.empty:
    st.error("❌ Failed to load 'expenses' sheet from Daily Transaction.xlsx. Please ensure the sheet exists.")
    st.stop()

# Normalize column names
def normalize_columns(df):
    if not df.empty:
        df.columns = [re.sub(r'[^a-z0-9]', '', col.lower()) for col in df.columns]
    return df

df_purchase = normalize_columns(df_purchase)
df_ghs = normalize_columns(df_ghs)
df_swap = normalize_columns(df_swap)
df_usdngn = normalize_columns(df_usdngn)
df_expense = normalize_columns(df_expense)

# Date Filter
st.markdown("### 🗕️ Date Filter", unsafe_allow_html=True)
start_date = st.date_input("Start Date", value=datetime.today().replace(day=1))
end_date = st.date_input("End Date", value=datetime.today())

def filter_by_date(df, date_col="date"):
    if not df.empty and date_col in df.columns:
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            return df[(df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)]
        except KeyError:
            st.error(f"❌ Date column '{date_col}' not found in DataFrame.")
            return pd.DataFrame()
    return pd.DataFrame()

# Apply date filter
df_purchase = filter_by_date(df_purchase)
df_ghs = filter_by_date(df_ghs)
df_swap = filter_by_date(df_swap)
df_usdngn = filter_by_date(df_usdngn)
df_expense = filter_by_date(df_expense)

# Helper functions
def get_col(df, key):
    return next((col for col in df.columns if key in col), None)

def val(df, key):
    col = get_col(df, key)
    return df[col].sum() if col is not None and not df.empty else 0

def mean(df, key):
    col = get_col(df, key)
    return df[col].mean() if col is not None and not df.empty else 0

def safe(value):
    try:
        return 0 if pd.isna(value) else round(value, 2)
    except (TypeError, ValueError):
        return 0

def currency_label(metric):
    if metric in ["USD/NGN Profit", "Amount in NGN", "Converted Expenses"]:
        return "NGN "  # Using NGN to avoid Unicode issues with fpdf
    elif metric in ["Profit in USD", "Total Gross Income", "Amount in USD", "Total Expenses", "Net Profit", "Purchase Trade", "GHS Trade", "USD/NGN Transactions", "USD/USDT Swapped", "Total Bought", "Total Traded"]:
        return "$"
    elif metric == "Average Rate":
        return ""
    else:
        return ""

# Convert relevant columns to numeric
for frame, keys in [
    (df_purchase, ['tradesize']),
    (df_ghs, ['tradesize']),
    (df_usdngn, ['fcyval', 'profit', 'buyrate']),
    (df_swap, ['usdtdue', 'netprofit']),
    (df_expense, ['amountngn', 'amountusd'])
]:
    for key in keys:
        col = get_col(frame, key)
        if col:
            frame[col] = pd.to_numeric(frame[col], errors='coerce')

# Calculate metrics
purchase_sum = val(df_purchase, 'tradesize')
ghs_sum = val(df_ghs, 'tradesize')
total_bought = purchase_sum + ghs_sum
usdngn_fcy = val(df_usdngn, 'fcyval')
usdt_due = val(df_swap, 'usdtdue')
total_traded = total_bought + usdngn_fcy + usdt_due
usdngn_profit = val(df_usdngn, 'profit')
buy_rate_avg = mean(df_usdngn, 'buyrate')
profit_usd = usdngn_profit / buy_rate_avg if buy_rate_avg else 0
swap_net_income = val(df_swap, 'netprofit')
total_gross_income = profit_usd + swap_net_income
amt_ngn = val(df_expense, 'amountngn')
converted_exp = amt_ngn / buy_rate_avg if buy_rate_avg else 0
amt_usd = val(df_expense, 'amountusd')
total_expenses = converted_exp + amt_usd
net_profit = total_gross_income - total_expenses

# Display Summary Metrics
st.markdown("---\n### 🧾 <b>Summary Metrics</b>\n", unsafe_allow_html=True)

def styled_metric(label, value):
    prefix = currency_label(label)
    html = f"<div style='font-size:15px; font-weight:bold;'>{label}</div><div style='font-size:26px; color:#2E8B57; font-weight:700;'>{prefix}{safe(value):,.2f}</div>"
    return st.markdown(html, unsafe_allow_html=True)

summary_data = [
    ("Purchase Trade", purchase_sum),
    ("GHS Trade", ghs_sum),
    ("Total Bought", total_bought),
    ("USD/NGN Transactions", usdngn_fcy),
    ("USD/USDT Swapped", usdt_due),
    ("Total Traded", total_traded),
    ("USD/NGN Profit", usdngn_profit),
    ("Average Rate", buy_rate_avg),
    ("Profit in USD", profit_usd),
    ("Net Income USD/USDT", swap_net_income),
    ("Total Gross Income", total_gross_income),
    ("Amount in NGN", amt_ngn),
    ("Converted Expenses", converted_exp),
    ("Amount in USD", amt_usd),
    ("Total Expenses", total_expenses),
    ("Net Profit", net_profit)
]

for i in range(0, len(summary_data), 3):
    cols = st.columns(3)
    for j, (label, valx) in enumerate(summary_data[i:i+3]):
        with cols[j]:
            styled_metric(label, valx)

# --- Charts Section ---
st.markdown("### 📈 Trends Over Time")

# Chart 1: USD/NGN Profit Over Time
if not df_usdngn.empty:
    df_usdngn['date'] = pd.to_datetime(df_usdngn['date']).dt.date
    fig1 = px.line(df_usdngn, x='date', y='profit', title="USD/NGN Profit Over Time")
    st.plotly_chart(fig1, use_container_width=True)

    # Export chart as PNG
    chart1_output = BytesIO()
    fig1.write_image(chart1_output, format="png", engine="kaleido")
    chart1_output.seek(0)

    st.download_button(
        label="📥 Download USD/NGN Profit Chart (PNG)",
        data=chart1_output,
        file_name="usd_ngn_profit_chart.png",
        mime="image/png"
    )

# Chart 2: Purchase Trades Over Time
if not df_purchase.empty:
    df_purchase['date'] = pd.to_datetime(df_purchase['date']).dt.date
    fig2 = px.bar(df_purchase, x='date', y='tradesize', title="Purchase Trades Over Time")
    st.plotly_chart(fig2, use_container_width=True)

    # Export chart as PNG
    chart2_output = BytesIO()
    fig2.write_image(chart2_output, format="png", engine="kaleido")
    chart2_output.seek(0)

    st.download_button(
        label="📥 Download Purchase Trades Chart (PNG)",
        data=chart2_output,
        file_name="purchase_trades_chart.png",
        mime="image/png"
    )

# Chart 3: Total Expenses Over Time
if not df_expense.empty:
    df_expense['date'] = pd.to_datetime(df_expense['date']).dt.date
    df_expense['total_exp'] = df_expense[['amountngn', 'amountusd']].sum(axis=1)
    fig3 = px.area(df_expense, x='date', y='total_exp', title="Total Expenses Over Time")
    st.plotly_chart(fig3, use_container_width=True)

    # Export chart as PNG
    chart3_output = BytesIO()
    fig3.write_image(chart3_output, format="png", engine="kaleido")
    chart3_output.seek(0)

    st.download_button(
        label="📥 Download Total Expenses Chart (PNG)",
        data=chart3_output,
        file_name="total_expenses_chart.png",
        mime="image/png"
    )

# --- Export Section ---
st.markdown("### 📄 Export Reports")

# Excel Export (Using openpyxl)
excel_output = BytesIO()
df_export = pd.DataFrame(summary_data, columns=["Metric", "Amount"])
df_export["Amount"] = df_export["Amount"].apply(safe)

with pd.ExcelWriter(excel_output, engine="openpyxl") as writer:
    df_export.to_excel(writer, index=False, sheet_name="Summary")
    writer.close()

st.download_button(
    label="📥 Download Excel Report",
    data=excel_output.getvalue(),
    file_name="salmnine_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# PDF Export (Simple Table Summary)
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "Salmnine Summary Report", border=False, ln=True, align='C')
        self.ln(10)

    def chapter_title(self, title):
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, data):
        self.set_font("Arial", '', 11)
        for label, amount in data:
            self.cell(100, 10, label, 1)
            self.cell(40, 10, f"{currency_label(label)}{safe(amount):,.2f}", 1, ln=True)

pdf = PDF()
pdf.add_page()
pdf.chapter_title("Summary Metrics")
pdf.chapter_body(summary_data)

pdf_output = BytesIO()
pdf.output(pdf_output)
pdf_output.seek(0)

st.download_button(
    label="📄 Download PDF Report",
    data=pdf_output,
    file_name="salmnine_report.pdf",
    mime="application/pdf"
)