# DEVELOPMENT GUIDE

## 📋 Project Structure Summary

```
minecraft-devops-platform/
├── .github/
│   └── workflows/              # CI/CD workflows (GitHub Actions)
│       ├── deploy.yml         # (To be created)
│       ├── test.yml           # (To be created)
│       └── README.md          # Workflow documentation
│
├── src/                        # Main source code
│   ├── __init__.py            # Package initialization
│   │
│   ├── backup/                # Phase 1: Backup System
│   │   ├── __init__.py
│   │   ├── backup_manager.py  # Main backup logic
│   │   ├── retention.py       # Backup retention policies
│   │   └── gdrive_client.py   # Google Drive integration (optional)
│   │
│   ├── updates/               # Phase 2: Plugin Updates
│   │   ├── __init__.py
│   │   ├── plugin_checker.py  # Monitor plugin updates
│   │   ├── deployer.py        # Deploy plugins
│   │   └── sources/           # Plugin source clients
│   │       ├── __init__.py
│   │       ├── spigot.py      # SpigotMC API
│   │       ├── modrinth.py    # Modrinth API
│   │       ├── hangar.py      # Hangar/PaperMC API
│   │       └── github.py      # GitHub releases
│   │
│   ├── testing/               # Phase 3: Automated Testing
│   │   ├── __init__.py
│   │   ├── test_runner.py     # Test execution
│   │   └── test_cases.py      # Test definitions
│   │
│   ├── pterodactyl/           # Pterodactyl API Client
│   │   ├── __init__.py
│   │   └── client.py          # Core API client
│   │
│   ├── notifications/         # Notifications
│   │   ├── __init__.py
│   │   └── discord.py         # Discord webhooks
│   │
│   ├── api/                   # FastAPI REST API
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app
│   │   └── routes/            # API endpoints
│   │       └── __init__.py
│   │
│   └── utils/                 # Utilities
│       └── __init__.py
│
├── config/                    # Configuration files
│   ├── servers.yaml           # Server definitions
│   ├── plugins.yaml           # Plugin configuration
│   ├── notifications.yaml     # Notification settings
│   └── README.md              # Config documentation
│
├── tests/                     # Unit tests
│   ├── test_backup.py         # Backup tests
│   ├── test_updates.py        # Update tests
│   └── test_deployment.py     # Deployment tests
│
├── logs/                      # Log files (created at runtime)
│   └── .gitkeep
│
├── docs/                      # Documentation (optional)
│   └── .gitkeep
│
├── dashboard/                 # Phase 4: Web Dashboard (optional)
│   ├── src/                   # Frontend source
│   ├── public/                # Static assets
│   └── package.json           # Node.js dependencies
│
├── .github/                   # GitHub configuration
│   └── copilot-instructions.md
│
├── .gitignore                 # Git ignore rules
├── .env.example               # Environment variables template
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Docker Compose setup
├── requirements.txt           # Python dependencies
└── README.md                  # Main documentation
```

## 🚀 Next Steps

### Phase 1: Backup System (Current Focus)

1. **BackupManager Implementation**
   - Pterodactyl API integration
   - Full backup logic
   - Incremental backup logic
   - Restore functionality

2. **RetentionPolicy Implementation**
   - Cleanup old backups
   - Policy enforcement

3. **GoogleDriveClient Implementation (Optional)**
   - Upload backups to Google Drive
   - Download backup restoration

### Phase 2: Plugin Updates

1. Implement plugin source clients (SpigotMC, Modrinth, Hangar, GitHub)
2. Complete PluginChecker
3. Complete PluginDeployer

### Phase 3: Automated Testing

1. Implement TestRunner
2. Create specific TestCase implementations
3. Integration with deployment workflow

### Phase 4: Web Dashboard

1. Set up React/Vue.js frontend
2. Create dashboard UI
3. API integration

## 🛠️ Development Workflow

### 1. Setup Environment

```bash
# Clone and navigate
cd minecraft-devops-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure .env
cp .env.example .env
# Edit .env with your credentials
```

### 2. Development

```bash
# Edit code in src/

# Run tests
pytest tests/ -v

# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/
```

### 3. Run Locally

#### Option A: Direct Python
```bash
# Set environment
export PYTHONPATH=.

# Run API
uvicorn src.api.main:app --reload --port 8000
```

#### Option B: Docker
```bash
# Build
docker build -t minecraft-devops:latest .

# Run
docker run -p 8000:8000 --env-file .env minecraft-devops:latest
```

#### Option C: Docker Compose
```bash
# Up
docker-compose up -d

# Down
docker-compose down

# Logs
docker-compose logs -f devops-api
```

### 4. Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_backup.py -v

# Coverage report
pytest tests/ --cov=src --cov-report=html
```

### 5. Code Quality

```bash
# Format
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

## 📝 File Template

When creating new modules, use this template:

```python
"""
Module Name
Brief description
"""

import logging

logger = logging.getLogger(__name__)


class YourClass:
    """
    Class description.
    
    Attributes:
        attr1: Description
        attr2: Description
    """
    
    def __init__(self, param1, param2=None):
        """
        Initialize YourClass.
        
        Args:
            param1: Parameter description
            param2: Optional parameter
        """
        self.param1 = param1
        self.param2 = param2
    
    def your_method(self, arg1) -> bool:
        """
        Method description.
        
        Args:
            arg1: Argument description
            
        Returns:
            Return value description
        """
        # TODO: Implement logic
        pass
```

## 🔧 Configuration Management

### servers.yaml
- Pterodactyl server IDs
- Backup schedules (cron format)
- Backup strategies

### plugins.yaml
- Plugin names and sources
- Version tracking
- Auto-update settings

### notifications.yaml
- Discord webhook URLs
- Event filtering
- Notification levels

## 📦 Dependencies

Key packages:
- **FastAPI**: Web framework
- **python-dotenv**: Environment variable management
- **PyYAML**: Configuration file parsing
- **requests**: HTTP client for APIs
- **schedule**: Task scheduling
- **pytest**: Testing framework

See `requirements.txt` for complete list.

## 🐳 Docker

### Build
```bash
docker build -t minecraft-devops:latest .
```

### Run
```bash
docker run -p 8000:8000 \
  -e PTERODACTYL_API_KEY=your_key \
  -e DISCORD_WEBHOOK_URL=your_webhook \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  minecraft-devops:latest
```

### Compose
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## 🐛 Troubleshooting

### Import Errors
- Ensure `PYTHONPATH` includes project root
- Install dependencies: `pip install -r requirements.txt`

### Pterodactyl Connection
- Verify API key is correct
- Check panel URL is accessible
- Review API documentation

### Discord Notifications
- Validate webhook URL
- Check Discord permissions
- Test webhook manually

## 📚 Resources

- [Pterodactyl API Docs](https://pterodactyl.io/api/overview.html)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [PyYAML Docs](https://pyyaml.org/)
- [Python Logging](https://docs.python.org/3/library/logging.html)

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/backup-system`
2. Make changes and test
3. Format code: `black` + `isort`
4. Lint: `flake8` + `mypy`
5. Write/update tests
6. Commit with clear messages
7. Push and create PR

## ✅ Checklist for New Features

- [ ] Create module/class skeleton
- [ ] Add docstrings
- [ ] Create test file
- [ ] Implement logic with TODO markers
- [ ] Write unit tests
- [ ] Format code
- [ ] Pass all tests
- [ ] Update documentation
- [ ] Create PR with description

---

**Happy Coding!** 🎮

For questions or issues, refer to README.md or check the GitHub issues.
