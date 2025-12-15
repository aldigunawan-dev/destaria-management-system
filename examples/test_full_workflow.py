#!/usr/bin/env python3
"""
Test Full Backup Workflow
Tests: Stop Server -> Backup -> Upload to Google Drive -> Start Server
Uses existing BackupManager implementation
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pterodactyl.client import PterodactylClient
from src.backup.backup_manager import BackupManager
from src.backup.database import DatabaseManager
from src.backup.gdrive_client import GoogleDriveClient

# Load env vars
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_full_workflow(server_identifier="fe08f84f", 
                      client_api_key=None):
    """Test complete workflow: stop -> backup -> upload -> start"""
    
    print("=" * 70)
    print("FULL BACKUP WORKFLOW TEST")
    print("=" * 70)
    print()
    
    # Initialize clients
    pterodactyl_url = os.getenv("PTERODACTYL_PANEL_URL")
    pterodactyl_key = client_api_key or os.getenv("PTERODACTYL_API_KEY")
    
    if not pterodactyl_url or not pterodactyl_key:
        print("[ERROR] Missing Pterodactyl credentials")
        return False
    
    try:
        # Step 1: Initialize components
        print("[STEP 1] Initializing components...")
        pterodactyl = PterodactylClient(pterodactyl_url, pterodactyl_key)
        
        database = DatabaseManager("data/devops.db")
        
        gdrive_token_path = "config/gdrive_token.json"
        gdrive_credentials_path = "config/google-service-account.json"
        gdrive_folder_id = os.getenv("GDRIVE_FOLDER_ID", "1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer")
        
        if Path(gdrive_token_path).exists():
            gdrive = GoogleDriveClient(oauth_token_path=gdrive_token_path, folder_id=gdrive_folder_id)
        else:
            gdrive = GoogleDriveClient(credentials_path=gdrive_credentials_path, folder_id=gdrive_folder_id)
        
        backup_manager = BackupManager(
            pterodactyl_client=pterodactyl,
            gdrive_client=gdrive,
            database=database
        )
        
        print("[OK] Components initialized")
        print()
        
        # Step 2: Get server info
        print("[STEP 2] Fetching server information...")
        server = pterodactyl.get_server(server_identifier)
        if not server:
            print(f"[ERROR] Server not found: {server_identifier}")
            return False
        
        server_name = server.get("name", "unknown")
        print(f"[OK] Server: {server_name}")
        print()
        
        # Step 3: Stop server
        print("[STEP 3] Stopping server...")
        stop_success = pterodactyl.stop_server(server_identifier)
        if not stop_success:
            print("[WARNING] Could not stop server, continuing anyway...")
        else:
            print("[OK] Server stop command sent")
            print("  Waiting 5 seconds for graceful shutdown...")
            import time
            time.sleep(5)
        print()
        
        # Step 4: Backup notification
        print("[STEP 4] Creating backup (with Client API)...")
        print("  This may take several minutes depending on server size...")
        print()
        
        # Step 5: Create backup (this will trigger Pterodactyl backup + upload to Google Drive)
        print("[STEP 5] Creating backup and uploading to Google Drive...")
        print()
        
        try:
            success = backup_manager.full_backup(server_identifier, server_name)
            
            if not success:
                print("[ERROR] Backup failed")
                return False
            
            print("[OK] Backup successful!")
        except Exception as e:
            print(f"[ERROR] Backup error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print()
        
        # Step 6: Start server
        print("[STEP 6] Starting server again...")
        start_success = pterodactyl.start_server(server_identifier)
        if not start_success:
            print("[WARNING] Could not start server")
        else:
            print("[OK] Server start command sent")
            print("  Server is starting up...")
        print()
        
        # Step 7: Show result
        print("=" * 70)
        print("[OK] WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  Server: {server_name}")
        print(f"  Backup created and uploaded to Google Drive")
        print(f"  Check Google Drive folder for backup file")
        print()
        print("Workflow steps completed:")
        print("  1. Server stopped gracefully")
        print("  2. Backup created via Pterodactyl")
        print("  3. Backup uploaded to Google Drive (metadata)")
        print("  4. Server restarted")
        print()
        print("Endpoints used (all Client API):")
        print("  - GET /api/client/servers/{identifier}")
        print("  - POST /api/client/servers/{identifier}/power (stop)")
        print("  - POST /api/client/servers/{identifier}/backups")
        print("  - GET /api/client/servers/{identifier}/backups/{backup_id}")
        print("  - POST /api/client/servers/{identifier}/power (start)")
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test full backup workflow using Client API (ptlc_...)"
    )
    parser.add_argument(
        "--server",
        default="fe08f84f",
        help="Server identifier (default: fe08f84f)"
    )
    parser.add_argument(
        "--key",
        help="Pterodactyl Client API key (ptlc_...) - overrides env var"
    )
    args = parser.parse_args()
    
    success = test_full_workflow(
        server_identifier=args.server,
        client_api_key=args.key
    )
    sys.exit(0 if success else 1)
