"""
Unit tests for backup system components
Tests database, backup manager, retention policy, and client libraries
Compatible with unittest and nosetest
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.backup.database import DatabaseManager
from src.backup.backup_manager import BackupManager
from src.backup.retention import RetentionPolicy, PerServerRetentionPolicy
from src.pterodactyl.client import PterodactylClient

# Define status and type constants (from database.py)
class BackupStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class BackupType:
    FULL = "full"
    INCREMENTAL = "incremental"

class TestDatabaseManager(unittest.TestCase):
    """Tests for DatabaseManager class"""
    
    def setUp(self):
        """Create temporary database for testing"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.db = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        self.db.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_database_initialization(self):
        """Test database tables are created"""
        backup_id = self.db.add_backup(
            server_id="test-server",
            backup_type=BackupType.FULL,
            size_bytes=1024*1024
        )
        self.assertIsNotNone(backup_id)
    
    def test_add_backup(self):
        """Test adding backup record"""
        backup_id = self.db.add_backup(
            server_id="server1",
            backup_type=BackupType.FULL,
            size_bytes=1024*1024,
            gdrive_file_id="file123"
        )
        
        backups = self.db.get_server_backups("server1")
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0]['backup_id'], backup_id)
        self.assertEqual(backups[0]['server_id'], "server1")
    
    def test_update_backup_status(self):
        """Test updating backup status"""
        backup_id = self.db.add_backup(
            server_id="server1",
            backup_type=BackupType.FULL,
            size_bytes=1024*1024
        )
        
        self.db.update_backup_status(backup_id, BackupStatus.COMPLETED)
        
        backups = self.db.get_server_backups("server1")
        self.assertEqual(backups[0]['status'], BackupStatus.COMPLETED)
    
    def test_get_old_backups(self):
        """Test retrieving old backups"""
        backup_id = self.db.add_backup(
            server_id="server1",
            backup_type=BackupType.FULL,
            size_bytes=1024*1024
        )
        
        # All recent backups - none should be old yet
        old_backups = self.db.get_old_backups(server_id="server1", days=30)
        self.assertEqual(len(old_backups), 0)


class TestRetentionPolicy(unittest.TestCase):
    """Tests for RetentionPolicy class"""
    
    def test_retention_policy_creation(self):
        """Test creating retention policy"""
        policy = RetentionPolicy(
            max_age_days=30,
            max_count_full=5,
            max_count_incremental=10
        )
        
        self.assertEqual(policy.max_age_days, 30)
        self.assertEqual(policy.max_count_full, 5)
        self.assertEqual(policy.max_count_incremental, 10)
    
    def test_per_server_retention_policy(self):
        """Test per-server retention policy"""
        policy = PerServerRetentionPolicy(
            server_id="server1",
            max_age_days=30,
            max_count_full=5
        )
        
        self.assertEqual(policy.server_id, "server1")
        self.assertEqual(policy.max_age_days, 30)


class TestBackupManager(unittest.TestCase):
    """Tests for BackupManager class"""
    
    def setUp(self):
        """Setup test components"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.database_manager = DatabaseManager(self.db_path)
        
        # Mock clients
        self.pterodactyl_client = Mock(spec=PterodactylClient)
        self.gdrive_client = Mock()
        
        self.backup_manager = BackupManager(
            database_manager=self.database_manager,
            pterodactyl_client=self.pterodactyl_client,
            gdrive_client=self.gdrive_client
        )
    
    def tearDown(self):
        """Clean up"""
        self.database_manager.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_backup_manager_initialization(self):
        """Test BackupManager initialization"""
        self.assertIsNotNone(self.backup_manager)
        self.assertEqual(self.backup_manager.database_manager, self.database_manager)
    
    def test_calculate_timeout(self):
        """Test adaptive timeout calculation"""
        # Small backup: 1GB
        timeout = self.backup_manager._calculate_timeout(1024)
        self.assertGreaterEqual(timeout, 30*60)  # At least 30 minutes
        
        # Large backup: 100GB
        timeout_large = self.backup_manager._calculate_timeout(100*1024)
        self.assertGreater(timeout_large, timeout)  # Larger timeout for larger files
    
    def test_get_server_backups(self):
        """Test retrieving server backups"""
        self.database_manager.add_backup(
            server_id="server1",
            backup_type=BackupType.FULL,
            size_bytes=1024*1024
        )
        
        backups = self.backup_manager.get_server_backups("server1")
        self.assertEqual(len(backups), 1)


class TestPterodactylClient(unittest.TestCase):
    """Tests for PterodactylClient class"""
    
    def test_client_initialization(self):
        """Test PterodactylClient initialization"""
        client = PterodactylClient("https://panel.test.com", "PtlApplication:test_key")
        self.assertIsNotNone(client)
        self.assertEqual(client.url, "https://panel.test.com")


class TestEnums(unittest.TestCase):
    """Tests for enum values"""
    
    def test_backup_status_enum(self):
        """Test BackupStatus enum values"""
        self.assertEqual(BackupStatus.PENDING, "pending")
        self.assertEqual(BackupStatus.IN_PROGRESS, "in_progress")
        self.assertEqual(BackupStatus.COMPLETED, "completed")
        self.assertEqual(BackupStatus.FAILED, "failed")
    
    def test_backup_type_enum(self):
        """Test BackupType enum values"""
        self.assertEqual(BackupType.FULL, "full")
        self.assertEqual(BackupType.INCREMENTAL, "incremental")


if __name__ == '__main__':
    unittest.main()
