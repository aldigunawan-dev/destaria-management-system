"""
Notifications Module
Handles sending notifications (Discord, etc.)
"""

from .discord import DiscordNotifier

__all__ = ["DiscordNotifier"]
