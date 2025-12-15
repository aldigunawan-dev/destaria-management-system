#!/usr/bin/env python3
"""
Scheduler Integration Example
Menunjukkan cara mengintegrasikan backup ke scheduler otomatis
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from src.backup.scheduler import BackupScheduler
from src.backup.backup_manager import BackupManager
from src.backup.database import DatabaseManager
from src.pterodactyl.client import PterodactylClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_scheduler():
    """
    Setup and start automated backup scheduler
    """
    print("\n" + "="*60)
    print("BACKUP SCHEDULER SETUP")
    print("="*60)
    
    try:
        # Get credentials
        pterodactyl_url = os.getenv("PTERODACTYL_PANEL_URL")
        pterodactyl_key = os.getenv("PTERODACTYL_API_KEY")
        
        if not pterodactyl_url or not pterodactyl_key:
            print("\n❌ Missing environment variables!")
            print("\nSet environment variables:")
            print("  $env:PTERODACTYL_PANEL_URL = 'https://panel.myserver.com'")
            print("  $env:PTERODACTYL_API_KEY = 'ptlc_...'")
            return False
        
        # Initialize clients
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
        
        # Initialize scheduler
        logger.info("Initializing scheduler...")
        scheduler = BackupScheduler(
            backup_manager=backup_manager,
            database_manager=database,
            max_concurrent=3,
            timezone="UTC"
        )
        
        # Load schedule from config
        config_path = "config/servers.yaml"
        if not os.path.exists(config_path):
            print(f"\n❌ Config file not found: {config_path}")
            print("\nCreate config/servers.yaml with content like:")
            print("""
servers:
  - id: "server-1"
    name: "MainServer"
    backup_schedule: "0 2 * * *"  # Daily at 02:00 AM
""")
            return False
        
        logger.info(f"Loading schedule from {config_path}...")
        scheduled_count = scheduler.schedule_servers(config_path)
        
        print(f"\n✅ Scheduler initialized!")
        print(f"   Scheduled servers: {scheduled_count}")
        
        # Start scheduler
        logger.info("Starting scheduler...")
        scheduler.start()
        
        print("\n📅 Scheduler running!")
        print("   Press Ctrl+C to stop")
        print("\n📋 Scheduled jobs:")
        for job_id, job in scheduler.jobs.items():
            print(f"   - {job.name}")
            print(f"     Trigger: {job.trigger}")
        
        # Keep running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping scheduler...")
            scheduler.stop()
            print("✅ Scheduler stopped")
            return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Exception occurred")
        return False

def show_example_config():
    """Show example servers.yaml config"""
    print("\n" + "="*60)
    print("EXAMPLE: servers.yaml Configuration")
    print("="*60)
    
    config = """
servers:
  - id: "server-1"
    name: "MainServer"
    enabled: true
    backup_schedule: "0 2 * * *"      # Daily at 02:00 AM (UTC)
    
  - id: "server-2"
    name: "SecondaryServer"
    enabled: true
    backup_schedule: "0 3 * * *"      # Daily at 03:00 AM (UTC)
    
  - id: "server-3"
    name: "ArenaServer"
    enabled: false                     # Disabled - no backups
    backup_schedule: "0 2 * * 0"       # Would be Sundays at 02:00 AM

# Cron syntax: minute hour day month weekday
# Examples:
#   "0 2 * * *"       - Every day at 02:00
#   "0 2 * * 0"       - Every Sunday at 02:00
#   "0 2 * * 1-5"     - Every weekday (Mon-Fri) at 02:00
#   "0 2 * * 1-6"     - Every day except Sunday at 02:00
#   "0 */4 * * *"     - Every 4 hours
#   "*/30 * * * *"    - Every 30 minutes
"""
    
    print(config)
    
    print("\n💡 Save this as: config/servers.yaml")

def main():
    """Main menu"""
    while True:
        print("\n" + "="*60)
        print("BACKUP SCHEDULER EXAMPLE")
        print("="*60)
        print("\nOptions:")
        print("1. Setup and start scheduler")
        print("2. Show example config")
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == "1":
            if setup_scheduler():
                print("\n✅ Scheduler setup successful!")
            else:
                print("\n❌ Scheduler setup failed!")
        
        elif choice == "2":
            show_example_config()
        
        elif choice == "3":
            print("\nExiting...")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
