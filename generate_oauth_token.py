#!/usr/bin/env python3
"""
Generate OAuth Token for Google Drive (Workspace Account)
Generates token.json that can be used for automated uploads
"""

import os
import sys
from pathlib import Path

# Check dependencies
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("[ERROR] google-auth-oauthlib not installed")
    print("Install with: pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = ['https://www.googleapis.com/auth/drive']

def generate_oauth_token():
    """
    Generate OAuth token through browser login
    """
    
    print("=" * 70)
    print("GOOGLE DRIVE OAUTH TOKEN GENERATOR")
    print("=" * 70)
    print()
    print("This will generate a token.json file for your Workspace account.")
    print("You'll need to log in with your Workspace Google account.")
    print()
    
    # Check for OAuth credentials
    oauth_config = "config/oauth_credentials.json"
    
    if not Path(oauth_config).exists():
        print("[ERROR] OAuth credentials file not found!")
        print()
        print("Steps to create OAuth credentials:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Click 'Create Credentials' → 'OAuth 2.0 Client ID'")
        print("3. Choose 'Desktop application'")
        print("4. Download the JSON file")
        print("5. Save as: config/oauth_credentials.json")
        print()
        print("Note: Make sure Google Drive API is enabled in your Google Cloud project")
        return False
    
    try:
        print("[INFO] Starting OAuth flow...")
        print()
        
        # Create the OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            oauth_config, 
            scopes=SCOPES
        )
        
        print("[INFO] Opening browser for authentication...")
        print("      If browser doesn't open automatically, visit the URL shown")
        print()
        
        # Run the local server
        creds = flow.run_local_server(port=0)
        
        # Save credentials
        token_path = "config/gdrive_token.json"
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())
        
        print()
        print("=" * 70)
        print("[OK] OAuth token generated successfully!")
        print("=" * 70)
        print()
        print(f"Token saved to: {token_path}")
        print()
        print("Next steps:")
        print("1. Update GoogleDriveClient initialization:")
        print("   gdrive = GoogleDriveClient(")
        print("       oauth_token_path='config/gdrive_token.json',")
        print("       folder_id='1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer'  # Your folder ID")
        print("   )")
        print()
        print("2. Or set environment variables:")
        print("   export GDRIVE_TOKEN_PATH='config/gdrive_token.json'")
        print("   export GDRIVE_FOLDER_ID='1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer'")
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to generate token: {e}")
        print()
        print("Troubleshooting:")
        print("- Make sure oauth_credentials.json is valid")
        print("- Make sure you're using the correct Google account")
        print("- Check that Google Drive API is enabled")
        print()
        return False


if __name__ == "__main__":
    success = generate_oauth_token()
    sys.exit(0 if success else 1)
