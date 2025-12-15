#!/usr/bin/env python3
"""
API Usage Example
Menunjukkan cara call backup endpoint dari REST API
"""

import requests
import json
from typing import Dict, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"  # Default API URL
TIMEOUT = 30

class BackupAPIClient:
    """Simple client untuk backup API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def health_check(self) -> bool:
        """Check if API is running"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=TIMEOUT
            )
            return response.status_code == 200
        except:
            return False
    
    def trigger_full_backup(self, server_id: str) -> Optional[Dict]:
        """Trigger full backup"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/backup/full/{server_id}",
                json={},
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def trigger_maintenance_backup(self, server_id: str) -> Optional[Dict]:
        """Trigger maintenance mode backup"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/backup/maintenance/{server_id}",
                json={},
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_backup_status(self, backup_id: str) -> Optional[Dict]:
        """Get backup status"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/backup/status/{backup_id}",
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def list_backups(self, server_id: str, limit: int = 10) -> Optional[Dict]:
        """List backups for server"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/backup/history/{server_id}",
                params={"limit": limit},
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_scheduler_status(self) -> Optional[Dict]:
        """Get scheduler status"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/scheduler/status",
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None

def example_usage():
    """Example usage"""
    print("\n" + "="*60)
    print("BACKUP API CLIENT EXAMPLE")
    print("="*60)
    
    # Initialize client
    client = BackupAPIClient()
    
    # Check if API is running
    print("\n1️⃣  Checking API health...")
    if not client.health_check():
        print("❌ API is not running!")
        print("   Start API with: python src/main.py")
        return
    
    print("✅ API is running!")
    
    # Get scheduler status
    print("\n2️⃣  Getting scheduler status...")
    scheduler_status = client.get_scheduler_status()
    if scheduler_status:
        print("✅ Scheduler status:")
        print(json.dumps(scheduler_status, indent=2))
    
    # Trigger full backup
    print("\n3️⃣  Triggering full backup...")
    backup_result = client.trigger_full_backup("server-1")
    if backup_result:
        backup_id = backup_result.get("backup_id")
        print(f"✅ Backup triggered!")
        print(f"   Backup ID: {backup_id}")
        
        # Check backup status
        print("\n4️⃣  Checking backup status...")
        status = client.get_backup_status(backup_id)
        if status:
            print("✅ Backup status:")
            print(json.dumps(status, indent=2))
    
    # List backups
    print("\n5️⃣  Listing recent backups...")
    backups = client.list_backups("server-1", limit=5)
    if backups:
        print("✅ Recent backups:")
        print(json.dumps(backups, indent=2))

def show_curl_examples():
    """Show curl examples"""
    print("\n" + "="*60)
    print("CURL EXAMPLES (for testing API)")
    print("="*60)
    
    examples = """
# 1. Health check
curl http://localhost:8000/health

# 2. Trigger full backup
curl -X POST http://localhost:8000/api/backup/full/server-1

# 3. Trigger maintenance backup
curl -X POST http://localhost:8000/api/backup/maintenance/server-1

# 4. Get backup status
curl http://localhost:8000/api/backup/status/backup-xyz

# 5. List backups
curl http://localhost:8000/api/backup/history/server-1?limit=10

# 6. Get scheduler status
curl http://localhost:8000/api/scheduler/status

# 7. Pause scheduler
curl -X POST http://localhost:8000/api/scheduler/pause

# 8. Resume scheduler
curl -X POST http://localhost:8000/api/scheduler/resume
"""
    
    print(examples)

def main():
    """Main menu"""
    while True:
        print("\n" + "="*60)
        print("API CLIENT EXAMPLE")
        print("="*60)
        print("\nOptions:")
        print("1. Run example usage")
        print("2. Show curl examples")
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == "1":
            example_usage()
        
        elif choice == "2":
            show_curl_examples()
        
        elif choice == "3":
            print("\nExiting...")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
