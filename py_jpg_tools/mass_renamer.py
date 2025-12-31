import os
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
from geopy.geocoders import Nominatim
from datetime import datetime
import time
from unidecode import unidecode
import re

"""
Photo Filename Organizer: originalfilename_coordinates_streetname_timestamp

This script recursively scans all files in the specified INPUT_FOLDER 
and its subfolders. For each supported file (png, mp4, jpg, jpeg, gif, mov):

1. Keeps the original filename, cleaned of any previously appended
   coordinates/street/timestamp blocks to avoid stacking on repeated runs.
2. Extracts GPS coordinates from the photo's EXIF metadata (if available).
3. Uses Nominatim geolocation to get street and suburb/neighbourhood names.
4. Extracts the photo's timestamp from EXIF (DateTimeOriginal or DateTime), 
   or falls back to the file modification time if missing.
5. Builds a new filename in the format:
       originalfilename_coordinates_streetname_timestamp.ext
   Example: IMG_1234_48.85661_2.35222_Rue_des_Martyrs_Montmartre_2025-12-30_15-45-22.jpg
6. Converts all non-ASCII characters to ASCII and replaces spaces with underscores.
7. Truncates filenames longer than MAX_FILENAME_LEN to ensure compatibility with Windows.
8. Handles duplicate filenames by appending a counter (1), (2), etc.
9. Skips locked or in-use files and logs them to a text file.
10. Folder names are never modified; only file names are renamed.
11. DRY_RUN mode can be enabled to preview changes without actually renaming.

Configuration:
- INPUT_FOLDER: path to the folder containing files to process.
- DRY_RUN: True/False to simulate or execute renaming.
- LOCKED_LOG: path to a log file for locked files.
- SUPPORTED_EXTENSIONS: tuple of file extensions to process.
- MAX_FILENAME_LEN: maximum filename length for safety on Windows.
"""

# ---------------- CONFIG ----------------
INPUT_FOLDER = "icloud"
DRY_RUN = False
LOCKED_LOG = "locked_files.txt"
SUPPORTED_EXTENSIONS = ("png", "mp4", ".jpg", ".jpeg", ".gif", ".mov")
MAX_FILENAME_LEN = 150  # Windows-safe max length

geolocator = Nominatim(user_agent="photo_renamer")

# ---------------- HELPERS ----------------
def get_exif(img_path):
    try:
        image = Image.open(img_path)
        exif = image._getexif()
        if not exif:
            return {}
        return {TAGS.get(tag): val for tag, val in exif.items()}
    except Exception:
        return {}

def _convert_to_degrees(value):
    def to_float(v):
        try:
            return float(v)
        except TypeError:
            return v.numerator / v.denominator
    d, m, s = value
    return to_float(d) + to_float(m)/60 + to_float(s)/3600

def get_gps_location(exif):
    gps_info = exif.get("GPSInfo")
    if not gps_info:
        return None
    try:
        lat = _convert_to_degrees(gps_info[2])
        if gps_info[1] != 'N': lat = -lat
        lon = _convert_to_degrees(gps_info[4])
        if gps_info[3] != 'E': lon = -lon
        return lat, lon
    except Exception:
        return None

def get_location_name(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True, timeout=10)
        if location and location.raw and 'address' in location.raw:
            addr = location.raw['address']
            street = addr.get('road') or "UnknownStreet"
            suburb = addr.get('suburb') or addr.get('neighbourhood') or addr.get('village') or addr.get('town') or addr.get('city') or "UnknownLocation"
            # ASCII safe
            street = unidecode(street).replace(" ", "_") or "UnknownStreet"
            suburb = unidecode(suburb).replace(" ", "_") or "UnknownLocation"
            return f"{street}_{suburb}"
    except Exception:
        pass
    return "UnknownLocation"

def get_photo_datetime(file_path):
    """Get photo taken datetime from EXIF, fallback to file modification time"""
    try:
        image = Image.open(file_path)
        exif = image._getexif()
        if exif:
            dt = exif.get(36867) or exif.get(306)  # DateTimeOriginal or DateTime
            if dt:
                return datetime.strptime(dt, "%Y:%m:%d %H:%M:%S").strftime("%Y-%m-%d_%H-%M-%S")
    except Exception:
        pass
    ts = os.path.getmtime(file_path)
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H-%M-%S")

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

def clean_original_name(stem):
    """
    Remove any previously appended coordinates/street/timestamp blocks
    to prevent stacking on repeated runs.
    """
    pattern = r"(?:_\d+\.\d+_\d+\.\d+_[A-Za-z0-9_]+_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})+"
    cleaned = re.sub(pattern, '', stem)
    return cleaned or "File"

# ---------------- MAIN ----------------
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

        filename_prefix = "UnknownCoords"
        location_name = "UnknownLocation"

        if file.lower().endswith((".jpg", ".jpeg")):
            exif = get_exif(src_path)
            gps = get_gps_location(exif)
            if gps:
                filename_prefix = f"{gps[0]:.5f}_{gps[1]:.5f}"
                location_name = get_location_name(*gps)
                time.sleep(1)  # polite pause for Nominatim

        timestamp = get_photo_datetime(src_path)
        original_name = clean_original_name(src_path.stem)
        original_name = unidecode(original_name).replace(" ", "_")

        # Build new filename
        new_filename = f"{original_name}_{filename_prefix}_{location_name}_{timestamp}{src_path.suffix}"

        # Truncate to MAX_FILENAME_LEN
        if len(new_filename) > MAX_FILENAME_LEN:
            ext = src_path.suffix
            name_without_ext = new_filename[:-len(ext)]
            new_filename = name_without_ext[:MAX_FILENAME_LEN - len(ext)] + ext

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

# Write locked files to log
if locked_files:
    with open(LOCKED_LOG, "w") as f:
        for fpath in locked_files:
            f.write(fpath + "\n")
    print(f"Locked files logged to {LOCKED_LOG}")
