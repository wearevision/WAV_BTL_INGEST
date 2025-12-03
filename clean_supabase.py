#!/usr/bin/env python3
"""
Script to clean all data from Supabase 'events' table and 'events' bucket.
WARNING: This deletes everything.
"""

import os
import sys
from dotenv import load_dotenv

# Add pipeline directory to path
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

    print("⚠️  WARNING: This will DELETE ALL data in 'events' table and bucket.")
    confirm = input("Type 'DELETE' to confirm: ")
    if confirm != "DELETE":
        print("Operation cancelled.")
        sys.exit(0)

    print("\n1. Cleaning Database Table 'events'...")
    try:
        status = client.delete_all("events")
        print(f"   ✅ Table cleaned (Status: {status})")
    except Exception as e:
        print(f"   ❌ Error cleaning table: {e}")

    print("\n2. Cleaning Storage Bucket 'events'...")
    try:
        count = client.empty_bucket("events")
        print(f"   ✅ Bucket cleaned ({count} files deleted)")
    except Exception as e:
        print(f"   ❌ Error cleaning bucket: {e}")

    print("\n✨ Cleanup complete.")

if __name__ == "__main__":
    main()
