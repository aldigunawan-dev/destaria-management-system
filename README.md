# Minecraft Server DevOps Platform

A comprehensive DevOps platform for managing Minecraft servers using the Pterodactyl panel. Currently focused on automated backup management with infrastructure for plugin updates, testing, and deployment.

## 🎯 Project Overview

This platform provides automated management of Minecraft servers with a focus on:

- **Backup System** (Phase 1 - Current Focus)
  - Full and incremental backups
  - Automated backup scheduling
  - Retention policies
  - Google Drive integration (optional)

- **Plugin Management** (Phase 2)
  - Monitor plugin updates from multiple sources (SpigotMC, Modrinth, Hangar, GitHub)
  - Automated plugin deployment
  - Test server validation
  - Discord notifications

- **Configuration Management** (Phase 3)
  - Server configuration version control
  - Configuration rollback
  - Environment management

- **Web Dashboard** (Phase 4)
  - Monitor backup status
  - View plugin updates
  - Manage deployments
  - Configuration management UI

## 📋 Project Structure

```
minecraft-devops-platform/
├── .github/
│   └── workflows/              # GitHub Actions CI/CD
├── src/
│   ├── backup/                 # Backup management system
│   ├── updates/                # Plugin update management
│   │   ├── sources/            # Plugin source clients
│   │   └── deployer.py
│   ├── testing/                # Automated testing
│   ├── pterodactyl/            # Pterodactyl API client
│   ├── notifications/          # Discord & other notifications
│   └── api/                    # FastAPI REST API
├── config/                     # Configuration files
├── tests/                      # Unit tests
├── Dockerfile                  # Docker container
├── docker-compose.yml          # Docker Compose setup
├── requirements.txt            # Python dependencies
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- Pterodactyl Panel with API access
- Google Drive Account (for backups)
- Discord Webhook URL (optional, for notifications)

### Quick Setup

**For detailed setup instructions including credential management, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd minecraft-devops-platform
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup credentials** (see [SETUP_GUIDE.md](SETUP_GUIDE.md))
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (Pterodactyl API key, Google credentials, etc)
   ```

5. **Configure servers**
   ```bash
   # Edit config/servers.yaml with your server details
   # Edit config/plugins.yaml if planning to use plugin updates
   # Edit config/notifications.yaml for Discord settings
   ```

6. **Test connections**
   ```bash
   python -c "
   from dotenv import load_dotenv
   from src.pterodactyl.client import PterodactylClient
   from src.backup.gdrive_client import GoogleDriveClient
   
   load_dotenv()
   ptero = PterodactylClient()
   gdrive = GoogleDriveClient()
   print('✓ All connections successful!')
   "
   ```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f devops-api
```

## 📚 Module Documentation

### Backup System (`src/backup/`)
- **BackupManager**: Handles full and incremental backups via Pterodactyl API
- **RetentionPolicy**: Manages backup lifecycle and cleanup
- **GoogleDriveClient**: Optional cloud backup storage

**Status**: Implementation ready, awaiting code

### Plugin Updates (`src/updates/`)
- **PluginChecker**: Monitors plugin updates from configured sources
- **PluginDeployer**: Deploys plugins to test and production servers
- **Sources**: Clients for SpigotMC, Modrinth, Hangar, and GitHub

**Status**: Scaffold complete, implementation pending

### Testing (`src/testing/`)
- **TestRunner**: Executes automated tests on deployments
- **TestCases**: Plugin compatibility, server startup, command execution tests

**Status**: Framework ready

### Pterodactyl API (`src/pterodactyl/`)
- **PterodactylClient**: Core API client for server management

**Status**: Scaffold ready for implementation

### Notifications (`src/notifications/`)
- **DiscordNotifier**: Sends notifications to Discord webhooks

**Status**: Framework ready

### REST API (`src/api/`)
- **FastAPI**: Modern Python web framework
- **Routes**: Endpoints for backup, update, and deployment operations

**Status**: Basic setup complete

## 🔧 Configuration Files

### `config/servers.yaml`
Define your Minecraft servers and their backup schedules

### `config/plugins.yaml`
List plugins to monitor for updates and configure auto-update behavior

### `config/notifications.yaml`
Configure Discord webhooks and notification preferences

### `.env`
Set sensitive data like API keys (never commit to git)

## 📝 Environment Variables

```bash
PTERODACTYL_API_KEY      # Pterodactyl panel API key
DISCORD_WEBHOOK_URL      # Discord webhook for notifications
BACKUP_STORAGE_PATH      # Where to store backup metadata
BACKUP_RETENTION_DAYS    # Days to keep backups (default: 30)
LOG_LEVEL               # Logging level (INFO, DEBUG, etc.)
```

## 🧪 Testing

Run tests with pytest:

```bash
pytest tests/ -v
pytest tests/ --cov=src  # With coverage report
```

## 📝 Development

### Code Style
- Use Black for formatting: `black src/`
- Use isort for imports: `isort src/`
- Lint with flake8: `flake8 src/`
- Type check with mypy: `mypy src/`

### Git Workflow
1. Create feature branch: `git checkout -b feature/backup-system`
2. Make changes and commit
3. Push and create Pull Request
4. Ensure CI/CD passes

## 🗺️ Roadmap

- [x] Phase 1: Project structure and backup framework
- [ ] Phase 2: Implement full backup system
- [ ] Phase 3: Implement incremental backup system
- [ ] Phase 4: Plugin update monitoring
- [ ] Phase 5: Automated testing system
- [ ] Phase 6: Web dashboard
- [ ] Phase 7: Production deployment

## 🤝 Contributing

Contributions are welcome! Please:
1. Follow the code style guidelines
2. Add tests for new features
3. Update documentation
4. Create descriptive commit messages

## 📄 License

[Specify your license here]

## 📧 Support

For issues, questions, or suggestions, please open an issue on GitHub.

## 🔐 Security Notes

- Never commit `.env` files with real API keys
- Keep Pterodactyl API keys secure
- Use environment variables for sensitive data
- Regularly rotate API keys
- Use HTTPS for all API communications

---

**Status**: Alpha Development - Focus on Backup System Implementation

Last Updated: 2025-12-15
