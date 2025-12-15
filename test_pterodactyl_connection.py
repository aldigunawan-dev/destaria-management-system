#!/usr/bin/env python3
"""
Quick test untuk verify Pterodactyl API connection
"""

import os
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_connection():
    """Test Pterodactyl API connection"""
    
    print("\n" + "="*60)
    print("PTERODACTYL API CONNECTION TEST")
    print("="*60)
    
    # Check environment variables
    print("\n1️⃣  Checking environment variables...")
    
    pterodactyl_url = os.getenv("PTERODACTYL_PANEL_URL")
    pterodactyl_key = os.getenv("PTERODACTYL_API_KEY")
    
    if not pterodactyl_url:
        print("❌ PTERODACTYL_PANEL_URL not set!")
        print("\n   Set it with:")
        print("   $env:PTERODACTYL_PANEL_URL = 'https://panel.example.com'")
        return False
    
    if not pterodactyl_key:
        print("❌ PTERODACTYL_API_KEY not set!")
        print("\n   Set it with:")
        print("   $env:PTERODACTYL_API_KEY = 'ptlc_...'")
        return False
    
    print(f"✅ Panel URL: {pterodactyl_url}")
    print(f"✅ API Key: {pterodactyl_key[:10]}... (hidden for security)")
    
    # Test connection
    print("\n2️⃣  Testing API connection...")
    
    try:
        from src.pterodactyl.client import PterodactylClient
        
        client = PterodactylClient(
            base_url=pterodactyl_url,
            api_key=pterodactyl_key
        )
        
        print("✅ PterodactylClient initialized successfully!")
        
        # Get servers list
        print("\n3️⃣  Fetching servers list...")
        servers = client.get_servers()
        
        if servers:
            print(f"✅ Found {len(servers)} servers!")
            print("\n   Servers:")
            for server in servers:
                server_id = server.get('id') or server.get('attributes', {}).get('id')
                server_name = server.get('name') or server.get('attributes', {}).get('name')
                status = server.get('status') or server.get('attributes', {}).get('status', 'unknown')
                
                if server_id:
                    print(f"   - {server_name or 'Unknown'} (ID: {server_id}, Status: {status})")
            
            return True
        else:
            print("⚠️  No servers found (or empty response)")
            print("   This might be OK if API is working but no servers exist")
            return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Full error traceback:")
        
        print("\n💡 Troubleshooting:")
        print("   1. Verify Panel URL is correct (https:// not http://)")
        print("   2. Verify API Key is correct (should start with 'ptlc_')")
        print("   3. Check if API key has 'Servers Read' permission")
        print("   4. Make sure Panel is accessible from this machine")
        
        return False

def test_server_status():
    """Test getting specific server status"""
    
    print("\n" + "="*60)
    print("SERVER STATUS TEST")
    print("="*60)
    
    server_id = input("\nEnter server ID to test (from list above): ").strip()
    
    if not server_id:
        print("Skipped")
        return
    
    try:
        pterodactyl_url = os.getenv("PTERODACTYL_PANEL_URL")
        pterodactyl_key = os.getenv("PTERODACTYL_API_KEY")
        
        from src.pterodactyl.client import PterodactylClient
        
        client = PterodactylClient(
            base_url=pterodactyl_url,
            api_key=pterodactyl_key
        )
        
        print(f"\n📊 Fetching status for server: {server_id}...")
        
        server = client.get_server(server_id)
        
        if server:
            print("✅ Server details:")
            print(f"   Name: {server.get('name', 'Unknown')}")
            print(f"   Status: {server.get('status', 'Unknown')}")
            print(f"   CPU Limit: {server.get('cpu', '?')}%")
            print(f"   Memory Limit: {server.get('memory', '?')} MB")
            
            # Try to get server status (online/offline)
            print("\n📡 Fetching server resource status...")
            status = client.get_server_status(server_id)
            
            if status:
                print("✅ Server is responsive!")
                print(f"   Current State: {status.get('current_state', 'unknown')}")
                print(f"   CPU: {status.get('resources', {}).get('cpu_absolute', '?')}%")
                print(f"   Memory: {status.get('resources', {}).get('memory', '?')} MB")
            else:
                print("⚠️  Server status not available (might be offline)")
        else:
            print("❌ Server not found!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Full error:")

def test_send_command():
    """Test sending command to server"""
    
    print("\n" + "="*60)
    print("SEND COMMAND TEST")
    print("="*60)
    
    server_id = input("\nEnter server ID: ").strip()
    if not server_id:
        print("Skipped")
        return
    
    command = input("Enter command to send (e.g., 'say Hello!'): ").strip()
    if not command:
        print("Skipped")
        return
    
    try:
        pterodactyl_url = os.getenv("PTERODACTYL_PANEL_URL")
        pterodactyl_key = os.getenv("PTERODACTYL_API_KEY")
        
        from src.pterodactyl.client import PterodactylClient
        
        client = PterodactylClient(
            base_url=pterodactyl_url,
            api_key=pterodactyl_key
        )
        
        print(f"\n📢 Sending command to {server_id}: {command}")
        
        success = client.send_command(server_id, command)
        
        if success:
            print("✅ Command sent successfully!")
        else:
            print("❌ Failed to send command")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main test runner"""
    
    # Test connection
    if not test_connection():
        print("\n❌ Connection test failed!")
        print("Please fix environment variables and try again")
        return False
    
    print("\n✅ CONNECTION TEST PASSED!")
    
    # Additional tests
    while True:
        print("\n" + "="*60)
        print("ADDITIONAL TESTS")
        print("="*60)
        print("\n1. Test server status")
        print("2. Test send command (say)")
        print("3. Exit")
        
        choice = input("\nSelect (1-3): ").strip()
        
        if choice == "1":
            test_server_status()
        elif choice == "2":
            test_send_command()
        elif choice == "3":
            break
        else:
            print("Invalid choice")
    
    print("\n" + "="*60)
    print("TEST COMPLETE!")
    print("="*60)
    print("\n✅ Your Pterodactyl API is working!")
    print("\nNext steps:")
    print("1. Run: python examples/test_backup_simple.py")
    print("2. Setup scheduler: python examples/setup_scheduler.py")
    print("3. Start API: python src/main.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
