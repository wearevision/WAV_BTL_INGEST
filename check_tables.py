import os
import sys
import requests
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "pipeline"))
from pipeline.supabase_client import SupabaseConfig

def main():
    load_dotenv()
    config = SupabaseConfig.from_env()
    
    print(f"Checking Supabase URL: {config.url}")
    
    headers = {
        "apikey": config.key,
        "Authorization": f"Bearer {config.key}"
    }
    
    # 1. Check root (OpenAPI description or list of tables)
    resp = requests.get(f"{config.url}/rest/v1/", headers=headers)
    print(f"Root status: {resp.status_code}")
    if resp.status_code == 200:
        # Usually returns OpenAPI JSON or list of definitions
        try:
            data = resp.json()
            print("Available definitions (tables):")
            if "definitions" in data:
                for table in data["definitions"]:
                    print(f" - {table}")
            else:
                print(data.keys())
        except:
            print(resp.text[:200])
            
    # 2. Check 'events' specifically
    resp = requests.get(f"{config.url}/rest/v1/events", headers=headers, params={"limit": 1})
    print(f"Table 'events' status: {resp.status_code}")
    print(resp.text)

if __name__ == "__main__":
    main()
