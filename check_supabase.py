#!/usr/bin/env python3
"""Check what's in Supabase KV store"""
import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "pipeline"))
from pipeline.supabase_client import SupabaseClient, SupabaseConfig

def main():
    load_dotenv()
    config = SupabaseConfig.from_env()
    
    print(f"Fetching data from KV store...")
    import requests
    
    url = f"{config.url}/rest/v1/kv_store_c4bb2206?key=eq.wav_events&select=value"
    headers = {
        "Authorization": f"Bearer {config.key}",
        "apikey": config.key,
    }
    
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        if data:
            events = data[0]["value"]
            print(f"\n✅ Found {len(events)} events in KV store")
            print(f"\nFirst event:")
            print(json.dumps(events[0], indent=2))
            
            # Check image URLs
            print(f"\n📸 Checking image URLs:")
            for i, event in enumerate(events[:3], 1):
                print(f"\nEvent {i}: {event.get('slug', 'no-slug')}")
                print(f"  Cover: {event.get('cover_url', 'NONE')}")
                if event.get('gallery_urls'):
                    print(f"  Gallery: {len(event['gallery_urls'])} images")
        else:
            print("⚠️  No data found in KV store")
    else:
        print(f"❌ Error: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    main()
