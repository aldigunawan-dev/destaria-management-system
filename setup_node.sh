#!/bin/bash
# Setup script untuk jalankan Destaria Backup System di Linux Node
# Usage: bash setup_node.sh

set -e

echo "=================================================="
echo "Destaria Backup System - Node Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${YELLOW}[STEP 1]${NC} Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python3 not found. Please install Python3 first."
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}[OK]${NC} $PYTHON_VERSION"
echo ""

# Step 2: Check pip
echo -e "${YELLOW}[STEP 2]${NC} Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} pip3 not found. Please install pip3 first."
    exit 1
fi
echo -e "${GREEN}[OK]${NC} pip3 found"
echo ""

# Step 3: Get project path
echo -e "${YELLOW}[STEP 3]${NC} Setting up project path..."
PROJECT_PATH="${1:-.}"
if [ ! -f "$PROJECT_PATH/requirements.txt" ]; then
    echo -e "${RED}[ERROR]${NC} requirements.txt not found in $PROJECT_PATH"
    echo "Usage: bash setup_node.sh /path/to/destaria-management-project"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Project path: $PROJECT_PATH"
cd "$PROJECT_PATH"
echo ""

# Step 4: Install dependencies
echo -e "${YELLOW}[STEP 4]${NC} Installing Python dependencies..."
pip3 install -q -r requirements.txt
echo -e "${GREEN}[OK]${NC} Dependencies installed"
echo ""

# Step 5: Check .env file
echo -e "${YELLOW}[STEP 5]${NC} Checking .env configuration..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[WARNING]${NC} .env file not found"
    echo "Creating .env template..."
    cat > .env << 'EOF'
# Pterodactyl Configuration
PTERODACTYL_PANEL_URL=https://panel.destaria.com
PTERODACTYL_API_KEY=ptlc_YOUR_KEY_HERE

# Google Drive Configuration
GDRIVE_FOLDER_ID=1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer

# Server Configuration
MINECRAFT_SERVER_ID=fe08f84f
EOF
    echo -e "${YELLOW}[ACTION REQUIRED]${NC} Please edit .env file with your credentials:"
    echo "  nano .env"
    echo ""
    exit 1
else
    echo -e "${GREEN}[OK]${NC} .env file exists"
fi
echo ""

# Step 6: Check config files
echo -e "${YELLOW}[STEP 6]${NC} Checking configuration files..."
CONFIG_FILES=("config/notifications.yaml" "config/plugins.yaml" "config/servers.yaml" "config/gdrive_token.json")
for file in "${CONFIG_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}[WARNING]${NC} Missing: $file"
    else
        echo -e "${GREEN}[OK]${NC} Found: $file"
    fi
done
echo ""

# Step 7: Check database
echo -e "${YELLOW}[STEP 7]${NC} Checking database..."
if [ ! -d "data" ]; then
    mkdir -p data
    echo -e "${GREEN}[OK]${NC} Created data directory"
else
    echo -e "${GREEN}[OK]${NC} Data directory exists"
fi
echo ""

# Step 8: Test Pterodactyl connection
echo -e "${YELLOW}[STEP 8]${NC} Testing Pterodactyl API connection..."
python3 << 'PYEOF'
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path.cwd()))

try:
    from src.pterodactyl.client import PterodactylClient
    
    pterodactyl_url = os.getenv('PTERODACTYL_PANEL_URL')
    pterodactyl_key = os.getenv('PTERODACTYL_API_KEY')
    
    if not pterodactyl_url or not pterodactyl_key:
        print("[ERROR] Missing Pterodactyl credentials in .env")
        sys.exit(1)
    
    pterodactyl = PterodactylClient(pterodactyl_url, pterodactyl_key)
    servers = pterodactyl.get_servers()
    
    if servers:
        print(f"[OK] Connected to Pterodactyl - Found {len(servers)} server(s)")
        for server in servers[:3]:
            print(f"    - {server.get('name')} ({server.get('identifier')})")
    else:
        print("[WARNING] Connected but no servers found")
        
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Pterodactyl connection test failed"
    exit 1
fi
echo ""

# Step 9: Run test script
echo -e "${YELLOW}[STEP 9]${NC} Running backup workflow test..."
echo "=================================================="
echo ""
python3 examples/test_backup_workflow_simple.py
TEST_RESULT=$?

echo ""
echo "=================================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}[SUCCESS]${NC} Setup and test completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Review test results above"
    echo "  2. Check Google Drive folder for backups (if upload enabled)"
    echo "  3. Run additional tests if needed"
    echo ""
    echo "To run tests again:"
    echo "  python3 examples/test_backup_workflow_simple.py"
    echo "  python3 examples/test_upload_existing_backup.py"
else
    echo -e "${RED}[FAILED]${NC} Test failed with exit code $TEST_RESULT"
    exit $TEST_RESULT
fi
