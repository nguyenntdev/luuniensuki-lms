#!/usr/bin/env bash
set -Eeuo pipefail

# ==============================================================================
# LƯU NIÊN — Staging Automated Rollback Script
# Reverts staging stack to previous stable image tag or git revision
# Reference: docs/rbpc/STAGING_DEPLOYMENT_SPEC.md (Section 7.1)
# ==============================================================================

STAGING_DIR="${STAGING_DIR:-/opt/luuniensuki-lms}"
PREV_COMMIT="${1:-HEAD~1}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"
HEALTH_PORT="${HEALTH_PORT:-8443}"

echo "[$(date '+%F %T')] INITIATING STAGING ROLLBACK to ${PREV_COMMIT}..."
cd "${STAGING_DIR}"

compose_args=(-f "${COMPOSE_FILE}")
if [[ -f docker-compose.override.yml ]]; then
  compose_args+=(-f docker-compose.override.yml)
fi
if [[ -f "${ENV_FILE}" ]]; then
  compose_args+=(--env-file "${ENV_FILE}")
fi

# 1. Stop current application containers (leave DB running to preserve data)
echo "Stopping web, api, api_rust, ai_teacher_agent..."
docker compose "${compose_args[@]}" stop web api api_rust ai_teacher_agent

# 2. Reset codebase to previous known-good commit
echo "Checking out ${PREV_COMMIT}..."
git checkout "${PREV_COMMIT}"

# 3. Fast-rebuild & restart application services
echo "Rebuilding and restarting stack..."
docker compose "${compose_args[@]}" up -d --build api api_rust web ai_teacher_agent nginx

# 4. Run post-rollback health check
echo "Waiting for health check..."
sleep 5
HEALTH_CODE=$(curl -sk -o /dev/null -w "%{http_code}" "https://127.0.0.1:${HEALTH_PORT}/health" || true)

if [[ "${HEALTH_CODE}" == "200" ]]; then
  echo "[$(date '+%F %T')] ROLLBACK SUCCESSFUL. System restored to HTTP 200."
  docker compose "${compose_args[@]}" ps
  exit 0
else
  echo "[$(date '+%F %T')] CRITICAL: Rollback health check failed with HTTP ${HEALTH_CODE}!"
  docker compose "${compose_args[@]}" logs --tail=50 api_rust api
  exit 1
fi
