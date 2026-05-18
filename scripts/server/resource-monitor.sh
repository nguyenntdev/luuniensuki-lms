#!/usr/bin/env bash
set -Eeuo pipefail

# Runtime resource monitor for Luuniensuki LMS.
# Reads optional config from /etc/luuniensuki-monitor.env.
# Exits non-zero when alerts are raised.

APP_DIR="${APP_DIR:-/opt/luuniensuki-lms}"
ENV_PATH="${ENV_PATH:-/etc/luuniensuki-monitor.env}"
TAG="luuniensuki-monitor"

if [[ -f "${ENV_PATH}" ]]; then
  # shellcheck source=/dev/null
  source "${ENV_PATH}"
fi

DISK_WARN_PCT="${DISK_WARN_PCT:-88}"
MEM_WARN_PCT="${MEM_WARN_PCT:-92}"
SWAP_WARN_PCT="${SWAP_WARN_PCT:-80}"
MIN_FREE_GB="${MIN_FREE_GB:-2}"
MAX_LOAD_1M="${MAX_LOAD_1M:-8}"
CHECK_URL="${CHECK_URL:-https://127.0.0.1:8443/health}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"
FAIL_ON_ALERT="${FAIL_ON_ALERT:-0}"

alerts=()

add_alert() {
  alerts+=("$1")
}

if ! command -v docker >/dev/null 2>&1; then
  add_alert "docker command not found"
fi

disk_pct="$(df -P / | awk 'NR==2 {gsub("%","",$5); print $5+0}')"
disk_free_gb="$(df -BG / | awk 'NR==2 {gsub("G","",$4); print $4+0}')"
if [[ "${disk_pct}" -ge "${DISK_WARN_PCT}" ]]; then
  add_alert "disk usage high: ${disk_pct}% >= ${DISK_WARN_PCT}%"
fi
if [[ "${disk_free_gb}" -lt "${MIN_FREE_GB}" ]]; then
  add_alert "disk free low: ${disk_free_gb}GB < ${MIN_FREE_GB}GB"
fi

mem_pct="$(free | awk '/Mem:/ {printf "%.0f", $3*100/$2}')"
if [[ "${mem_pct}" -ge "${MEM_WARN_PCT}" ]]; then
  add_alert "memory usage high: ${mem_pct}% >= ${MEM_WARN_PCT}%"
fi

swap_total="$(free | awk '/Swap:/ {print $2+0}')"
if [[ "${swap_total}" -gt 0 ]]; then
  swap_used="$(free | awk '/Swap:/ {print $3+0}')"
  swap_pct="$(( swap_used * 100 / swap_total ))"
  if [[ "${swap_pct}" -ge "${SWAP_WARN_PCT}" ]]; then
    add_alert "swap usage high: ${swap_pct}% >= ${SWAP_WARN_PCT}%"
  fi
fi

load_1m="$(awk '{print $1}' /proc/loadavg)"
if awk -v v="${load_1m}" -v t="${MAX_LOAD_1M}" 'BEGIN { exit !(v>t) }'; then
  add_alert "load average high: ${load_1m} > ${MAX_LOAD_1M}"
fi

health_code="$(curl -sk -o /dev/null -w '%{http_code}' "${CHECK_URL}" || true)"
if [[ "${health_code}" != "200" ]]; then
  add_alert "health endpoint returned ${health_code} (${CHECK_URL})"
fi

if [[ -f "${APP_DIR}/docker-compose.prod.yml" && -f "${APP_DIR}/.env.prod" ]] && command -v docker >/dev/null 2>&1; then
  pushd "${APP_DIR}" >/dev/null
  compose_files=(-f docker-compose.prod.yml)
  if [[ -f docker-compose.override.yml ]]; then
    compose_files+=(-f docker-compose.override.yml)
  fi
  compose_cmd=(docker compose "${compose_files[@]}" --env-file .env.prod)
  running_services="$("${compose_cmd[@]}" ps --services --status running 2>/dev/null || true)"

  critical_services=(db livekit nginx api ai_teacher_agent web)
  for svc in "${critical_services[@]}"; do
    if ! grep -qx "${svc}" <<< "${running_services}"; then
      add_alert "service not running: ${svc}"
    fi
  done
  popd >/dev/null
else
  add_alert "compose files or env missing under ${APP_DIR}"
fi

timestamp="$(date '+%F %T')"
if [[ "${#alerts[@]}" -eq 0 ]]; then
  msg="OK host=$(hostname) disk=${disk_pct}% mem=${mem_pct}% health=${health_code}"
  echo "[${timestamp}] ${msg}"
  logger -t "${TAG}" "${msg}" || true
  exit 0
fi

joined="$(printf '%s | ' "${alerts[@]}")"
joined="${joined% | }"
msg="ALERT host=$(hostname): ${joined}"
echo "[${timestamp}] ${msg}"
logger -p daemon.warning -t "${TAG}" "${msg}" || true

if [[ -n "${ALERT_WEBHOOK_URL}" ]]; then
  escaped="$(printf '%s' "${msg}" | sed 's/"/\\"/g')"
  payload="{\"text\":\"${escaped}\"}"
  curl -fsS -m 12 -H 'Content-Type: application/json' \
    -d "${payload}" "${ALERT_WEBHOOK_URL}" >/dev/null || true
fi

if [[ "${FAIL_ON_ALERT}" == "1" ]]; then
  exit 1
fi

exit 0
