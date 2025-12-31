import os
from pathlib import Path
from unidecode import unidecode


"""transliterates all folders names to ascii characters"""

# ---------------- CONFIG ----------------
ROOT_FOLDER = "icloud"
DRY_RUN = False  # Set to False to actually rename

# ---------------- MAIN ----------------
def rename_folders_to_english(path):
    path = Path(path)
    
    # Walk from bottom up to rename deepest folders first
    for folder in sorted(path.rglob('*'), key=lambda p: -len(p.parts)):
        if folder.is_dir():
            new_name = unidecode(folder.name).replace(" ", "_")
            if new_name != folder.name:
                new_path = folder.parent / new_name
                if DRY_RUN:
                    print(f"[DRY-RUN] Rename: {folder} -> {new_path}")
                else:
                    try:
                        folder.rename(new_path)
                        print(f"Renamed: {folder} -> {new_path}")
                    except Exception as e:
                        print(f"Failed to rename {folder}: {e}")

# ---------------- EXECUTE ----------------
rename_folders_to_english(ROOT_FOLDER)
