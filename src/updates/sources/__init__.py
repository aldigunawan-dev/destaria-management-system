"""
Plugin Sources Module
Contains clients for different plugin repositories
"""

from .spigot import SpigotClient
from .modrinth import ModrinthClient
from .hangar import HangarClient
from .github import GitHubClient

__all__ = ["SpigotClient", "ModrinthClient", "HangarClient", "GitHubClient"]
