#!/usr/bin/env python3
"""
Script to convert all .mov videos in `organized_events` to H.264 MP4 (720p).
Updates metadata.json references and deletes original .mov files.

Usage:
    python convert_videos.py [--dry-run]
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List

ORGANIZED_EVENTS_DIR = Path("organized_events")

def get_mov_files() -> List[Path]:
    """Recursively find all .mov files (case insensitive)."""
    mov_files = []
    for root, _, files in os.walk(ORGANIZED_EVENTS_DIR):
        for file in files:
            if file.lower().endswith(".mov"):
                mov_files.append(Path(root) / file)
    return sorted(mov_files)

def convert_video(input_path: Path, dry_run: bool) -> bool:
    """Convert video to mp4 using ffmpeg."""
    output_path = input_path.with_suffix(".mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "23",
        "-vf", "scale=-2:720",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_path)
    ]
    
    if dry_run:
        print(f"  [DRY RUN] Would run: {' '.join(cmd)}")
        return True
        
    try:
        print(f"  Converting: {input_path.name} -> {output_path.name}...")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if output_path.exists() and output_path.stat().st_size > 0:
            return True
        else:
            print(f"  ❌ Conversion failed: Output file empty or missing.")
            return False
    except subprocess.CalledProcessError as e:
        print(f"  ❌ FFmpeg error: {e}")
        return False

def update_metadata(folder_path: Path, old_filename: str, new_filename: str, dry_run: bool) -> None:
    """Update metadata.json to replace old filename with new filename."""
    metadata_path = folder_path / "metadata.json"
    if not metadata_path.exists():
        return

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if old_filename in content:
            if dry_run:
                print(f"  [DRY RUN] Would update metadata: {old_filename} -> {new_filename}")
            else:
                new_content = content.replace(old_filename, new_filename)
                with open(metadata_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"  ✅ Metadata updated.")
    except Exception as e:
        print(f"  ❌ Error updating metadata: {e}")

def main():
    parser = argparse.ArgumentParser(description="Convert videos to MP4.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing.")
    args = parser.parse_args()

    # Check ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: ffmpeg is not installed or not in PATH.")
        sys.exit(1)

    files = get_mov_files()
    print(f"Found {len(files)} .mov files to convert.")
    print("-" * 60)

    success_count = 0
    
    for i, mov_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing {mov_path.name}...")
        
        if convert_video(mov_path, args.dry_run):
            # Update metadata
            update_metadata(mov_path.parent, mov_path.name, mov_path.with_suffix(".mp4").name, args.dry_run)
            
            # Delete original
            if not args.dry_run:
                try:
                    mov_path.unlink()
                    print(f"  🗑️  Deleted original: {mov_path.name}")
                    success_count += 1
                except OSError as e:
                    print(f"  ❌ Error deleting file: {e}")
            else:
                print(f"  [DRY RUN] Would delete: {mov_path.name}")
                success_count += 1
        
        print("-" * 40)

    if args.dry_run:
        print(f"\n[DRY RUN] Completed. Would convert {success_count} videos.")
    else:
        print(f"\n✅ Completed. Converted {success_count}/{len(files)} videos.")

if __name__ == "__main__":
    main()
