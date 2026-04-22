#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Missing compose file: $COMPOSE_FILE" >&2
  exit 1
fi

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

docker compose -f "$COMPOSE_FILE" exec -T api python -m backend.provision_live_demo \
  --email "${DEMO_LIVE_TEACHER_EMAIL:-live.teacher@histolab.icu}" \
  --password "${DEMO_LIVE_TEACHER_PASSWORD:-LiveTeacher@2026}" \
  --display-name "${DEMO_LIVE_TEACHER_NAME:-Live Demo Teacher}" \
  --class-name "${DEMO_LIVE_CLASS_NAME:-AI Teacher 3D Demo Class}" \
  --session-title "${DEMO_LIVE_SESSION_TITLE:-AI Teacher 3D Live Session}" \
  --max-students "${DEMO_LIVE_MAX_STUDENTS:-60}" \
  --base-url "${DEMO_LIVE_BASE_URL:-https://lms.histolab.icu}"
