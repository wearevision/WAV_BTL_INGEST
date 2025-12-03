import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "pipeline"))
from pipeline.supabase_client import SupabaseClient, SupabaseConfig

def main():
    load_dotenv()
    try:
        config = SupabaseConfig.from_env()
        client = SupabaseClient(config)
    except Exception as e:
        print(f"❌ Error initializing Supabase client: {e}")
        sys.exit(1)

    print("Fetching one event from Supabase...")
    # Using REST API to get 1 event
    url = f"{config.url}/rest/v1/events?select=*&limit=1"
    headers = {
        "Authorization": f"Bearer {config.key}",
        "apikey": config.key,
        "Content-Type": "application/json"
    }
    
    import requests
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        events = resp.json()
        if events:
            event = events[0]
            with open("reference_event.json", "w") as f:
                json.dump(event, f, indent=2)
            print("✅ Exported 'reference_event.json'")
            print(json.dumps(event, indent=2))
        else:
            print("⚠️  No events found in table 'events'. Cannot create reference.")
            # Create a dummy reference based on schema if empty?
            # Or ask user to provide one?
            # For now, just warn.
    else:
        print(f"❌ Error fetching event: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    main()
