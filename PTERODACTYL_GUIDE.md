# Pterodactyl Integration Guide

## Critical Discovery: API Key Types & Endpoints

### API Key Types (MOST IMPORTANT)

Pterodactyl memiliki **dua jenis API key yang BERBEDA**:

| Key Type | Format | Untuk | Digunakan di |
|----------|--------|-------|-------------|
| **Application API** | `ptla_...` | Admin operations (create servers, manage users) | Admin panel saja ❌ |
| **Client API** | `ptlc_...` | User-level operations (backups, files, commands) | **Backup system ✓** |

**⚠️ UNTUK BACKUP, HARUS GUNAKAN `ptlc_` KEY!**

### Endpoint Differences

**Backup Operations (SEMUA pakai `/api/client/`):**
- `POST /api/client/servers/{identifier}/backups` - Create backup
- `GET /api/client/servers/{identifier}/backups/{backup_id}` - Get status
- `DELETE /api/client/servers/{identifier}/backups/{backup_id}` - Delete

### Server Identifier vs Internal ID

Penting dibedakan:
- **`identifier`** (UUID format: `fe08f84f`) - Digunakan di **API calls**
- **`internal_id`** (angka: `24`) - Untuk tampilan UI panel saja

**Contoh dari Destaria panel:**
```json
{
  "identifier": "fe08f84f",      // <-- USE THIS FOR API
  "internal_id": 24,              // <-- NOT for API
  "name": "test management system",
  "uuid": "fe08f84f-0a08-4522-9e92-b00f1653ba86"
}
```

## Setup Configuration

### 1. Get Your API Key

**Path di Pterodactyl Panel:**
- Admin: Settings → API → Create New → **Client API** (bukan Application!)
- User: Account → API Tokens

### 2. Get Server Identifier

**Method 1: Via API (Recommended)**
```python
import os
from src.pterodactyl.client import PterodactylClient

client = PterodactylClient(
    base_url="https://panel.destaria.com",
    api_key="ptlc_..."
)

servers = client.get_servers()
for server in servers:
    print(f"Name: {server['name']}, Identifier: {server['identifier']}")
```

**Method 2: Via Panel UI**
- Buka panel → Servers
- Lihat URL: `https://panel.destaria.com/server/{identifier}`
- Extract bagian `{identifier}`

### 3. Update Configuration

File: `config/servers.yaml`
```yaml
servers:
  test:
    id: "fe08f84f"                 # <-- Use identifier, not internal_id!
    name: "test management system"
    backup_enabled: true
    backup_schedule: "0 2 * * 1-6"
    backup_type: "full"

pterodactyl:
  panel_url: "https://panel.destaria.com"
  api_key: "${PTERODACTYL_API_KEY}"  # Set via environment
```

### 4. Set Environment Variables

**PowerShell (Windows):**
```powershell
$env:PTERODACTYL_PANEL_URL = "https://panel.destaria.com"
$env:PTERODACTYL_API_KEY = "ptlc_..."
```

**Bash (Linux/Mac):**
```bash
export PTERODACTYL_PANEL_URL="https://panel.destaria.com"
export PTERODACTYL_API_KEY="ptlc_..."
```

## Testing

### 1. List Available Servers

```bash
python check_api.py
```

### 2. Test Backup

```bash
python examples/test_backup_simple.py
```

Expected output:
```
[OK] Backup succeeded!
   Backup ID: backup_fe08f84f_7981e2ed
   Status: {'status': 'completed', ...}
```

## Common Errors & Solutions

### Error: "Resource not found: /api/application/servers/..."
- **Cause**: Wrong API endpoint (using Application instead of Client)
- **Fix**: Ensure code uses `/api/client/servers/` not `/api/application/servers/`

### Error: "Resource not found: /api/client/servers/24/..."
- **Cause**: Using `internal_id` (24) instead of `identifier` (fe08f84f)
- **Fix**: Always use `identifier` field from API, not the numeric ID

### Error: "Authentication failed" / "Invalid key"
- **Cause**: Wrong key type (ptla_ instead of ptlc_) or expired key
- **Fix**: Generate new **Client API** key (ptlc_), not Application API key

### Error: "Server not found" (404)
- **Cause**: Wrong server identifier
- **Fix**: Run `python check_api.py` to list correct identifiers

## Code Changes Made

### Files Updated:
1. **src/pterodactyl/client.py**
   - `get_servers()` - Changed to `/api/client`, added attribute parsing
   - `get_server()` - Changed to `/api/client`
   - `get_backup()` - Changed to `/api/client`
   - `delete_backup()` - Changed to `/api/client`

2. **config/servers.yaml**
   - Updated `test.id` from "24" to "fe08f84f"

### What Works Now:
- ✅ Connect to Pterodactyl panel with Client API key
- ✅ List all accessible servers with correct identifiers
- ✅ Create backups on any accessible server
- ✅ Monitor backup status
- ✅ Clean up old backups

## Next Steps

1. **Scheduler**: Setup APScheduler untuk automatic backups
2. **Google Drive**: Upload backups ke Google Drive
3. **Retention**: Automatic cleanup old backups
4. **Monitoring**: Discord notifications for backup status
