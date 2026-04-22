# GitHub Actions CI/CD Setup Guide

This document describes how to configure GitHub Actions for automatic deployment of Luuniensuki LMS.

## Workflows

### 1. CI Workflow (`ci.yml`)

Runs on every push and pull request to `main` branch:
- **Backend**: Python tests with PostgreSQL
- **Frontend**: Lint, build, and E2E tests with Playwright

### 2. Deploy Workflow (`deploy.yml`)

Runs on push to `main` branch (after CI passes):
- Connects to production server via SSH
- Pulls latest code
- Rebuilds Docker containers
- Runs database migrations
- Performs health check

## Required Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### Required Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SERVER_HOST` | Production server IP address | `36.50.26.18` |
| `SERVER_USER` | SSH username | `root` or `deploy` |
| `SSH_PRIVATE_KEY` | Private SSH key for authentication | See below |
| `SERVER_PORT` | SSH port (optional, default: 22) | `22` |

## Setting Up SSH Key Authentication

### 1. Generate SSH Key Pair

On your local machine:

```bash
# Generate a new SSH key pair (no passphrase for CI/CD)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy -N ""

# This creates two files:
# - ~/.ssh/github_actions_deploy (private key)
# - ~/.ssh/github_actions_deploy.pub (public key)
```

### 2. Add Public Key to Server

```bash
# Copy public key to server
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub root@36.50.26.18

# Or manually append to authorized_keys
cat ~/.ssh/github_actions_deploy.pub | ssh root@36.50.26.18 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 3. Add Private Key to GitHub Secrets

```bash
# Copy the private key content
cat ~/.ssh/github_actions_deploy

# Go to GitHub → Repository → Settings → Secrets → Actions
# Create new secret: SSH_PRIVATE_KEY
# Paste the entire private key content (including BEGIN and END lines)
```

### 4. Add Other Secrets

In GitHub repository settings, add:

```
SERVER_HOST = 36.50.26.18
SERVER_USER = root
SERVER_PORT = 22
```

## Environment Setup

Create a GitHub Environment for additional protection:

1. Go to **Settings** → **Environments**
2. Create environment: `production`
3. Add protection rules:
   - Required reviewers (optional)
   - Wait timer (optional)
   - Deployment branches: `main`

## Testing the Workflow

### Manual Trigger

```bash
# Trigger deployment manually (with option to skip tests)
gh workflow run deploy.yml
```

### Check Workflow Status

```bash
# View recent workflow runs
gh run list

# View specific run details
gh run view <run-id>
```

## Troubleshooting

### SSH Connection Issues

1. Verify SSH key is correctly added:
   ```bash
   ssh -i ~/.ssh/github_actions_deploy root@36.50.26.18
   ```

2. Check server SSH config allows key authentication:
   ```bash
   # On server, check /etc/ssh/sshd_config
   PubkeyAuthentication yes
   ```

3. Verify file permissions on server:
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   ```

### Docker Issues

1. Check container logs:
   ```bash
   docker compose -f docker-compose.prod.yml logs --tail=50
   ```

2. Verify Docker service is running:
   ```bash
   systemctl status docker
   ```

### Health Check Failures

1. Check if all containers are running:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```

2. Test health endpoint directly:
   ```bash
   curl -v https://lms.histolab.icu/health
   ```

## Security Best Practices

1. **Use dedicated deploy user** instead of root:
   ```bash
   # On server
   useradd -m -s /bin/bash deploy
   usermod -aG docker deploy
   ```

2. **Limit SSH key permissions** in `authorized_keys`:
   ```
   command="/opt/deploy-only.sh",no-port-forwarding,no-X11-forwarding ssh-ed25519 AAAA...
   ```

3. **Rotate SSH keys periodically** (every 90 days)

4. **Enable branch protection** on `main`:
   - Require pull request reviews
   - Require status checks to pass
   - Require linear history

## Workflow Diagram

```
┌─────────────────┐
│   Push to main  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Run Tests     │
│  (CI Workflow)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Tests Pass?    │────▶│  Skip Deploy    │
│                 │ No  │                 │
└────────┬────────┘     └─────────────────┘
         │ Yes
         ▼
┌─────────────────┐
│   SSH to Server │
│   Pull Code     │
│   Build & Start │
│   Health Check  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Notify        │
│   (Summary)     │
└─────────────────┘
```

## Related Files

- `.github/workflows/ci.yml` - CI workflow
- `.github/workflows/deploy.yml` - CD workflow
- `docker-compose.prod.yml` - Production Docker config
- `docs/DEPLOYMENT_CUUDINH.md` - Manual deployment guide