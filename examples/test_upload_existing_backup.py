#!/usr/bin/env python3
"""
Test Upload Existing Backup to Google Drive

Lists backups on Pterodactyl server and uploads one to Google Drive.
No new backup creation - uses existing backups only.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import tempfile

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pterodactyl.client import PterodactylClient
from src.backup.gdrive_client import GoogleDriveClient

# Load env vars
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_upload_existing_backup(server_identifier="fe08f84f"):
    """Test uploading an existing backup from Pterodactyl to Google Drive"""
    
    print("=" * 70)
    print("TEST: UPLOAD EXISTING BACKUP TO GOOGLE DRIVE")
    print("=" * 70)
    print()
    
    # Initialize clients
    pterodactyl_url = os.getenv("PTERODACTYL_PANEL_URL")
    pterodactyl_key = os.getenv("PTERODACTYL_API_KEY")
    
    if not pterodactyl_url or not pterodactyl_key:
        print("[ERROR] Missing Pterodactyl credentials")
        return False
    
    try:
        # Step 1: Initialize Pterodactyl client
        print("[STEP 1] Connecting to Pterodactyl...")
        pterodactyl = PterodactylClient(pterodactyl_url, pterodactyl_key)
        print("[OK] Connected to Pterodactyl")
        print()
        
        # Step 2: Get server info
        print("[STEP 2] Fetching server information...")
        server = pterodactyl.get_server(server_identifier)
        if not server:
            print(f"[ERROR] Server not found: {server_identifier}")
            return False
        
        server_name = server.get("name", "Unknown")
        print(f"[OK] Server: {server_name}")
        print()
        
        # Step 3: List existing backups
        print("[STEP 3] Listing existing backups...")
        backups = pterodactyl.list_backups(server_identifier)
        
        if not backups:
            print("[WARNING] No backups found on this server")
            print("[INFO] Create a backup first using: python examples/test_full_workflow.py")
            return False
        
        print(f"[OK] Found {len(backups)} backup(s):")
        for i, backup in enumerate(backups, 1):
            backup_id = backup.get("uuid", "Unknown")
            size_gb = backup.get("bytes", 0) / (1024**3)
            created = backup.get("created_at", "Unknown")
            print(f"  {i}. {backup_id[:8]}... ({size_gb:.2f} GB) - {created}")
        print()
        
        # Step 4: Use first backup
        selected_backup = backups[0]
        backup_id = selected_backup.get("uuid")
        backup_size = selected_backup.get("bytes", 0)
        
        print(f"[STEP 4] Selected backup: {backup_id}")
        print(f"  Size: {backup_size / (1024**3):.2f} GB")
        print()
        
        # Step 5: Get download URL
        print("[STEP 5] Getting backup download URL...")
        download_url = pterodactyl.get_backup_download_url(server_identifier, backup_id)
        
        if not download_url:
            print("[ERROR] Failed to get download URL")
            return False
        
        print(f"[OK] Download URL obtained")
        print(f"  URL: {download_url[:100]}...")
        print()
        
        # Step 6: Download backup
        print("[STEP 6] Downloading backup (this may take a while)...")
        import requests
        
        backup_filename = f"{backup_id[:8]}.tar.gz"
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, backup_filename)
        
        try:
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            downloaded = 0
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress_mb = downloaded / (1024**2)
                        print(f"  Downloaded: {progress_mb:.1f} MB", end='\r')
            
            print(f"  Downloaded: {os.path.getsize(temp_file) / (1024**3):.2f} GB          ")
            print("[OK] Backup downloaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to download backup: {e}")
            return False
        
        print()
        
        # Step 7: Initialize Google Drive client
        print("[STEP 7] Initializing Google Drive client...")
        gdrive_token_path = "config/gdrive_token.json"
        gdrive_credentials_path = "config/google-service-account.json"
        gdrive_folder_id = os.getenv("GDRIVE_FOLDER_ID", "1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer")
        
        if Path(gdrive_token_path).exists():
            gdrive = GoogleDriveClient(oauth_token_path=gdrive_token_path, folder_id=gdrive_folder_id)
        else:
            gdrive = GoogleDriveClient(credentials_path=gdrive_credentials_path, folder_id=gdrive_folder_id)
        
        print("[OK] Google Drive client initialized")
        print()
        
        # Step 8: Upload to Google Drive
        print("[STEP 8] Uploading backup to Google Drive...")
        gdrive_file_id, gdrive_url = gdrive.upload_backup(
            server_name, 
            backup_id, 
            temp_file,
            file_size=backup_size
        )
        
        if gdrive_file_id:
            print(f"[OK] Upload successful!")
            print(f"  File ID: {gdrive_file_id}")
            if gdrive_url:
                print(f"  URL: {gdrive_url}")
        else:
            print("[ERROR] Upload failed")
            return False
        
        print()
        
        # Step 9: Cleanup
        print("[STEP 9] Cleaning up...")
        try:
            os.remove(temp_file)
            print(f"[OK] Temporary file deleted: {temp_file}")
        except Exception as e:
            print(f"[WARNING] Failed to delete temp file: {e}")
        
        print()
        
        # Summary
        print("=" * 70)
        print("[SUCCESS] BACKUP UPLOADED TO GOOGLE DRIVE!")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  Server: {server_name}")
        print(f"  Backup ID: {backup_id}")
        print(f"  Size: {backup_size / (1024**3):.2f} GB")
        print(f"  Google Drive File ID: {gdrive_file_id}")
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_upload_existing_backup()
    sys.exit(0 if success else 1)
