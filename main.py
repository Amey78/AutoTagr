# main.py
import os
import time
import streamlit as st
from PIL import Image
from extractor import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    extract_text_from_excel,
    extract_text_from_csv
)
from summarizer import generate_summary, generate_tags
from sorter import sort_files

# ==============================
# Temporary folder setup & cleanup
# ==============================
TEMP_FOLDER = "temp_uploaded"
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# Cleanup old temp files on startup
for f in os.listdir(TEMP_FOLDER):
    try:
        os.remove(os.path.join(TEMP_FOLDER, f))
    except:
        pass

# ==============================
# Helper: Render Tags
# ==============================
def render_tags(tags):
    if not tags:
        st.write("—")
        return
    st.markdown(
        " ".join(
            [
                f"<span style='padding:4px 10px; border-radius:12px; "
                f"background:#3B82F6; color:white; font-size:13px; "
                f"display:inline-block; margin:3px'>{t}</span>"
                for t in tags
            ]
        ),
        unsafe_allow_html=True,
    )

# ==============================
# Streamlit Config
# ==============================
st.set_page_config(page_title="AutoTagr - Smart File Organizer", layout="wide")
st.title("📂 AutoTagr – Smart File Organizer with AI Labeling")

# ==============================
# Global CSS
# ==============================
st.markdown(
    """
    <style>
    .stProgress > div > div { height: 4px !important; }
    .stProgress p { margin-top: 4px !important; font-size: 12px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================
# Session State
# ==============================
if "summary" not in st.session_state: st.session_state.summary = ""
if "tags" not in st.session_state: st.session_state.tags = []
if "uploaded_file_path" not in st.session_state: st.session_state.uploaded_file_path = ""
if "folder_path" not in st.session_state: st.session_state.folder_path = ""

# ==============================
# Layout Columns
# ==============================
col1, col2, col3 = st.columns([4,2,4])

# ==============================
# LEFT: File Summarization
# ==============================
with col1:
    st.subheader("📄 File Summarization + Tags")

    uploaded_file = st.file_uploader("Upload a file", type=["pdf","docx","txt","xls","xlsx","csv","png","jpg","jpeg"])
    if uploaded_file is not None:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext in [".png",".jpg",".jpeg"]:
            image = Image.open(uploaded_file)
            st.image(image, caption="📷 Uploaded Image Preview", use_column_width=True)
            st.session_state.uploaded_file_path = ""
        else:
            file_path = os.path.join(TEMP_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
            st.session_state.uploaded_file_path = file_path

    max_words = st.slider("🔧 Set Summary Word Limit", min_value=50, max_value=400, value=150, step=50)

    if st.button("Generate Summary"):
        if st.session_state.uploaded_file_path:
            progress_bar = st.progress(0)
            status = st.empty()

            fp = st.session_state.uploaded_file_path
            text = ""
            if fp.endswith(".pdf"): text = extract_text_from_pdf(fp)
            elif fp.endswith(".docx"): text = extract_text_from_docx(fp)
            elif fp.endswith(".txt"): text = extract_text_from_txt(fp)
            elif fp.endswith((".xls",".xlsx")): text = extract_text_from_excel(fp)
            elif fp.endswith(".csv"): text = extract_text_from_csv(fp)

            if text and not text.startswith("Error"):
                progress_bar.progress(30)
                status.write("🤖 Generating summary...")
                summary = generate_summary(text, max_words=max_words)
                progress_bar.progress(70)
                tags = generate_tags(text)
                progress_bar.progress(100)
                status.write("✅ Done! 100%")
                st.session_state.summary = summary
                st.session_state.tags = tags
                st.success("✅ Summary and Tags generated successfully!")

                # Cleanup temp file after summary
                try: os.remove(fp); st.session_state.uploaded_file_path = ""
                except: pass
            else:
                st.error("⚠️ No text could be extracted from the file.")
        else:
            st.warning("⚠️ Please upload a supported file.")

    if st.session_state.summary:
        st.write("### 📑 Summary")
        st.write(st.session_state.summary)

        if st.session_state.tags:
            st.write("### 🏷 Suggested Tags")
            render_tags(st.session_state.tags)

        # Clear + Download buttons stacked under summary
        if st.button("Clear Summary"):
            st.session_state.summary = ""
            st.session_state.tags = []

        st.download_button(
            label="📥 Download Summary",
            data=st.session_state.summary,
            file_name="summary.txt",
            mime="text/plain"
        )

# ==============================
# MIDDLE: Folder Sorting (Streamlit-compatible)
# ==============================
with col2:
    st.subheader("📂 Folder Sorting")

    # Manual folder path input
    folder_input = st.text_input("📂 Enter folder path manually", value=st.session_state.folder_path)
    if st.button("Set Folder"):
        if os.path.exists(folder_input):
            st.session_state.folder_path = folder_input
            st.success(f"📁 Folder set manually: {folder_input}")
        else:
            st.error("Invalid folder path")

    # Sort folder button
    if st.button("Sort Folder"):
        if st.session_state.folder_path and os.path.exists(st.session_state.folder_path):
            result = sort_files(st.session_state.folder_path)
            st.success(result)
        else:
            st.error("Please select a valid folder.")

    # Sort + AI auto-rename
    if st.button("Sort All (AI + Rename)"):
        if st.session_state.folder_path and os.path.exists(st.session_state.folder_path):
            with st.spinner("⏳ Sorting with AI..."):
                result = auto_rename_files(st.session_state.folder_path)
                st.success(result)
        else:
            st.error("Please select a valid folder.")

# ==============================
# RIGHT: Quick Preview
# ==============================
with col3:
    st.subheader("👀 Quick Preview")

    if st.session_state.folder_path and os.path.exists(st.session_state.folder_path):
        files = [f for f in os.listdir(st.session_state.folder_path) if os.path.isfile(os.path.join(st.session_state.folder_path,f))]
        if files:
            for file in files:
                file_path = os.path.join(st.session_state.folder_path, file)
                with st.expander(f"📄 {file}"):
                    try:
                        ext = file.lower()
                        text = ""
                        if ext.endswith(".pdf"): text = extract_text_from_pdf(file_path)
                        elif ext.endswith(".docx"): text = extract_text_from_docx(file_path)
                        elif ext.endswith(".txt"): text = extract_text_from_txt(file_path)
                        elif ext.endswith((".xls",".xlsx")): text = extract_text_from_excel(file_path)
                        elif ext.endswith(".csv"): text = extract_text_from_csv(file_path)

                        if ext.endswith((".pdf",".docx",".txt",".xls",".xlsx",".csv")) and text and not text.startswith(("Error","⚠️")):
                            icon_col, bar_col = st.columns([1,6])
                            with icon_col:
                                if ext.endswith(".pdf"): st.image("https://img.icons8.com/color/48/pdf.png", width=36)
                                elif ext.endswith(".docx"): st.image("https://img.icons8.com/color/48/ms-word.png", width=36)
                                elif ext.endswith((".xls",".xlsx",".csv")): st.image("https://img.icons8.com/color/48/ms-excel.png", width=36)
                                else: st.image("https://img.icons8.com/color/48/txt.png", width=36)
                            with bar_col:
                                progress_bar = st.progress(0)
                                status = st.empty()
                                summary = ""
                                tags = []
                                try:
                                    progress_bar.progress(30)
                                    status.write("🤖 Generating summary...")
                                    summary = generate_summary(text, max_words=50)
                                    progress_bar.progress(70)
                                    tags = generate_tags(text)
                                    progress_bar.progress(100)
                                    status.write("✅ Done! 100%")
                                except Exception as e: status.write(f"❌ Error: {e}")
                            st.write("**Summary:**", summary)
                            if tags:
                                st.write("**Tags:**")
                                render_tags(tags)
                        elif ext.endswith((".png",".jpg",".jpeg")):
                            st.image(file_path, width=200)
                            with st.expander("🔍 View Full Image"): st.image(file_path, use_container_width=True)
                            st.markdown("**🖼️ Image File Preview shown above**")
                        else:
                            st.write("⚠️ Unsupported file format.")
                    except Exception as e: st.write(f"❌ Error: {e}")
        else: st.info("No files found in the selected folder.")
    else: st.info("📂 Select a folder to preview files.")

# --- Full-width CSS for Quick Preview bar ---
st.markdown(
    """
    <style>
    .stProgress > div > div {
        height: 4px !important;
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
