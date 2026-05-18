#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://lms.histolab.icu}"
LIVE_SESSION_ID="${LIVE_SESSION_ID:-}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
SSH_TARGET="${SSH_TARGET:-}"
SSH_PASSWORD="${SSH_PASSWORD:-}"
REMOTE_APP_DIR="${REMOTE_APP_DIR:-/opt/luuniensuki-lms}"

failures=0

check() {
  local name="$1"
  shift
  echo "==> ${name}"
  if "$@"; then
    echo "OK ${name}"
  else
    echo "FAIL ${name}" >&2
    failures=$((failures + 1))
  fi
}

check_health() {
  local payload
  payload="$(curl -fsS --max-time 10 "${BASE_URL%/}/health")"
  echo "${payload}"
  [[ "${payload}" == *'"status":"ok"'* ]]
}

check_frontend() {
  curl -fsSI --max-time 10 "${BASE_URL%/}/" | grep -qiE '^HTTP/.* (200|30[1278])'
}

check_live_page() {
  [[ -n "${LIVE_SESSION_ID}" ]] || return 0
  curl -fsSI --max-time 10 "${BASE_URL%/}/live/${LIVE_SESSION_ID}" | grep -qiE '^HTTP/.* (200|30[1278])'
}

check_observability() {
  [[ -n "${LIVE_SESSION_ID}" && -n "${AUTH_TOKEN}" ]] || return 0
  curl -fsS --max-time 15 \
    -H "Authorization: Bearer ${AUTH_TOKEN}" \
    "${BASE_URL%/}/api/v1/live-sessions/${LIVE_SESSION_ID}/observability" \
    | grep -q '"success_rate"'
}

check_remote_docker() {
  [[ -n "${SSH_TARGET}" && -n "${SSH_PASSWORD}" ]] || return 0
  command -v sshpass >/dev/null 2>&1
  sshpass -p "${SSH_PASSWORD}" ssh -o StrictHostKeyChecking=no "${SSH_TARGET}" \
    "cd '${REMOTE_APP_DIR}' && docker compose ps --format '{{.Service}} {{.State}}' | sort"
}

check "public health" check_health
check "frontend entry" check_frontend
check "live page route" check_live_page
check "live observability API" check_observability
check "remote docker services" check_remote_docker

if [[ "${failures}" -gt 0 ]]; then
  echo "${failures} smoke check(s) failed." >&2
  exit 1
fi

echo "All live production smoke checks passed."
