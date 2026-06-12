# GitHub Actions CI/CD Setup Guide

This document describes how to configure GitHub Actions for automatic deployment of Luuniensuki LMS.

## Workflows

Both workflows live in `.github/workflows/` and are present in the repo.

### 1. CI Workflow (`ci.yml`)

Runs on every push and pull request to the `main` branch. Two parallel jobs:

- **backend** — spins up a `postgres:15` service, sets up **Python 3.11**, installs
  `backend/requirements.txt` + `backend/requirements-dev.txt`, then runs `pytest`
  (with `DATABASE_URL` pointing at the service DB).
- **frontend** (working dir `./frontend`) — Node 20, `npm ci`, `npm run lint:ci`
  (ESLint with `--max-warnings=0`), `npm run build` (which runs `tsc --noEmit` via the
  `prebuild` hook), installs Playwright browsers, then runs the **smoke** E2E subset
  (`npx playwright test` with `PLAYWRIGHT_GREP='@smoke'`).

### 2. Deploy Workflow (`deploy.yml`)

Runs on push to `main`, or manually via `workflow_dispatch` (with a `skip_tests` boolean
input). Jobs:

- **test** (skipped when `skip_tests=true`) — postgres service, **Python 3.12**, runs
  `pytest tests/backend`, then Node 20 frontend `npm ci` + `lint:ci` + `build`.
- **deploy** — runs after `test` succeeds or is skipped, using the `production`
  GitHub Environment. It SSHes to the server via `appleboy/ssh-action` and on the server:
  - `git fetch origin main` + `git reset --hard origin/main`
  - `docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod pull`
  - `... up -d --build`
  - `... run --rm api alembic upgrade head`
  - `docker image prune -f`
  - health check: `curl -sf https://lms.histolab.icu/health`
- **notify** — writes a deployment summary to the job summary.

> The deploy job expects the repo checked out at `/opt/luuniensuki-lms` on the server with a
> populated `.env.prod` (see [DEPLOYMENT_CUUDINH.md](DEPLOYMENT_CUUDINH.md) and
> [SECRETS.md](SECRETS.md)).

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
# Trigger deployment manually
gh workflow run deploy.yml

# Skip the test job (deploy straight away)
gh workflow run deploy.yml -f skip_tests=true
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

1. Check container logs (prod stack uses both compose files):
   ```bash
   docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod logs --tail=50
   ```

2. Verify Docker service is running:
   ```bash
   systemctl status docker
   ```

### Health Check Failures

1. Check if all containers are running:
   ```bash
   docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod ps
   ```

2. Test health endpoint directly (served via the Rust gateway):
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
- `docker-compose.prod.yml` / `docker-compose.override.yml` - Production Docker config
- `docs/DEPLOYMENT_CUUDINH.md` - Manual deployment guide
- `docs/SECRETS.md` - Required secrets and fail-closed validation