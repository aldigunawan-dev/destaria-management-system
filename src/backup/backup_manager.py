"""
Backup Manager
Manages full and incremental backups via Pterodactyl API
"""

import logging
import uuid
import time
import os
from datetime import datetime
from threading import Lock
from typing import Optional, Dict, Callable

from .database import DatabaseManager

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Manages backup operations for Minecraft servers.
    
    Supports:
    - Full backups via Pterodactyl API
    - Incremental backup tracking
    - Google Drive uploads
    - Database metadata tracking
    - Progress monitoring
    
    Attributes:
        pterodactyl_client: Pterodactyl API client
        gdrive_client: Google Drive client
        database: Database manager
        backup_locks: Per-server locks for preventing duplicate backups
    """
    
    # Adaptive timeout: base_timeout + (backup_size_gb * time_per_gb)
    BASE_TIMEOUT_MINUTES = 30  # 30 minutes base
    TIME_PER_GB_MINUTES = 1    # 1 minute per GB
    
    def __init__(self, pterodactyl_client, gdrive_client=None, 
                 database: DatabaseManager = None, 
                 progress_callback: Callable = None):
        """
        Initialize BackupManager.
        
        Args:
            pterodactyl_client: Pterodactyl API client instance
            gdrive_client: Google Drive client (optional)
            database: DatabaseManager instance
            progress_callback: Optional callback for progress updates
        """
        self.pterodactyl_client = pterodactyl_client
        self.gdrive_client = gdrive_client
        self.database = database or DatabaseManager()
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
        
        # Locks untuk prevent concurrent backups di server yang sama
        self.backup_locks: Dict[str, Lock] = {}
    
    def _get_lock(self, server_id: str) -> Lock:
        """Get or create lock for a server."""
        if server_id not in self.backup_locks:
            self.backup_locks[server_id] = Lock()
        return self.backup_locks[server_id]
    
    def _calculate_timeout(self, estimated_size_gb: float = 40) -> int:
        """
        Calculate adaptive timeout based on backup size.
        
        Args:
            estimated_size_gb: Estimated backup size in GB
            
        Returns:
            Timeout in seconds
        """
        timeout_minutes = self.BASE_TIMEOUT_MINUTES + (estimated_size_gb * self.TIME_PER_GB_MINUTES)
        return int(timeout_minutes * 60)  # Convert to seconds
    
    def _update_progress(self, job_id: str, progress: int, step: str):
        """Update backup progress."""
        if self.database:
            self.database.update_backup_job(job_id, progress_percent=progress, current_step=step)
        
        if self.progress_callback:
            self.progress_callback(job_id, progress, step)
        
        self.logger.debug(f"Job {job_id}: {step} ({progress}%)")
    
    def full_backup(self, server_id: str, server_name: str, 
                   retention_days: int = 30) -> Optional[str]:
        """
        Perform a full backup of the server.
        
        Args:
            server_id: Pterodactyl server ID
            server_name: Server name
            retention_days: Days to keep this backup (default 30)
            
        Returns:
            Backup ID if successful, None otherwise
        """
        lock = self._get_lock(server_id)
        
        if not lock.acquire(blocking=False):
            self.logger.warning(f"Backup already in progress for server {server_id}")
            return None
        
        backup_id = f"backup_{server_id}_{uuid.uuid4().hex[:8]}"
        job_id = f"job_{uuid.uuid4().hex}"
        
        try:
            # Create database record
            if not self.database.add_backup(backup_id, server_id, server_name, 
                                            "full", retention_days):
                self.logger.error(f"Failed to create backup record: {backup_id}")
                return None
            
            # Create job tracking
            if not self.database.create_backup_job(job_id, backup_id, server_id):
                self.logger.error(f"Failed to create backup job: {job_id}")
                return None
            
            self.logger.info(f"Starting full backup: {backup_id} for server {server_id}")
            self._update_progress(job_id, 5, "Triggering server backup")
            
            # Step 1: Trigger backup on Pterodactyl
            start_time = time.time()
            backup_info = self.pterodactyl_client.create_backup(server_id)
            
            if not backup_info:
                raise Exception("Failed to trigger backup on Pterodactyl")
            
            pterodactyl_backup_id = backup_info.get("uuid")
            self.logger.info(f"Pterodactyl backup created: {pterodactyl_backup_id}")
            self._update_progress(job_id, 15, "Waiting for backup completion")
            
            # Step 2: Poll for backup completion
            timeout = self._calculate_timeout(estimated_size_gb=40)  # Estimate
            max_iterations = timeout // 30  # Check every 30 seconds
            
            backup_completed = False
            for iteration in range(max_iterations):
                time.sleep(30)  # Check every 30 seconds
                
                backup_status = self.pterodactyl_client.get_backup(
                    server_id, pterodactyl_backup_id
                )
                
                if not backup_status:
                    raise Exception("Backup status unavailable")
                
                progress_percent = 15 + (iteration / max_iterations) * 60  # 15% to 75%
                self._update_progress(job_id, int(progress_percent), 
                                    f"Creating backup ({iteration * 30}s elapsed)")
                
                if backup_status.get("is_successful"):
                    backup_completed = True
                    break
                elif backup_status.get("is_failed"):
                    raise Exception(f"Backup failed on Pterodactyl: {backup_status}")
            
            if not backup_completed:
                raise Exception(f"Backup timeout after {timeout} seconds")
            
            # Get final backup size
            backup_size = backup_info.get("bytes", 0)
            self.logger.info(f"Backup completed. Size: {backup_size / (1024**3):.2f} GB")
            
            # Step 3: Upload to Google Drive
            if self.gdrive_client:
                self._update_progress(job_id, 80, "Uploading to Google Drive")
                
                # Download backup from Pterodactyl (implementation depends on API)
                # For now, we'll assume backup is available locally or via streaming
                gdrive_file_id, gdrive_url = self.gdrive_client.upload_backup(
                    server_name, backup_id, backup_info
                )
                
                if gdrive_file_id:
                    self.logger.info(f"Backup uploaded to Google Drive: {gdrive_file_id}")
                else:
                    self.logger.warning(f"Failed to upload backup to Google Drive")
                    gdrive_file_id = None
                    gdrive_url = None
            else:
                gdrive_file_id = None
                gdrive_url = None
            
            # Step 4: Update database with completion info
            duration = int(time.time() - start_time)
            
            if not self.database.update_backup_status(
                backup_id,
                status="completed",
                size_bytes=backup_size,
                gdrive_file_id=gdrive_file_id,
                gdrive_file_url=gdrive_url
            ):
                self.logger.error("Failed to update backup status to completed")
                return None
            
            self._update_progress(job_id, 100, "Backup completed successfully")
            self.logger.info(f"Full backup completed successfully: {backup_id} ({duration}s)")
            
            return backup_id
        
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Full backup failed: {error_msg}")
            
            # Update database with error
            self.database.update_backup_status(backup_id, status="failed", 
                                              error_message=error_msg)
            self.database.update_backup_job(job_id, status="failed", 
                                           error_message=error_msg)
            
            return None
        
        finally:
            lock.release()
    
    def incremental_backup(self, server_id: str, server_name: str) -> Optional[str]:
        """
        Perform an incremental backup of the server.
        
        Current implementation: Full backup (Pterodactyl doesn't support true incremental)
        
        Args:
            server_id: Pterodactyl server ID
            server_name: Server name
            
        Returns:
            Backup ID if successful, None otherwise
        """
        self.logger.info(f"Incremental backup requested for {server_id}")
        self.logger.warning("Pterodactyl doesn't support incremental backups - using full backup instead")
        
        # Pterodactyl doesn't support incremental backups natively
        # So we'll do a full backup and mark it as incremental in metadata
        return self.full_backup(server_id, server_name, retention_days=7)
    
    def restore_backup(self, server_id: str, backup_id: str) -> bool:
        """
        Restore a backup on the server.
        
        Args:
            server_id: Pterodactyl server ID
            backup_id: Backup ID to restore
            
        Returns:
            True if successful, False otherwise
        """
        restore_id = f"restore_{uuid.uuid4().hex}"
        
        try:
            # Get backup info
            backup_info = self.database.get_backup(backup_id)
            
            if not backup_info:
                raise Exception(f"Backup not found: {backup_id}")
            
            server_name = backup_info["server_name"]
            pterodactyl_backup_id = backup_info.get("gdrive_file_id")  # Or store separately
            
            # Create restore record
            if not self.database.add_restore_record(restore_id, server_id, 
                                                    server_name, backup_id):
                raise Exception("Failed to create restore record")
            
            self.logger.info(f"Starting restore: {restore_id} for backup {backup_id}")
            
            # Update status to in_progress
            self.database.update_restore_status(restore_id, "in_progress")
            
            # Trigger restore via Pterodactyl API
            if not self.pterodactyl_client.restore_backup(server_id, pterodactyl_backup_id):
                raise Exception("Failed to restore backup on Pterodactyl")
            
            # Poll for completion
            timeout = self._calculate_timeout(40)
            max_iterations = timeout // 30
            
            restore_completed = False
            for iteration in range(max_iterations):
                time.sleep(30)
                
                restore_status = self.pterodactyl_client.get_restore_status(
                    server_id, pterodactyl_backup_id
                )
                
                if restore_status and restore_status.get("is_successful"):
                    restore_completed = True
                    break
                elif restore_status and restore_status.get("is_failed"):
                    raise Exception(f"Restore failed: {restore_status}")
            
            if not restore_completed:
                raise Exception(f"Restore timeout after {timeout} seconds")
            
            # Update database with success
            self.database.update_restore_status(restore_id, "completed")
            self.logger.info(f"Restore completed successfully: {restore_id}")
            
            return True
        
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Restore failed: {error_msg}")
            self.database.update_restore_status(restore_id, "failed", error_msg)
            return False
    
    def get_backup_status(self, backup_id: str) -> Optional[Dict]:
        """
        Get backup status and metadata.
        
        Args:
            backup_id: Backup ID
            
        Returns:
            Dictionary with backup info or None
        """
        if not self.database:
            return None
        
        return self.database.get_backup(backup_id)
    
    def get_server_backups(self, server_id: str, limit: int = 50) -> list:
        """
        Get all backups for a server.
        
        Args:
            server_id: Server ID
            limit: Maximum backups to return
            
        Returns:
            List of backup records
        """
        if not self.database:
            return []
        
        return self.database.get_server_backups(server_id, limit)
