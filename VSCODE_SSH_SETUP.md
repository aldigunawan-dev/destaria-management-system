# VS Code Remote SSH Setup Guide

## Step 1: Install Remote - SSH Extension

1. **Buka VS Code**
2. **Ctrl+Shift+X** (Open Extensions)
3. Search: `Remote - SSH`
4. Install extension dari Microsoft
5. Tunggu sampai selesai install

## Step 2: Setup SSH Connection

### Method A: Via Command Palette (Recommended)

1. **Ctrl+Shift+P** (Command Palette)
2. Type: `Remote-SSH: Connect to Host`
3. Input format: `user@hostname`
   - Example: `root@panel.destaria.com`
   - Or: `ubuntu@192.168.1.100`
4. **Enter**, tunggu connection established
5. Password prompt akan muncul (input SSH password)

### Method B: Via SSH Config File

1. **Ctrl+Shift+P** → `Remote-SSH: Open Configuration File...`
2. Select `~/.ssh/config`
3. Add entry:
```
Host destaria-node
    HostName panel.destaria.com
    User root
    Port 22
    IdentityFile ~/.ssh/id_rsa
```
4. Save file
5. **Ctrl+Shift+P** → `Remote-SSH: Connect to Host...` → select `destaria-node`

## Step 3: Open Project Folder

Setelah SSH connected (lihat "SSH: destaria-node" di bottom left):

1. **File** → **Open Folder**
2. Navigate ke: `/path/to/destaria-management-project`
3. **OK**
4. Folder akan terbuka (first time akan install VS Code server di node)
5. Tunggu ~1 menit untuk setup

## Step 4: Setup Terminal

1. **Ctrl+`** (Open Terminal)
2. Terminal sekarang terhubung ke node
3. Run setup script:

```bash
# Pastikan di folder project
pwd

# Run setup script
bash setup_node.sh
```

## Step 5: Run Tests

Terminal VS Code sekarang bisa run Python scripts:

```bash
# Test simple workflow
python3 examples/test_backup_workflow_simple.py

# Check backups
python3 check_backups.py
```

## Tips

### 1. Edit Files Langsung di Node
- File explorer di VS Code menampilkan node filesystem
- Edit file, Ctrl+S otomatis save ke node
- No FTP needed!

### 2. Debug & Terminal
- Terminal di VS Code = terminal node
- Lihat output real-time
- Ctrl+C untuk stop script

### 3. Quick Commands
```bash
# Check Python version
python3 --version

# View .env
cat .env

# Check backups
ls -lah data/

# View logs (live)
tail -f logs/*.log
```

### 4. If SSH Disconnects
- VS Code auto-reconnect
- Or manually: **Ctrl+Shift+P** → `Remote-SSH: Reopen in SSH`

## Troubleshooting

### "SSH connection failed"
- Check host/username correct
- Verify SSH access: `ssh user@host` dari local terminal
- Check firewall (port 22 open)

### "Permission denied"
- Wrong password
- Check SSH key permissions: `chmod 600 ~/.ssh/id_rsa`
- Verify user punya akses ke folder

### "VS Code server installation failed"
- Node perlu internet untuk download
- Check node bisa akses `https://code.visualstudio.com`
- Or pre-install: `code-server` di node

### "Module not found"
- Dependencies belum install
- Run: `bash setup_node.sh`

## Next: Running Tests

Setelah setup selesai, jalankan di terminal VS Code:

```bash
# Option 1: Interactive test menu
bash test_node.sh

# Option 2: Direct tests
python3 examples/test_backup_workflow_simple.py
python3 examples/test_upload_existing_backup.py
python3 check_backups.py
```

## Notes

- **VS Code Remote** = Full IDE di node
- **No installation** di local (except VS Code + extension)
- **Native performance** di node (no latency)
- **File sync** otomatis
- **Perfect untuk production** setup

Enjoy! 🚀
