#!/usr/bin/env python3
"""Check for event folders with no media."""
import os
from pathlib import Path

def main():
    base_dir = Path("organized_events")
    if not base_dir.exists():
        print("❌ 'organized_events' directory not found.")
        return

    folders = [f for f in base_dir.iterdir() if f.is_dir() and f.name != "OJO"]
    folders.sort()
    
    empty_folders = []
    
    print(f"Checking {len(folders)} folders for media...")
    print("-" * 60)
    
    for folder in folders:
        # Check for images
        images = list(folder.glob("final_*.jpg")) + list(folder.glob("selected_*.jpg")) + list(folder.glob("selected_*.jpeg"))
        
        # Check for videos
        videos = list(folder.glob("clip_*.mp4"))
        
        if not images and not videos:
            empty_folders.append(folder.name)
            print(f"❌ No media: {folder.name}")
            
    print("-" * 60)
    print(f"Total folders with no media: {len(empty_folders)}")

if __name__ == "__main__":
    main()
