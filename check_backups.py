#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from pathlib import Path
import sys

project_root = Path.cwd()
sys.path.insert(0, str(project_root))
from src.pterodactyl.client import PterodactylClient

load_dotenv()
pterodactyl_url = os.getenv('PTERODACTYL_PANEL_URL')
pterodactyl_key = os.getenv('PTERODACTYL_API_KEY')
pterodactyl = PterodactylClient(pterodactyl_url, pterodactyl_key)
backups = pterodactyl.list_backups('fe08f84f')
print(f"Found {len(backups)} backups:\n")
for b in backups[:10]:
    size_gb = b.get('bytes', 0) / (1024**3)
    uuid = b.get('uuid', 'unknown')[:8]
    created = b.get('created_at', 'unknown')
    print(f"ID: {uuid}... | Size: {size_gb:.3f} GB | Created: {created}")
