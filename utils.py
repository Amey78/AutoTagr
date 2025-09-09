# utils.py
# Small helper utilities for AutoTagr project

import os
import glob


def cleanup_temp_files(temp_dir=".", pattern="temp_uploaded*"):
    """
    Remove temporary uploaded files (like PDFs, DOCX, TXT).
    Default: temp_uploaded.* files in current folder
    """
    try:
        for file in glob.glob(os.path.join(temp_dir, pattern)):
            if os.path.isfile(file):
                os.remove(file)
        return "✅ Temp files cleaned."
    except Exception as e:
        return f"⚠️ Cleanup failed: {e}"
