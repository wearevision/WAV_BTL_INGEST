#!/usr/bin/env python3
"""
IMPROVED Media Curation Script
- Considers ALL images (selected + extracted_frame)
- Higher diversity threshold (very different images only)
- Cleans up non-final images after selection
"""

import argparse
import os
import shutil
from pathlib import Path
from typing import List, Tuple
import json

try:
    from PIL import Image
    import imagehash
except ImportError:
    print("Installing required dependencies...")
    os.system("pip install Pillow imagehash")
    from PIL import Image
    import imagehash


def get_image_hash(img_path: str) -> imagehash.ImageHash:
    """Get perceptual hash of image for similarity detection."""
    try:
        img = Image.open(img_path)
        return imagehash.phash(img, hash_size=16)
    except Exception as e:
        print(f"  ⚠️  Error hashing {img_path}: {e}")
        return None


def calculate_diversity_score(hashes: List[imagehash.ImageHash], new_hash: imagehash.ImageHash) -> float:
    """Calculate how diverse a new image is compared to already selected ones."""
    if not hashes:
        return 100.0
    
    distances = [new_hash - h for h in hashes]
    return sum(distances) / len(distances)


def select_best_images(
    image_paths: List[str],
    target_count: int = 6,
    similarity_threshold: int = 15,  # INCREASED from 10 (more different)
) -> List[str]:
    """
    Select VERY diverse images using perceptual hashing.
    
    Args:
        image_paths: List of image paths to choose from
        target_count: Number of images to select (default 6)
        similarity_threshold: Hamming distance threshold (HIGHER = more different)
    """
    if len(image_paths) <= target_count:
        return image_paths[:target_count]
    
    # Calculate hashes for all images
    image_data = []
    for path in image_paths:
        hash_val = get_image_hash(path)
        if hash_val:
            size = os.path.getsize(path)
            image_data.append((path, hash_val, size))
    
    if not image_data:
        return []
    
    # Sort by size (prefer higher quality)
    image_data.sort(key=lambda x: x[2], reverse=True)
    
    # Select hero (first/largest image)
    selected = [image_data[0]]
    selected_hashes = [image_data[0][1]]
    
    # Select remaining with MAXIMUM diversity
    candidates = image_data[1:]
    
    while len(selected) < target_count and candidates:
        best_candidate = None
        best_diversity = -1
        
        for candidate in candidates:
            path, hash_val, size = candidate
            
            # Check if too similar to already selected
            min_distance = min(hash_val - h for h in selected_hashes)
            if min_distance < similarity_threshold:
                continue  # Too similar, skip
            
            # Calculate diversity score
            diversity = calculate_diversity_score(selected_hashes, hash_val)
            
            if diversity > best_diversity:
                best_diversity = diversity
                best_candidate = candidate
        
        if best_candidate:
            selected.append(best_candidate)
            selected_hashes.append(best_candidate[1])
            candidates.remove(best_candidate)
        else:
            # No more diverse candidates found
            # Lower threshold slightly and try again
            threshold = similarity_threshold - 2
            while threshold > 5 and len(selected) < target_count and candidates:
                for candidate in candidates:
                    _, hash_val, _ = candidate
                    min_distance = min(hash_val - h for h in selected_hashes)
                    if min_distance >= threshold:
                        selected.append(candidate)
                        selected_hashes.append(hash_val)
                        candidates.remove(candidate)
                        break
                else:
                    threshold -= 2
            break
    
    return [path for path, _, _ in selected]


def curate_event(event_dir: Path, dry_run: bool = False, clean: bool = True) -> Tuple[int, int]:
    """
    Curate media for a single event.
    Args:
        clean: If True, delete non-final images after selection
    Returns: (original_count, final_count)
    """
    # Find ALL images (selected + extracted_frame)
    all_patterns = [
        "selected_*.jpg",
        "selected_*.jpeg",
        "extracted_frame_*.jpg",
        "extracted_frame_*.jpeg"
    ]
    
    image_files = []
    for pattern in all_patterns:
        image_files.extend(event_dir.glob(pattern))
    
    image_files = sorted(set(image_files))  # Remove duplicates
    
    if not image_files:
        return (0, 0)
    
    original_count = len(image_files)
    
    # Select best 6 with HIGH diversity
    selected = select_best_images([str(p) for p in image_files], target_count=6, similarity_threshold=15)
    
    if dry_run:
        print(f"    [DRY RUN] Would keep {len(selected)}/{original_count} VERY different images")
        return (original_count, len(selected))
    
    # Create final_*.jpg files
    for i, img_path in enumerate(selected):
        new_name = f"final_{i:02d}.jpg"
        new_path = event_dir / new_name
        # Delete existing final if exists
        if new_path.exists():
            new_path.unlink()
        shutil.copy2(img_path, new_path)
    
    # CLEAN UP: Remove all selected_* and extracted_frame_* files
    if clean:
        for pattern in all_patterns:
            for old_file in event_dir.glob(pattern):
                try:
                    old_file.unlink()
                except Exception as e:
                    print(f"    ⚠️  Could not delete {old_file.name}: {e}")
    
    # Update metadata.json
    metadata_path = event_dir / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            if "media" in metadata:
                new_media = []
                for i in range(len(selected)):
                    new_media.append({
                        "type": "image",
                        "local_path": f"final_{i:02d}.jpg"
                    })
                metadata["media"] = new_media
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"    ⚠️  Error updating metadata: {e}")
    
    print(f"    ✅ Selected {len(selected)}/{original_count} VERY different images (cleaned: {clean})")
    return (original_count, len(selected))


def main():
    parser = argparse.ArgumentParser(description="Curate event media with HIGH diversity")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without changes")
    parser.add_argument("--no-clean", action="store_true", help="Don't delete original files")
    parser.add_argument("--limit", type=int, help="Process only N events")
    args = parser.parse_args()
    
    base_dir = Path("organized_events")
    event_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name != "OJO"]
    event_dirs.sort()
    
    if args.limit:
        event_dirs = event_dirs[:args.limit]
    
    print(f"📸 Curating media for {len(event_dirs)} events...")
    print(f"   Diversity: HIGH (threshold=15)")
    print(f"   Cleanup: {'OFF' if args.no_clean else 'ON'}")
    print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("-" * 60)
    
    total_before = 0
    total_after = 0
    
    for i, event_dir in enumerate(event_dirs, 1):
        print(f"[{i}/{len(event_dirs)}] {event_dir.name}")
        before, after = curate_event(event_dir, dry_run=args.dry_run, clean=not args.no_clean)
        total_before += before
        total_after += after
    
    print("=" * 60)
    print(f"✨ Curation complete!")
    print(f"   Before: {total_before} images")
    print(f"   After: {total_after} images")
    print(f"   Reduction: {total_before - total_after} images ({100 * (total_before - total_after) / total_before if total_before > 0 else 0:.1f}%)")


if __name__ == "__main__":
    main()
