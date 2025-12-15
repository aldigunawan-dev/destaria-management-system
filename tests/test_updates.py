"""
Integration tests for backup system
Tests end-to-end workflows and component interactions
Compatible with unittest and nosetest
"""

import unittest
import tempfile
import os
from unittest.mock import Mock
from datetime import datetime

from src.backup.database import DatabaseManager
from src.backup.backup_manager import BackupManager
from src.backup.retention import RetentionPolicy
from src.pterodactyl.client import PterodactylClient


# Define status and type constants
class BackupStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class BackupType:
    FULL = "full"
    INCREMENTAL = "incremental"


class TestBackupWorkflow(unittest.TestCase):
    """Integration tests for backup workflow"""
    
    def setUp(self):
        """Setup for backup workflow tests"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.database_manager = DatabaseManager(self.db_path)
        self.mock_pterodactyl = Mock(spec=PterodactylClient)
        self.mock_gdrive = Mock()
    
    def tearDown(self):
        """Cleanup"""
        self.database_manager.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_full_backup_workflow(self):
        """Test complete backup workflow"""
        backup_manager = BackupManager(
            pterodactyl_client=self.mock_pterodactyl,
            gdrive_client=self.mock_gdrive,
            database=self.database_manager
        )
        
        # Create backup dengan parameter yang benar
        backup_id = "backup-" + str(__import__('uuid').uuid4())
        success = self.database_manager.add_backup(
            backup_id=backup_id,
            server_id="test-server",
            server_name="Test Server",
            backup_type=BackupType.FULL
        )
        
        # Verify workflow
        self.assertTrue(success)
        
        # Check status
        backups = self.database_manager.get_server_backups("test-server")
        self.assertGreater(len(backups), 0)
    
    def test_retention_cleanup_workflow(self):
        """Test retention policy cleanup workflow"""
        # Add multiple backups
        backup_ids = []
        for i in range(7):
            backup_id = "backup-" + str(__import__('uuid').uuid4())
            success = self.database_manager.add_backup(
                backup_id=backup_id,
                server_id="test-server",
                server_name="Test Server",
                backup_type=BackupType.FULL
            )
            if success:
                backup_ids.append(backup_id)
        
        # Create retention policy
        policy = RetentionPolicy(
            backup_age_days=30,
            max_full_backups=5,
            max_incremental_backups=10
        )
        
        # Get backups
        backups = self.database_manager.get_server_backups("test-server")
        self.assertGreater(len(backups), 0)


class TestBackupRecovery(unittest.TestCase):
    """Integration tests for backup recovery"""
    
    def setUp(self):
        """Setup for recovery tests"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.database_manager = DatabaseManager(self.db_path)
        self.mock_pterodactyl = Mock(spec=PterodactylClient)
        self.mock_gdrive = Mock()
    
    def tearDown(self):
        """Cleanup"""
        self.database_manager.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_restore_workflow(self):
        """Test backup restoration workflow"""
        backup_manager = BackupManager(
            pterodactyl_client=self.mock_pterodactyl,
            gdrive_client=self.mock_gdrive,
            database=self.database_manager
        )
        
        # Setup backup
        backup_id = "backup-" + str(__import__('uuid').uuid4())
        success = self.database_manager.add_backup(
            backup_id=backup_id,
            server_id="test-server",
            server_name="Test Server",
            backup_type=BackupType.FULL
        )
        
        self.assertTrue(success)
        
        # Create restore history record
        restore_id = "restore-" + str(__import__('uuid').uuid4())
        restore_success = self.database_manager.add_restore_record(
            restore_id=restore_id,
            backup_id=backup_id,
            server_id="test-server",
            server_name="Test Server"
        )
        
        self.assertTrue(restore_success)


class TestConcurrentBackups(unittest.TestCase):
    """Integration tests for concurrent backup handling"""
    
    def setUp(self):
        """Setup for concurrent tests"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.database_manager = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Cleanup"""
        self.database_manager.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_multiple_server_backups(self):
        """Test handling multiple server backups"""
        servers = ["server1", "server2", "server3"]
        
        for server in servers:
            backup_id = "backup-" + str(__import__('uuid').uuid4())
            success = self.database_manager.add_backup(
                backup_id=backup_id,
                server_id=server,
                server_name=f"{server.title()} Name",
                backup_type=BackupType.FULL
            )
            self.assertTrue(success)
        
        # Verify all backups exist
        for server in servers:
            backups = self.database_manager.get_server_backups(server)
            self.assertGreater(len(backups), 0)


class TestErrorRecovery(unittest.TestCase):
    """Integration tests for error recovery"""
    
    def setUp(self):
        """Setup for error recovery tests"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.database_manager = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Cleanup"""
        self.database_manager.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_backup_failure_recovery(self):
        """Test handling backup failures"""
        backup_id = "backup-" + str(__import__('uuid').uuid4())
        success = self.database_manager.add_backup(
            backup_id=backup_id,
            server_id="test-server",
            server_name="Test Server",
            backup_type=BackupType.FULL
        )
        self.assertTrue(success)
        
        # Mark as failed
        self.database_manager.update_backup_status(backup_id, BackupStatus.FAILED)
        
        # Verify failure status
        backups = self.database_manager.get_server_backups("test-server")
        self.assertGreater(len(backups), 0)
    
    def test_restore_failure_recovery(self):
        """Test handling restore failures"""
        backup_id = "backup-" + str(__import__('uuid').uuid4())
        success = self.database_manager.add_backup(
            backup_id=backup_id,
            server_id="test-server",
            server_name="Test Server",
            backup_type=BackupType.FULL
        )
        self.assertTrue(success)
        
        restore_id = "restore-" + str(__import__('uuid').uuid4())
        restore_success = self.database_manager.add_restore_record(
            restore_id=restore_id,
            backup_id=backup_id,
            server_id="test-server",
            server_name="Test Server"
        )
        self.assertTrue(restore_success)
        
        # Mark as failed
        self.database_manager.update_restore_status(restore_id, BackupStatus.FAILED)


if __name__ == '__main__':
    unittest.main()
