# Configuration Files Guide

## servers.yaml
Configure your Minecraft servers, their IDs, and backup schedules.

**Variables:**
- `id`: Pterodactyl server ID
- `name`: Human-readable server name
- `backup_schedule`: Cron expression for backup timing
- `backup_type`: "full" or "incremental"

## plugins.yaml
List all plugins you want to monitor for updates.

**Variables:**
- `source`: Where to find updates (spigot, modrinth, hangar, github)
- `auto_update`: Whether to automatically update this plugin
- `current_version`: Current installed version (for reference)

## notifications.yaml
Configure Discord and other notification settings.

**Variables:**
- `webhook_url`: Discord webhook URL from environment
- `events`: Which events trigger notifications

## Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
PTERODACTYL_PANEL_URL=https://your-panel.com
PTERODACTYL_API_KEY=your_key_here
DISCORD_WEBHOOK_URL=your_webhook_here
```

## Tips

- Use environment variables for sensitive data
- Don't commit real API keys or webhooks
- Validate YAML syntax before deploying
- Test configurations with dry-run first
