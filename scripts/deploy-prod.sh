#!/usr/bin/env bash
# Deploy the current `main` branch to production.
#
# Usage:
#   ./scripts/deploy-prod.sh              # interactive, asks for confirmation
#   ./scripts/deploy-prod.sh --yes        # skip the confirmation prompt
#   ./scripts/deploy-prod.sh --skip-migrations
#
# Environment:
#   PROD_SSH_HOST   default: 36.50.26.18
#   PROD_SSH_USER   default: root
#   PROD_PATH       default: /opt/luuniensuki-lms
#   COMPOSE_FILE    default: docker-compose.prod.yml
#
# Authentication:
#   Use an SSH key. If you really must use a password, set it in
#   ~/.deploy-secrets (mode 600) as `PROD_SSH_PASSWORD=...` and install
#   sshpass locally — but prefer `ssh-copy-id` once and never look back.

set -euo pipefail

PROD_SSH_HOST="${PROD_SSH_HOST:-36.50.26.18}"
PROD_SSH_USER="${PROD_SSH_USER:-root}"
PROD_PATH="${PROD_PATH:-/opt/luuniensuki-lms}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
SMOKE_HOST="${SMOKE_HOST:-https://lms.histolab.icu}"

SKIP_PROMPT=0
SKIP_MIGRATIONS=0
for arg in "$@"; do
  case "$arg" in
    --yes|-y) SKIP_PROMPT=1 ;;
    --skip-migrations) SKIP_MIGRATIONS=1 ;;
    *) echo "Unknown flag: $arg" >&2; exit 2 ;;
  esac
done

# Optional password file. Default path is gitignored.
SECRETS_FILE="${HOME}/.deploy-secrets"
if [[ -f "$SECRETS_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$SECRETS_FILE"
fi

ssh_run() {
  local cmd="$1"
  if [[ -n "${PROD_SSH_PASSWORD:-}" ]]; then
    if ! command -v sshpass >/dev/null; then
      echo "PROD_SSH_PASSWORD set but sshpass is not installed." >&2
      exit 1
    fi
    SSHPASS="$PROD_SSH_PASSWORD" sshpass -e ssh \
      -o StrictHostKeyChecking=accept-new \
      "${PROD_SSH_USER}@${PROD_SSH_HOST}" "$cmd"
  else
    ssh -o StrictHostKeyChecking=accept-new \
      "${PROD_SSH_USER}@${PROD_SSH_HOST}" "$cmd"
  fi
}

green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
red() { printf '\033[31m%s\033[0m\n' "$*" >&2; }

green "==> Deploy plan"
echo "  Host:     ${PROD_SSH_USER}@${PROD_SSH_HOST}"
echo "  Path:     ${PROD_PATH}"
echo "  Compose:  ${COMPOSE_FILE}"
echo "  Migrate:  $([[ $SKIP_MIGRATIONS -eq 1 ]] && echo NO || echo YES)"
echo "  Smoke:    ${SMOKE_HOST}"

if [[ $SKIP_PROMPT -eq 0 ]]; then
  read -r -p "Proceed? [y/N] " ans
  case "$ans" in y|Y|yes|YES) ;; *) red "Aborted."; exit 1 ;; esac
fi

green "==> [1/6] git fetch + checkout main on remote"
ssh_run "cd '${PROD_PATH}' && git fetch --all && git checkout main && git pull --ff-only"

green "==> [2/6] capture current image IDs (for rollback)"
ssh_run "cd '${PROD_PATH}' && docker compose -f '${COMPOSE_FILE}' images api_rust web | tee /tmp/lms-pre-deploy-images.txt"

if [[ $SKIP_MIGRATIONS -eq 0 ]]; then
  green "==> [3/6] alembic upgrade head (via api container)"
  ssh_run "cd '${PROD_PATH}' && docker compose -f '${COMPOSE_FILE}' run --rm api alembic upgrade head"
else
  yellow "==> [3/6] SKIPPED migrations"
fi

green "==> [4/6] docker build api_rust web"
ssh_run "cd '${PROD_PATH}' && docker compose -f '${COMPOSE_FILE}' build api_rust web"

green "==> [5/6] up -d api_rust web (rolling)"
ssh_run "cd '${PROD_PATH}' && docker compose -f '${COMPOSE_FILE}' up -d api_rust web"

green "==> [6/6] smoke tests"
fail=0
for path in / /dashboard /timeline /trails /health /api/v1/timeline/events /api/v1/trails; do
  code=$(curl -k -sS -o /dev/null -w '%{http_code}' "${SMOKE_HOST}${path}" || echo 000)
  printf '  %-40s -> %s\n' "$path" "$code"
  case "$path" in
    /api/v1/trails)
      # Requires auth, so 401 is the expected healthy response.
      [[ "$code" == "401" || "$code" == "200" ]] || fail=1 ;;
    *)
      [[ "$code" == "200" ]] || fail=1 ;;
  esac
done

# /api/v1/ranks should be 401 unauth (sanity check that auth still works)
ranks_code=$(curl -k -sS -o /dev/null -w '%{http_code}' "${SMOKE_HOST}/api/v1/ranks" || echo 000)
printf '  %-40s -> %s\n' "/api/v1/ranks (expect 401)" "$ranks_code"
[[ "$ranks_code" == "401" ]] || fail=1

if [[ $fail -ne 0 ]]; then
  red "Smoke tests FAILED. To rollback see /tmp/lms-pre-deploy-images.txt on the server."
  red "Quick rollback: docker compose -f ${COMPOSE_FILE} up -d --no-deps api_rust web (with previous image tag)"
  exit 1
fi

green "==> Deploy succeeded"
