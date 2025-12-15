# 🔐 Security Checklist - Pre-GitHub Push

Gunakan checklist ini sebelum melakukan `git push` ke GitHub untuk memastikan tidak ada credential sensitif yang ter-commit.

## ✅ Pre-Push Verification

### 1. Check Git Status
```bash
git status
```
**Pastikan output tidak menunjukkan:**
- ❌ `.env`
- ❌ `*.json` (credential files)
- ❌ `/data/` folder
- ❌ `config/google-service-account.json`
- ❌ `config/notifications.yaml` (jika berisi webhook URL)

---

### 2. Verify .gitignore Configuration

```bash
# Pastikan file-file sensitif di-ignore
git check-ignore -v .env
git check-ignore -v config/google-service-account.json
git check-ignore -v /data/
```

**Expected output:** Setiap command harus menunjukkan path dan rule yang mengecualukan file tersebut.

**If files are NOT ignored:**
1. Update `.gitignore` dengan path yang benar
2. Remove dari git history: `git rm --cached filename`
3. Commit changes

---

### 3. Check Staged Changes

```bash
git diff --cached
```

**Scan output untuk:**
- ❌ API keys atau tokens
- ❌ Database passwords
- ❌ Private email addresses
- ❌ File paths ke credential files
- ❌ Google credential content

---

### 4. Verify Recent Commits

```bash
# Check last 5 commits
git log --oneline -5

# Check content dari specific commit
git show <commit-hash>
```

**Jika sudah ada credential di history:**
```bash
# Remove file from history (DANGEROUS - coordinate dengan team)
git filter-branch --tree-filter 'rm -f config/google-service-account.json' HEAD

# Atau gunakan BFG Repo-Cleaner
# https://rtyley.github.io/bfg-repo-cleaner/
```

---

### 5. Files Safe to Commit

✅ SAFE (tidak mengandung secrets):
- `README.md`
- `SETUP_GUIDE.md`
- `.env.example` (template saja, tanpa values)
- `requirements.txt`
- Source code Python (`src/**/*.py`)
- Docker files (`Dockerfile`, `docker-compose.yml` - tanpa hardcoded values)
- Config templates (`config/servers.yaml.example`, etc)
- Documentation

---

### 6. Configuration File Templates

Untuk file konfigurasi yang sensitif, buat template `.example`:

```bash
# Good practice
config/servers.yaml.example       ✅ Commit ini
config/servers.yaml               ❌ Jangan commit (di-.gitignore)

config/notifications.yaml.example ✅ Commit ini
config/notifications.yaml         ❌ Jangan commit (di-.gitignore)
```

**Template example:**
```yaml
# config/servers.yaml.example
servers:
  - id: "server-1"
    name: "Production"
    pterodactyl_server_id: "1"
    backup_schedule: "0 2 * * *"  # 2 AM daily
    # Real file would have actual server IDs
```

---

## 🔍 Sensitive Data Scanning Tools

Gunakan tools ini untuk double-check:

### Option 1: git-secrets (Recommended)
```bash
# Install
brew install git-secrets  # macOS
# atau download dari https://github.com/awslabs/git-secrets

# Setup
git secrets --install
git secrets --register-aws

# Scan
git secrets --scan
```

### Option 2: TruffleHog
```bash
# Install
pip install truffleHog

# Scan repository
trufflehog filesystem . --json
```

### Option 3: GitGuardian CLI
```bash
# Install
pip install gitguardian-cli

# Scan
ggshield secret scan path .
```

---

## 📝 Final Pre-Push Checklist

- [ ] Ran `git status` - no `.env`, JSON files, or `/data/` shown
- [ ] Ran `git check-ignore` - sensitive files are properly ignored
- [ ] Ran `git diff --cached` - no secrets in staged changes
- [ ] Checked recent commits - no credentials in history
- [ ] Verified `.gitignore` contains all sensitive file patterns
- [ ] Tested `.env.example` template is clear and documented
- [ ] Ran git-secrets/TruffleHog scan - no alerts
- [ ] Asked team members to verify - no security concerns
- [ ] Ready to push to GitHub ✅

---

## 🚀 Safe Push to GitHub

```bash
# After verification above
git add .
git commit -m "Setup secure credential management and pre-push checks"
git push origin main
```

---

## ⚠️ If You Accidentally Committed Secrets

### Immediate Actions:

1. **Revoke compromised credentials immediately**
   - Generate new Pterodactyl API key
   - Create new Google Service Account
   - Update Discord webhook
   - Update all passwords

2. **Remove from git history**
   ```bash
   # Option A: BFG (faster for large repos)
   git clone --mirror https://github.com/user/repo.git
   bfg --delete-files google-service-account.json repo.git

   # Option B: git filter-branch
   git filter-branch --tree-filter 'rm -f config/google-service-account.json' HEAD
   git push origin --force-with-lease
   ```

3. **Notify collaborators**
   - Tell team to pull latest changes
   - Provide new credentials through secure channel

4. **Force GitHub to purge**
   - GitHub's cache will be updated within hours
   - Monitor for automated alerts from GitHub/GitGuardian

---

## 📚 References

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [git-secrets GitHub](https://github.com/awslabs/git-secrets)
- [TruffleHog GitHub](https://github.com/trufflesecurity/trufflehog)
- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

**Last Updated:** December 2024
