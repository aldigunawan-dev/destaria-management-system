"""
FastAPI Application
Main API entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Minecraft DevOps Platform API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# TODO: Import and include routers
# from .routes import backup_routes, update_routes, etc.
# app.include_router(backup_routes.router, prefix="/api/backup", tags=["backup"])
