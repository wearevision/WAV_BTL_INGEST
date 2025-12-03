#!/usr/bin/env python3
"""
Cleanup script to remove 'extracted_frames' folders and update metadata.json.
"""

import os
import shutil
import json
from pathlib import Path

def cleanup_event(event_dir: Path):
    """
    Removes 'extracted_frames' folder and updates metadata.json for a single event.
    """
    extracted_frames_dir = event_dir / "extracted_frames"
    metadata_path = event_dir / "metadata.json"
    
    # 1. Remove extracted_frames folder
    if extracted_frames_dir.exists() and extracted_frames_dir.is_dir():
        print(f"  🗑️  Removing {extracted_frames_dir.name}...")
        try:
            shutil.rmtree(extracted_frames_dir)
        except Exception as e:
            print(f"    ❌ Error removing directory: {e}")

    # 2. Update metadata.json
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            original_media_count = len(metadata.get("media", []))
            
            # Filter out media items that are in extracted_frames
            if "media" in metadata:
                new_media = []
                for item in metadata["media"]:
                    local_path = item.get("local_path", "")
                    if "extracted_frames" not in local_path:
                        new_media.append(item)
                
                metadata["media"] = new_media
            
            # Save if changes were made
            if len(metadata.get("media", [])) != original_media_count:
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                print(f"  📝 Updated metadata.json (removed {original_media_count - len(metadata['media'])} items)")
                
        except Exception as e:
            print(f"    ❌ Error updating metadata: {e}")

def main():
    base_dir = Path("organized_events")
    if not base_dir.exists():
        print("❌ 'organized_events' directory not found.")
        return

    event_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name != "OJO"]
    event_dirs.sort()
    
    print(f"🧹 Cleaning up 'extracted_frames' from {len(event_dirs)} events...")
    
    for i, event_dir in enumerate(event_dirs, 1):
        # Only print if we are actually doing something to reduce noise, 
        # or check if the folder exists before printing the event name
        if (event_dir / "extracted_frames").exists():
            print(f"[{i}/{len(event_dirs)}] {event_dir.name}")
            cleanup_event(event_dir)

    print("\n✨ Cleanup complete!")

if __name__ == "__main__":
    main()
