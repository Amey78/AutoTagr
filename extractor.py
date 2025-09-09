
# extractor.py
# Handles text extraction from PDF, DOCX, TXT, Excel, and CSV (safe for big files)

import os
import docx
import pandas as pd
from PyPDF2 import PdfReader


def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""

        # If nothing extracted, show warning
        if not text.strip():
            return "⚠️ Empty or scanned PDF (no extractable text)."
    except Exception as e:
        return f"Error reading PDF: {e}"
    return text.strip()


def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs]) or "⚠️ Empty DOCX file."
    except Exception as e:
        return f"Error reading DOCX: {e}"


def extract_text_from_txt(file_path):
    """Extract text from a TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read() or "⚠️ Empty TXT file."
    except Exception as e:
        return f"Error reading TXT: {e}"


def extract_text_from_excel(file_path):
    """Extract text from an Excel file (all sheets, safe for big files)."""
    try:
        df = pd.read_excel(file_path, sheet_name=None)  # read all sheets
        text = ""
        for sheet, data in df.items():
            text += f"\n--- Sheet: {sheet} ---\n"
            text += data.head(10).to_string(index=False)  # only 10 rows per sheet
            if data.shape[0] > 10:
                text += f"\n... ({data.shape[0]} rows total)"
        return text if text.strip() else "⚠️ Empty Excel file."
    except Exception as e:
        return f"Error reading Excel: {e}"


def extract_text_from_csv(file_path):
    """Extract text + description from a CSV file (handles big files)."""
    try:
        df = pd.read_csv(file_path)

        description = f"This CSV contains {df.shape[0]} rows and {df.shape[1]} columns."
        
        if df.shape[0] > 0:
            sample_row = df.iloc[0].to_dict()
            description += f" Example row: {sample_row}."
        
        # Show only first 10 rows
        preview = df.head(10).to_string(index=False)

        return description + "\n\nSample Data (first 10 rows):\n" + preview
    except Exception as e:
        return f"Error reading CSV: {e}"


def extract_text(file_path):
    """Detect file type and extract text accordingly."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    elif ext in [".xls", ".xlsx"]:
        return extract_text_from_excel(file_path)
    elif ext == ".csv":
        return extract_text_from_csv(file_path)
    else:
        return "⚠️ Unsupported file format."
