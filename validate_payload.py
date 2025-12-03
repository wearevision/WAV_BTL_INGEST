#!/usr/bin/env python3
"""
Validation script to ensure migrated events match expected schema.
Compares against a reference event from current Supabase setup.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set


def load_reference(path: str = "reference_event.json") -> Dict:
    """Load reference event structure from JSON file."""
    if not Path(path).exists():
        print(f"❌ Reference file not found: {path}")
        print("   Create it by exporting one current event from Supabase:")
        print("   SELECT * FROM events LIMIT 1;")
        sys.exit(1)
    
    with open(path, "r") as f:
        return json.load(f)


def get_schema(obj: Dict, prefix: str = "") -> Set[str]:
    """Extract schema (field paths and types) from nested dict."""
    schema = set()
    
    for key, value in obj.items():
        path = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            schema.add(f"{path}:object")
            schema.update(get_schema(value, path))
        elif isinstance(value, list):
            schema.add(f"{path}:array")
            if value and isinstance(value[0], dict):
                schema.update(get_schema(value[0], f"{path}[]"))
        else:
            schema.add(f"{path}:{type(value).__name__}")
    
    return schema


def validate_event(test_event: Dict, reference: Dict) -> List[str]:
    """
    Validate test event against reference schema.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    ref_schema = get_schema(reference)
    test_schema = get_schema(test_event)
    
    # Check for missing fields
    missing = ref_schema - test_schema
    if missing:
        errors.append(f"Missing fields: {sorted(missing)}")
    
    # Check for extra fields (warning, not error)
    extra = test_schema - ref_schema
    if extra:
        print(f"⚠️  Extra fields (may be OK): {sorted(extra)}")
    
    # Check required fields are not null
    required_fields = ["id", "slug", "title", "cover_url"]
    for field in required_fields:
        if field not in test_event or test_event[field] is None:
            errors.append(f"Required field '{field}' is missing or null")
    
    # Check URL accessibility (basic format check)
    url_fields = ["cover_url"]
    if "gallery_urls" in test_event:
        url_fields.append("gallery_urls")
    
    for field in url_fields:
        if field in test_event:
            urls = test_event[field] if isinstance(test_event[field], list) else [test_event[field]]
            for url in urls:
                if url and not url.startswith("http"):
                    errors.append(f"Invalid URL in '{field}': {url}")
    
    return errors


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate event payload")
    parser.add_argument("--reference", default="reference_event.json", help="Reference event JSON")
    parser.add_argument("--test", required=True, help="Test event JSON to validate")
    args = parser.parse_args()
    
    # Load files
    reference = load_reference(args.reference)
    
    if not Path(args.test).exists():
        print(f"❌ Test file not found: {args.test}")
        sys.exit(1)
    
    with open(args.test, "r") as f:
        test_event = json.load(f)
    
    # Validate
    print("🔍 Validating event structure...")
    print(f"   Reference: {args.reference}")
    print(f"   Test: {args.test}")
    print()
    
    errors = validate_event(test_event, reference)
    
    if errors:
        print("❌ Validation FAILED:")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)
    else:
        print("✅ Validation PASSED!")
        print("   Event structure matches reference.")
        print("   Safe to proceed with migration.")


if __name__ == "__main__":
    main()
