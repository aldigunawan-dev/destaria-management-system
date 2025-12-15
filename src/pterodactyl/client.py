"""
Pterodactyl API Client
Handles all interactions with Pterodactyl Panel API v1
"""

import logging
import requests
from typing import Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class PterodactylClient:
    """
    Client for Pterodactyl Panel API v1.
    
    Handles server management, backups, and command execution.
    Includes retry logic and rate limiting handling.
    
    Attributes:
        base_url: Pterodactyl panel base URL
        api_key: Pterodactyl application API key
        session: Requests session with retry strategy
    """
    
    # API rate limiting
    REQUEST_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    RETRY_BACKOFF = 1.0  # seconds
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize Pterodactyl client.
        
        Args:
            base_url: Pterodactyl panel base URL (e.g., https://panel.example.com)
            api_key: Pterodactyl application API key (not client key)
            
        Raises:
            ValueError: If base_url or api_key is empty
        """
        if not base_url or not api_key:
            raise ValueError("base_url and api_key are required")
        
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # Setup session with retry strategy
        self.session = self._create_session()
        self._test_connection()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy."""
        session = requests.Session()
        
        # Retry strategy for transient failures
        # Note: method_whitelist deprecated in urllib3 2.0+, use allowed_methods instead
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=self.RETRY_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"]  # urllib3 2.0+ compatible
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "Application/vnd.pterodactyl.v1+json"
        }
    
    def _test_connection(self):
        """Test API connection and authentication."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/application/servers",
                headers=self._get_headers(),
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            self.logger.info(f"Pterodactyl API connection successful: {self.base_url}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to connect to Pterodactyl API: {e}")
            raise
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None,
                     timeout: int = None) -> Optional[Dict]:
        """
        Make HTTP request to Pterodactyl API with error handling.
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (without base URL)
            data: Request data for POST/PUT
            timeout: Request timeout in seconds
            
        Returns:
            Response JSON or None on error
        """
        url = f"{self.base_url}{endpoint}"
        timeout = timeout or self.REQUEST_TIMEOUT
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                headers=self._get_headers(),
                timeout=timeout
            )
            response.raise_for_status()
            
            # Some endpoints return empty responses
            if response.text:
                return response.json()
            return {"success": True}
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"Resource not found: {endpoint}")
                return None
            self.logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {endpoint}: {e}")
            return None
        except ValueError as e:
            self.logger.error(f"Invalid JSON response from {endpoint}: {e}")
            return None
    
    def get_servers(self) -> List[Dict]:
        """
        Get list of all servers for current user (Client API).
        
        Returns:
            List of server dictionaries with identifier, name, and attributes
        """
        try:
            result = self._make_request("GET", "/api/client")
            
            if not result:
                return []
            
            # API returns paginated results with nested structure
            servers = result.get("data", [])
            self.logger.info(f"Retrieved {len(servers)} servers from Client API")
            
            # Extract relevant fields from nested attributes
            processed_servers = []
            for server in servers:
                if server.get("object") == "server":
                    attrs = server.get("attributes", {})
                    processed_servers.append({
                        "identifier": attrs.get("identifier"),
                        "name": attrs.get("name"),
                        "uuid": attrs.get("uuid"),
                        "internal_id": attrs.get("internal_id"),
                        "node": attrs.get("node"),
                        "attributes": attrs  # Keep full attributes
                    })
            
            self.logger.debug(f"Processed {len(processed_servers)} servers")
            return processed_servers
        
        except Exception as e:
            self.logger.error(f"Error getting servers: {e}")
            return []
    
    def get_server(self, server_id: str) -> Optional[Dict]:
        """
        Get detailed server information (Client API).
        
        Args:
            server_id: Pterodactyl server identifier (not internal_id)
            
        Returns:
            Server dictionary with full details or None
        """
        try:
            result = self._make_request("GET", f"/api/client/servers/{server_id}")
            
            if not result:
                self.logger.warning(f"Server not found: {server_id}")
                return None
            
            server_data = result.get("attributes", result)
            self.logger.debug(f"Retrieved server details: {server_id}")
            
            return server_data
        
        except Exception as e:
            self.logger.error(f"Error getting server {server_id}: {e}")
            return None
    
    def create_backup(self, server_id: str) -> Optional[Dict]:
        """
        Create a backup of the server.
        
        Args:
            server_id: Pterodactyl server ID
            
        Returns:
            Backup info dict with uuid and details, or None on failure
        """
        try:
            # Trigger backup creation using Client API (not Application API)
            result = self._make_request(
                "POST",
                f"/api/client/servers/{server_id}/backups",
                timeout=10
            )
            
            if not result:
                self.logger.error(f"Failed to create backup for server {server_id}")
                return None
            
            backup_data = result.get("attributes", result)
            backup_id = backup_data.get("uuid")
            
            self.logger.info(f"Backup creation triggered: {backup_id} for server {server_id}")
            
            return backup_data
        
        except Exception as e:
            self.logger.error(f"Error creating backup for server {server_id}: {e}")
            return None
    
    def get_backup(self, server_id: str, backup_id: str) -> Optional[Dict]:
        """
        Get backup status and details (Client API).
        
        Args:
            server_id: Pterodactyl server identifier (not internal_id)
            backup_id: Backup UUID
            
        Returns:
            Backup info dict with status, or None
        """
        try:
            result = self._make_request(
                "GET",
                f"/api/client/servers/{server_id}/backups/{backup_id}"
            )
            
            if not result:
                return None
            
            backup_data = result.get("attributes", result)
            
            # Normalize status checking
            is_successful = backup_data.get("completed_at") is not None
            is_failed = backup_data.get("failed_at") is not None
            
            return {
                **backup_data,
                "is_successful": is_successful,
                "is_failed": is_failed
            }
        
        except Exception as e:
            self.logger.error(f"Error getting backup {backup_id}: {e}")
            return None
    
    def get_backup_download_url(self, server_id: str, backup_id: str) -> Optional[str]:
        """
        Get download URL for a backup (Client API).
        
        Args:
            server_id: Pterodactyl server identifier (not internal_id)
            backup_id: Backup UUID
            
        Returns:
            Download URL or None
        """
        try:
            result = self._make_request(
                "GET",
                f"/api/client/servers/{server_id}/backups/{backup_id}/download"
            )
            
            if not result:
                self.logger.warning(f"Could not get download URL for backup {backup_id}")
                return None
            
            # Response format: { "object": "backup_download", "attributes": { "url": "..." } }
            download_url = result.get("attributes", {}).get("url") or result.get("url")
            
            if download_url:
                self.logger.info(f"Download URL obtained for backup {backup_id}")
                return download_url
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting download URL for backup {backup_id}: {e}")
            return None
    
    def list_backups(self, server_id: str, limit: int = 100) -> List[Dict]:
        """
        List all backups for a server (Client API).
        
        Args:
            server_id: Pterodactyl server identifier (not internal_id)
            limit: Maximum number of backups to return
            
        Returns:
            List of backup dicts, or empty list
        """
        try:
            # Add pagination parameter to endpoint
            result = self._make_request(
                "GET",
                f"/api/client/servers/{server_id}/backups?per_page={limit}"
            )
            
            if not result:
                return []
            
            # Response format: { "object": "list", "data": [...], "meta": {...} }
            backups_data = result.get("data", [])
            
            backups = []
            for backup in backups_data:
                backup_attrs = backup.get("attributes", backup)
                
                # Normalize status
                backup_attrs["is_successful"] = backup_attrs.get("completed_at") is not None
                backup_attrs["is_failed"] = backup_attrs.get("failed_at") is not None
                
                backups.append(backup_attrs)
            
            self.logger.info(f"Found {len(backups)} backup(s) for server {server_id}")
            return backups
        
        except Exception as e:
            self.logger.error(f"Error listing backups for server {server_id}: {e}")
            return []
    
    def delete_backup(self, server_id: str, backup_id: str) -> bool:
        """
        Delete a backup (Client API).
        
        Args:
            server_id: Pterodactyl server identifier (not internal_id)
            backup_id: Backup UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._make_request(
                "DELETE",
                f"/api/client/servers/{server_id}/backups/{backup_id}"
            )
            
            if result is None:
                return False
            
            self.logger.info(f"Backup deleted: {backup_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error deleting backup {backup_id}: {e}")
            return False
    
    def send_command(self, server_id: str, command: str) -> bool:
        """
        Send a command to the server console.
        
        Args:
            server_id: Pterodactyl server ID
            command: Command to send (e.g., "say Hello!")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._make_request(
                "POST",
                f"/api/application/servers/{server_id}/command",
                data={"command": command}
            )
            
            if result is None:
                return False
            
            self.logger.debug(f"Command sent to {server_id}: {command}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error sending command to server {server_id}: {e}")
            return False
    
    def get_server_status(self, server_id: str) -> Optional[Dict]:
        """
        Get current server status (online, memory, CPU, etc.).
        
        Args:
            server_id: Pterodactyl server ID
            
        Returns:
            Status dictionary or None
        """
        try:
            result = self._make_request(
                "GET",
                f"/api/client/servers/{server_id}/resources"
            )
            
            if not result:
                return None
            
            status_data = result.get("attributes", result)
            self.logger.debug(f"Server status retrieved: {server_id}")
            
            return status_data
        
        except Exception as e:
            self.logger.error(f"Error getting server status for {server_id}: {e}")
            return None
    
    def start_server(self, server_id: str) -> bool:
        """
        Start the server.
        
        Args:
            server_id: Pterodactyl server ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Application API uses DELETE with signal parameter
            result = self._make_request(
                "POST",
                f"/api/application/servers/{server_id}/power",
                data={"signal": "start"}
            )
            
            if result is None:
                return False
            
            self.logger.info(f"Server start command sent: {server_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error starting server {server_id}: {e}")
            return False
    
    def stop_server(self, server_id: str) -> bool:
        """
        Stop the server gracefully (Application API).
        
        Args:
            server_id: Pterodactyl server ID or identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try with identifier first, then with numeric ID
            endpoints = [
                f"/api/application/servers/{server_id}/power?signal=stop",
                f"/api/application/servers/{server_id}/power"  # With DELETE method
            ]
            
            for endpoint in endpoints:
                result = self._make_request("DELETE", endpoint)
                
                if result is not None:
                    self.logger.info(f"Server stop command sent: {server_id}")
                    return True
            
            self.logger.warning(f"Could not stop server {server_id}")
            return False
        
        except Exception as e:
            self.logger.error(f"Error stopping server {server_id}: {e}")
            return False
    
    def restart_server(self, server_id: str) -> bool:
        """
        Restart the server.
        
        Args:
            server_id: Pterodactyl server ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._make_request(
                "POST",
                f"/api/application/servers/{server_id}/power",
                data={"signal": "restart"}
            )
            
            if result is None:
                return False
            
            self.logger.info(f"Server restart command sent: {server_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error restarting server {server_id}: {e}")
            return False
    
    def restore_backup(self, server_id: str, backup_id: str) -> bool:
        """
        Restore a backup on the server.
        
        Args:
            server_id: Pterodactyl server ID
            backup_id: Backup UUID to restore
            
        Returns:
            True if restore triggered successfully, False otherwise
        """
        try:
            result = self._make_request(
                "POST",
                f"/api/application/servers/{server_id}/backups/{backup_id}/restore",
                timeout=10
            )
            
            if result is None:
                return False
            
            self.logger.info(f"Backup restore triggered: {backup_id} for server {server_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error restoring backup {backup_id}: {e}")
            return False
    
    def close(self):
        """Close session and cleanup resources."""
        if self.session:
            self.session.close()
            self.logger.info("Pterodactyl client session closed")
