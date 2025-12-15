"""
Backup Manager
Manages full and incremental backups via Pterodactyl API
"""

import logging
import uuid
import time
import os
from datetime import datetime
from threading import Lock, Thread
from typing import Optional, Dict, Callable

from .database import DatabaseManager

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Manages backup operations for Minecraft servers.
    
    Supports:
    - Full backups via Pterodactyl API
    - Incremental backups with maintenance mode (server stop with warnings)
    - Incremental backup tracking
    - Google Drive uploads
    - Database metadata tracking
    - Progress monitoring
    
    Methods:
    - full_backup(): Full backup while server running
    - incremental_backup(): Incremental backup (full backup with shorter retention)
    - incremental_backup_with_maintenance(): Backup with server maintenance mode
    - restore_backup(): Restore from backup
    
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
    
    def _upload_to_gdrive_async(self, backup_id: str, server_name: str, backup_info: Dict):
        """
        Upload backup to Google Drive asynchronously (background thread).
        
        Note: Pterodactyl stores backups internally. To upload, we would need
        to download first. For now, we store backup metadata on Google Drive.
        """
        try:
            if not self.gdrive_client:
                return None, None
            
            self.logger.info(f"Background: Starting backup metadata upload for {backup_id}")
            
            # Create a metadata JSON file about the backup
            import json
            from io import BytesIO
            
            metadata = {
                "backup_id": backup_id,
                "server_name": server_name,
                "size_bytes": backup_info.get("bytes", 0),
                "created_at": backup_info.get("created_at"),
                "completed_at": backup_info.get("completed_at"),
                "is_successful": backup_info.get("is_successful"),
                "checksum": backup_info.get("checksum"),
                "uploaded_at": datetime.now().isoformat()
            }
            
            # Upload metadata file to Google Drive
            try:
                gdrive_file_id = self.gdrive_client.upload_metadata_file(server_name, backup_id, metadata)
                if gdrive_file_id:
                    self.logger.info(f"Background: Metadata uploaded - {gdrive_file_id}")
                    # Update database dengan Google Drive metadata file ID
                    if self.database:
                        self.database.update_backup_status(
                            backup_id,
                            status="completed",
                            gdrive_file_id=gdrive_file_id
                        )
                    return gdrive_file_id, None
            except Exception as e:
                self.logger.error(f"Failed to upload metadata: {e}")
            
            self.logger.warning(f"Background: Failed to upload metadata for {backup_id}")
            return None, None
        
        except Exception as e:
            self.logger.error(f"Background: Error uploading {backup_id}: {e}")
            return None, None
    
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
            
            # Step 1: Trigger backup on Pterodactyl (with retry on rate limit)
            start_time = time.time()
            backup_info = None
            max_retries = 5
            retry_delay = 5  # Start with 5 seconds
            
            for attempt in range(max_retries):
                backup_info = self.pterodactyl_client.create_backup(server_id)
                
                if backup_info:
                    break
                
                if attempt < max_retries - 1:
                    self.logger.warning(f"Backup trigger failed, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                    self._update_progress(job_id, 5, f"Retrying backup (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)  # Exponential backoff, max 60s
            
            if not backup_info:
                raise Exception("Failed to trigger backup on Pterodactyl after multiple retries")
            
            pterodactyl_backup_id = backup_info.get("uuid")
            self.logger.info(f"Pterodactyl backup created: {pterodactyl_backup_id}")
            self._update_progress(job_id, 15, "Waiting for backup completion")
            
            # Step 2: Poll for backup completion
            # Timeout: max 10 minutes (600 seconds) for backup to complete
            POLL_INTERVAL = 10  # Check every 10 seconds
            MAX_WAIT_TIME = 600  # 10 minutes max
            max_iterations = MAX_WAIT_TIME // POLL_INTERVAL
            
            backup_completed = False
            for iteration in range(max_iterations):
                time.sleep(POLL_INTERVAL)
                
                backup_status = self.pterodactyl_client.get_backup(
                    server_id, pterodactyl_backup_id
                )
                
                if not backup_status:
                    self.logger.warning("Backup status unavailable, retrying...")
                    continue
                
                elapsed = (iteration + 1) * POLL_INTERVAL
                progress_percent = 15 + min(60, (elapsed / MAX_WAIT_TIME) * 60)  # 15% to 75%
                self._update_progress(job_id, int(progress_percent), 
                                    f"Backup in progress ({elapsed}s elapsed)")
                
                # Debug: Log the backup status
                self.logger.debug(f"Poll #{iteration}: Status={backup_status.get('is_successful')}, "
                                f"completed_at={backup_status.get('completed_at')}, "
                                f"failed_at={backup_status.get('failed_at')}")
                
                if backup_status.get("is_successful"):
                    backup_completed = True
                    self.logger.info(f"Backup completed after {elapsed} seconds")
                    break
                elif backup_status.get("is_failed"):
                    raise Exception(f"Backup failed on Pterodactyl: {backup_status}")
            
            if not backup_completed:
                raise Exception(f"Backup timeout after {MAX_WAIT_TIME} seconds")
            
            # Get final backup size
            backup_size = backup_info.get("bytes", 0)
            self.logger.info(f"Backup completed. Size: {backup_size / (1024**3):.2f} GB")
            
            # Step 3: Update database with initial completion (no gdrive info yet)
            self.database.update_backup_status(
                backup_id,
                status="completed",
                size_bytes=backup_size
            )
            
            # Step 4: Upload to Google Drive (BACKGROUND THREAD)
            # Non-blocking, database already updated
            if self.gdrive_client:
                self.logger.info(f"Starting background Google Drive upload for {backup_id}")
                self._update_progress(job_id, 85, "Google Drive upload in background")
                
                # Start upload in background thread
                upload_thread = Thread(
                    target=self._upload_to_gdrive_async,
                    args=(backup_id, server_name, backup_info),
                    daemon=True
                )
                upload_thread.start()
                self.logger.info(f"Background upload thread started for {backup_id}")
            
            # Step 5: Update final status
            duration = int(time.time() - start_time)
            
            self._update_progress(job_id, 100, "Backup completed (Google Drive upload in background)")
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
    
    def incremental_backup_with_maintenance(self, server_id: str, server_name: str,
                                           retention_days: int = 7) -> Optional[str]:
        """
        Incremental backup dengan server maintenance mode.
        
        Strategy:
        1. Send warning message 5 menit sebelum server stop
        2. Countdown messages setiap menit
        3. Stop server gracefully
        4. Perform full backup (safe ketika server stopped)
        5. Start server kembali
        6. Send online message
        
        Ideal untuk backup tengah malam saat players offline.
        
        Args:
            server_id: Pterodactyl server ID
            server_name: Server name
            retention_days: Retention period (default 7 hari untuk incremental)
        
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
                                            "incremental", retention_days):
                self.logger.error(f"Failed to create backup record: {backup_id}")
                return None
            
            # Create job tracking
            if not self.database.create_backup_job(job_id, backup_id, server_id):
                self.logger.error(f"Failed to create backup job: {job_id}")
                return None
            
            self.logger.info(f"Starting incremental backup with maintenance: {backup_id}")
            
            start_time = time.time()
            
            # PHASE 1: Warning countdown (5 minutes)
            self.logger.info(f"Sending shutdown warnings to {server_name}")
            self._update_progress(job_id, 5, "Sending server warnings")
            
            # Send initial warning: 5 menit
            self.pterodactyl_client.send_command(
                server_id,
                "say [System] Server akan di-restart dalam 5 menit untuk backup"
            )
            time.sleep(60)
            
            # Send warning: 4 menit
            self.pterodactyl_client.send_command(
                server_id,
                "say [System] Server akan di-restart dalam 4 menit"
            )
            time.sleep(60)
            
            # Send warning: 3 menit
            self.pterodactyl_client.send_command(
                server_id,
                "say [System] Server akan di-restart dalam 3 menit"
            )
            time.sleep(60)
            
            # Send warning: 2 menit
            self.pterodactyl_client.send_command(
                server_id,
                "say [System] Server akan di-restart dalam 2 menit"
            )
            time.sleep(60)
            
            # Send warning: 1 menit
            self.pterodactyl_client.send_command(
                server_id,
                "say [System] Server akan di-restart dalam 1 menit"
            )
            time.sleep(30)
            
            # Final warning: 30 detik
            self.pterodactyl_client.send_command(
                server_id,
                "say [System] Server restart sekarang!"
            )
            time.sleep(30)
            
            # PHASE 2: Stop server gracefully
            self.logger.info(f"Stopping server {server_name}")
            self._update_progress(job_id, 15, "Stopping server")
            
            if not self.pterodactyl_client.stop_server(server_id):
                raise Exception(f"Failed to stop server {server_id}")
            
            # Wait untuk server fully shutdown
            time.sleep(5)
            self.logger.info(f"Server {server_name} stopped successfully")
            self._update_progress(job_id, 20, "Server stopped, starting backup")
            
            # PHASE 3: Perform backup (server is now stopped - SAFE!)
            self.logger.info(f"Starting backup for {server_name} (server offline)")
            self._update_progress(job_id, 25, "Triggering backup")
            
            backup_info = self.pterodactyl_client.create_backup(server_id)
            
            if not backup_info:
                raise Exception("Failed to trigger backup on Pterodactyl")
            
            pterodactyl_backup_id = backup_info.get("uuid")
            self.logger.info(f"Pterodactyl backup created: {pterodactyl_backup_id}")
            self._update_progress(job_id, 30, "Waiting for backup completion")
            
            # Poll untuk completion
            timeout = self._calculate_timeout(estimated_size_gb=40)
            max_iterations = timeout // 30
            backup_completed = False
            
            for iteration in range(max_iterations):
                time.sleep(30)
                
                backup_status = self.pterodactyl_client.get_backup(
                    server_id, pterodactyl_backup_id
                )
                
                if not backup_status:
                    raise Exception("Backup status unavailable")
                
                progress_percent = 30 + (iteration / max_iterations) * 50  # 30% to 80%
                self._update_progress(job_id, int(progress_percent),
                                    f"Backup in progress ({iteration * 30}s)")
                
                if backup_status.get("is_successful"):
                    backup_completed = True
                    break
                elif backup_status.get("is_failed"):
                    raise Exception(f"Backup failed on Pterodactyl")
            
            if not backup_completed:
                raise Exception(f"Backup timeout after {timeout} seconds")
            
            # Get backup info
            backup_size = backup_info.get("bytes", 0)
            self.logger.info(f"Backup completed. Size: {backup_size / (1024**3):.2f} GB")
            
            # PHASE 4: Start server IMMEDIATELY (don't wait for Google Drive)
            self.logger.info(f"Starting server {server_name} immediately after backup")
            self._update_progress(job_id, 85, "Starting server (Google Drive upload in background)")
            
            if not self.pterodactyl_client.start_server(server_id):
                self.logger.error(f"Failed to start server {server_id}")
                # Retry once more
                time.sleep(5)
                if not self.pterodactyl_client.start_server(server_id):
                    raise Exception(f"Failed to start server {server_id}")
            
            # Wait untuk server fully online
            time.sleep(5)
            self.logger.info(f"Server {server_name} started successfully")
            
            # Send online message
            self.pterodactyl_client.send_command(
                server_id,
                "say [System] Server backup selesai. Selamat bermain!"
            )
            
            # PHASE 5: Upload to Google Drive (BACKGROUND THREAD)
            # This happens after server is online, so players can join immediately
            gdrive_file_id = None
            gdrive_url = None
            
            if self.gdrive_client:
                self.logger.info(f"Starting background Google Drive upload for {backup_id}")
                self._update_progress(job_id, 90, "Server online, Google Drive upload in background")
                
                # Start upload in background thread
                upload_thread = Thread(
                    target=self._upload_to_gdrive_async,
                    args=(backup_id, server_name, backup_info),
                    daemon=True
                )
                upload_thread.start()
                self.logger.info(f"Background upload thread started for {backup_id}")
            
            # PHASE 6: Update database with backup completion
            duration = int(time.time() - start_time)
            
            # Update status (might be updated again by background thread with gdrive info)
            if not self.database.update_backup_status(
                backup_id,
                status="completed",
                size_bytes=backup_size,
                gdrive_file_id=gdrive_file_id,
                gdrive_file_url=gdrive_url
            ):
                self.logger.error("Failed to update backup status to completed")
                return None
            
            self._update_progress(job_id, 100, "Backup completed, server online")
            self.logger.info(f"Incremental backup with maintenance completed: {backup_id} ({duration}s)")
            
            return backup_id
        
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Incremental backup with maintenance failed: {error_msg}")
            
            # Update database with error
            self.database.update_backup_status(backup_id, status="failed",
                                              error_message=error_msg)
            self.database.update_backup_job(job_id, status="failed",
                                           error_message=error_msg)
            
            # EMERGENCY: Ensure server is started
            try:
                self.logger.error("EMERGENCY: Attempting to restart server after failure")
                self.pterodactyl_client.start_server(server_id)
                time.sleep(5)
                self.pterodactyl_client.send_command(
                    server_id,
                    "say [System] Emergency restart completed. Backup failed."
                )
            except Exception as restart_error:
                self.logger.critical(f"CRITICAL: Failed to restart server after backup failure: {restart_error}")
            
            return None
        
        finally:
            lock.release()
    
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
