"""
FastAPI Application
Main API entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .routes import backup_routes

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Minecraft DevOps Platform API",
    description="API for managing Minecraft server backups, updates, and deployments",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(backup_routes.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Minecraft DevOps Platform API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "backup": "/api/backup",
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

