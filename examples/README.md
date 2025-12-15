# Backup System Testing & Usage Guide

Panduan lengkap untuk menggunakan dan test backup system.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Method 1: Direct Testing](#method-1-direct-testing)
3. [Method 2: Scheduler Integration](#method-2-scheduler-integration)
4. [Method 3: REST API](#method-3-rest-api)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

```bash
# Set environment variables (PowerShell)
$env:PTERODACTYL_PANEL_URL = "https://panel.myserver.com"
$env:PTERODACTYL_API_KEY = "ptlc_..."
$env:GDRIVE_CREDENTIALS_PATH = "config/google-service-account.json"
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir data

# Verify database
python -c "from src.backup.database import DatabaseManager; db = DatabaseManager(); print('✅ Database ready')"
```

---

## Method 1: Direct Testing

### Example 1: Simple Full Backup

**Use case:** Test backup saat server masih running

```bash
# Run test script
python examples/test_backup_simple.py
```

**Output:**
```
============================================================
TEST 1: Simple Full Backup (Server Running)
============================================================

✅ Backup succeeded!
   Backup ID: backup_server-1_abc123
   Status: {'id': 'backup_server-1_abc123', 'status': 'completed', ...}
```

**Code example:**
```python
from src.backup.backup_manager import BackupManager
from src.backup.database import DatabaseManager
from src.pterodactyl.client import PterodactylClient

# Setup
database = DatabaseManager(db_path="data/devops.db")
pterodactyl_client = PterodactylClient(
    base_url="https://panel.myserver.com",
    api_key="ptlc_..."
)

backup_manager = BackupManager(
    pterodactyl_client=pterodactyl_client,
    database=database
)

# Run backup
backup_id = backup_manager.full_backup(
    server_id="server-1",
    server_name="MainServer",
    retention_days=30
)
```

### Example 2: Maintenance Mode Backup

**Use case:** Test backup dengan server stop/start (untuk testing saja!)

```bash
# ⚠️  WARNING: Server will be stopped!
python examples/test_backup_simple.py
# Select: 2. Incremental Backup with Maintenance Mode
# Type: YES
```

**Timeline:**
```
02:00:00 → Send 5-minute countdown
02:01:00 → "Server akan di-restart dalam 4 menit"
02:02:00 → "Server akan di-restart dalam 3 menit"
02:03:00 → "Server akan di-restart dalam 2 menit"
02:04:00 → "Server akan di-restart dalam 1 menit"
02:04:30 → "Server restart sekarang!"
02:05:00 → Server STOP
02:05:10 → Backup START (server offline - SAFE!)
02:15:10 → Backup DONE
02:15:20 → Server START
02:15:25 → Server ONLINE ✅
02:15:30 → "Server backup selesai. Selamat bermain!"
```

**Code example:**
```python
backup_id = backup_manager.incremental_backup_with_maintenance(
    server_id="server-1",
    server_name="MainServer",
    retention_days=7
)

# Server downtime: ~10-15 minutes
# Google Drive upload happens in background
```

---

## Method 2: Scheduler Integration

### Setup Automated Backups

```bash
# Run scheduler setup
python examples/setup_scheduler.py
# Select: 1. Setup and start scheduler
```

### Create servers.yaml Configuration

```yaml
# config/servers.yaml

servers:
  minecraft-main:
    id: "server-1"
    name: "MainServer"
    backup_schedule: "0 2 * * 1-6"    # Mon-Sat at 02:00 AM
    
  minecraft-secondary:
    id: "server-2"
    name: "SecondaryServer"
    backup_schedule: "0 3 * * 0"      # Sunday at 03:00 AM
```

### Cron Schedule Examples

```
0 2 * * *       → Every day at 02:00
0 2 * * 0       → Every Sunday at 02:00
0 2 * * 1-5     → Weekdays (Mon-Fri) at 02:00
0 2 * * 1-6     → Every day except Sunday at 02:00
0 */4 * * *     → Every 4 hours
*/30 * * * *    → Every 30 minutes
```

### Start Scheduler

```bash
# Method 1: Direct Python
python examples/setup_scheduler.py
# Select: 1. Setup and start scheduler

# Method 2: From main.py (production)
python src/main.py
```

**Output:**
```
📅 Scheduler running!
   Press Ctrl+C to stop

📋 Scheduled jobs:
   - Backup MainServer
     Trigger: cron[day_of_week='mon-sat', hour='2', minute='0']
   - Backup SecondaryServer
     Trigger: cron[day_of_week='sun', hour='3', minute='0']
```

---

## Method 3: REST API

### Start API Server

```bash
python src/main.py
# API will run on http://localhost:8000
```

### Test with Python Client

```bash
python examples/api_client.py
# Select: 1. Run example usage
```

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Trigger Full Backup
```bash
curl -X POST http://localhost:8000/api/backup/full/server-1
```

Response:
```json
{
  "backup_id": "backup_server-1_abc123",
  "status": "running",
  "server_id": "server-1"
}
```

#### Get Backup Status
```bash
curl http://localhost:8000/api/backup/status/backup_server-1_abc123
```

Response:
```json
{
  "id": "backup_server-1_abc123",
  "server_id": "server-1",
  "status": "completed",
  "size_bytes": 5368709120,
  "created_at": "2025-12-15T02:15:00",
  "completed_at": "2025-12-15T02:25:00",
  "gdrive_file_id": "1aB2cDeFg...",
  "gdrive_file_url": "https://drive.google.com/..."
}
```

#### List Backups
```bash
curl http://localhost:8000/api/backup/history/server-1?limit=10
```

#### Scheduler Status
```bash
curl http://localhost:8000/api/scheduler/status
```

Response:
```json
{
  "status": "running",
  "running_backups": 1,
  "total_jobs": 2,
  "jobs": [
    {
      "id": "backup_server-1",
      "name": "Backup MainServer",
      "trigger": "cron[day_of_week='mon-sat', hour='2', minute='0']"
    }
  ]
}
```

---

## Configuration

### Environment Variables

```bash
# Required
PTERODACTYL_PANEL_URL = "https://panel.myserver.com"
PTERODACTYL_API_KEY = "ptlc_..."

# Optional (Google Drive)
GDRIVE_CREDENTIALS_PATH = "config/google-service-account.json"

# Optional (Discord Notifications)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."

# Optional (Database)
SQLITE_DB_PATH = "data/devops.db"

# Optional (API Server)
API_PORT = 8000
API_HOST = "0.0.0.0"
```

### Retention Policies

Edit dalam code (backup_manager.py):

```python
# Full backup retention
backup_manager.full_backup(
    server_id="server-1",
    retention_days=30  # Keep 30 days
)

# Incremental backup retention
backup_manager.incremental_backup_with_maintenance(
    server_id="server-1",
    retention_days=7   # Keep 7 days (shorter)
)
```

---

## Troubleshooting

### Issue: API Connection Failed

```
❌ Failed to connect to Pterodactyl API: ...
```

**Solution:**
```bash
# Check environment variables
echo $env:PTERODACTYL_PANEL_URL
echo $env:PTERODACTYL_API_KEY

# Verify connection
curl -H "Authorization: Bearer $env:PTERODACTYL_API_KEY" \
  https://panel.myserver.com/api/application/servers
```

### Issue: Database Error

```
❌ Database connection error: ...
```

**Solution:**
```bash
# Create data directory
mkdir data

# Reset database
rm data/devops.db
python -c "from src.backup.database import DatabaseManager; db = DatabaseManager()"

# Verify
ls data/devops.db
```

### Issue: Backup Timeout

```
❌ Backup timeout after 1800 seconds
```

**Solution:**
- Server backup terlalu besar
- Increase timeout di BackupManager:
```python
# In backup_manager.py
BASE_TIMEOUT_MINUTES = 60  # Instead of 30
```

### Issue: Server Not Starting After Maintenance Backup

```
❌ CRITICAL: Failed to restart server after backup failure
```

**Solution:**
- Restart server manually di Pterodactyl panel
- Check server logs
- Run manual `start_server()` call:
```python
pterodactyl_client.start_server("server-1")
```

---

## Best Practices

### Scheduling

**Recommended:**
```yaml
# Daily incremental (Monday-Saturday) - Maintenance mode
- schedule: "0 2 * * 1-6"      # 02:00 AM
  type: "incremental"
  retention_days: 7

# Weekly full backup (Sunday) - Maintenance mode
- schedule: "0 2 * * 0"        # Sunday 02:00 AM
  type: "full"
  retention_days: 30
```

**Benefits:**
- Off-peak timing (2 AM, no players)
- Incremental saves storage (80% reduction)
- Full backup weekly for consistency
- Server downtime only 15-20 minutes

### Monitoring

```python
# Check backup status regularly
status = backup_manager.get_backup_status(backup_id)

if status['status'] == 'completed':
    print(f"✅ Backup succeeded")
elif status['status'] == 'failed':
    print(f"❌ Backup failed: {status['error_message']}")
```

### Retention

Default policies:
- **Full backups**: Keep latest 5, up to 30 days old
- **Incremental backups**: Keep latest 10, up to 7 days old
- **Restore history**: Keep 30 days

Adjust di `config/retention.yaml` atau code.

---

## Support

For issues or questions:
1. Check logs: `logs/backup.log`
2. Review code: `src/backup/backup_manager.py`
3. Test manually: `python examples/test_backup_simple.py`
