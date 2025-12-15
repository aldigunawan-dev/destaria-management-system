#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pterodactyl.client import PterodactylClient

url = os.getenv('PTERODACTYL_PANEL_URL')
key = os.getenv('PTERODACTYL_API_KEY')

print(f"Panel URL: {url}")
print(f"API Key: {key[:10]}...")
print("\n" + "="*60)

try:
    client = PterodactylClient(url, key)
    result = client._make_request("GET", "/api/client")
    
    print("Raw API Response:")
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
