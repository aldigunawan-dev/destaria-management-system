"""
Discord Notifications Module
Sends rich notifications to Discord webhooks with backup status and details.
"""

import logging
import requests
from datetime import datetime
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """
    Sends messages and notifications to Discord via webhooks.
    
    Features:
    - Rich embed messages with formatting
    - Backup status notifications
    - Progress tracking
    - Error alerts with stack traces
    """
    
    def __init__(self, webhook_url: str):
        """
        Initialize Discord notifier.
        
        Args:
            webhook_url: Discord webhook URL
            
        Raises:
            ValueError: If webhook_url is None or empty
        """
        if not webhook_url:
            raise ValueError("Discord webhook URL cannot be empty")
        
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)
    
    def send_message(self, content: str = None, embed: Dict = None) -> bool:
        """
        Send a message to Discord.
        
        Args:
            content: Plain text message content (optional)
            embed: Discord embed dict (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {}
            
            if content:
                payload['content'] = content
            
            if embed:
                payload['embeds'] = [embed]
            
            if not payload:
                self.logger.warning("No content or embed provided")
                return False
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                self.logger.debug("Message sent to Discord")
                return True
            else:
                self.logger.error(
                    f"Discord webhook returned {response.status_code}: {response.text}"
                )
                return False
        
        except requests.exceptions.Timeout:
            self.logger.error("Discord webhook request timed out")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Discord webhook request failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending Discord message: {e}")
            return False
    
    def send_backup_started(self, server_name: str, server_id: str) -> bool:
        """
        Send notification that backup has started.
        
        Args:
            server_name: Server name
            server_id: Server ID
            
        Returns:
            True if successful
        """
        embed = {
            "title": "🔄 Backup Started",
            "description": f"Backup process initiated for **{server_name}**",
            "color": 3447003,  # Blue
            "fields": [
                {"name": "Server", "value": server_name, "inline": True},
                {"name": "Server ID", "value": server_id, "inline": True},
                {"name": "Time", "value": datetime.now().isoformat(), "inline": False},
            ],
            "footer": {"text": "Minecraft DevOps Backup System"}
        }
        
        return self.send_message(embed=embed)
    
    def send_backup_completed(
        self,
        server_name: str,
        server_id: str,
        backup_id: str,
        file_size_bytes: int,
        duration_seconds: float,
        gdrive_url: str = None
    ) -> bool:
        """
        Send notification that backup has completed successfully.
        
        Args:
            server_name: Server name
            server_id: Server ID
            backup_id: Backup ID
            file_size_bytes: Backup file size in bytes
            duration_seconds: Backup duration in seconds
            gdrive_url: Google Drive file URL (optional)
            
        Returns:
            True if successful
        """
        # Format size
        size_mb = file_size_bytes / (1024 * 1024)
        if size_mb > 1024:
            size_str = f"{size_mb / 1024:.2f} GB"
        else:
            size_str = f"{size_mb:.2f} MB"
        
        # Format duration
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        duration_str = f"{minutes}m {seconds}s"
        
        fields = [
            {"name": "Server", "value": server_name, "inline": True},
            {"name": "Status", "value": "✅ Success", "inline": True},
            {"name": "Backup ID", "value": backup_id, "inline": False},
            {"name": "File Size", "value": size_str, "inline": True},
            {"name": "Duration", "value": duration_str, "inline": True},
        ]
        
        if gdrive_url:
            fields.append({
                "name": "Google Drive",
                "value": f"[View Backup]({gdrive_url})",
                "inline": False
            })
        
        embed = {
            "title": "✅ Backup Completed",
            "description": f"Backup completed successfully for **{server_name}**",
            "color": 3066993,  # Green
            "fields": fields,
            "footer": {"text": "Minecraft DevOps Backup System"},
            "timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(embed=embed)
    
    def send_backup_failed(
        self,
        server_name: str,
        server_id: str,
        error_message: str,
        error_trace: str = None
    ) -> bool:
        """
        Send notification that backup failed.
        
        Args:
            server_name: Server name
            server_id: Server ID
            error_message: Error message
            error_trace: Full error traceback (optional)
            
        Returns:
            True if successful
        """
        fields = [
            {"name": "Server", "value": server_name, "inline": True},
            {"name": "Status", "value": "❌ Failed", "inline": True},
            {"name": "Error", "value": error_message, "inline": False},
        ]
        
        # Add traceback if available (truncate if too long)
        if error_trace:
            if len(error_trace) > 1024:
                error_trace = error_trace[:1021] + "..."
            fields.append({
                "name": "Traceback",
                "value": f"```{error_trace}```",
                "inline": False
            })
        
        embed = {
            "title": "❌ Backup Failed",
            "description": f"Backup failed for **{server_name}**",
            "color": 15158332,  # Red
            "fields": fields,
            "footer": {"text": "Minecraft DevOps Backup System"},
            "timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(embed=embed)
    
    def send_backup_progress(
        self,
        server_name: str,
        progress_percent: int,
        current_mb: int = None,
        total_mb: int = None
    ) -> bool:
        """
        Send backup progress update.
        
        Args:
            server_name: Server name
            progress_percent: Progress percentage (0-100)
            current_mb: Current bytes processed (optional)
            total_mb: Total bytes to process (optional)
            
        Returns:
            True if successful
        """
        # Create progress bar
        bar_length = 20
        filled = int(bar_length * progress_percent / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        fields = [
            {"name": "Server", "value": server_name, "inline": True},
            {"name": "Progress", "value": f"{progress_percent}%", "inline": True},
            {"name": "Progress Bar", "value": f"`{bar}`", "inline": False},
        ]
        
        if current_mb and total_mb:
            fields.append({
                "name": "Size",
                "value": f"{current_mb:.0f} MB / {total_mb:.0f} MB",
                "inline": False
            })
        
        embed = {
            "title": "📊 Backup Progress",
            "description": f"Uploading backup for **{server_name}**",
            "color": 10181046,  # Orange
            "fields": fields,
            "footer": {"text": "Minecraft DevOps Backup System"}
        }
        
        return self.send_message(embed=embed)
    
    def send_retention_cleanup(
        self,
        server_name: str,
        deleted_count: int,
        freed_space_mb: float,
        failed_count: int = 0
    ) -> bool:
        """
        Send notification about retention cleanup.
        
        Args:
            server_name: Server name
            deleted_count: Number of backups deleted
            freed_space_mb: Space freed in MB
            failed_count: Number of failed deletions (optional)
            
        Returns:
            True if successful
        """
        fields = [
            {"name": "Server", "value": server_name, "inline": True},
            {"name": "Deleted", "value": str(deleted_count), "inline": True},
            {"name": "Space Freed", "value": f"{freed_space_mb:.2f} MB", "inline": True},
        ]
        
        if failed_count > 0:
            fields.append({
                "name": "Failed Deletions",
                "value": str(failed_count),
                "inline": True
            })
        
        embed = {
            "title": "🧹 Retention Cleanup Completed",
            "description": f"Old backups removed for **{server_name}**",
            "color": 9807270,  # Purple
            "fields": fields,
            "footer": {"text": "Minecraft DevOps Backup System"},
            "timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(embed=embed)
    
    def send_restore_started(
        self,
        server_name: str,
        backup_id: str
    ) -> bool:
        """
        Send notification that restore has started.
        
        Args:
            server_name: Server name
            backup_id: Backup ID being restored
            
        Returns:
            True if successful
        """
        embed = {
            "title": "♻️ Restore Started",
            "description": f"Restoring backup on **{server_name}**",
            "color": 10181046,  # Orange
            "fields": [
                {"name": "Server", "value": server_name, "inline": True},
                {"name": "Backup ID", "value": backup_id, "inline": True},
                {"name": "Time", "value": datetime.now().isoformat(), "inline": False},
            ],
            "footer": {"text": "Minecraft DevOps Backup System"}
        }
        
        return self.send_message(embed=embed)
    
    def send_restore_completed(
        self,
        server_name: str,
        backup_id: str,
        duration_seconds: float
    ) -> bool:
        """
        Send notification that restore completed successfully.
        
        Args:
            server_name: Server name
            backup_id: Backup ID that was restored
            duration_seconds: Restore duration in seconds
            
        Returns:
            True if successful
        """
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        duration_str = f"{minutes}m {seconds}s"
        
        embed = {
            "title": "✅ Restore Completed",
            "description": f"Backup restored successfully on **{server_name}**",
            "color": 3066993,  # Green
            "fields": [
                {"name": "Server", "value": server_name, "inline": True},
                {"name": "Duration", "value": duration_str, "inline": True},
                {"name": "Backup ID", "value": backup_id, "inline": False},
            ],
            "footer": {"text": "Minecraft DevOps Backup System"},
            "timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(embed=embed)
    
    def send_restore_failed(
        self,
        server_name: str,
        backup_id: str,
        error_message: str
    ) -> bool:
        """
        Send notification that restore failed.
        
        Args:
            server_name: Server name
            backup_id: Backup ID
            error_message: Error message
            
        Returns:
            True if successful
        """
        embed = {
            "title": "❌ Restore Failed",
            "description": f"Restore failed on **{server_name}**",
            "color": 15158332,  # Red
            "fields": [
                {"name": "Server", "value": server_name, "inline": True},
                {"name": "Backup ID", "value": backup_id, "inline": True},
                {"name": "Error", "value": error_message, "inline": False},
            ],
            "footer": {"text": "Minecraft DevOps Backup System"},
            "timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(embed=embed)
    
    def send_system_status(
        self,
        status: str,
        message: str,
        running_backups: int = 0,
        scheduled_jobs: int = 0
    ) -> bool:
        """
        Send system status notification.
        
        Args:
            status: System status (running, paused, error)
            message: Status message
            running_backups: Number of running backups
            scheduled_jobs: Number of scheduled jobs
            
        Returns:
            True if successful
        """
        color_map = {
            'running': 3066993,  # Green
            'paused': 10181046,  # Orange
            'error': 15158332,  # Red
        }
        
        fields = [
            {"name": "Status", "value": status, "inline": True},
            {"name": "Message", "value": message, "inline": False},
        ]
        
        if running_backups >= 0:
            fields.append({
                "name": "Running Backups",
                "value": str(running_backups),
                "inline": True
            })
        
        if scheduled_jobs >= 0:
            fields.append({
                "name": "Scheduled Jobs",
                "value": str(scheduled_jobs),
                "inline": True
            })
        
        embed = {
            "title": "📋 System Status",
            "description": "Backup System Status Update",
            "color": color_map.get(status, 0),
            "fields": fields,
            "footer": {"text": "Minecraft DevOps Backup System"},
            "timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(embed=embed)


def init_discord_notifier(webhook_url: str = None) -> Optional[DiscordNotifier]:
    """
    Initialize Discord notifier from environment or parameter.
    
    Args:
        webhook_url: Discord webhook URL (uses env var if not provided)
        
    Returns:
        DiscordNotifier instance or None if no webhook configured
    """
    if not webhook_url:
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        logger.warning("Discord webhook not configured - notifications disabled")
        return None
    
    try:
        return DiscordNotifier(webhook_url)
    except Exception as e:
        logger.error(f"Failed to initialize Discord notifier: {e}")
        return None
