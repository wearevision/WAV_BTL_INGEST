#!/usr/bin/env python3
"""List all events in Supabase with their slugs and ogImage status"""
import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "pipeline"))
from pipeline.supabase_client import SupabaseClient, SupabaseConfig

def main():
    load_dotenv()
    config = SupabaseConfig.from_env()
    
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
            print(f"\n✅ Total events in database: {len(events)}\n")
            print("=" * 80)
            
            for i, event in enumerate(events, 1):
                slug = event.get('slug', 'NO-SLUG')
                has_og = 'ogImage' in event and event['ogImage']
                og_status = "✅" if has_og else "❌"
                
                print(f"{i:3d}. {slug:60s} OG: {og_status}")
                
                if not has_og:
                    print(f"      → Missing ogImage!")
            
            print("=" * 80)
            print(f"\nEvents with ogImage: {sum(1 for e in events if e.get('ogImage'))}/{len(events)}")
            print(f"Events missing ogImage: {sum(1 for e in events if not e.get('ogImage'))}/{len(events)}")
        else:
            print("⚠️  No data found")
    else:
        print(f"❌ Error: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    main()
