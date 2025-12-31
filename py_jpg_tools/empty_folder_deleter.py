import os
from pathlib import Path

"""deletes empty folders"""


# ---------------- CONFIG ----------------
ROOT_FOLDER = "icloud"
DRY_RUN = False  # Set to False to actually delete

# ---------------- MAIN ----------------
def delete_empty_folders(path):
    path = Path(path)
    deleted_folders = []

    # Walk the directory tree from the bottom up
    for folder in sorted(path.rglob('*'), key=lambda p: -p.parts.__len__()):
        if folder.is_dir():
            try:
                if not any(folder.iterdir()):  # folder is empty
                    if DRY_RUN:
                        print(f"[DRY-RUN] Would delete: {folder}")
                    else:
                        folder.rmdir()
                        print(f"Deleted: {folder}")
                        deleted_folders.append(folder)
            except Exception as e:
                print(f"Failed to delete {folder}: {e}")

    return deleted_folders

# ---------------- EXECUTE ----------------
deleted = delete_empty_folders(ROOT_FOLDER)
if DRY_RUN:
    print("Dry-run completed. No folders were deleted.")
else:
    print(f"Deleted {len(deleted)} empty folders.")
