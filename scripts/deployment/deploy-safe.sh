#!/usr/bin/env bash
set -Eeuo pipefail

# Production-safe deployment script for Luuniensuki LMS.
# - Syncs repository to server with strict excludes
# - Builds services sequentially to reduce peak resource usage
# - Applies migrations and health checks

SERVER_IP="${SERVER_IP:-36.50.26.18}"
SERVER_USER="${SERVER_USER:-root}"
SSH_PORT="${SSH_PORT:-22}"
REMOTE_DIR="${REMOTE_DIR:-/opt/luuniensuki-lms}"
DOMAIN="${DOMAIN:-lms.histolab.icu}"

SERVER_PASS=""
RUN_SYNC=1
RUN_MIGRATIONS=1
SKIP_HEALTH=0
REBUILD_ALL=0
DRY_RUN=0

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

usage() {
  cat <<'EOF'
Usage: ./scripts/deployment/deploy-safe.sh [options]

Options:
  -p, --password <value>      SSH password (uses sshpass)
      --no-sync               Skip rsync step
      --no-migrate            Skip alembic migration
      --skip-health           Skip post-deploy health checks
      --rebuild-all           Build with --no-cache
      --dry-run               Print actions without making changes
  -h, --help                  Show this help
EOF
}

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*"; }
die() { printf '[%s] ERROR: %s\n' "$(date '+%F %T')" "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--password)
      [[ $# -ge 2 ]] || die "Missing value for $1"
      SERVER_PASS="$2"
      shift 2
      ;;
    --password=*)
      SERVER_PASS="${1#*=}"
      shift
      ;;
    --no-sync)
      RUN_SYNC=0
      shift
      ;;
    --no-migrate)
      RUN_MIGRATIONS=0
      shift
      ;;
    --skip-health)
      SKIP_HEALTH=1
      shift
      ;;
    --rebuild-all)
      REBUILD_ALL=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

require_cmd rsync
require_cmd ssh

if [[ -n "$SERVER_PASS" ]]; then
  require_cmd sshpass
fi

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -p "$SSH_PORT")

run_ssh() {
  local remote_cmd="$1"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] ssh ${SERVER_USER}@${SERVER_IP} \"$remote_cmd\""
    return 0
  fi

  if [[ -n "$SERVER_PASS" ]]; then
    sshpass -p "$SERVER_PASS" ssh "${SSH_OPTS[@]}" \
      "${SERVER_USER}@${SERVER_IP}" "$remote_cmd"
  else
    ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_IP}" "$remote_cmd"
  fi
}

run_ssh_stdin() {
  local env_prefix="$1"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] remote deploy script execution skipped"
    return 0
  fi

  if [[ -n "$SERVER_PASS" ]]; then
    sshpass -p "$SERVER_PASS" ssh "${SSH_OPTS[@]}" \
      "${SERVER_USER}@${SERVER_IP}" "${env_prefix} bash -s"
  else
    ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_IP}" "${env_prefix} bash -s"
  fi
}

run_rsync() {
  local -a args=("$@")
  local rsync_ssh="ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -p ${SSH_PORT}"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] rsync ${args[*]}"
    return 0
  fi

  if [[ -n "$SERVER_PASS" ]]; then
    sshpass -p "$SERVER_PASS" rsync "${args[@]}" \
      -e "$rsync_ssh"
  else
    rsync "${args[@]}" -e "$rsync_ssh"
  fi
}

log "Target: ${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}"
log "Project root: ${PROJECT_ROOT}"

log "Step 1/5: Preflight remote checks"
run_ssh "mkdir -p '${REMOTE_DIR}' && command -v docker >/dev/null && docker --version && docker compose version"

if [[ "$RUN_SYNC" -eq 1 ]]; then
  log "Step 2/5: Sync repository"
  RSYNC_ARGS=(
    -az
    --delete
    --partial
    --info=progress2
    --exclude=.git
    --exclude=.gitnexus
    --exclude=.venv
    --exclude=.venv311
    --exclude=__pycache__
    --exclude=.pytest_cache
    --exclude=node_modules
    --exclude=frontend/node_modules
    --exclude=frontend/.next
    --exclude=frontend/test-results
    --exclude=frontend/playwright-report
    --exclude=mobile/build
    --exclude=mobile/.dart_tool
    --exclude=target
    --exclude=backend-rust/target
    --exclude=.cargo
    --exclude=*.log
    --exclude=.coverage
    --exclude=.ruff_cache
    --exclude=.mypy_cache
    --exclude=*.pyc
    --exclude=.env
    --exclude=.env.local
    --exclude=.env.prod
    --exclude=certbot
    --exclude=backups
    --exclude=uploads
    --exclude=builds
  )

  run_rsync "${RSYNC_ARGS[@]}" \
    "${PROJECT_ROOT}/" "${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/"
else
  log "Step 2/5: Sync skipped (--no-sync)"
fi

log "Step 3/5: Build and start services on remote host"
run_ssh_stdin "REMOTE_DIR='${REMOTE_DIR}' REBUILD_ALL='${REBUILD_ALL}' RUN_MIGRATIONS='${RUN_MIGRATIONS}' SKIP_HEALTH='${SKIP_HEALTH}' DOMAIN='${DOMAIN}'" <<'REMOTE'
set -Eeuo pipefail

APP_DIR="${REMOTE_DIR}"
cd "${APP_DIR}"

[[ -f ".env.prod" ]] || { echo "Missing ${APP_DIR}/.env.prod"; exit 1; }
[[ -f "docker-compose.prod.yml" ]] || { echo "Missing ${APP_DIR}/docker-compose.prod.yml"; exit 1; }

compose_files=(-f docker-compose.prod.yml)
if [[ -f docker-compose.override.yml ]]; then
  compose_files+=(-f docker-compose.override.yml)
fi
compose_cmd=(docker compose "${compose_files[@]}" --env-file .env.prod)

disk_free_gb="$(df -BG / | awk 'NR==2 {gsub("G","",$4); print $4+0}')"
if [[ "${disk_free_gb}" -lt 2 ]]; then
  echo "Low disk free space: ${disk_free_gb}GB (<2GB). Aborting."
  exit 1
fi

echo "Compose files: ${compose_files[*]}"
"${compose_cmd[@]}" config >/dev/null

build_args=(--pull)
if [[ "${REBUILD_ALL}" == "1" ]]; then
  build_args+=(--no-cache)
fi

build_service() {
  local svc="$1"
  echo "Building ${svc}..."
  if ! "${compose_cmd[@]}" build "${build_args[@]}" "${svc}"; then
    if [[ "${svc}" == "web" ]]; then
      echo "BuildKit build failed for web; retrying with DOCKER_BUILDKIT=0"
      DOCKER_BUILDKIT=0 "${compose_cmd[@]}" build "${svc}"
    else
      return 1
    fi
  fi
}

build_service api
build_service api_rust
build_service ai_teacher_agent
build_service web

echo "Starting base services..."
"${compose_cmd[@]}" up -d db livekit janus-gateway

if [[ "${RUN_MIGRATIONS}" == "1" ]]; then
  echo "Running migrations..."
  "${compose_cmd[@]}" run --rm api alembic upgrade heads
fi

echo "Starting app services..."
"${compose_cmd[@]}" up -d api api_rust ai_teacher_agent web

echo "Starting reverse proxy edge..."
"${compose_cmd[@]}" up -d nginx

if [[ "${SKIP_HEALTH}" != "1" ]]; then
  echo "Waiting for health endpoint..."
  success=0
  for i in $(seq 1 30); do
    code="$(curl -sk -H "Host: ${DOMAIN}" -o /dev/null -w '%{http_code}' https://127.0.0.1:8443/health || true)"
    if [[ "${code}" == "200" ]]; then
      success=1
      break
    fi
    sleep 3
  done
  if [[ "${success}" -ne 1 ]]; then
    echo "Health check failed after deployment (HTTP ${code:-none})."
    "${compose_cmd[@]}" ps
    exit 1
  fi
fi

echo "Container status:"
"${compose_cmd[@]}" ps
REMOTE

log "Step 4/5: Post-deploy verification"
run_ssh "cd '${REMOTE_DIR}' && compose_args=(-f docker-compose.prod.yml) && [[ -f docker-compose.override.yml ]] && compose_args+=(-f docker-compose.override.yml); docker compose \"\${compose_args[@]}\" --env-file .env.prod ps"

if [[ "$SKIP_HEALTH" -eq 0 ]]; then
  run_ssh "curl -sk -H 'Host: ${DOMAIN}' -o /dev/null -w 'HTTPS /health => %{http_code}\n' https://127.0.0.1:8443/health"
fi

log "Step 5/5: Done"
log "Deployment completed successfully."
