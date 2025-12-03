#!/usr/bin/env python3
"""
Recursively inspect specific folders that were reported as empty
to find potential media files (images/videos).
"""
import os
from pathlib import Path

TARGET_FOLDERS = [
    "2013-verisure-cunaseg",
    "2016-converse-gathering",
    "2017-altra-produccion-e-influencer-marketing-costa-rica",
    "2017-converse-find-your-beat-1",
    "2018-mg-motor-exhibicion-alto-las-condes",
    "2018-mg-motor-stand-experiencia-e",
    "2019-bioritmo-lanzamiento-gimnasio-panama",
    "2019-pichara-stand-cosmetic-beauty-lima",
    "2019-soprole-stand-feria-laboral",
    "2020-birkenstock-apertura-tienda-bogota",
    "2021-converse-lanzamiento-edge-of-style",
    "2022-geely-ex5-stand-casa-costanera",
    "2022-hyundai-apertura-sucursal-peru",
    "2023-mg-motor-car-display"
]

MEDIA_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov', '.avi'}

def inspect_folder(folder_name):
    base_path = Path("organized_events") / folder_name
    if not base_path.exists():
        print(f"❌ Folder not found: {folder_name}")
        return

    print(f"\n📂 Inspecting: {folder_name}")
    found_media = []
    
    # Walk through all directories
    for root, dirs, files in os.walk(base_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in MEDIA_EXTENSIONS:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(base_path)
                found_media.append(str(rel_path))

    if found_media:
        print(f"   ✅ Found {len(found_media)} potential media files:")
        for m in found_media[:10]:  # Show first 10
            print(f"      - {m}")
        if len(found_media) > 10:
            print(f"      ... and {len(found_media) - 10} more")
    else:
        print("   ⚠️  No media files found (recursively)")

def main():
    print(f"🔍 Inspecting {len(TARGET_FOLDERS)} folders...")
    for folder in TARGET_FOLDERS:
        inspect_folder(folder)

if __name__ == "__main__":
    main()
