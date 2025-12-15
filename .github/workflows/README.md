# GitHub Actions Workflows
# CI/CD automation for testing and deployment

## Workflow Files

### deploy.yml
- Runs tests on push to main
- Builds Docker image
- Pushes to registry
- Deploys to production

### test.yml
- Runs tests on pull requests
- Code coverage checks
- Lint and format checks

## Setup Instructions

1. Create `.github/workflows/` directory
2. Add workflow YAML files
3. Configure secrets in GitHub repository:
   - PTERODACTYL_API_KEY
   - DISCORD_WEBHOOK_URL
   - DOCKER_REGISTRY_TOKEN
   - etc.

## Example Workflow Triggers

- Push to main: Deploy
- Push to develop: Test
- Pull requests: Test + Lint
- Schedule (cron): Backup validation, cleanup tasks
