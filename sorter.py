# sorter.py
# Handles file sorting and AI-based auto renaming

import os
import shutil
from summarizer import generate_summary, generate_tags
from extractor import extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt

# ==============================
# Basic Sort by File Type
# ==============================
def sort_files(folder_path: str, rename: bool = False):
    """
    Sort files into subfolders by their extension.
    If rename=True, use AI auto rename.
    """
    if not os.path.exists(folder_path):
        return "❌ Folder path does not exist."

    if rename:
        return auto_rename_files(folder_path)

    extensions = {
        ".pdf": "PDF",
        ".docx": "DOCX",
        ".txt": "TXT",
        ".jpg": "Images",
        ".jpeg": "Images",
        ".png": "Images",
        ".xls": "Excel",
        ".xlsx": "Excel",
        ".csv": "Excel"
    }

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)

        if os.path.isfile(file_path):
            ext = os.path.splitext(file)[1].lower()
            folder_name = extensions.get(ext, "Others")

            target_dir = os.path.join(folder_path, folder_name)
            os.makedirs(target_dir, exist_ok=True)

            shutil.move(file_path, os.path.join(target_dir, file))

    return "✅ Files sorted successfully."


# ==============================
# Sort + AI Auto Rename
# ==============================
def auto_rename_files(folder_path: str):
    """
    Uses AI (summary + tags) to rename files and sort them into folders.
    """
    if not os.path.exists(folder_path):
        return "❌ Folder path does not exist."

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)

        if not os.path.isfile(file_path):
            continue

        ext = os.path.splitext(file)[1].lower()
        text = ""

        try:
            if ext == ".pdf":
                text = extract_text_from_pdf(file_path)
            elif ext == ".docx":
                text = extract_text_from_docx(file_path)
            elif ext == ".txt":
                text = extract_text_from_txt(file_path)
        except Exception as e:
            print(f"⚠️ Could not extract text from {file}: {e}")

        # Generate summary + tags
        if text:
            summary = generate_summary(text, max_words=30)
            tags = generate_tags(text)

            # Pick best tag for filename
            tag_part = "_".join(tags[:2]) if tags else "Document"
            new_name = f"{tag_part}{ext}"

            target_dir = os.path.join(folder_path, ext.replace('.', '').upper())
            os.makedirs(target_dir, exist_ok=True)

            new_path = os.path.join(target_dir, new_name)

            # Handle duplicate names
            count = 1
            while os.path.exists(new_path):
                new_name = f"{tag_part}_{count}{ext}"
                new_path = os.path.join(target_dir, new_name)
                count += 1

            shutil.move(file_path, new_path)
        else:
            # Fallback → sort only
            target_dir = os.path.join(folder_path, "Others")
            os.makedirs(target_dir, exist_ok=True)
            shutil.move(file_path, os.path.join(target_dir, file))

    return "✅ Files sorted and renamed successfully."
