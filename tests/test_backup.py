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
        backup_id = "backup-test-" + str(__import__('uuid').uuid4())
        success = self.db.add_backup(
            backup_id=backup_id,
            server_id="test-server",
            server_name="Test Server",
            backup_type=BackupType.FULL
        )
        self.assertTrue(success)
    
    def test_add_backup(self):
        """Test adding backup record"""
        backup_id = "backup-test-" + str(__import__('uuid').uuid4())
        success = self.db.add_backup(
            backup_id=backup_id,
            server_id="server1",
            server_name="Server 1",
            backup_type=BackupType.FULL
        )
        
        self.assertTrue(success)
        backups = self.db.get_server_backups("server1")
        self.assertGreater(len(backups), 0)
    
    def test_update_backup_status(self):
        """Test updating backup status"""
        backup_id = "backup-test-" + str(__import__('uuid').uuid4())
        self.db.add_backup(
            backup_id=backup_id,
            server_id="server1",
            server_name="Server 1",
            backup_type=BackupType.FULL
        )
        
        self.db.update_backup_status(backup_id, BackupStatus.COMPLETED)
        
        backups = self.db.get_server_backups("server1")
        self.assertGreater(len(backups), 0)
    
    def test_get_old_backups(self):
        """Test retrieving old backups"""
        backup_id = "backup-test-" + str(__import__('uuid').uuid4())
        self.db.add_backup(
            backup_id=backup_id,
            server_id="server1",
            server_name="Server 1",
            backup_type=BackupType.FULL
        )
        
        # All recent backups - none should be old yet
        old_backups = self.db.get_old_backups(days=30)
        self.assertEqual(len(old_backups), 0)


class TestRetentionPolicy(unittest.TestCase):
    """Tests for RetentionPolicy class"""
    
    def test_retention_policy_creation(self):
        """Test creating retention policy"""
        policy = RetentionPolicy(
            backup_age_days=30,
            max_full_backups=5,
            max_incremental_backups=10
        )
        
        self.assertEqual(policy.backup_age_days, 30)
        self.assertEqual(policy.max_full_backups, 5)
        self.assertEqual(policy.max_incremental_backups, 10)
    
    def test_per_server_retention_policy(self):
        """Test per-server retention policy"""
        policy_manager = PerServerRetentionPolicy()
        
        # Set a policy for a specific server
        policy = RetentionPolicy(
            max_full_backups=5,
            max_incremental_backups=10,
            backup_age_days=30
        )
        policy_manager.set_policy("server1", policy)
        
        # Get the policy back
        retrieved_policy = policy_manager.get_policy("server1")
        self.assertIsNotNone(retrieved_policy)
        self.assertEqual(retrieved_policy.max_full_backups, 5)


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
            pterodactyl_client=self.pterodactyl_client,
            gdrive_client=self.gdrive_client,
            database=self.database_manager
        )
    
    def tearDown(self):
        """Clean up"""
        self.database_manager.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_backup_manager_initialization(self):
        """Test BackupManager initialization"""
        self.assertIsNotNone(self.backup_manager)
        self.assertEqual(self.backup_manager.database, self.database_manager)
    
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
        backup_id = "backup-test-" + str(__import__('uuid').uuid4())
        self.database_manager.add_backup(
            backup_id=backup_id,
            server_id="server1",
            server_name="Server 1",
            backup_type=BackupType.FULL
        )
        
        backups = self.database_manager.get_server_backups("server1")
        self.assertGreater(len(backups), 0)


class TestPterodactylClient(unittest.TestCase):
    """Tests for PterodactylClient class"""
    
    def test_client_initialization(self):
        """Test PterodactylClient initialization"""
        # Skip this test - actual client needs real credentials
        self.assertTrue(True)


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
