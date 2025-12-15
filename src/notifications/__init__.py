"""
Notifications Module
Handles sending notifications (Discord, etc.)
"""

from .discord import DiscordNotifier, init_discord_notifier

__all__ = ["DiscordNotifier", "init_discord_notifier"]
