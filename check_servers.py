#!/usr/bin/env python3
import os
import sys
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
    servers = client.get_servers()
    
    print("Available Servers:")
    print("="*60)
    for server in servers:
        identifier = server.get("identifier", "N/A")
        name = server.get("name", "N/A")
        print(f"  Identifier: {identifier}")
        print(f"  Name: {name}")
        print()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
