#!/usr/bin/env python3
"""Debug Google Drive Folder Creation"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backup.gdrive_client import GoogleDriveClient
import logging

logging.basicConfig(level=logging.DEBUG)

credentials_path = "config/google-service-account.json"
folder_id = "1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer"

gdrive = GoogleDriveClient(credentials_path, folder_id=folder_id)

# Try to create a test folder
print("Attempting to create test folder...")

file_metadata = {
    'name': 'test_folder_debug',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [folder_id]
}

try:
    request = gdrive.drive_service.files().create(
        body=file_metadata,
        fields='id',
        supportsAllDrives=True
    )
    
    print(f"Request created: {request}")
    response = request.execute()
    print(f"Response: {response}")
    print(f"Response type: {type(response)}")
    print(f"Response keys: {response.keys() if response else 'None'}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
