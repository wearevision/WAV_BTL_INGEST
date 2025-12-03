#!/usr/bin/env python3
"""
Migration script: organized_events → Supabase KV Store

Processes all events and uploads to Supabase key-value store with enhanced images.
Figma/Make expects all events in a single JSON array under key 'wav_events'.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import uuid

from dotenv import load_dotenv

# Add pipeline to path
sys.path.append(os.path.join(os.path.dirname(__file__), "pipeline"))

from pipeline.supabase_client import SupabaseClient, SupabaseConfig
from pipeline.image_enhancer import enhance_image
from categorize_events import categorize_event_from_dict


def get_event_folders(base_dir: str = "organized_events") -> List[Path]:
    """Get all event folders, excluding OJO."""
    base_path = Path(base_dir)
    folders = [f for f in base_path.iterdir() if f.is_dir() and f.name != "OJO"]
    return sorted(folders)


def slugify(value: str) -> str:
    """Normalize string to URL-safe slug."""
    import re
    import unicodedata
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def process_event(
    event_dir: Path,
    supabase: SupabaseClient,
    dry_run: bool = False,
    enhance: bool = True,
) -> Optional[Dict]:
    """
    Process a single event: enhance images, upload to storage, return event data.
    
    Returns:
        Event data dict if successful, None if failed
    """
    # Sanitize slug
    original_slug = event_dir.name
    slug = slugify(original_slug)
    
    metadata_path = event_dir / "metadata.json"
    
    # Load metadata
    if not metadata_path.exists():
        print(f"  ⚠️  No metadata.json found, skipping")
        return None
    
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    # Helper to find files case-insensitive
    def find_files(pattern_prefix: str, extensions: List[str]) -> List[Path]:
        found = []
        for ext in extensions:
            # Try lowercase and uppercase extensions
            found.extend(event_dir.glob(f"{pattern_prefix}*{ext}"))
            found.extend(event_dir.glob(f"{pattern_prefix}*{ext.upper()}"))
        return sorted(list(set(found))) # Deduplicate

    # Find images (final > selected)
    image_files = find_files("final_", [".jpg", ".jpeg", ".png", ".webp"])
    if not image_files:
        image_files = find_files("selected_", [".jpg", ".jpeg", ".png", ".webp"])
        
    # Find video clips (clip_ or video_)
    video_files = find_files("clip_", [".mp4", ".mov"])
    if not video_files:
        video_files = find_files("video_", [".mp4", ".mov"])
    
    if not image_files and not video_files:
        print(f"  ⚠️  No images or videos found, skipping")
        return None
    
    # Prepare temp directory for enhanced images
    temp_dir = event_dir / ".enhanced"
    if enhance and not dry_run:
        temp_dir.mkdir(exist_ok=True)
    
    # Process media (Images + Videos)
    gallery_items = []
    cover_url = ""
    
    # Combine media list (max 7 total files)
    media_list = []
    
    # Prioritize images, then videos
    for img in image_files:
        if len(media_list) >= 7:
            break
        media_list.append({"path": img, "type": "image"})
    
    for vid in video_files:
        if len(media_list) >= 7:
            break
        media_list.append({"path": vid, "type": "video"})
    
    for i, media in enumerate(media_list):
        file_path = media["path"]
        media_type = media["type"]
        
        if dry_run:
            print(f"    [DRY RUN] Would upload {media_type}: {file_path.name}")
            url = f"https://example.com/{slug}/gallery_{i:02d}.{'webp' if media_type == 'image' else 'mp4'}"
            gallery_items.append({
                "id": f"gallery-{i:03d}",
                "type": media_type,
                "url": url
            })
            if i == 0 and media_type == "image":
                cover_url = url
            continue
        
        # Prepare upload path
        if media_type == "image":
            # Enhance image
            if enhance:
                enhanced_path = temp_dir / f"enhanced_{i:02d}.webp"
                try:
                    enhance_image(str(file_path), str(enhanced_path))
                    upload_path = enhanced_path
                except Exception as e:
                    print(f"    ⚠️  Enhancement failed for {file_path.name}, using original: {e}")
                    upload_path = file_path
            else:
                upload_path = file_path
            dest_filename = f"gallery_{i:02d}.webp"
        else:
            # Video (no enhancement)
            upload_path = file_path
            dest_filename = f"gallery_{i:02d}.mp4"
        
        # Upload to Supabase Storage
        try:
            dest_path = f"{slug}/{dest_filename}"
            url = supabase.upload_file(str(upload_path), dest_path)
            
            gallery_items.append({
                "id": f"gallery-{i:03d}",
                "type": media_type,
                "url": url
            })
            
            # Set cover URL (first image)
            if not cover_url and media_type == "image":
                cover_url = url
            
            print(f"    ✅ Uploaded: {dest_filename} ({media_type})")
        except Exception as e:
            print(f"    ❌ Upload failed for {file_path.name}: {e}")
    
    # Cleanup temp directory
    if enhance and not dry_run and temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)
    
    # Prepare event data with CORRECT structure for frontend
    # Intelligent categorization
    category = categorize_event_from_dict({
        "title": metadata.get("content", {}).get("title", metadata.get("event_name", slug)),
        "description": metadata.get("content", {}).get("description", ""),
        "summary": metadata.get("content", {}).get("summary", ""),
        "keywords": metadata.get("content", {}).get("keywords", []),
        "event_name": metadata.get("event_name", ""),
        "slug": slug,
        "metadata": metadata
    })
    
    event_data = {
        "id": str(uuid.uuid4()),
        "slug": slug,
        "title": metadata.get("content", {}).get("title", metadata.get("event_name", slug)),
        "year": metadata.get("year", 2024),
        "brand": metadata.get("brand", ""),
        
        # Main image
        "image": cover_url,
        
        # OG Image for social sharing (NO logo - only if we have the real one)
        "ogImage": cover_url,
        
        # Gallery
        "gallery": gallery_items,
        
        # Content fields
        "description": metadata.get("content", {}).get("description", ""),
        "summary": metadata.get("content", {}).get("summary", ""),
        
        # INTELLIGENT CATEGORIZATION
        "category": category,
    }
    
    # Add optional fields if they exist
    if metadata.get("content", {}).get("highlights"):
        event_data["highlights"] = metadata["content"]["highlights"]
    
    if metadata.get("content", {}).get("keywords"):
        event_data["keywords"] = metadata["content"]["keywords"]
    
    if metadata.get("content", {}).get("hashtags"):
        event_data["hashtags"] = metadata["content"]["hashtags"]
    
    return event_data


def main():
    parser = argparse.ArgumentParser(description="Migrate events to Supabase KV Store")
    parser.add_argument("--limit", type=int, help="Process only N events")
    parser.add_argument("--skip", type=int, default=0, help="Skip first N events")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without uploading")
    parser.add_argument("--no-enhance", action="store_true", help="Skip image enhancement")
    parser.add_argument("--filter", type=str, help="Process only events matching this string")
    args = parser.parse_args()
    
    # Load environment
    load_dotenv()
    
    # Initialize Supabase
    try:
        config = SupabaseConfig.from_env()
        supabase = SupabaseClient(config)
    except Exception as e:
        print(f"❌ Supabase init failed: {e}")
        sys.exit(1)
    
    # Get event folders
    folders = get_event_folders()
    
    # Apply filter if specified
    if args.filter:
        folders = [f for f in folders if args.filter in f.name]
        if not folders:
            print(f"❌ No events found matching '{args.filter}'")
            sys.exit(1)
    
    # Apply skip/limit
    if args.skip:
        folders = folders[args.skip:]
    if args.limit:
        folders = folders[:args.limit]
    
    print(f"📦 Processing {len(folders)} events...")
    print(f"   Enhancement: {'ON' if not args.no_enhance else 'OFF'}")
    print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("-" * 60)
    
    # Process events and build array
    events_array = []
    success_count = 0
    
    for i, folder in enumerate(folders, 1):
        print(f"[{i}/{len(folders)}] {folder.name}")
        result = process_event(
            folder,
            supabase,
            dry_run=args.dry_run,
            enhance=not args.no_enhance,
        )
        if result:
            events_array.append(result)
            success_count += 1
        print()
    
    # Upsert to KV store (MERGE with existing, don't replace)
    print("=" * 60)
    if args.dry_run:
        print(f"[DRY RUN] Would merge {success_count} new events with existing events")
        print(f"Sample payload (first event):")
        if events_array:
            print(json.dumps(events_array[0], indent=2))
    else:
        try:
            # 1. Get existing events from KV store
            print(f"📥 Fetching existing events from KV store...")
            import requests
            url = f"{config.url}/rest/v1/kv_store_c4bb2206?key=eq.wav_events&select=value"
            headers = {
                "Authorization": f"Bearer {config.key}",
                "apikey": config.key,
            }
            resp = requests.get(url, headers=headers)
            
            existing_events = []
            if resp.status_code == 200:
                data = resp.json()
                if data and data[0].get("value"):
                    existing_events = data[0]["value"]
                    print(f"   Found {len(existing_events)} existing events")
            
            # 2. Merge: Add new events, update existing ones (by slug)
            print(f"🔄 Merging {success_count} new events with {len(existing_events)} existing...")
            
            # Create a dict for quick lookup by slug
            events_dict = {event["slug"]: event for event in existing_events}
            
            # Add/update new events
            updated_count = 0
            added_count = 0
            for new_event in events_array:
                slug = new_event["slug"]
                if slug in events_dict:
                    # Update existing event
                    events_dict[slug] = new_event
                    updated_count += 1
                else:
                    # Add new event
                    events_dict[slug] = new_event
                    added_count += 1
            
            # Convert back to array
            merged_events = list(events_dict.values())
            
            # Sort by year and slug for consistency (handle year as string or int)
            def get_year(e):
                year = e.get("year", 0)
                try:
                    return int(year) if year else 0
                except (ValueError, TypeError):
                    return 0
            
            merged_events.sort(key=lambda e: (get_year(e), e.get("slug", "")))
            
            print(f"   📊 Added: {added_count}, Updated: {updated_count}, Total: {len(merged_events)}")
            
            # 3. Upsert merged array
            print(f"📤 Upserting {len(merged_events)} total events to KV store...")
            result = supabase.upsert_kv("wav_events", merged_events)
            print(f"✅ Successfully upserted to 'wav_events' key!")
            print(f"   Final count: {len(merged_events)} events")
        except Exception as e:
            print(f"❌ KV upsert failed: {e}")
            sys.exit(1)
        
    print(f"✨ Migration complete! {success_count}/{len(folders)} events processed.")


if __name__ == "__main__":
    main()
