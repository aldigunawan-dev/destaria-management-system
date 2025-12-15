"""
Database Module
SQLite database setup and schema for backup tracking
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database for backup tracking.
    
    Tables:
        - backups: Backup metadata and history
        - backup_jobs: Active/completed backup job tracking
        - restore_history: Restore operation history
    """
    
    def __init__(self, db_path: str = "/data/devops.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._ensure_db_directory()
        self._create_connection()
        self._create_tables()
    
    def _ensure_db_directory(self):
        """Create database directory if it doesn't exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Database directory ready: {db_dir}")
    
    def _create_connection(self):
        """Create connection pool."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.logger.info(f"Database connected: {self.db_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Database connection error: {e}")
            raise
    
    def _create_tables(self):
        """Create all required tables if they don't exist."""
        cursor = self.conn.cursor()
        
        try:
            # Backups table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    id TEXT PRIMARY KEY,
                    server_id TEXT NOT NULL,
                    server_name TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    size_bytes INTEGER,
                    compressed_size_bytes INTEGER,
                    duration_seconds INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    gdrive_file_id TEXT,
                    gdrive_file_url TEXT,
                    error_message TEXT,
                    retention_days INTEGER DEFAULT 30,
                    compressed BOOLEAN DEFAULT 0
                )
            """)
            
            # Backup jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_jobs (
                    job_id TEXT PRIMARY KEY,
                    backup_id TEXT NOT NULL,
                    server_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    progress_percent INTEGER DEFAULT 0,
                    current_step TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    estimated_completion TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (backup_id) REFERENCES backups(id)
                )
            """)
            
            # Restore history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS restore_history (
                    id TEXT PRIMARY KEY,
                    server_id TEXT NOT NULL,
                    server_name TEXT NOT NULL,
                    backup_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration_seconds INTEGER,
                    error_message TEXT,
                    FOREIGN KEY (backup_id) REFERENCES backups(id)
                )
            """)
            
            # Create indices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_backups_server_id 
                ON backups(server_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_backups_created_at 
                ON backups(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_backup_jobs_server_id 
                ON backup_jobs(server_id)
            """)
            
            self.conn.commit()
            self.logger.info("Database tables initialized successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating tables: {e}")
            raise
    
    def add_backup(self, backup_id: str, server_id: str, server_name: str,
                   backup_type: str, retention_days: int = 30) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO backups 
                (id, server_id, server_name, backup_type, status, retention_days)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (backup_id, server_id, server_name, backup_type, "pending", retention_days))
            self.conn.commit()
            self.logger.info(f"Backup record created: {backup_id}")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error adding backup: {e}")
            return False
    
    def update_backup_status(self, backup_id: str, status: str, 
                            size_bytes: int = None, 
                            gdrive_file_id: str = None,
                            gdrive_file_url: str = None,
                            error_message: str = None) -> bool:
        cursor = self.conn.cursor()
        try:
            if status == "completed":
                cursor.execute("""
                    UPDATE backups 
                    SET status = ?, size_bytes = ?, completed_at = CURRENT_TIMESTAMP,
                        gdrive_file_id = ?, gdrive_file_url = ?
                    WHERE id = ?
                """, (status, size_bytes, gdrive_file_id, gdrive_file_url, backup_id))
            elif status == "failed":
                cursor.execute("""
                    UPDATE backups 
                    SET status = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, error_message, backup_id))
            else:
                cursor.execute("""
                    UPDATE backups 
                    SET status = ?
                    WHERE id = ?
                """, (status, backup_id))
            
            self.conn.commit()
            self.logger.info(f"Backup status updated: {backup_id}  {status}")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error updating backup status: {e}")
            return False
    
    def create_backup_job(self, job_id: str, backup_id: str, 
                         server_id: str) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO backup_jobs 
                (job_id, backup_id, server_id, status, progress_percent, current_step)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (job_id, backup_id, server_id, "running", 0, "starting"))
            self.conn.commit()
            self.logger.info(f"Backup job created: {job_id}")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error creating backup job: {e}")
            return False
    
    def update_backup_job(self, job_id: str, progress_percent: int = None,
                         current_step: str = None, status: str = None,
                         error_message: str = None) -> bool:
        cursor = self.conn.cursor()
        try:
            update_fields = []
            params = []
            
            if progress_percent is not None:
                update_fields.append("progress_percent = ?")
                params.append(progress_percent)
            if current_step is not None:
                update_fields.append("current_step = ?")
                params.append(current_step)
            if status is not None:
                update_fields.append("status = ?")
                params.append(status)
            if error_message is not None:
                update_fields.append("error_message = ?")
                params.append(error_message)
            
            if update_fields:
                params.append(job_id)
                query = f"UPDATE backup_jobs SET {', '.join(update_fields)} WHERE job_id = ?"
                cursor.execute(query, params)
                self.conn.commit()
                self.logger.debug(f"Job updated: {job_id}")
                return True
            return False
        except sqlite3.Error as e:
            self.logger.error(f"Error updating backup job: {e}")
            return False
    
    def get_backup(self, backup_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM backups WHERE id = ?", (backup_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting backup: {e}")
            return None
    
    def get_server_backups(self, server_id: str, limit: int = 50) -> List[Dict]:
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM backups 
                WHERE server_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (server_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting server backups: {e}")
            return []
    
    def get_old_backups(self, days: int = 30) -> List[Dict]:
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM backups 
                WHERE created_at < datetime('now', '-' || retention_days || ' days')
                AND status = 'completed'
                ORDER BY created_at ASC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting old backups: {e}")
            return []
    
    def delete_backup_record(self, backup_id: str) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM backups WHERE id = ?", (backup_id,))
            self.conn.commit()
            self.logger.info(f"Backup record deleted: {backup_id}")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting backup record: {e}")
            return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM backup_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting job status: {e}")
            return None
    
    def add_restore_record(self, restore_id: str, server_id: str, 
                          server_name: str, backup_id: str) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO restore_history 
                (id, server_id, server_name, backup_id, status)
                VALUES (?, ?, ?, ?, ?)
            """, (restore_id, server_id, server_name, backup_id, "pending"))
            self.conn.commit()
            self.logger.info(f"Restore record created: {restore_id}")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error adding restore record: {e}")
            return False
    
    def update_restore_status(self, restore_id: str, status: str,
                             error_message: str = None) -> bool:
        cursor = self.conn.cursor()
        try:
            if status == "completed":
                cursor.execute("""
                    UPDATE restore_history 
                    SET status = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, restore_id))
            elif status == "failed":
                cursor.execute("""
                    UPDATE restore_history 
                    SET status = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, error_message, restore_id))
            else:
                cursor.execute("""
                    UPDATE restore_history 
                    SET status = ?
                    WHERE id = ?
                """, (status, restore_id))
            
            self.conn.commit()
            self.logger.info(f"Restore status updated: {restore_id}  {status}")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error updating restore status: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.close()


def init_database(db_path: str = "/data/devops.db") -> DatabaseManager:
    """Initialize and return database manager."""
    return DatabaseManager(db_path)
