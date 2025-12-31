import os
from pathlib import Path


"""counts files in a folder"""
# ---------------- CONFIG ----------------
FOLDER_PATH = "icloud"
RECURSIVE = True  # Set to False to only count files in the top-level folder

# ---------------- MAIN ----------------
def count_files(folder_path, recursive=True):
    folder = Path(folder_path)
    if recursive:
        return sum(1 for _ in folder.rglob('*') if _.is_file())
    else:
        return sum(1 for _ in folder.iterdir() if _.is_file())

# ---------------- EXECUTE ----------------
file_count = count_files(FOLDER_PATH, RECURSIVE)
print(f"Total files in '{FOLDER_PATH}': {file_count}")
