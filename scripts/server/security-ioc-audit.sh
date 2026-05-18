#!/usr/bin/env bash
set -Eeuo pipefail

# IOC and persistence audit for Linux hosts running Luuniensuki LMS.
# Exit codes:
#   0 = clean
#   2 = suspicious indicators found

AUDIT_TAG="luuniensuki-security-audit"
APP_DIR="${APP_DIR:-/opt/luuniensuki-lms}"

findings=0

log() {
  local msg="$*"
  printf '[%s] %s\n' "$(date '+%F %T')" "$msg"
  logger -t "${AUDIT_TAG}" "$msg" || true
}

flag() {
  local msg="$*"
  findings=$((findings + 1))
  log "FINDING #${findings}: ${msg}"
}

check_processes() {
  local out
  out="$(ps auxww | grep -E 'xmrig|kryptex|stratum|kdevtmpfsi|kinsing|systemd -c \.config\.json' | grep -v 'grep -E' || true)"
  if [[ -n "${out}" ]]; then
    flag "Suspicious processes:\n${out}"
  fi
}

neutralize_known_service() {
  local unit_file="/etc/systemd/system/systemd.service"
  local suspicious=0

  if systemctl list-unit-files | grep -q '^systemd\.service'; then
    suspicious=1
  fi
  if [[ -f "${unit_file}" ]] && grep -q "System Proxy Service" "${unit_file}" 2>/dev/null; then
    suspicious=1
  fi

  if [[ "${suspicious}" -eq 1 ]]; then
    flag "Known malicious unit systemd.service detected; applying neutralization"
    systemctl stop systemd.service || true
    systemctl disable systemd.service || true
    systemctl mask systemd.service || true
    rm -f /etc/systemd/system/systemd.service
    rm -f /usr/local/bin/systemd /usr/local/bin/.config.json
    systemctl daemon-reload || true
  fi
}

check_persistence() {
  local out
  out="$(
    grep -RInE 'kryptex|xmrig|stratum|/usr/local/bin/systemd|\.config\.json|System Proxy Service' \
      /etc/systemd /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.weekly /etc/crontab \
      /root/.profile /root/.bashrc /root/.bash_profile /root/.config \
      2>/dev/null | head -n 200 || true
  )"
  if [[ -n "${out}" ]]; then
    flag "Persistence indicators in system config:\n${out}"
  fi
}

check_files() {
  local -a suspects=(
    "/usr/local/bin/systemd"
    "/usr/local/bin/.config.json"
    "/tmp/kdevtmpfsi"
    "/tmp/kinsing"
    "/var/tmp/.javaxxx"
    "/etc/ld.so.preload"
  )

  local path
  for path in "${suspects[@]}"; do
    if [[ -e "${path}" ]]; then
      flag "Suspicious file exists: ${path}"
    fi
  done
}

check_ports() {
  local out
  out="$(
    ss -plant 2>/dev/null | grep -E ':(3333|4444|5555|7777|14444|33333|45560)([[:space:]]|$)' || true
  )"
  if [[ -n "${out}" ]]; then
    flag "Suspicious outbound mining ports in use:\n${out}"
  fi
}

check_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    return 0
  fi

  local out
  out="$(docker ps -a --format '{{.Names}} {{.Image}}' | grep -Ei 'xmrig|miner|kryptex|kinsing|kdevtmpfsi' || true)"
  if [[ -n "${out}" ]]; then
    flag "Suspicious container names/images:\n${out}"
  fi
}

main() {
  log "Starting IOC audit on host $(hostname) (app dir: ${APP_DIR})"

  check_processes
  neutralize_known_service
  check_persistence
  check_files
  check_ports
  check_docker

  if [[ "${findings}" -gt 0 ]]; then
    log "Audit completed with ${findings} finding(s)."
    exit 2
  fi

  log "Audit completed cleanly (0 findings)."
}

main "$@"
