# 09_CICD.md (CI + Deployment Automation)

## Goal

Add a CI pipeline that blocks broken changes and a deploy workflow that updates the VPS reliably.

## Current State

- No GitHub Actions workflows.
- Deploy is manual (run docker compose on VPS).

## CI (Required)

### CI Workflow Responsibilities

- Backend:
  - lint (optional first iteration)
  - unit/integration tests (pytest)
  - docker build (optional)
- Frontend:
  - `npm ci`
  - `next build`

### Suggested Workflow Layout

```
.github/workflows/ci.yml
  - python tests
  - node build
```

## CD (Optional but Recommended)

### Deployment Strategy (Simple VPS)

Deploy on `main` or release tags:

1. SSH into VPS
2. `git pull` (or fetch the release artifact)
3. `docker compose up -d --build`
4. Run migrations (`alembic upgrade head`)
5. Run seed (idempotent)
6. Health check (`/api/v1/health`)

### Secrets

Store as GitHub Actions secrets:

- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_PRIVATE_KEY`
- `DEPLOY_PATH` (e.g. `/opt/luuniensuki-lms`)

Do **not** store:
- root passwords
- `.env.prod` in git

## Tasks

- [ ] **CI-01**: Add `.github/workflows/ci.yml` (python + node jobs)
- [ ] **CI-02**: Add caching for pip/npm
- [ ] **CI-03**: Add coverage report artifact (pytest-cov)
- [ ] **CD-01**: Add `.github/workflows/deploy-production.yml` (manual trigger or tag)
- [ ] **CD-02**: Add deploy health check step (curl `/api/v1/health`)
- [ ] **CD-03**: Add rollback note (pin previous image tag or git sha)

## Definition of Done

- PRs cannot merge if backend tests or frontend build fail.
- A single command (or GitHub workflow) can deploy a new release to the VPS.

