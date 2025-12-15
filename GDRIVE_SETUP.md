# Google Drive Setup - OAuth untuk Workspace Account

## Masalah dengan Service Account

Service Account tidak bisa akses folder shared yang dimiliki akun Workspace Anda. Error:
```
File not found: 1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer
```

**Solusi:** Gunakan OAuth login dengan akun Workspace Anda sendiri.

---

## Setup OAuth Step-by-Step

### Step 1: Create OAuth Credentials di Google Cloud Console

1. Go to: https://console.cloud.google.com
2. Pilih project Anda (atau create new project)
3. Go to: **APIs & Services** → **Credentials**
4. Click **+ Create Credentials** → **OAuth client ID**
5. Choose **Desktop application**
6. Click **Create**
7. Download JSON file
8. Save sebagai: `config/oauth_credentials.json`

### Step 2: Enable Google Drive API

1. Di Google Cloud Console, go to: **APIs & Services** → **Library**
2. Search for: "Google Drive API"
3. Click **Enable**

### Step 3: Generate Token (Interactive Login)

Run script untuk generate token:
```bash
python generate_oauth_token.py
```

Script akan:
1. Open browser untuk login
2. Ask permission to access Drive
3. Generate `config/gdrive_token.json`

### Step 4: Update Code

Update test script atau main.py:

```python
from src.backup.gdrive_client import GoogleDriveClient

gdrive = GoogleDriveClient(
    oauth_token_path="config/gdrive_token.json",
    folder_id="1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer"
)
```

Atau gunakan environment variables:
```bash
export GDRIVE_TOKEN_PATH="config/gdrive_token.json"
export GDRIVE_FOLDER_ID="1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer"
```

---

## File Structure

```
config/
  oauth_credentials.json      ← Download dari GCP (secret, don't share)
  gdrive_token.json           ← Generated automatically (safe, user-specific)
  google-service-account.json ← Still needed for other stuff
```

---

## GoogleDriveClient Usage

### With OAuth (Workspace Account) - RECOMMENDED

```python
gdrive = GoogleDriveClient(
    oauth_token_path="config/gdrive_token.json",
    folder_id="1-bICGl5sV4ha_Ylpqe95ETQXaJ4braer"
)
```

### With Service Account (Legacy, need Shared Drive)

```python
gdrive = GoogleDriveClient(
    credentials_path="config/google-service-account.json",
    folder_id="shared_drive_id"
)
```

---

## Troubleshooting

### Browser Tidak Terbuka
Check console output untuk URL dan manual copy-paste.

### "Invalid credentials" Error
Pastikan oauth_credentials.json valid dan tidak di-edit.

### "Permission Denied" saat Upload
Token mungkin expired - regenerate dengan: `python generate_oauth_token.py`

---

## Next: Test Upload

```bash
python examples/test_gdrive_upload.py
```
