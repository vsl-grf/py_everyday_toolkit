import os
from pathlib import Path

# ---------------- CONFIG ----------------
INPUT_FOLDER = "icloud"  # change to your folder
DRY_RUN = False
LOCKED_LOG = "locked_files_keep_IMG.txt"
SUPPORTED_EXTENSIONS = (".png", ".mp4", ".jpg", ".jpeg", ".gif", ".mov")

def is_file_locked(filepath):
    try:
        os.rename(filepath, filepath)
        return False
    except OSError:
        return True

def resolve_duplicate(dest_path):
    counter = 1
    base = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent
    while dest_path.exists():
        dest_path = parent / f"{base}({counter}){suffix}"
        counter += 1
    return dest_path

locked_files = []

for root, _, files in os.walk(INPUT_FOLDER):
    for file in files:
        if not file.lower().endswith(SUPPORTED_EXTENSIONS):
            continue

        src_path = Path(root) / file

        if is_file_locked(src_path):
            print(f"Locked file skipped: {src_path}")
            locked_files.append(str(src_path))
            continue

        stem = src_path.stem
        if "IMG" in stem:
            # keep "IMG" and everything after
            new_stem = stem.split("IMG", 1)[1]
            new_stem = "IMG" + new_stem  # prepend IMG back
            new_stem = new_stem.strip("_- ")  # remove any leading underscores/dashes
        else:
            new_stem = stem

        new_filename = f"{new_stem}{src_path.suffix}"
        dest_path = resolve_duplicate(src_path.parent / new_filename)

        if DRY_RUN:
            print(f"[DRY-RUN] Rename {src_path.name} -> {new_filename}")
        else:
            try:
                src_path.rename(dest_path)
                print(f"Renamed {src_path.name} -> {new_filename}")
            except PermissionError:
                print(f"PermissionError, skipping: {src_path.name}")
                locked_files.append(str(src_path))

if locked_files:
    with open(LOCKED_LOG, "w") as f:
        for fpath in locked_files:
            f.write(fpath + "\n")
    print(f"Locked files logged to {LOCKED_LOG}")




"""
Photo Filename Cleaner: Keep Only "IMG" and Everything After

This script recursively scans all files in the specified INPUT_FOLDER 
and its subfolders. For each file with a supported extension (png, mp4, jpg, jpeg, gif, mov):

1. If the filename contains "IMG", everything **before "IMG" is removed**, 
   but "IMG" and all characters after it are preserved.
2. Leading underscores or dashes immediately before "IMG" are stripped.
3. Files without "IMG" in the name are left unchanged.
4. Duplicate filenames in the same folder are handled by appending 
   a counter like (1), (2), etc.
5. Locked or in-use files are skipped and logged to a text file.
6. Folder names are never modified; only file names are renamed.
7. DRY_RUN mode can be enabled to preview changes without actually renaming.

Configuration:
- INPUT_FOLDER: path to the folder containing files to process.
- DRY_RUN: True/False to simulate or execute renaming.
- LOCKED_LOG: path to a log file for locked files.
- SUPPORTED_EXTENSIONS: tuple of file extensions to process.
"""
