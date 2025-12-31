import os
import shutil
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from geopy.geocoders import Nominatim
import time

# ---------------- CONFIG ----------------
INPUT_FOLDER = "icloud"
OUTPUT_FOLDER = "icloud"
DRY_RUN = False
LOCKED_LOG = "locked_files.txt"
SUPPORTED_EXTENSIONS = (".png")

# ---------------- HELPERS ----------------
geolocator = Nominatim(user_agent="photo_sorter")

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

def reverse_geocode(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True, timeout=10)
        if location and location.raw and 'address' in location.raw:
            addr = location.raw['address']
            city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('hamlet') or "UnknownCity"
            country = addr.get('country') or "UnknownCountry"
            # Replace spaces with underscores for folder names
            return f"{country.replace(' ', '_')}/{city.replace(' ', '_')}"
    except Exception:
        pass
    # fallback to coordinates
    return f"{lat:.5f}_{lon:.5f}"


def is_file_locked(filepath):
    try:
        os.rename(filepath, filepath)
        return False
    except OSError:
        return True

def get_file_date(file_path):
    ts = os.path.getmtime(file_path)
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

def resolve_duplicate(dest_path):
    counter = 1
    base = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent
    while dest_path.exists():
        dest_path = parent / f"{base}({counter}){suffix}"
        counter += 1
    return dest_path

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

        location_folder = "Unknown"

        if file.lower().endswith((".jpg", ".jpeg")):
            exif = get_exif(src_path)
            gps = get_gps_location(exif)
            if gps:
                # Reverse geocode
                location_folder = reverse_geocode(*gps)
                # Be nice to Nominatim API (avoid hitting too fast)
                time.sleep(1)
            else:
                location_folder = get_file_date(src_path)
        else:
            # GIF/MOV fallback to creation/modification date
            location_folder = get_file_date(src_path)

        dest_dir = Path(OUTPUT_FOLDER) / location_folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = resolve_duplicate(dest_dir / file)

        if DRY_RUN:
            print(f"[DRY-RUN] Move {src_path} -> {dest_path}")
        else:
            try:
                shutil.move(str(src_path), str(dest_path))
                print(f"Moved {src_path} -> {dest_path}")
            except PermissionError:
                print(f"PermissionError, skipping: {src_path}")
                locked_files.append(str(src_path))

# Write locked files to log
if locked_files:
    with open(LOCKED_LOG, "w") as f:
        for fpath in locked_files:
            f.write(fpath + "\n")
    print(f"Locked files logged to {LOCKED_LOG}")
