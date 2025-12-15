"""
Backup Retention Policy
Manages backup lifecycle and automatic cleanup based on policies
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Optional

logger = logging.getLogger(__name__)


class RetentionPolicy:
    """
    Manages backup retention policies and cleanup.
    
    Features:
    - Age-based retention (days)
    - Count-based retention (max backups to keep)
    - Per-server policies
    - Automatic cleanup scheduling
    
    Attributes:
        max_full_backups: Maximum number of full backups to keep per server
        max_incremental_backups: Maximum incremental backups per full backup
        backup_age_days: Maximum age of backups in days
    """
    
    def __init__(self, max_full_backups: int = 5, 
                 max_incremental_backups: int = 10,
                 backup_age_days: int = 30):
        """
        Initialize RetentionPolicy.
        
        Args:
            max_full_backups: Maximum full backups to keep (default: 5)
            max_incremental_backups: Maximum incremental per full (default: 10)
            backup_age_days: Maximum backup age in days (default: 30)
        """
        self.max_full_backups = max_full_backups
        self.max_incremental_backups = max_incremental_backups
        self.backup_age_days = backup_age_days
        self.logger = logging.getLogger(__name__)
    
    def should_delete_backup(self, backup_created_at: datetime) -> bool:
        """
        Check if a backup should be deleted based on age policy.
        
        Args:
            backup_created_at: Creation timestamp of the backup
            
        Returns:
            True if backup should be deleted (too old), False otherwise
        """
        if not isinstance(backup_created_at, datetime):
            try:
                backup_created_at = datetime.fromisoformat(str(backup_created_at))
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid date format: {backup_created_at}")
                return False
        
        age = datetime.now() - backup_created_at
        max_age = timedelta(days=self.backup_age_days)
        
        should_delete = age > max_age
        
        if should_delete:
            days_old = age.days
            self.logger.info(f"Backup is {days_old} days old - exceeds {self.backup_age_days} day limit")
        
        return should_delete
    
    def get_backups_to_delete(self, all_backups: List[Dict], 
                              server_id: str = None) -> List[Dict]:
        """
        Determine which backups should be deleted based on policies.
        
        Applies both age-based and count-based retention rules.
        
        Args:
            all_backups: List of backup dictionaries with 'created_at' field
            server_id: Optional server ID to filter backups
            
        Returns:
            List of backup dictionaries that should be deleted
        """
        if not all_backups:
            return []
        
        backups_to_delete = []
        
        # Filter by server if specified
        if server_id:
            backups = [b for b in all_backups if b.get('server_id') == server_id]
        else:
            backups = all_backups
        
        # Sort by creation time (newest first)
        sorted_backups = sorted(
            backups,
            key=lambda b: b.get('created_at', ''),
            reverse=True
        )
        
        # Apply age-based retention
        for backup in sorted_backups:
            if self.should_delete_backup(backup.get('created_at')):
                backups_to_delete.append(backup)
            else:
                break  # Backups are sorted newest first
        
        # Apply count-based retention
        # Keep only max_full_backups
        full_backups = [b for b in sorted_backups 
                       if b.get('backup_type') == 'full']
        
        if len(full_backups) > self.max_full_backups:
            excess_full = full_backups[self.max_full_backups:]
            for backup in excess_full:
                if backup not in backups_to_delete:
                    backups_to_delete.append(backup)
                    self.logger.info(f"Backup exceeds max count policy: {backup.get('id')}")
        
        return backups_to_delete
    
    def cleanup_old_backups(self, all_backups: List[Dict], 
                           delete_callback: Callable[[str], bool] = None,
                           server_id: str = None) -> Dict[str, int]:
        """
        Execute cleanup of old backups based on retention policy.
        
        Args:
            all_backups: List of all backup dictionaries
            delete_callback: Callback function to actually delete backups (backup_id) -> bool
            server_id: Optional filter by server
            
        Returns:
            Dictionary with cleanup statistics
            {
                'total_backups': int,
                'deleted': int,
                'failed': int,
                'skipped': int,
                'freed_space_bytes': int
            }
        """
        stats = {
            'total_backups': len(all_backups),
            'deleted': 0,
            'failed': 0,
            'skipped': 0,
            'freed_space_bytes': 0
        }
        
        if not all_backups:
            self.logger.info("No backups to cleanup")
            return stats
        
        backups_to_delete = self.get_backups_to_delete(all_backups, server_id)
        
        if not backups_to_delete:
            self.logger.info("No backups meet deletion criteria")
            return stats
        
        self.logger.info(f"Cleanup: {len(backups_to_delete)} backups eligible for deletion")
        
        for backup in backups_to_delete:
            backup_id = backup.get('id')
            backup_size = backup.get('size_bytes', 0)
            
            try:
                # Call delete callback if provided
                if delete_callback:
                    success = delete_callback(backup_id)
                else:
                    # Default: just log
                    success = True
                
                if success:
                    stats['deleted'] += 1
                    stats['freed_space_bytes'] += backup_size
                    self.logger.info(
                        f"Deleted backup: {backup_id} "
                        f"({backup_size / (1024**3):.2f} GB)"
                    )
                else:
                    stats['failed'] += 1
                    self.logger.warning(f"Failed to delete backup: {backup_id}")
            
            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"Error deleting backup {backup_id}: {e}")
        
        # Log summary
        freed_gb = stats['freed_space_bytes'] / (1024**3)
        self.logger.info(
            f"Cleanup completed: "
            f"deleted={stats['deleted']}, "
            f"failed={stats['failed']}, "
            f"freed={freed_gb:.2f}GB"
        )
        
        return stats
    
    def get_policy_summary(self) -> Dict[str, any]:
        """
        Get summary of current retention policy.
        
        Returns:
            Dictionary describing the policy
        """
        return {
            'max_full_backups': self.max_full_backups,
            'max_incremental_backups': self.max_incremental_backups,
            'backup_age_days': self.backup_age_days,
            'description': (
                f"Keep up to {self.max_full_backups} full backups "
                f"and {self.max_incremental_backups} incremental backups, "
                f"delete backups older than {self.backup_age_days} days"
            )
        }


class PerServerRetentionPolicy:
    """
    Per-server retention policies with individual configurations.
    """
    
    def __init__(self):
        """Initialize per-server policies."""
        self.policies: Dict[str, RetentionPolicy] = {}
        self.default_policy = RetentionPolicy()
        self.logger = logging.getLogger(__name__)
    
    def set_policy(self, server_id: str, policy: RetentionPolicy):
        """
        Set retention policy for a specific server.
        
        Args:
            server_id: Server ID
            policy: RetentionPolicy instance
        """
        self.policies[server_id] = policy
        self.logger.info(f"Set retention policy for server: {server_id}")
    
    def get_policy(self, server_id: str) -> RetentionPolicy:
        """
        Get retention policy for a server (or default).
        
        Args:
            server_id: Server ID
            
        Returns:
            RetentionPolicy instance
        """
        return self.policies.get(server_id, self.default_policy)
    
    def cleanup_server_backups(self, server_id: str, all_backups: List[Dict],
                              delete_callback: Callable = None) -> Dict:
        """
        Cleanup backups for a specific server using its policy.
        
        Args:
            server_id: Server ID
            all_backups: List of all backups
            delete_callback: Callback to execute deletions
            
        Returns:
            Cleanup statistics
        """
        policy = self.get_policy(server_id)
        return policy.cleanup_old_backups(all_backups, delete_callback, server_id)
