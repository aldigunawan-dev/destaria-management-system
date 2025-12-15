# 📤 Publishing to GitHub - Quick Reference

## Step 1: Run Security Verification

```bash
python verify_security.py
```

**Expected output:**
```
✅ SECURITY CHECK PASSED - Safe to push to GitHub!
```

If you see ❌ errors, fix them before proceeding (see SECURITY_CHECKLIST.md).

---

## Step 2: Verify Repo is Clean

```bash
# Check status
git status

# Should show only tracked Python files and documentation
# Should NOT show: .env, config/google-service-account.json, /data/
```

---

## Step 3: Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Create new repository:
   - **Repository name:** `destaria-minecraft-devops` (or your choice)
   - **Description:** Minecraft Server DevOps Platform with Backup & Plugin Management
   - **Visibility:** Public or Private (your choice)
   - **Don't add:** README, .gitignore, or license (we already have these)
3. Click **Create repository**

---

## Step 4: Add Remote & Push

```bash
# Add GitHub remote (replace USERNAME and REPO_NAME)
git remote add origin https://github.com/USERNAME/REPO_NAME.git

# Or if using SSH:
git remote add origin git@github.com:USERNAME/REPO_NAME.git

# Verify remote
git remote -v

# Set main branch
git branch -M main

# Push all changes
git push -u origin main
```

---

## Step 5: Verify GitHub Upload

1. Go to your repository on GitHub
2. Verify:
   - ✅ Code files are there (`src/`, `config/`, `tests/`, etc)
   - ✅ README.md is displayed
   - ✅ SETUP_GUIDE.md and SECURITY_CHECKLIST.md exist
   - ❌ No `.env` file
   - ❌ No `google-service-account.json`
   - ❌ No `/data/` folder
   - ❌ No credentials visible anywhere

---

## Step 6: Add GitHub README Badges (Optional)

Edit README.md to add badges:

```markdown
# Minecraft Server DevOps Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive DevOps platform for managing Minecraft servers using Pterodactyl Panel...
```

---

## Step 7: Add Topics (GitHub Repository Tags)

Go to repository **Settings** > **About** > Add topics:
- `minecraft`
- `devops`
- `pterodactyl`
- `backup`
- `automation`
- `python`

---

## Step 8: Setup GitHub Security (Recommended)

### Enable Branch Protection
1. **Settings** > **Branches**
2. Add rule for `main` branch:
   - ✅ Require pull request reviews
   - ✅ Require status checks to pass
   - ✅ Include administrators

### Enable Dependabot
1. **Settings** > **Security & analysis**
2. Enable **Dependabot alerts**
3. Enable **Dependabot security updates**

### Enable Code Scanning
1. **Security** > **Code scanning**
2. Click **Set up code scanning**
3. Choose analysis tool (e.g., CodeQL)

---

## Step 9: Create Initial Documentation Issues (Optional)

Create GitHub Issues to track pending work:

```markdown
## Issue: Step 6 - Scheduler Implementation
- [ ] Create src/backup/scheduler.py
- [ ] APScheduler integration
- [ ] ThreadPoolExecutor for parallel execution
```

---

## Step 10: Share with Team

Now you can share the repo:

```
GitHub: https://github.com/USERNAME/REPO_NAME
Setup: See SETUP_GUIDE.md in repository
```

**Important:** Each team member should:
1. Clone repo
2. Create their own `.env` file locally
3. Get their own credentials (Pterodactyl API key, Google Service Account)
4. Never commit `.env` or credential files

---

## Troubleshooting

### "fatal: not a git repository"
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO_NAME.git
git push -u origin main
```

### "rejected because the remote contains work that you do not have"
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Accidentally pushed .env file
```bash
# Remove from GitHub (CRITICAL - revoke all credentials immediately)
git rm --cached .env
git commit -m "Remove .env file"
git push
# Then revoke all API keys and credentials!
```

### Want to make repo private
```
GitHub > Settings > Danger zone > Change repository visibility
```

---

## Post-Publish Checklist

- [ ] Repository is accessible on GitHub
- [ ] No credential files visible
- [ ] SETUP_GUIDE.md is in repository
- [ ] SECURITY_CHECKLIST.md is in repository
- [ ] README.md displays correctly
- [ ] Topics/tags are set
- [ ] Team members can clone repo
- [ ] Team members can create own .env file
- [ ] All credential files are in .gitignore

---

## Next Steps After Publishing

1. **Share repository link** with team members
2. **Each team member should:**
   - Clone repository
   - Follow SETUP_GUIDE.md
   - Create own `.env` file
   - Get their own Pterodactyl API key
   - Create their own Google Service Account
3. **Continue development** (Steps 6-10 of backup system)
4. **Setup CI/CD** (GitHub Actions for testing)
5. **Documentation** - Keep SETUP_GUIDE and README updated

---

## Quick Copy-Paste Setup

```bash
# 1. Initialize git (if not already)
git init

# 2. Add and commit all files
git add .
git commit -m "Initial commit: Minecraft DevOps Platform Phase 1"

# 3. Set main branch
git branch -M main

# 4. Add remote (replace USERNAME/REPO)
git remote add origin https://github.com/USERNAME/REPO.git

# 5. Push to GitHub
git push -u origin main

# 6. Verify (go to GitHub URL above)
# 7. Run security check one more time
python verify_security.py
```

---

**Ready to publish?** Run `python verify_security.py` and then follow the "Step 4" above!
