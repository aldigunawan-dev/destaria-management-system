"""
Google Drive Client
Handles backup uploads to Google Drive using Service Account
"""

import logging
import os
import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Callable
from datetime import datetime
import io

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload

logger = logging.getLogger(__name__)


class GoogleDriveClient:
    """
    Client for uploading/managing backups on Google Drive.
    
    Features:
    - Service Account authentication
    - Resumable uploads for large files (40GB+)
    - Chunk-based upload with progress tracking
    - Automatic folder structure creation
    - File listing and deletion
    
    Attributes:
        drive_service: Google Drive API service instance
        folder_id: Minecraft-Backups folder ID
    """
    
    # Upload configuration
    SCOPES = ['https://www.googleapis.com/auth/drive']
    CHUNK_SIZE = 256 * 1024 * 1024  # 256 MB chunks for large files
    
    def __init__(self, credentials_path: str, folder_name: str = "Minecraft-Backups",
                 progress_callback: Callable = None):
        """
        Initialize Google Drive client.
        
        Args:
            credentials_path: Path to Google Service Account JSON credentials
            folder_name: Name of backup folder in Google Drive
            progress_callback: Optional callback for upload progress (callback(progress_percent))
            
        Raises:
            FileNotFoundError: If credentials file doesn't exist
            GoogleAuthError: If authentication fails
        """
        self.credentials_path = credentials_path
        self.folder_name = folder_name
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
        
        # Verify credentials file exists
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
        
        # Authenticate and build service
        try:
            self.credentials = self._load_credentials()
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            self.logger.info("Google Drive client initialized")
        except GoogleAuthError as e:
            self.logger.error(f"Google authentication failed: {e}")
            raise
        
        # Get or create Minecraft-Backups folder
        self.folder_id = self._get_or_create_folder(folder_name)
        if not self.folder_id:
            raise RuntimeError(f"Failed to get/create folder: {folder_name}")
    
    def _load_credentials(self) -> Credentials:
        """
        Load service account credentials from JSON file.
        
        Returns:
            Credentials object for Google Drive API
            
        Raises:
            GoogleAuthError: If credentials are invalid
        """
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self.logger.info(f"Service account credentials loaded: {self.credentials_path}")
            return credentials
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {e}")
            raise GoogleAuthError(f"Invalid credentials: {e}")
    
    def _execute_request(self, request, request_name: str = "request") -> Optional[Dict]:
        """
        Execute API request with error handling.
        
        Args:
            request: Google API request object
            request_name: Name for logging
            
        Returns:
            Response data or None on error
        """
        try:
            response = request.execute()
            return response
        except HttpError as e:
            if e.resp.status == 404:
                self.logger.warning(f"{request_name} not found")
                return None
            self.logger.error(f"HTTP error in {request_name}: {e.resp.status} - {e.content}")
            return None
        except Exception as e:
            self.logger.error(f"Error executing {request_name}: {e}")
            return None
    
    def _get_or_create_folder(self, folder_name: str) -> Optional[str]:
        """
        Get folder ID or create if doesn't exist.
        
        Args:
            folder_name: Name of folder to find/create
            
        Returns:
            Folder ID or None
        """
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            request = self.drive_service.files().list(
                q=query,
                spaces='drive',
                pageSize=1,
                fields='files(id, name)'
            )
            
            response = self._execute_request(request, f"Search folder '{folder_name}'")
            
            if response and response.get('files'):
                folder_id = response['files'][0]['id']
                self.logger.info(f"Found existing folder: {folder_name} ({folder_id})")
                return folder_id
            
            # Create folder if not found
            self.logger.info(f"Creating new folder: {folder_name}")
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            request = self.drive_service.files().create(
                body=file_metadata,
                fields='id'
            )
            
            response = self._execute_request(request, f"Create folder '{folder_name}'")
            
            if response:
                folder_id = response['id']
                self.logger.info(f"Folder created: {folder_name} ({folder_id})")
                return folder_id
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting/creating folder: {e}")
            return None
    
    def _ensure_subfolder(self, parent_id: str, subfolder_name: str) -> Optional[str]:
        """
        Get or create subfolder under parent folder.
        
        Args:
            parent_id: Parent folder ID
            subfolder_name: Subfolder name
            
        Returns:
            Subfolder ID or None
        """
        try:
            query = f"name='{subfolder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false and '{parent_id}' in parents"
            request = self.drive_service.files().list(
                q=query,
                spaces='drive',
                pageSize=1,
                fields='files(id)'
            )
            
            response = self._execute_request(request, f"Search subfolder '{subfolder_name}'")
            
            if response and response.get('files'):
                return response['files'][0]['id']
            
            # Create subfolder
            file_metadata = {
                'name': subfolder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            request = self.drive_service.files().create(
                body=file_metadata,
                fields='id'
            )
            
            response = self._execute_request(request, f"Create subfolder '{subfolder_name}'")
            
            if response:
                return response['id']
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error managing subfolder: {e}")
            return None
    
    def upload_backup(self, server_name: str, backup_id: str, 
                     file_path: str, file_size: int = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Upload backup file to Google Drive using resumable upload.
        
        Supports large files (40GB+) with chunked upload and progress tracking.
        Folder structure: Minecraft-Backups/{server_name}/{YYYY-MM-DD}/
        
        Args:
            server_name: Server name
            backup_id: Backup ID
            file_path: Path to backup file
            file_size: File size in bytes (for progress tracking)
            
        Returns:
            Tuple of (file_id, file_url) or (None, None) on failure
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Backup file not found: {file_path}")
            
            if not file_size:
                file_size = os.path.getsize(file_path)
            
            # Create folder structure: server_name / date
            date_folder = datetime.now().strftime("%Y-%m-%d")
            
            server_folder = self._ensure_subfolder(self.folder_id, server_name)
            if not server_folder:
                raise RuntimeError(f"Failed to create server folder: {server_name}")
            
            date_subfolder = self._ensure_subfolder(server_folder, date_folder)
            if not date_subfolder:
                raise RuntimeError(f"Failed to create date folder: {date_folder}")
            
            self.logger.info(f"Uploading backup: {backup_id} ({file_size / (1024**3):.2f} GB)")
            
            # Prepare file metadata
            filename = f"{backup_id}.tar.gz"
            file_metadata = {
                'name': filename,
                'parents': [date_subfolder],
                'description': f"Minecraft {server_name} backup - {backup_id}"
            }
            
            # Use resumable upload for large files
            media = MediaFileUpload(
                file_path,
                mimetype='application/gzip',
                resumable=True,
                chunksize=self.CHUNK_SIZE
            )
            
            request = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            )
            
            # Execute upload with progress tracking
            response = None
            uploaded_size = 0
            
            while True:
                try:
                    status, response = request.next_chunk()
                    
                    if status:
                        uploaded_size = int(status.progress() * file_size)
                        progress_percent = int((uploaded_size / file_size) * 100)
                        
                        if self.progress_callback:
                            self.progress_callback(progress_percent)
                        
                        self.logger.debug(f"Upload progress: {progress_percent}% ({uploaded_size / (1024**3):.2f} GB)")
                    
                    if response:
                        break
                
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        # Retryable error
                        self.logger.warning(f"Temporary upload error, retrying: {e.resp.status}")
                        time.sleep(5)
                        continue
                    else:
                        raise
            
            file_id = response['id']
            file_url = response.get('webViewLink')
            
            self.logger.info(f"Backup uploaded successfully: {file_id}")
            self.logger.info(f"Google Drive link: {file_url}")
            
            return file_id, file_url
        
        except Exception as e:
            self.logger.error(f"Failed to upload backup: {e}")
            return None, None
    
    def download_backup(self, file_id: str, destination: str) -> bool:
        """
        Download backup file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            destination: Local destination path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Downloading backup: {file_id} to {destination}")
            
            request = self.drive_service.files().get_media(fileId=file_id)
            
            # Download file in chunks
            with open(destination, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress_percent = int(status.progress() * 100)
                        
                        if self.progress_callback:
                            self.progress_callback(progress_percent)
                        
                        self.logger.debug(f"Download progress: {progress_percent}%")
            
            self.logger.info(f"Backup downloaded successfully: {destination}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to download backup: {e}")
            return False
    
    def delete_backup(self, file_id: str) -> bool:
        """
        Delete backup file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            request = self.drive_service.files().delete(fileId=file_id)
            self._execute_request(request, f"Delete file {file_id}")
            
            self.logger.info(f"Backup deleted: {file_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to delete backup: {e}")
            return False
    
    def list_backups(self, server_name: str = None) -> List[Dict]:
        """
        List all backup files in Google Drive.
        
        Args:
            server_name: Optional filter by server name
            
        Returns:
            List of backup file info dicts
        """
        try:
            backups = []
            
            # Build query
            if server_name:
                # Search in specific server folder
                server_folder = self._ensure_subfolder(self.folder_id, server_name)
                if not server_folder:
                    return []
                
                query = f"'{server_folder}' in parents and trashed=false"
            else:
                # Search all backups
                query = f"'{self.folder_id}' in parents and trashed=false"
            
            request = self.drive_service.files().list(
                q=query,
                spaces='drive',
                pageSize=100,
                fields='files(id, name, size, createdTime, webViewLink)'
            )
            
            while request:
                response = self._execute_request(request, "List backups")
                
                if not response:
                    break
                
                for file_info in response.get('files', []):
                    backups.append({
                        'id': file_info['id'],
                        'name': file_info['name'],
                        'size_bytes': int(file_info.get('size', 0)),
                        'created_at': file_info.get('createdTime'),
                        'url': file_info.get('webViewLink')
                    })
                
                request = self.drive_service.files().list_next(request, response)
            
            self.logger.info(f"Found {len(backups)} backups")
            return backups
        
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
            return []
    
    def close(self):
        """Close client and cleanup resources."""
        # HTTP connection will be cleaned up automatically
        self.logger.info("Google Drive client closed")
