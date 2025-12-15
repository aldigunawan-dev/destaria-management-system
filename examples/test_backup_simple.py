#!/usr/bin/env python3
"""
Simple Backup Testing Example
Menunjukkan cara menggunakan BackupManager untuk testing
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backup.backup_manager import BackupManager
from src.backup.database import DatabaseManager
from src.pterodactyl.client import PterodactylClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_simple_full_backup():
    """
    Test 1: Simple full backup (server running)
    
    Requirements:
    - Pterodactyl API key
    - Database setup
    """
    print("\n" + "="*60)
    print("TEST 1: Simple Full Backup (Server Running)")
    print("="*60)
    
    try:
        # Get credentials dari environment
        pterodactyl_url = os.getenv("PTERODACTYL_PANEL_URL")
        pterodactyl_key = os.getenv("PTERODACTYL_API_KEY")
        
        if not pterodactyl_url or not pterodactyl_key:
            print("❌ Missing environment variables!")
            print("   Set:")
            print("   - PTERODACTYL_PANEL_URL")
            print("   - PTERODACTYL_API_KEY")
            return False
        
        # Initialize clients
        logger.info("Initializing clients...")
        database = DatabaseManager(db_path="data/devops.db")
        pterodactyl_client = PterodactylClient(
            base_url=pterodactyl_url,
            api_key=pterodactyl_key
        )
        
        # Create BackupManager
        backup_manager = BackupManager(
            pterodactyl_client=pterodactyl_client,
            gdrive_client=None,  # Skip Google Drive for this test
            database=database
        )
        
        # Execute full backup
        logger.info("Starting full backup...")
        backup_id = backup_manager.full_backup(
            server_id="server-1",
            server_name="TestServer",
            retention_days=30
        )
        
        if backup_id:
            print(f"\n✅ Backup succeeded!")
            print(f"   Backup ID: {backup_id}")
            
            # Get status
            status = backup_manager.get_backup_status(backup_id)
            print(f"   Status: {status}")
            return True
        else:
            print(f"\n❌ Backup failed!")
            return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Exception occurred")
        return False

def test_maintenance_backup():
    """
    Test 2: Incremental backup with maintenance mode
    
    WARNING: Ini akan STOP & START server Anda!
    Hanya jalankan saat tidak ada players online!
    
    Requirements:
    - Server harus accessible
    - No players online
    """
    print("\n" + "="*60)
    print("TEST 2: Incremental Backup with Maintenance Mode")
    print("="*60)
    print("\n⚠️  WARNING: This test will STOP and START your server!")
    print("   Make sure NO PLAYERS are online!")
    
    confirm = input("\nType 'YES' to continue: ")
    if confirm.upper() != "YES":
        print("❌ Cancelled by user")
        return False
    
    try:
        # Get credentials
        pterodactyl_url = os.getenv("PTERODACTYL_PANEL_URL")
        pterodactyl_key = os.getenv("PTERODACTYL_API_KEY")
        
        if not pterodactyl_url or not pterodactyl_key:
            print("❌ Missing environment variables!")
            return False
        
        # Initialize
        logger.info("Initializing clients...")
        database = DatabaseManager(db_path="data/devops.db")
        pterodactyl_client = PterodactylClient(
            base_url=pterodactyl_url,
            api_key=pterodactyl_key
        )
        
        backup_manager = BackupManager(
            pterodactyl_client=pterodactyl_client,
            gdrive_client=None,
            database=database
        )
        
        # Execute maintenance backup
        print("\n🔄 Starting incremental backup with maintenance mode...")
        print("   Timeline:")
        print("   1. Send 5-minute warning countdown")
        print("   2. Stop server (graceful shutdown)")
        print("   3. Create backup (server offline)")
        print("   4. Start server")
        print("   5. Send online notification")
        
        backup_id = backup_manager.incremental_backup_with_maintenance(
            server_id="server-1",
            server_name="TestServer",
            retention_days=7
        )
        
        if backup_id:
            print(f"\n✅ Maintenance backup succeeded!")
            print(f"   Backup ID: {backup_id}")
            
            status = backup_manager.get_backup_status(backup_id)
            print(f"   Status: {status}")
            return True
        else:
            print(f"\n❌ Maintenance backup failed!")
            return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Exception occurred")
        return False

def show_menu():
    """Show test menu"""
    print("\n" + "="*60)
    print("BACKUP MANAGER TEST SUITE")
    print("="*60)
    print("\nAvailable tests:")
    print("1. Simple Full Backup (server running)")
    print("2. Incremental Backup with Maintenance Mode")
    print("3. Exit")
    print("\nNote: Set environment variables first:")
    print("  $env:PTERODACTYL_PANEL_URL = 'https://panel.myserver.com'")
    print("  $env:PTERODACTYL_API_KEY = 'ptlc_...'")

def main():
    """Main test runner"""
    while True:
        show_menu()
        choice = input("\nSelect test (1-3): ").strip()
        
        if choice == "1":
            success = test_simple_full_backup()
            print("\n" + "="*60)
            print(f"Result: {'✅ PASSED' if success else '❌ FAILED'}")
            print("="*60)
        
        elif choice == "2":
            success = test_maintenance_backup()
            print("\n" + "="*60)
            print(f"Result: {'✅ PASSED' if success else '❌ FAILED'}")
            print("="*60)
        
        elif choice == "3":
            print("\nExiting...")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
