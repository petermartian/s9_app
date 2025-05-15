# Export utilities for Excel and PDF
import streamlit as st
import pandas as pd
from fpdf import FPDF
import os


def export_to_excel(df, filename="export.xlsx"):
    path = os.path.join("data", filename)
    df.to_excel(path, index=False)
    return path

def export_to_pdf(df, filename="export.pdf"):
    path = os.path.join("data", filename)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    col_width = pdf.w / (len(df.columns) + 1)
    row_height = 10

    # Header
    for col in df.columns:
        pdf.cell(col_width, row_height, str(col), border=1)
    pdf.ln(row_height)

    # Rows
    for i in range(len(df)):
        for col in df.columns:
            pdf.cell(col_width, row_height, str(df.iloc[i][col]), border=1)
        pdf.ln(row_height)

    pdf.output(path)
    return path
