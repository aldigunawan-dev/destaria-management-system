#!/usr/bin/env python3
"""
Simple Backup Testing Example
"""

import os
import sys
import logging
import yaml
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backup.backup_manager import BackupManager
from src.backup.database import DatabaseManager
from src.pterodactyl.client import PterodactylClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_simple_full_backup():
    """Test 1: Simple full backup (server running)"""
    print("\n" + "="*60)
    print("TEST 1: Simple Full Backup (Server Running)")
    print("="*60)
    
    try:
        pterodactyl_url = os.getenv("PTERODACTYL_PANEL_URL")
        pterodactyl_key = os.getenv("PTERODACTYL_API_KEY")
        
        if not pterodactyl_url or not pterodactyl_key:
            print("[ERROR] Missing environment variables!")
            print("   Set:")
            print("   - PTERODACTYL_PANEL_URL")
            print("   - PTERODACTYL_API_KEY")
            return False
        
        if pterodactyl_key.startswith("ptla_"):
            print("[ERROR] WRONG API KEY TYPE!")
            print("   Current key: Application API (ptla_...)")
            print("   Required key: Client API (ptlc_...)")
            print("\n   How to get Client API key:")
            print("   1. Log in to Pterodactyl Panel as the server owner")
            print("   2. Click your account name -> API Credentials")
            print("   3. Create new API Token (NOT Application Token)")
            print("   4. Set env var: $env:PTERODACTYL_API_KEY = 'ptlc_...'")
            return False
        
        config_path = project_root / "config" / "servers.yaml"
        if not config_path.exists():
            print(f"[ERROR] Config file not found: {config_path}")
            return False
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config or 'servers' not in config or len(config['servers']) == 0:
            print("[ERROR] No servers configured in config/servers.yaml")
            return False
        
        servers_dict = config['servers']
        first_server_name = list(servers_dict.keys())[0]
        server_config = servers_dict[first_server_name]
        server_id = str(server_config.get('id'))
        server_name = server_config.get('name', first_server_name)
        
        print(f"   Using server: {server_name} (ID: {server_id})")
        
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
        
        logger.info("Starting full backup...")
        backup_id = backup_manager.full_backup(
            server_id=server_id,
            server_name=server_name,
            retention_days=30
        )
        
        if backup_id:
            print(f"\n[OK] Backup succeeded!")
            print(f"   Backup ID: {backup_id}")
            
            status = backup_manager.get_backup_status(backup_id)
            print(f"   Status: {status}")
            return True
        else:
            print(f"\n[ERROR] Backup failed!")
            return False
    
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        logger.exception("Exception occurred")
        return False

def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("BACKUP MANAGER TEST SUITE")
    print("="*60)
    print("\nRunning: Simple Full Backup (server running)")
    print("\nNote: Set environment variables first:")
    print("  $env:PTERODACTYL_PANEL_URL = 'https://panel.destaria.com'")
    print("  $env:PTERODACTYL_API_KEY = 'ptlc_...'")
    
    success = test_simple_full_backup()
    print("\n" + "="*60)
    print(f"Result: {'OK PASSED' if success else 'ERROR FAILED'}")
    print("="*60)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
