# Setup Destaria Backup System di Linux Node

## Prerequisites
- Python 3.8+
- pip3
- SSH access ke node
- Pterodactyl panel credentials (Client API key)

## Option 1: Automatic Setup (Recommended)

### Step 1: Copy project ke node
```bash
# Di local machine
scp -r . user@node:/path/to/destaria-management-project

# Atau jika sudah ada git:
ssh user@node
cd /path/to/destaria-management-project
git pull
```

### Step 2: Run setup script
```bash
ssh user@node
cd /path/to/destaria-management-project
bash setup_node.sh
```

Script akan:
- ✓ Check Python 3
- ✓ Install dependencies dari requirements.txt
- ✓ Setup .env file
- ✓ Test Pterodactyl connection
- ✓ Run backup workflow test

## Option 2: Manual Setup

### Step 1: Install dependencies
```bash
ssh user@node
cd /path/to/destaria-management-project

# Install Python packages
pip3 install -r requirements.txt

# Packages yang diinstall:
# - requests (HTTP client)
# - google-auth, google-auth-oauthlib (Google Drive API)
# - python-dotenv (Environment variables)
# - apscheduler (Scheduler - untuk nanti)
```

### Step 2: Setup environment variables
```bash
# Create .env file dengan credentials
nano .env
```

Content .env:
```
PTERODACTYL_PANEL_URL=https://panel.destaria.com
PTERODACTYL_API_KEY=ptlc_YOUR_KEY_HERE
GDRIVE_FOLDER_ID=1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer
MINECRAFT_SERVER_ID=fe08f84f
```

### Step 3: Setup Google Drive OAuth (opsional)
```bash
# Jika mau upload ke Google Drive:
python3 generate_oauth_token.py

# Ikuti instruksi untuk authenticate dengan Google account
# Token akan tersimpan di config/gdrive_token.json
```

### Step 4: Test connection
```bash
python3 << 'EOF'
from src.pterodactyl.client import PterodactylClient
import os
from dotenv import load_dotenv

load_dotenv()
pterodactyl = PterodactylClient(
    os.getenv('PTERODACTYL_PANEL_URL'),
    os.getenv('PTERODACTYL_API_KEY')
)
servers = pterodactyl.get_servers()
print(f"Connected! Found {len(servers)} servers")
EOF
```

### Step 5: Run tests
```bash
# Test 1: Simple workflow (recommended untuk first test)
python3 examples/test_backup_workflow_simple.py

# Test 2: Upload existing backup (jika OAuth setup)
python3 examples/test_upload_existing_backup.py

# Test 3: Check existing backups
python3 check_backups.py
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'requests'"
```bash
pip3 install requests
# atau
pip3 install -r requirements.txt
```

### "PTERODACTYL_PANEL_URL not found"
```bash
# Check .env file
cat .env

# Make sure .env exists dan berisi credentials
```

### "Failed to connect to Pterodactyl"
```bash
# Check API credentials
# Pastikan menggunakan Client API key (ptlc_...), bukan Application API (ptla_...)
# Test manual connection
curl -H "Authorization: Bearer ptlc_YOUR_KEY" \
     https://panel.destaria.com/api/client/servers
```

### "Permission denied" saat delete backup
```bash
# Check API key permissions
# Pastikan API key punya akses ke delete backups
```

## Struktur File di Node

```
/path/to/destaria-management-project/
├── .env                              # Environment variables
├── requirements.txt                  # Python dependencies
├── setup_node.sh                     # Setup script
├── test_node.sh                      # Test runner
├── check_backups.py                  # Check existing backups
├── src/
│   ├── pterodactyl/                  # Pterodactyl API client
│   ├── backup/                       # Backup manager
│   └── ...
├── examples/
│   ├── test_backup_workflow_simple.py    # Main test (recommended)
│   ├── test_upload_existing_backup.py    # Upload test
│   └── test_full_workflow.py             # Full workflow test
├── config/
│   ├── gdrive_token.json             # Google Drive OAuth token
│   └── ...
└── data/
    └── devops.db                     # SQLite database
```

## Untuk Production

Setelah manual testing berhasil, setup scheduled backups:

```bash
# Edit config untuk schedule
nano config/servers.yaml

# Start scheduler daemon (nanti akan di-implement)
python3 src/main.py --daemon
```

## Notes

- **Server kosong di test**: Backup 0GB adalah normal (test server tanpa data)
- **Production server**: Backup akan 1-10+ GB tergantung data
- **Polling interval**: 5-10 detik (dapat di-customize di test script)
- **Timeout**: 10 menit default (cukup untuk server 40GB+)
- **Rate limit**: Pterodactyl membatasi 1 backup per server per 5 detik

## Support

Jika ada error:
1. Check logs di terminal
2. Run setup_node.sh lagi
3. Verify .env credentials
4. Check Pterodactyl API status
