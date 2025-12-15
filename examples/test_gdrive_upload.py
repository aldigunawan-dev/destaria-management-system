#!/usr/bin/env python3
"""
Test Google Drive Upload
Tests uploading a backup file to Google Drive
"""

import os
import sys
import logging
import argparse
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backup.gdrive_client import GoogleDriveClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_gdrive_upload(keep_backup=False):
    """Test Google Drive upload with Service Account or OAuth
    
    Args:
        keep_backup: If True, keep uploaded backup in Google Drive (for inspection)
                    If False, delete backup after test (default)
    """
    
    print("=" * 60)
    print("GOOGLE DRIVE UPLOAD TEST")
    print("=" * 60)
    print()
    
    # Try OAuth first (has storage quota), then Service Account
    credentials_path = "config/google-service-account.json"
    token_path = "config/gdrive_token.json"
    folder_id = os.getenv("GDRIVE_FOLDER_ID", "1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer")
    
    print(f"Folder ID: {folder_id}")
    print()
    
    if Path(token_path).exists():
        print("[INFO] Using OAuth Token (Workspace account)...")
        use_oauth = True
    elif Path(credentials_path).exists():
        print("[INFO] Using Service Account...")
        use_oauth = False
    else:
        print(f"[ERROR] No credentials found!")
        print(f"  - {token_path}")
        print(f"  - {credentials_path}")
        return False
    
    try:
        # Initialize Google Drive client
        print("[INFO] Initializing Google Drive client...")
        if use_oauth:
            gdrive = GoogleDriveClient(oauth_token_path=token_path, folder_id=folder_id)
        else:
            gdrive = GoogleDriveClient(credentials_path=credentials_path, folder_id=folder_id)
        print("[OK] Google Drive client initialized")
        print()
        
        # List existing backups in Google Drive
        print("[INFO] Listing existing backups in Google Drive...")
        backups = gdrive.list_backups()
        print(f"[INFO] Found {len(backups)} existing backups:")
        for backup in backups[:5]:  # Show first 5
            size_mb = backup.get('size_bytes', 0) / (1024 * 1024)
            print(f"  - {backup.get('name')} ({size_mb:.2f} MB)")
            print(f"    Created: {backup.get('created_at')}")
        if len(backups) > 5:
            print(f"  ... and {len(backups) - 5} more")
        print()
        
        # Create mock backup file for testing
        print("[INFO] Creating mock backup file...")
        mock_backup_dir = Path("data/mock_backups")
        mock_backup_dir.mkdir(parents=True, exist_ok=True)
        
        test_file_path = mock_backup_dir / "backup_fe08f84f_test_upload.tar.gz"
        
        # Create a small test file
        with open(test_file_path, 'wb') as f:
            f.write(b"Mock backup data - this is a test file\n" * 1000)
        
        file_size = test_file_path.stat().st_size
        print(f"[OK] Test file created: {test_file_path}")
        print(f"     Size: {file_size} bytes ({file_size / (1024 * 1024):.2f} MB)")
        print()
        
        # Upload to Google Drive
        print("[INFO] Uploading backup to Google Drive...")
        print("  Server: test management system")
        print("  Backup ID: backup_fe08f84f_test_upload")
        print()
        
        gdrive_file_id, gdrive_url = gdrive.upload_backup(
            server_name="test management system",
            backup_id="backup_fe08f84f_test_upload",
            file_path=str(test_file_path),
            file_size=file_size
        )
        
        if gdrive_file_id:
            print(f"[OK] Upload succeeded!")
            print(f"  File ID: {gdrive_file_id}")
            print(f"  URL: {gdrive_url}")
            print()
            
            # Give Drive API a moment to finalize
            time.sleep(2)
            
            # List backups again to verify
            print("[INFO] Verifying uploaded file...")
            updated_backups = gdrive.list_backups("test management system")
            
            found = False
            for backup in updated_backups:
                if gdrive_file_id in backup.get('id'):
                    found = True
                    print(f"[OK] File verified!")
                    print(f"  Name: {backup.get('name')}")
                    print(f"  Size: {backup.get('size_bytes')} bytes")
                    print(f"  Created: {backup.get('created_at')}")
                    break
            
            if not found:
                print("[WARNING] Could not verify uploaded file in listing")
            
            print()
            
            # Clean up local test file
            print("[INFO] Cleaning up local files...")
            test_file_path.unlink()
            
            # Delete from Google Drive (unless --keep is specified)
            if keep_backup:
                print("[INFO] Keeping backup in Google Drive (--keep flag set)")
                print(f"  File ID: {gdrive_file_id}")
                print(f"  URL: {gdrive_url}")
            else:
                print("[INFO] Deleting test file from Google Drive...")
                if gdrive.delete_backup(gdrive_file_id):
                    print("[OK] Test file deleted from Google Drive")
                else:
                    print("[WARNING] Failed to delete test file from Google Drive")
            
            return True
        else:
            print("[ERROR] Upload failed")
            return False
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Test Google Drive backup upload functionality"
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep uploaded backup in Google Drive for inspection (default: delete after test)"
    )
    args = parser.parse_args()
    
    success = test_gdrive_upload(keep_backup=args.keep)
    print()
    print("=" * 60)
    if success:
        print("Result: OK PASSED")
    else:
        print("Result: ERROR FAILED")
    print("=" * 60)
    sys.exit(0 if success else 1)
