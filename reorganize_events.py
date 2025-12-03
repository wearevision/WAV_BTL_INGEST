#!/usr/bin/env python3
"""
Script to reorganize event folders in `organized_events` by distributing years linearly
from 2007 to 2025.

Usage:
    python reorganize_events.py [--dry-run]
"""

import argparse
import json
import math
import os
import re
import shutil
from pathlib import Path
from typing import List, Tuple

ORGANIZED_EVENTS_DIR = Path("organized_events")
START_YEAR = 2007
END_YEAR = 2025
IGNORE_FOLDERS = {"OJO", ".DS_Store"}

def get_event_folders() -> List[Path]:
    """Get list of valid event folders sorted alphabetically."""
    folders = []
    if not ORGANIZED_EVENTS_DIR.exists():
        return []
        
    for item in ORGANIZED_EVENTS_DIR.iterdir():
        if item.name in IGNORE_FOLDERS or item.name.startswith("."):
            continue
        if item.is_dir():
            folders.append(item)
    
    return sorted(folders, key=lambda p: p.name)

def calculate_year(index: int, total: int) -> int:
    """Calculate year based on linear interpolation."""
    if total <= 1:
        return START_YEAR
    
    progress = index / (total - 1)
    year_range = END_YEAR - START_YEAR
    return START_YEAR + int(round(progress * year_range))

def parse_folder_name(folder_name: str) -> Tuple[str, str]:
    """Extract year and slug from folder name.
    Expected format: 'YYYY-slug-text' or just 'slug-text'
    Returns: (original_year_str, slug_body)
    """
    match = re.match(r"^(\d{4})-(.+)$", folder_name)
    if match:
        return match.group(1), match.group(2)
    return "", folder_name

def update_metadata(file_path: Path, new_year: int, new_slug: str, dry_run: bool) -> None:
    """Update metadata.json with new year and slug."""
    if not file_path.exists():
        print(f"  ⚠️  Metadata file not found: {file_path}")
        return

    if dry_run:
        print(f"  [DRY RUN] Would update metadata: year={new_year}, slug={new_slug}")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        data["year"] = new_year
        data["slug"] = new_slug
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"  ❌ Error updating metadata: {e}")

def main():
    parser = argparse.ArgumentParser(description="Reorganize event folders.")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without executing them.")
    args = parser.parse_args()

    folders = get_event_folders()
    total_folders = len(folders)
    
    print(f"Found {total_folders} folders to process.")
    print(f"Target range: {START_YEAR} -> {END_YEAR}")
    print("-" * 60)
    print(f"{'IDX':<4} | {'OLD NAME':<40} | {'NEW YEAR':<8} | {'NEW NAME'}")
    print("-" * 60)

    for i, folder in enumerate(folders):
        new_year = calculate_year(i, total_folders)
        _, slug_body = parse_folder_name(folder.name)
        
        new_folder_name = f"{new_year}-{slug_body}"
        new_folder_path = folder.parent / new_folder_name
        
        print(f"{i:<4} | {folder.name:<40} | {new_year:<8} | {new_folder_name}")
        
        if folder.name == new_folder_name:
            continue

        if not args.dry_run:
            # 1. Rename folder
            try:
                folder.rename(new_folder_path)
                
                # 2. Update metadata inside the NEW path
                metadata_path = new_folder_path / "metadata.json"
                update_metadata(metadata_path, new_year, new_folder_name, args.dry_run)
                
            except Exception as e:
                print(f"  ❌ Error processing {folder.name}: {e}")
        else:
             # In dry run, we simulate metadata update on the old path just to show the log
             metadata_path = folder / "metadata.json"
             update_metadata(metadata_path, new_year, new_folder_name, args.dry_run)

    if args.dry_run:
        print("\n[DRY RUN] No changes were made. Run without --dry-run to execute.")
    else:
        print("\n✅ Reorganization complete.")

if __name__ == "__main__":
    main()
