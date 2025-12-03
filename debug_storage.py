import os
import sys
from dotenv import load_dotenv
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "pipeline"))
from pipeline.supabase_client import SupabaseClient, SupabaseConfig

def main():
    load_dotenv()
    config = SupabaseConfig.from_env()
    client = SupabaseClient(config)
    
    print("Listing first 10 items in 'events' bucket:")
    files = client.list_files("events", limit=10)
    print(json.dumps(files, indent=2))

if __name__ == "__main__":
    main()
