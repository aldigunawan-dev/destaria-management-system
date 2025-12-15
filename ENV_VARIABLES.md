# 🔑 Environment Variables Reference

Dokumentasi lengkap untuk semua environment variables yang diperlukan.

## Core Configuration

### Logging Configuration
- **LOG_LEVEL** - Default: `INFO`
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - Debug untuk development, INFO untuk production

### Database Configuration
- **SQLITE_DB_PATH** - Default: `/data/devops.db`
  - Lokasi file SQLite database
  - Windows: `C:\data\devops.db` atau custom path
  - Linux/Mac: `/data/devops.db` atau `/opt/devops/devops.db`
  - Folder akan di-create otomatis jika tidak ada

---

## Pterodactyl Panel Configuration

**Required untuk backup system berfungsi**

### PTERODACTYL_PANEL_URL
```
Format: https://your-panel-domain.com
Example: https://pterodactyl.example.com
```
- Base URL Pterodactyl Panel Anda
- Tidak perlu trailing slash
- Harus HTTPS untuk production

### PTERODACTYL_API_KEY
```
Format: PtlApplication:xxxxx... (panjang token)
Example: PtlApplication:d7a2c3b4e5f6g7h8i9j0k1l2m3n4o5p6
```

**Cara mendapatkan:**
1. Login ke Pterodactyl Panel **sebagai admin**
2. Admin Panel → **API** → **Application API** (bukan Client API!)
3. Click **Create New**
4. Isi:
   - Description: `Minecraft Backup System`
   - Allowed IPs: Leave empty untuk allow semua
   - Permissions: Cek `backups.*`, `servers:view`
5. Click **Create Token**
6. Copy token (jangan copy lagi - tidak ada second copy)
7. Paste ke `.env` sebagai PTERODACTYL_API_KEY

**PENTING:** Gunakan APPLICATION API KEY, bukan Client API Key!

---

## Google Drive Configuration

**Required untuk backup ke Google Drive**

### GDRIVE_CREDENTIALS_PATH
```
Default: config/google-service-account.json
```
- Path ke Google Service Account JSON credentials file
- File ini di-gitignore (tidak akan di-commit)
- Harus di-download dari Google Cloud Console

**Cara mendapatkan Service Account:**

1. Buka [Google Cloud Console](https://console.cloud.google.com/)

2. **Buat/Pilih Project:**
   - Top left corner: Select project dropdown
   - Click **NEW PROJECT**
   - Nama: `Minecraft Backup`
   - Click **CREATE**

3. **Enable Google Drive API:**
   - Search: "Google Drive API"
   - Click result
   - Click **ENABLE**

4. **Create Service Account:**
   - Go to: **APIs & Services** → **Credentials**
   - Click **+ CREATE CREDENTIALS**
   - Choose: **Service Account**
   - Fill form:
     - Service account name: `minecraft-backup`
     - Service account ID: auto-filled
     - Click **CREATE AND CONTINUE**
   - Skip optional settings
   - Click **DONE**

5. **Create JSON Key:**
   - Di halaman Service Accounts, click nama service account
   - Go to **KEYS** tab
   - Click **ADD KEY** → **Create new key**
   - Choose **JSON**
   - Click **CREATE**
   - File auto-download
   - **SAVE THIS FILE!**

6. **Copy ke project:**
   ```bash
   # Windows
   copy "C:\Users\YourUser\Downloads\project-key-*.json" "config\google-service-account.json"
   
   # Linux/Mac
   cp ~/Downloads/project-key-*.json config/google-service-account.json
   ```

7. **Share folder dengan Service Account:**
   - Buat folder di Google Drive: `Minecraft-Backups`
   - Buka JSON file, cari "client_email"
   - Copy email: `minecraft-backup@project-id.iam.gserviceaccount.com`
   - Share folder ke email tersebut dengan permission **Editor**
   - Service account sekarang bisa upload ke folder

### GDRIVE_FOLDER_NAME
```
Default: Minecraft-Backups
```
- Nama folder di Google Drive
- Folder harus sudah di-share dengan service account email
- Backup akan di-organize: `Minecraft-Backups/{server_name}/{YYYY-MM-DD}/`

---

## Discord Notifications (Optional)

**Optional - untuk notifikasi backup ke Discord**

### DISCORD_WEBHOOK_URL
```
Format: https://discordapp.com/api/webhooks/WEBHOOK_ID/WEBHOOK_TOKEN
Example: https://discordapp.com/api/webhooks/123456789012345678/abc...
```

**Cara membuat Discord Webhook:**

1. Buka Discord Server Anda
2. Server Settings → **Integrations** → **Webhooks**
3. Click **NEW WEBHOOK**
4. Setup:
   - Name: `Minecraft Backup Bot`
   - Channel: Pilih channel untuk notifikasi
   - Icon: Optional, upload bot icon
5. Click **COPY WEBHOOK URL**
6. Paste ke `.env` sebagai DISCORD_WEBHOOK_URL

**Test Webhook (Optional):**
```bash
curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Test message from backup system"}' \
    YOUR_WEBHOOK_URL_HERE
```

---

## Backup Settings

### BACKUP_TIMEOUT_BASE_MINUTES
```
Default: 30 (30 menit)
```
- Base timeout untuk backup operations
- Actual timeout = base + (1 minute per GB)
- Contoh: 30 base + 10 GB = 40 menit timeout
- Sesuaikan jika backup sering timeout

### BACKUP_MAX_CONCURRENT
```
Default: 3
Recommended: 2-4
```
- Maximum concurrent backups yang jalan bersamaan
- Lebih tinggi = cepat tapi resource-intensive
- Lebih rendah = slower tapi stable
- Adjust berdasarkan server resources

### BACKUP_CHUNK_SIZE_MB
```
Default: 256 (256 MB per chunk)
```
- Ukuran chunk untuk Google Drive upload
- Larger = faster upload, lebih RAM
- Smaller = slower upload, lebih stable
- 256 MB recommended untuk 40GB+ files

---

## Retention Policy

### RETENTION_MAX_AGE_DAYS
```
Default: 30
```
- Delete backup older than ini banyak hari
- Contoh: 30 = hapus backup lebih dari sebulan
- Override per-server di config/servers.yaml

### RETENTION_MAX_COUNT_FULL
```
Default: 5
```
- Keep maksimal 5 full backups per server
- Older full backups dihapus otomatis
- Plus age-based cleanup

### RETENTION_MAX_COUNT_INCREMENTAL
```
Default: 10
```
- Keep maksimal 10 incremental backups per server
- (Sekarang: incremental = full, untuk future enhancement)

---

## API Server Configuration

### API_HOST
```
Default: 0.0.0.0
```
- Host untuk REST API server
- `0.0.0.0` = accessible dari semua network interfaces
- `localhost` = hanya local access

### API_PORT
```
Default: 8000
```
- Port untuk REST API
- Docker: 8000 (inside container)
- Host port: bisa different (set di docker-compose.yml)

### API_RELOAD
```
Default: false
Options: true, false
```
- Auto-reload API saat code berubah
- `true` = development only
- `false` = production

---

## Docker Configuration

### DOCKER_BACKUP_DIR
```
Default: /backups
```
- Directory inside container untuk temp backup files
- Mounted volume path
- Data persisted ke host jika di-mount dengan volume

---

## Complete .env Example

```ini
# Logging
LOG_LEVEL=INFO

# Database
SQLITE_DB_PATH=/data/devops.db

# Pterodactyl
PTERODACTYL_PANEL_URL=https://pterodactyl.example.com
PTERODACTYL_API_KEY=PtlApplication:xxxxxxxxxxxxxxxxxxxx

# Google Drive
GDRIVE_CREDENTIALS_PATH=config/google-service-account.json
GDRIVE_FOLDER_NAME=Minecraft-Backups

# Discord (Optional)
DISCORD_WEBHOOK_URL=https://discordapp.com/api/webhooks/123/abc

# Backup Settings
BACKUP_TIMEOUT_BASE_MINUTES=30
BACKUP_MAX_CONCURRENT=3
BACKUP_CHUNK_SIZE_MB=256

# Retention Policy
RETENTION_MAX_AGE_DAYS=30
RETENTION_MAX_COUNT_FULL=5
RETENTION_MAX_COUNT_INCREMENTAL=10

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# Docker
DOCKER_BACKUP_DIR=/backups
```

---

## Environment Variable Loading

Code automatically loads `.env` file:

```python
from dotenv import load_dotenv
import os

load_dotenv()

pterodactyl_url = os.getenv("PTERODACTYL_PANEL_URL")
api_key = os.getenv("PTERODACTYL_API_KEY")
```

### Precedence (di mana environment variables di-cari):
1. OS environment variables (highest priority)
2. `.env` file
3. `.env.local` file
4. Default values dalam code (lowest priority)

---

## Validation & Testing

**Verify environment variables loaded correctly:**

```bash
python -c "
import os
from dotenv import load_dotenv

load_dotenv()

vars = ['PTERODACTYL_PANEL_URL', 'PTERODACTYL_API_KEY', 'GDRIVE_CREDENTIALS_PATH']
for var in vars:
    value = os.getenv(var)
    if value:
        # Show first/last chars, hide middle
        if len(value) > 20:
            display = value[:4] + '...' + value[-4:]
        else:
            display = '***'
        print(f'✓ {var}: {display}')
    else:
        print(f'✗ {var}: NOT SET')
"
```

---

## Security Notes

- 🔒 **NEVER** commit `.env` file to Git
- 🔒 **NEVER** hardcode credentials in source code
- 🔒 **NEVER** share API keys via email/chat
- 🔒 Use different credentials per environment
- 🔒 Rotate credentials regularly
- 🔒 Keep `google-service-account.json` PRIVATE

---

## Common Issues

### "KeyError: 'PTERODACTYL_API_KEY'"
**Solution:** Pastikan variable ada di `.env` dan file di-load dengan `load_dotenv()`

### "FileNotFoundError: google-service-account.json"
**Solution:** 
1. Check path di `.env`
2. Verify file exists di `config/google-service-account.json`
3. Run dari project root directory

### "Connection refused" (Pterodactyl)
**Solution:**
1. Verify PTERODACTYL_PANEL_URL is correct
2. Check firewall/network access ke panel
3. Verify API key has `backups.*` permission

### "Unauthorized" (Google Drive)
**Solution:**
1. Verify JSON file is valid
2. Check folder is shared dengan service account email
3. Verify service account has Editor permission

---

**Last Updated:** December 2024  
**Questions?** See SETUP_GUIDE.md for detailed instructions
