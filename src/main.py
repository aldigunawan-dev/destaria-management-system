"""
Main Application Entry Point
Initialize all components and start the backup system
"""

import os
import sys
import logging
import signal
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

import uvicorn
from fastapi import Depends

from .backup.database import DatabaseManager
from .pterodactyl.client import PterodactylClient
from .backup.gdrive_client import GoogleDriveClient
from .backup.backup_manager import BackupManager
from .backup.retention import PerServerRetentionPolicy
from .backup.scheduler import init_scheduler
from .notifications.discord import init_discord_notifier
from .api.main import app


# Load environment variables from .env file
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/app.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


# Global component instances
database_manager: Optional[DatabaseManager] = None
pterodactyl_client: Optional[PterodactylClient] = None
gdrive_client: Optional[GoogleDriveClient] = None
backup_manager: Optional[BackupManager] = None
scheduler = None
notifier = None


def load_yaml_config(config_name: str) -> dict:
    """Load YAML configuration file."""
    config_path = Path("config") / f"{config_name}.yaml"
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return {}
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading {config_path}: {e}")
        return {}


def initialize_components():
    """Initialize all application components."""
    global database_manager, pterodactyl_client, gdrive_client, backup_manager, scheduler, notifier
    
    logger.info("=" * 60)
    logger.info("Initializing Minecraft DevOps Backup System")
    logger.info("=" * 60)
    
    # 1. Initialize Database
    logger.info("📦 Initializing Database Manager...")
    sqlite_db_path = os.getenv("SQLITE_DB_PATH", "/data/devops.db")
    database_manager = DatabaseManager(sqlite_db_path)
    logger.info(f"✅ Database initialized at {sqlite_db_path}")
    
    # 2. Initialize Pterodactyl Client
    logger.info("🦖 Initializing Pterodactyl Client...")
    pterodactyl_url = os.getenv("PTERODACTYL_PANEL_URL")
    pterodactyl_key = os.getenv("PTERODACTYL_API_KEY")
    
    if not pterodactyl_url or not pterodactyl_key:
        logger.error("❌ PTERODACTYL_PANEL_URL or PTERODACTYL_API_KEY not set in .env")
        sys.exit(1)
    
    pterodactyl_client = PterodactylClient(pterodactyl_url, pterodactyl_key)
    logger.info(f"✅ Pterodactyl Client initialized for {pterodactyl_url}")
    
    # 3. Initialize Google Drive Client
    logger.info("☁️ Initializing Google Drive Client...")
    gdrive_credentials = os.getenv("GDRIVE_CREDENTIALS_PATH", "config/google-service-account.json")
    
    if not Path(gdrive_credentials).exists():
        logger.error(f"❌ Google Service Account file not found: {gdrive_credentials}")
        logger.error("Please download it from Google Cloud Console and place it in the config folder")
        sys.exit(1)
    
    gdrive_client = GoogleDriveClient(gdrive_credentials)
    logger.info(f"✅ Google Drive Client initialized with {gdrive_credentials}")
    
    # 4. Initialize Backup Manager
    logger.info("🎯 Initializing Backup Manager...")
    backup_manager = BackupManager(
        database_manager=database_manager,
        pterodactyl_client=pterodactyl_client,
        gdrive_client=gdrive_client
    )
    logger.info("✅ Backup Manager initialized")
    
    # 5. Initialize Discord Notifier (optional)
    logger.info("💬 Initializing Discord Notifier...")
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if discord_webhook:
        notifier = init_discord_notifier(discord_webhook)
        logger.info("✅ Discord Notifier initialized")
    else:
        logger.warning("⚠️ DISCORD_WEBHOOK_URL not set - Discord notifications disabled")
    
    # 6. Initialize and Start Scheduler
    logger.info("⏰ Initializing Backup Scheduler...")
    servers_config = load_yaml_config("servers")
    
    scheduler = init_scheduler(
        backup_manager=backup_manager,
        database_manager=database_manager,
        notifier=notifier,
        max_concurrent=int(os.getenv("MAX_CONCURRENT_BACKUPS", "3"))
    )
    
    # Schedule backup jobs from config
    if servers_config and 'servers' in servers_config:
        try:
            scheduler.load_schedule_from_config(servers_config['servers'])
            logger.info(f"✅ Loaded {len(servers_config['servers'])} backup schedule(s)")
        except Exception as e:
            logger.error(f"❌ Error loading backup schedules: {e}")
    else:
        logger.warning("⚠️ No servers configured in config/servers.yaml")
    
    # 7. Setup Retention Policy (optional)
    logger.info("🧹 Setting up Retention Policy...")
    retention_config = load_yaml_config("retention")
    
    if retention_config and 'retention' in retention_config:
        try:
            for server_id, policy_config in retention_config['retention'].items():
                policy = PerServerRetentionPolicy(
                    server_id=server_id,
                    max_age_days=policy_config.get('max_age_days', 30),
                    max_count_full=policy_config.get('max_count_full', 5),
                    max_count_incremental=policy_config.get('max_count_incremental', 10)
                )
                logger.info(f"  - Server {server_id}: Keep {policy.max_age_days}d or {policy.max_count_full}/{policy.max_count_incremental} backups")
            logger.info("✅ Retention policies configured")
        except Exception as e:
            logger.warning(f"⚠️ Error loading retention policies: {e}")
    else:
        logger.warning("⚠️ No retention policies in config/retention.yaml - using defaults")
    
    # 8. Setup Dependency Injection for FastAPI
    logger.info("🔌 Setting up FastAPI Dependency Injection...")
    
    async def get_backup_manager() -> BackupManager:
        return backup_manager
    
    async def get_database_manager() -> DatabaseManager:
        return database_manager
    
    # Replace the placeholder functions in backup_routes
    from api.routes import backup_routes
    backup_routes.get_backup_manager = Depends(get_backup_manager)
    backup_routes.get_database_manager = Depends(get_database_manager)
    
    logger.info("✅ Dependency injection configured")
    
    # 9. Start Scheduler
    logger.info("🚀 Starting Backup Scheduler...")
    try:
        scheduler.start()
        logger.info("✅ Backup Scheduler started in background")
    except Exception as e:
        logger.error(f"❌ Error starting scheduler: {e}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("✅ All components initialized successfully!")
    logger.info("=" * 60)


def setup_shutdown_handler():
    """Setup graceful shutdown handler."""
    def shutdown_handler(signum, frame):
        logger.info("\n" + "=" * 60)
        logger.info("🛑 Shutdown signal received - cleaning up...")
        logger.info("=" * 60)
        
        # Stop scheduler
        if scheduler:
            try:
                scheduler.stop()
                logger.info("✅ Scheduler stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping scheduler: {e}")
        
        # Close database connections
        if database_manager:
            try:
                database_manager.close()
                logger.info("✅ Database connections closed")
            except Exception as e:
                logger.error(f"❌ Error closing database: {e}")
        
        logger.info("✅ Graceful shutdown complete")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)


def run_server():
    """Start the API server."""
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    logger.info(f"🌐 Starting API Server on {host}:{port}")
    logger.info(f"   📖 API Documentation: http://localhost:{port}/docs")
    logger.info(f"   🔌 API Root: http://localhost:{port}/")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=LOG_LEVEL.lower(),
    )


def main():
    """Main entry point."""
    try:
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Initialize components
        initialize_components()
        
        # Setup shutdown handler
        setup_shutdown_handler()
        
        # Run server
        run_server()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
