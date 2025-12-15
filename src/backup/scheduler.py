"""
Backup Scheduler Module
Schedules and manages automated backups using APScheduler and cron expressions.
"""

import logging
from typing import Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import yaml

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job

from src.backup.backup_manager import BackupManager
from src.backup.database import DatabaseManager

logger = logging.getLogger(__name__)


class BackupScheduler:
    """
    Manages automated backup scheduling using APScheduler.
    
    Features:
    - Parse cron expressions from config
    - Schedule backups per server
    - Limit concurrent backups (default: 3)
    - Track job status
    - Error handling and retry logic
    """
    
    def __init__(
        self,
        backup_manager: BackupManager,
        database_manager: DatabaseManager,
        max_concurrent: int = 3,
        timezone: str = "UTC"
    ):
        """
        Initialize backup scheduler.
        
        Args:
            backup_manager: BackupManager instance
            database_manager: DatabaseManager instance
            max_concurrent: Maximum concurrent backups (default: 3)
            timezone: Timezone for cron schedules (default: UTC)
        """
        self.backup_manager = backup_manager
        self.database_manager = database_manager
        self.max_concurrent = max_concurrent
        self.timezone = timezone
        self.logger = logging.getLogger(__name__)
        
        # Create scheduler
        self.scheduler = BackgroundScheduler(timezone=timezone)
        self.jobs: Dict[str, Job] = {}
        
        # Thread executor for concurrent backups
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        
        # Track running backups
        self.running_backups = {}
    
    def load_schedule_from_config(self, config_path: str) -> Dict:
        """
        Load server schedule from YAML config.
        
        Args:
            config_path: Path to servers.yaml config file
            
        Returns:
            Dict with server schedules
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config or 'servers' not in config:
                self.logger.warning(f"No servers found in config: {config_path}")
                return {}
            
            self.logger.info(f"Loaded {len(config['servers'])} servers from config")
            return config
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {config_path}")
            return {}
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing config: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error loading config: {e}")
            return {}
    
    def schedule_servers(self, config_path: str) -> int:
        """
        Schedule all servers from config.
        
        Args:
            config_path: Path to servers.yaml
            
        Returns:
            Number of servers scheduled
        """
        config = self.load_schedule_from_config(config_path)
        
        if not config or 'servers' not in config:
            self.logger.warning("No servers to schedule")
            return 0
        
        scheduled_count = 0
        
        for server in config.get('servers', []):
            if self._schedule_server(server):
                scheduled_count += 1
        
        self.logger.info(f"Scheduled {scheduled_count} servers")
        return scheduled_count
    
    def _schedule_server(self, server: Dict) -> bool:
        """
        Schedule a single server backup.
        
        Args:
            server: Server config dict
            
        Returns:
            True if scheduled successfully
        """
        try:
            server_id = server.get('id')
            server_name = server.get('name')
            backup_schedule = server.get('backup_schedule')
            
            if not server_id or not server_name:
                self.logger.warning(f"Skipping server without id/name: {server}")
                return False
            
            if not backup_schedule:
                self.logger.debug(f"No schedule for server: {server_name}")
                return False
            
            # Parse cron expression
            try:
                cron_trigger = CronTrigger.from_crontab(backup_schedule)
            except Exception as e:
                self.logger.error(f"Invalid cron schedule for {server_name}: {backup_schedule} - {e}")
                return False
            
            # Create job
            job_id = f"backup_{server_id}"
            
            job = self.scheduler.add_job(
                self._backup_wrapper,
                cron_trigger,
                id=job_id,
                name=f"Backup {server_name}",
                args=[server_id, server_name],
                replace_existing=True,
                misfire_grace_time=300,  # 5 minutes grace period
                coalesce=True,  # Don't run multiple missed jobs
            )
            
            self.jobs[job_id] = job
            
            self.logger.info(
                f"Scheduled backup for {server_name} "
                f"(ID: {server_id}) - Cron: {backup_schedule}"
            )
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error scheduling server: {e}")
            return False
    
    def _backup_wrapper(self, server_id: str, server_name: str):
        """
        Wrapper for backup job execution.
        
        Args:
            server_id: Server ID
            server_name: Server name
        """
        try:
            # Check concurrent limit
            if len(self.running_backups) >= self.max_concurrent:
                self.logger.warning(
                    f"Max concurrent backups ({self.max_concurrent}) reached. "
                    f"Skipping backup for {server_name}"
                )
                return
            
            # Track backup
            backup_id = f"{server_id}_{datetime.now().timestamp()}"
            self.running_backups[backup_id] = {
                'server_id': server_id,
                'server_name': server_name,
                'start_time': datetime.now(),
                'status': 'running'
            }
            
            self.logger.info(f"Starting scheduled backup for {server_name}")
            
            # Execute backup
            result = self.backup_manager.full_backup(
                server_id=server_id,
                server_name=server_name,
                progress_callback=self._progress_callback(backup_id)
            )
            
            # Update status
            self.running_backups[backup_id]['status'] = 'completed' if result else 'failed'
            self.running_backups[backup_id]['end_time'] = datetime.now()
            
            if result:
                self.logger.info(f"Scheduled backup completed for {server_name}: {result}")
            else:
                self.logger.error(f"Scheduled backup failed for {server_name}")
        
        except Exception as e:
            self.logger.error(f"Error in backup wrapper: {e}", exc_info=True)
            self.running_backups[backup_id]['status'] = 'error'
            self.running_backups[backup_id]['error'] = str(e)
        
        finally:
            # Remove from running if present
            if backup_id in self.running_backups:
                del self.running_backups[backup_id]
    
    def _progress_callback(self, backup_id: str) -> Callable:
        """
        Create progress callback for backup.
        
        Args:
            backup_id: Backup ID
            
        Returns:
            Callback function
        """
        def callback(current_bytes: int, total_bytes: int):
            if backup_id in self.running_backups:
                if total_bytes > 0:
                    progress = (current_bytes / total_bytes) * 100
                    self.running_backups[backup_id]['progress_percent'] = progress
        
        return callback
    
    def start(self):
        """Start the scheduler."""
        if self.scheduler.running:
            self.logger.warning("Scheduler is already running")
            return
        
        try:
            self.scheduler.start()
            self.logger.info("Backup scheduler started")
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self, wait: bool = True):
        """
        Stop the scheduler.
        
        Args:
            wait: Wait for running jobs to complete
        """
        if not self.scheduler.running:
            self.logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown(wait=wait)
            self.logger.info("Backup scheduler stopped")
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
    
    def pause(self):
        """Pause the scheduler (jobs won't run but scheduler stays alive)."""
        try:
            self.scheduler.pause()
            self.logger.info("Backup scheduler paused")
        except Exception as e:
            self.logger.error(f"Error pausing scheduler: {e}")
    
    def resume(self):
        """Resume the scheduler."""
        try:
            self.scheduler.resume()
            self.logger.info("Backup scheduler resumed")
        except Exception as e:
            self.logger.error(f"Error resuming scheduler: {e}")
    
    def get_jobs(self) -> Dict[str, Job]:
        """
        Get all scheduled jobs.
        
        Returns:
            Dict of job_id -> Job
        """
        return self.jobs
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get status of a specific job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status dict or None
        """
        job = self.jobs.get(job_id)
        
        if not job:
            return None
        
        return {
            'id': job.id,
            'name': job.name,
            'trigger': str(job.trigger),
            'next_run_time': job.next_run_time,
            'enabled': not job.is_paused,
        }
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if removed successfully
        """
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                self.logger.info(f"Removed job: {job_id}")
                return True
            
            self.logger.warning(f"Job not found: {job_id}")
            return False
        
        except Exception as e:
            self.logger.error(f"Error removing job: {e}")
            return False
    
    def get_running_backups(self) -> Dict:
        """
        Get currently running backups.
        
        Returns:
            Dict of running backup status
        """
        return self.running_backups.copy()
    
    def get_scheduler_status(self) -> Dict:
        """
        Get scheduler status.
        
        Returns:
            Status dict
        """
        return {
            'running': self.scheduler.running,
            'paused': self.scheduler._paused if hasattr(self.scheduler, '_paused') else False,
            'jobs_count': len(self.jobs),
            'running_backups_count': len(self.running_backups),
            'max_concurrent': self.max_concurrent,
        }
    
    def __del__(self):
        """Cleanup on destruction."""
        if self.scheduler.running:
            self.stop(wait=True)
        self.executor.shutdown(wait=True)


def init_scheduler(
    backup_manager: BackupManager,
    database_manager: DatabaseManager,
    config_path: str = "config/servers.yaml",
    max_concurrent: int = 3,
) -> BackupScheduler:
    """
    Initialize and start backup scheduler.
    
    Args:
        backup_manager: BackupManager instance
        database_manager: DatabaseManager instance
        config_path: Path to servers.yaml
        max_concurrent: Max concurrent backups
        
    Returns:
        Initialized BackupScheduler instance
    """
    scheduler = BackupScheduler(
        backup_manager=backup_manager,
        database_manager=database_manager,
        max_concurrent=max_concurrent,
    )
    
    scheduler.schedule_servers(config_path)
    scheduler.start()
    
    return scheduler
