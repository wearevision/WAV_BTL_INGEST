#!/usr/bin/env python3
import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "pipeline"))
from pipeline.supabase_client import SupabaseConfig

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
            target_slug = "2023-mistral-auspicios-y-activaciones"
            
            found = next((e for e in events if e["slug"] == target_slug), None)
            
            if found:
                print(f"✅ Found event: {target_slug}")
                print(json.dumps(found, indent=2))
            else:
                print(f"❌ Event {target_slug} not found in {len(events)} events")
                print("Available slugs:")
                for e in events:
                    print(f" - {e.get('slug')}")
        else:
            print("⚠️  No data found")
    else:
        print(f"❌ Error: {resp.status_code}")

if __name__ == "__main__":
    main()
