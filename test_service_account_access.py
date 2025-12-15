#!/usr/bin/env python3
"""
Test Service Account Access to Shared Folder
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.backup.gdrive_client import GoogleDriveClient
import logging

logging.basicConfig(level=logging.DEBUG)

credentials_path = "config/google-service-account.json"
folder_id = "1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer"

print("=" * 70)
print("SERVICE ACCOUNT ACCESS TEST")
print("=" * 70)
print()

try:
    # Initialize with folder ID
    print(f"[INFO] Service Account Email:")
    print(f"       destaria-devops@minecraft-devops-481312.iam.gserviceaccount.com")
    print()
    
    print(f"[INFO] Folder ID:")
    print(f"       {folder_id}")
    print()
    
    print("[TEST 1] Initialize GoogleDriveClient...")
    client = GoogleDriveClient(credentials_path=credentials_path, folder_id=folder_id)
    print("[OK] Client initialized")
    print()
    
    print("[TEST 2] Get folder info (READ)...")
    request = client.drive_service.files().get(
        fileId=folder_id,
        fields='id, name, mimeType, permissions',
        supportsAllDrives=True
    )
    result = request.execute()
    print("[OK] Can READ folder!")
    print(f"     Folder Name: {result.get('name')}")
    print(f"     MIME Type: {result.get('mimeType')}")
    print(f"     Permissions: {result.get('permissions', [])}")
    print()
    
    print("[TEST 3] List files in folder (READ)...")
    query = f"'{folder_id}' in parents and trashed=false"
    request = client.drive_service.files().list(
        q=query,
        spaces='drive',
        pageSize=10,
        fields='files(id, name)',
        supportsAllDrives=True
    )
    result = request.execute()
    files = result.get('files', [])
    print(f"[OK] Can LIST files! Found {len(files)} items")
    for f in files[:5]:
        print(f"     - {f['name']}")
    print()
    
    print("[TEST 4] Create test folder (WRITE)...")
    file_metadata = {
        'name': 'test_service_account_write',
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [folder_id]
    }
    request = client.drive_service.files().create(
        body=file_metadata,
        fields='id',
        supportsAllDrives=True
    )
    result = request.execute()
    test_folder_id = result.get('id')
    
    if test_folder_id:
        print(f"[OK] Can CREATE folders! Test folder ID: {test_folder_id}")
        print()
        
        # Clean up
        print("[TEST 5] Delete test folder (DELETE)...")
        request = client.drive_service.files().delete(
            fileId=test_folder_id,
            supportsAllDrives=True
        )
        request.execute()
        print("[OK] Can DELETE files!")
    else:
        print("[ERROR] Failed to create test folder")
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("[OK] Service Account CAN access shared folder!")
    print("     READ: Yes")
    print("     WRITE: Yes")
    print("     DELETE: Yes")
    print()
    print("Next step: Try test_gdrive_upload.py or update main.py to use service account")
    
except Exception as e:
    print()
    print("[ERROR] Service Account CANNOT access folder")
    print(f"Error: {e}")
    print()
    print("Possible causes:")
    print("1. Folder not shared with service account email")
    print("2. Service account doesn't have Editor role")
    print("3. Folder ID is incorrect")
    print()
    print("Solution:")
    print("1. Open folder in Google Drive")
    print("2. Share with: destaria-devops@minecraft-devops-481312.iam.gserviceaccount.com")
    print("3. Give Editor role")
    print("4. Wait a few minutes for permissions to propagate")
    print("5. Run this test again")
