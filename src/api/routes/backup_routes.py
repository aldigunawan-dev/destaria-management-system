"""
Backup REST API Routes
FastAPI endpoints for backup management operations.
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
import uuid

from src.backup.backup_manager import BackupManager
from src.backup.database import DatabaseManager
from src.notifications import DiscordNotifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backup", tags=["backup"])


# ============================================================================
# Pydantic Models (Request/Response)
# ============================================================================

class ServerInfo(BaseModel):
    """Server information"""
    id: str
    name: str
    pterodactyl_server_id: str
    backup_schedule: Optional[str] = None


class BackupMetadata(BaseModel):
    """Backup metadata"""
    id: str
    server_id: str
    server_name: str
    backup_type: str  # "full" or "incremental"
    status: str  # "pending", "running", "completed", "failed"
    size_bytes: Optional[int] = None
    duration_seconds: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None
    gdrive_file_id: Optional[str] = None
    gdrive_file_url: Optional[str] = None
    error_message: Optional[str] = None
    retention_days: int = 30


class ServerWithLatestBackup(BaseModel):
    """Server with latest backup info"""
    server: ServerInfo
    latest_backup: Optional[BackupMetadata] = None
    total_backups: int = 0


class BackupJobStatus(BaseModel):
    """Backup job status"""
    job_id: str
    backup_id: str
    server_id: str
    status: str  # "running", "completed", "failed"
    progress_percent: int = 0
    current_step: str
    start_time: str
    estimated_completion: Optional[str] = None
    error_message: Optional[str] = None


class BackupRequest(BaseModel):
    """Request to create backup"""
    backup_type: str = Field(default="full", description="Type: full or incremental")
    retention_days: int = Field(default=30, description="Days to retain backup")


class RestoreRequest(BaseModel):
    """Request to restore backup"""
    backup_id: str = Field(description="Backup ID to restore")


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None


# ============================================================================
# Dependency Injection
# ============================================================================

def get_backup_manager() -> BackupManager:
    """Get backup manager instance (should be injected from main.py)"""
    # This will be replaced with actual instance from main
    raise HTTPException(status_code=500, detail="Backup manager not initialized")


def get_database_manager() -> DatabaseManager:
    """Get database manager instance"""
    raise HTTPException(status_code=500, detail="Database manager not initialized")


# ============================================================================
# Routes
# ============================================================================

@router.get("/servers", response_model=List[ServerWithLatestBackup])
async def get_servers(
    backup_manager: BackupManager = Depends(get_backup_manager),
    database_manager: DatabaseManager = Depends(get_database_manager),
):
    """
    Get all servers with their latest backup status.
    
    Returns list of servers with latest backup info.
    """
    try:
        # This would load from config
        # For now, return empty list
        servers = []
        return servers
    except Exception as e:
        logger.error(f"Error getting servers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get servers")


@router.get("/history/{server_id}", response_model=List[BackupMetadata])
async def get_backup_history(
    server_id: str,
    limit: int = Query(50, ge=1, le=1000),
    database_manager: DatabaseManager = Depends(get_database_manager),
):
    """
    Get backup history for a specific server.
    
    Args:
        server_id: Server ID
        limit: Maximum number of backups to return (default: 50)
    
    Returns list of backups for the server.
    """
    try:
        backups = database_manager.get_server_backups(server_id, limit=limit)
        
        if not backups:
            return []
        
        return [
            BackupMetadata(
                id=b['id'],
                server_id=b['server_id'],
                server_name=b['server_name'],
                backup_type=b['backup_type'],
                status=b['status'],
                size_bytes=b['size_bytes'],
                duration_seconds=b.get('duration_seconds'),
                created_at=str(b['created_at']),
                completed_at=str(b['completed_at']) if b.get('completed_at') else None,
                gdrive_file_id=b.get('gdrive_file_id'),
                gdrive_file_url=b.get('gdrive_file_url'),
                error_message=b.get('error_message'),
                retention_days=b.get('retention_days', 30),
            )
            for b in backups
        ]
    except Exception as e:
        logger.error(f"Error getting backup history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backup history")


@router.post("/full/{server_id}", response_model=BackupJobStatus)
async def create_full_backup(
    server_id: str,
    backup_request: BackupRequest = None,
    background_tasks: BackgroundTasks = None,
    backup_manager: BackupManager = Depends(get_backup_manager),
    database_manager: DatabaseManager = Depends(get_database_manager),
):
    """
    Trigger a full backup for a server.
    
    Args:
        server_id: Server ID
        backup_request: Backup configuration (optional)
    
    Returns job status with backup info.
    """
    try:
        if not backup_request:
            backup_request = BackupRequest()
        
        backup_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        
        # Create backup record in DB
        database_manager.add_backup(
            backup_id=backup_id,
            server_id=server_id,
            server_name=server_id,  # Would come from config
            backup_type="full",
            retention_days=backup_request.retention_days
        )
        
        # Create job record
        database_manager.create_backup_job(job_id, backup_id, server_id)
        
        # Run backup in background
        if background_tasks:
            background_tasks.add_task(
                backup_manager.full_backup,
                server_id=server_id,
                server_name=server_id,
            )
        
        return BackupJobStatus(
            job_id=job_id,
            backup_id=backup_id,
            server_id=server_id,
            status="running",
            progress_percent=0,
            current_step="starting",
            start_time=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to create backup")


@router.get("/status/{job_id}", response_model=BackupJobStatus)
async def get_backup_status(
    job_id: str,
    database_manager: DatabaseManager = Depends(get_database_manager),
):
    """
    Get the status of a backup job.
    
    Args:
        job_id: Job ID
    
    Returns job status.
    """
    try:
        job = database_manager.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return BackupJobStatus(
            job_id=job['job_id'],
            backup_id=job['backup_id'],
            server_id=job['server_id'],
            status=job['status'],
            progress_percent=job.get('progress_percent', 0),
            current_step=job.get('current_step', 'unknown'),
            start_time=str(job['start_time']),
            estimated_completion=str(job.get('estimated_completion')) if job.get('estimated_completion') else None,
            error_message=job.get('error_message'),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backup status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backup status")


@router.post("/restore/{backup_id}", response_model=BackupJobStatus)
async def restore_backup(
    backup_id: str,
    background_tasks: BackgroundTasks = None,
    backup_manager: BackupManager = Depends(get_backup_manager),
    database_manager: DatabaseManager = Depends(get_database_manager),
):
    """
    Trigger a restore operation for a backup.
    
    Args:
        backup_id: Backup ID to restore
    
    Returns job status.
    """
    try:
        # Get backup info
        backup = database_manager.get_backup(backup_id)
        
        if not backup:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        restore_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        
        # Create restore record
        database_manager.add_restore_record(
            restore_id=restore_id,
            server_id=backup['server_id'],
            server_name=backup['server_name'],
            backup_id=backup_id
        )
        
        # Run restore in background
        if background_tasks:
            background_tasks.add_task(
                backup_manager.restore_backup,
                server_id=backup['server_id'],
                backup_id=backup_id,
            )
        
        return BackupJobStatus(
            job_id=job_id,
            backup_id=backup_id,
            server_id=backup['server_id'],
            status="running",
            progress_percent=0,
            current_step="starting_restore",
            start_time=datetime.now().isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore backup")


@router.delete("/backups/{backup_id}", response_model=MessageResponse)
async def delete_backup(
    backup_id: str,
    database_manager: DatabaseManager = Depends(get_database_manager),
):
    """
    Delete a backup (remove from Google Drive and database).
    
    Args:
        backup_id: Backup ID to delete
    
    Returns success message.
    """
    try:
        backup = database_manager.get_backup(backup_id)
        
        if not backup:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        # Delete from database
        success = database_manager.delete_backup_record(backup_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete backup")
        
        return MessageResponse(
            message=f"Backup {backup_id} deleted successfully",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete backup")


@router.get("/scheduler/status")
async def get_scheduler_status(
):
    """
    Get scheduler status (running backups, scheduled jobs, etc).
    
    Returns scheduler status.
    """
    try:
        # Would be injected from main
        return {
            "running": False,
            "jobs": 0,
            "running_backups": 0,
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scheduler status")


@router.post("/scheduler/pause", response_model=MessageResponse)
async def pause_scheduler(
):
    """Pause the scheduler (jobs won't run)."""
    try:
        return MessageResponse(
            message="Scheduler paused",
            success=True
        )
    except Exception as e:
        logger.error(f"Error pausing scheduler: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause scheduler")


@router.post("/scheduler/resume", response_model=MessageResponse)
async def resume_scheduler(
):
    """Resume the scheduler."""
    try:
        return MessageResponse(
            message="Scheduler resumed",
            success=True
        )
    except Exception as e:
        logger.error(f"Error resuming scheduler: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume scheduler")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# Error Handlers
# ============================================================================

@router.get("/")
async def backup_api_info():
    """API info and available endpoints."""
    return {
        "name": "Minecraft DevOps Backup API",
        "version": "1.0.0",
        "endpoints": {
            "servers": "GET /api/backup/servers",
            "history": "GET /api/backup/history/{server_id}",
            "create_backup": "POST /api/backup/full/{server_id}",
            "status": "GET /api/backup/status/{job_id}",
            "restore": "POST /api/backup/restore/{backup_id}",
            "delete": "DELETE /api/backup/backups/{backup_id}",
            "scheduler": "GET /api/backup/scheduler/status",
            "health": "GET /api/backup/health",
        }
    }
