# 🔐 Setup Guide - Secure Credentials Management

## Overview

Proyek ini menggunakan environment variables dan `.env` file untuk menyimpan kredensial sensitif. **Tidak ada credential yang akan di-commit ke GitHub** karena semua file sensitif sudah di-ignore.

---

## 📋 File yang Di-Ignore (Tidak akan di-commit)

```
.env                                      # Your local environment variables
config/google-service-account.json       # Google Service Account credentials
config/notifications.yaml.local          # Local notification config
config/servers.yaml.local                # Local server config
/data/devops.db                          # Database file
```

---

## 🚀 Setup Langkah-Langkah

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/destaria-devops.git
cd destaria-devops
```

### 2. Create `.env` File

```bash
# Copy template
cp .env.example .env

# Edit dengan editor favorit (Visual Studio Code, Notepad, dll)
# Windows
code .env

# Linux/Mac
nano .env
```

### 3. Setup Pterodactyl API Key

**Ambil dari Pterodactyl Panel:**

1. Login ke Pterodactyl Panel sebagai admin
2. Pergi ke **Admin Dashboard**
3. Pilih **API** → **Application API**
4. Klik **Create New** untuk membuat token baru
5. Isi form:
   - Description: `Minecraft Backup System`
   - Permissions: Centang `backups.*` dan `servers:view`
6. Klik **Create Token**
7. Copy token dan simpan ke `.env`:

```env
PTERODACTYL_API_KEY=your_long_token_here
PTERODACTYL_PANEL_URL=https://your-panel.example.com
```

### 4. Setup Google Service Account

**Buat Service Account di Google Cloud:**

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Buat **Project Baru** atau pilih yang sudah ada
3. **Enable Google Drive API:**
   - Pergi ke **APIs & Services** → **Library**
   - Cari "Google Drive API"
   - Klik **Enable**
4. **Buat Service Account:**
   - Pergi ke **APIs & Services** → **Credentials**
   - Klik **Create Credentials** → **Service Account**
   - Isi form:
     - Service account name: `minecraft-backup`
     - Click **Create and Continue**
   - Skip optional steps, klik **Done**
5. **Buat JSON Key:**
   - Di halaman Service Account, klik pada akun yang baru dibuat
   - Pergi ke tab **Keys**
   - Klik **Add Key** → **Create new key**
   - Pilih **JSON**
   - File akan otomatis di-download
6. **Simpan key ke project:**
   ```bash
   # Copy file ke config folder
   cp ~/Downloads/project-key-*.json config/google-service-account.json
   ```
7. **Update `.env`:**
   ```env
   GDRIVE_CREDENTIALS_PATH=config/google-service-account.json
   GDRIVE_FOLDER_NAME=Minecraft-Backups
   ```

8. **Share Google Drive Folder dengan Service Account:**
   - Buat folder di Google Drive dengan nama `Minecraft-Backups`
   - Buka email service account dari JSON file:
     ```json
     {
       "client_email": "minecraft-backup@your-project.iam.gserviceaccount.com"
     }
     ```
   - Share folder ke email tersebut dengan permission "Editor"

### 5. Setup Discord Webhook (Optional)

**Jika ingin notifikasi backup ke Discord:**

1. Buka Discord Server Anda
2. Pergi ke Server Settings → **Integrations** → **Webhooks**
3. Klik **New Webhook**
4. Setup webhook:
   - Name: `Minecraft Backup Bot`
   - Channel: Pilih channel untuk notifikasi
   - Copy **Webhook URL**
5. Simpan ke `.env`:
   ```env
   DISCORD_WEBHOOK_URL=https://discordapp.com/api/webhooks/123456/abcdef
   ```

### 6. Buat Database Directory

```bash
# Windows
mkdir C:\data

# Linux/Mac
mkdir -p /data
chmod 755 /data
```

Update `.env` jika menggunakan path berbeda:
```env
SQLITE_DB_PATH=C:\data\devops.db
```

### 7. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate venv
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 8. Test Connection

```bash
python -c "
import os
from dotenv import load_dotenv
from src.pterodactyl.client import PterodactylClient
from src.backup.gdrive_client import GoogleDriveClient
from src.backup.database import DatabaseManager

load_dotenv()

print('Testing connections...')

# Test Pterodactyl
try:
    ptero = PterodactylClient()
    servers = ptero.get_servers()
    print(f'✓ Pterodactyl Connected: {len(servers)} servers found')
except Exception as e:
    print(f'✗ Pterodactyl Failed: {e}')

# Test Google Drive
try:
    gdrive = GoogleDriveClient()
    print('✓ Google Drive Connected')
except Exception as e:
    print(f'✗ Google Drive Failed: {e}')

# Test Database
try:
    db = DatabaseManager()
    print('✓ Database Connected')
except Exception as e:
    print(f'✗ Database Failed: {e}')
"
```

---

## 🔒 Security Best Practices

### ✅ DO:
- ✅ Keep `.env` file **LOCAL ONLY** - never commit to Git
- ✅ Use strong, unique API keys
- ✅ Rotate keys periodically
- ✅ Add `.env` to `.gitignore` (sudah di-setup)
- ✅ Keep `google-service-account.json` **SECRET**
- ✅ Use separate credentials per environment (dev/staging/prod)
- ✅ Review `.gitignore` sebelum push ke GitHub

### ❌ DON'T:
- ❌ Commit `.env` file ke Git
- ❌ Hardcode credentials dalam source code
- ❌ Share credentials di chat/email
- ❌ Use same API key untuk semua environment
- ❌ Commit JSON credential files
- ❌ Upload ke public storage (AWS S3, Google Cloud Storage) tanpa encryption

---

## 📦 Production Deployment

Untuk deploy ke production server/Docker:

### Option 1: Environment Variables di System

```bash
# Linux - tambah ke ~/.bashrc atau /etc/environment
export PTERODACTYL_PANEL_URL="https://panel.example.com"
export PTERODACTYL_API_KEY="your_key_here"
export GDRIVE_CREDENTIALS_PATH="/opt/app/credentials/service-account.json"

# Docker - gunakan .env file atau docker-compose
```

### Option 2: Docker Compose Secrets

```yaml
# docker-compose.yml
services:
  devops:
    environment:
      PTERODACTYL_API_KEY: ${PTERODACTYL_API_KEY}
      GDRIVE_CREDENTIALS_PATH: /run/secrets/gdrive_creds
    secrets:
      - gdrive_creds

secrets:
  gdrive_creds:
    file: ./config/google-service-account.json
```

### Option 3: Kubernetes Secrets

```bash
kubectl create secret generic devops-secrets \
  --from-file=gdrive=config/google-service-account.json \
  --from-literal=api_key=$PTERODACTYL_API_KEY
```

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'dotenv'"
```bash
pip install python-dotenv
```

### "google-service-account.json not found"
```bash
# Pastikan file ada di config folder
ls -la config/google-service-account.json

# Atau update GDRIVE_CREDENTIALS_PATH di .env
```

### "Permission denied" (Google Drive)
- Cek bahwa folder sudah di-share dengan service account email
- Verify email di JSON file matches shared user

### "Unauthorized" (Pterodactyl)
- Pastikan menggunakan **Application API Key**, bukan Client Key
- Verify permissions mencakup `backups.*`

---

## 📝 Checklist Sebelum Push ke GitHub

Sebelum melakukan `git push`, pastikan:

- [ ] `.env` file sudah di-create locally (tidak di-commit)
- [ ] `config/google-service-account.json` ada di `.gitignore`
- [ ] Tidak ada credential yang visible di `.git status`
- [ ] `.gitignore` sudah updated dengan semua sensitive paths
- [ ] README sudah di-update dengan setup instructions
- [ ] Test connections berhasil sebelum push

```bash
# Verify sebelum push
git status                  # Pastikan tidak ada .env atau JSON files
git diff --cached           # Verify tidak ada secrets di staged files
cat .gitignore              # Verify sensitive files di-exclude
```

---

## 🔄 Team Collaboration

Jika tim mengakses project yang sama:

1. **Share hanya `.env.example` dan dokumentasi ini** melalui:
   - Private documentation/wiki
   - Email (untuk kredensial)
   - Secure note-taking app (1Password, Bitwarden, dll)

2. **Setiap team member harus:**
   - Clone repository
   - Create `.env` sendiri dengan credentials mereka
   - Never commit `.env` ke Git
   - Rotate credentials jika anggota tim keluar

3. **Setup CI/CD:**
   - Github Actions/GitLab CI: gunakan repository secrets
   - Jangan hardcode credentials di pipeline config

---

## 📚 References

- [python-dotenv Documentation](https://python-dotenv.readthedocs.io/)
- [Google Service Account Setup](https://cloud.google.com/iam/docs/service-account-overview)
- [Pterodactyl API Documentation](https://pterodactyl.io/api/overview.html)
- [12 Factor App - Config](https://12factor.net/config)

---

**Last Updated:** December 2024  
**Questions?** Buka issue di GitHub repository
