#!/usr/bin/env python3
"""
Fix existing 5 events in Supabase to use correct structure.
Changes:
- cover_url → image
- gallery_urls → gallery: [{id, type, url}]
- Remove metadata field
"""

import os
import sys
from dotenv import load_dotenv
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "pipeline"))
from pipeline.supabase_client import SupabaseClient, SupabaseConfig
from categorize_events import categorize_event_from_dict

def transform_event(event):
    """Transform event from current structure to correct structure."""
    # Get cover/main image URL
    main_image = event.get("image") or event.get("cover_url")
    
    # Categorize event intelligently
    category = categorize_event_from_dict(event)
    
    # Create new event with correct structure
    fixed_event = {
        "id": event.get("id"),
        "slug": event.get("slug"),
        "title": event.get("title"),
        "year": event.get("year"),
        "brand": event.get("brand"),
        
        # Main image
        "image": main_image,
        
        # OG Image for social sharing
        "ogImage": main_image,
        
        # Gallery
        "gallery": [],
        
        # Keep description if exists
        "description": event.get("description") or event.get("metadata", {}).get("content", {}).get("description", ""),
        
        # Optional fields
        "summary": event.get("summary") or event.get("metadata", {}).get("content", {}).get("summary", ""),
        
        # INTELLIGENT CATEGORIZATION (no logo field)
        "category": category,
    }
    
    # Transform gallery_urls OR gallery to correct format
    gallery_urls = event.get("gallery_urls") or []
    existing_gallery = event.get("gallery") or []
    
    if gallery_urls:
        # Old format: array of URLs
        for i, url in enumerate(gallery_urls):
            fixed_event["gallery"].append({
                "id": f"gallery-{i:03d}",
                "type": "image",
                "url": url
            })
    elif existing_gallery and isinstance(existing_gallery, list):
        # Already in correct format, just copy
        fixed_event["gallery"] = existing_gallery
    
    # Add highlights, keywords, hashtags if exists
    metadata_content = event.get("metadata", {}).get("content", {})
    highlights = metadata_content.get("highlights", [])
    if highlights:
        fixed_event["highlights"] = highlights
    if highlights:
        fixed_event["highlights"] = highlights
    
    # Add keywords if exists
    keywords = event.get("metadata", {}).get("content", {}).get("keywords", [])
    if keywords:
        fixed_event["keywords"] = keywords
    
    # Add hashtags if exists
    hashtags = event.get("metadata", {}).get("content", {}).get("hashtags", [])
    if hashtags:
        fixed_event["hashtags"] = hashtags
    
    return fixed_event


def main():
    load_dotenv()
    
    try:
        config = SupabaseConfig.from_env()
        client = SupabaseClient(config)
    except Exception as e:
        print(f"❌ Error initializing Supabase client: {e}")
        sys.exit(1)
    
    print("🔍 Fetching current events from KV store...")
    
    # Get current events
    import requests
    url = f"{config.url}/rest/v1/kv_store_c4bb2206?key=eq.wav_events&select=value"
    headers = {
        "Authorization": f"Bearer {config.key}",
        "apikey": config.key,
    }
    
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error fetching events: {resp.status_code} {resp.text}")
        sys.exit(1)
    
    data = resp.json()
    if not data:
        print("⚠️  No events found in KV store")
        sys.exit(0)
    
    current_events = data[0]["value"]
    print(f"✅ Found {len(current_events)} events")
    
    # Transform events
    print("\n🔧 Transforming events to correct structure...")
    fixed_events = []
    for i, event in enumerate(current_events, 1):
        print(f"  [{i}/{len(current_events)}] {event.get('slug', 'unknown')}")
        fixed = transform_event(event)
        fixed_events.append(fixed)
    
    print(f"\n✅ Transformed {len(fixed_events)} events")
    
    # Show sample of transformation
    print("\n📋 Sample transformed event:")
    print(json.dumps(fixed_events[0], indent=2))
    
    # Confirm before updating
    print("\n⚠️  This will UPDATE the KV store with the fixed structure.")
    confirm = input("Type 'YES' to proceed: ")
    if confirm != "YES":
        print("❌ Operation cancelled")
        sys.exit(0)
    
    # Update KV store
    print("\n📤 Updating KV store...")
    try:
        result = client.upsert_kv("wav_events", fixed_events)
        print(f"✅ Successfully updated KV store!")
        print(f"   New structure applied to {len(fixed_events)} events")
    except Exception as e:
        print(f"❌ Error updating KV store: {e}")
        sys.exit(1)
    
    print("\n✨ Done! Events now have correct structure for frontend.")
    print("   Visit btl.wearevision.cl to verify photos are visible.")


if __name__ == "__main__":
    main()
