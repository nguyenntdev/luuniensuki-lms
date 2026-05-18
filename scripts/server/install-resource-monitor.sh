#!/usr/bin/env bash
set -Eeuo pipefail

# Install systemd timer for scripts/server/resource-monitor.sh
# Run as root on the target server.

APP_DIR="${APP_DIR:-/opt/luuniensuki-lms}"
MONITOR_SCRIPT="${APP_DIR}/scripts/server/resource-monitor.sh"
ENV_FILE="/etc/luuniensuki-monitor.env"
SERVICE_FILE="/etc/systemd/system/luuniensuki-monitor.service"
TIMER_FILE="/etc/systemd/system/luuniensuki-monitor.timer"

[[ "${EUID}" -eq 0 ]] || { echo "Run as root."; exit 1; }
[[ -f "${MONITOR_SCRIPT}" ]] || { echo "Missing ${MONITOR_SCRIPT}"; exit 1; }

chmod +x "${MONITOR_SCRIPT}"

if [[ ! -f "${ENV_FILE}" ]]; then
  cat > "${ENV_FILE}" <<'EOF'
# Thresholds
DISK_WARN_PCT=88
MEM_WARN_PCT=92
SWAP_WARN_PCT=80
MIN_FREE_GB=2
MAX_LOAD_1M=8

# Internal health endpoint (uses local TLS)
CHECK_URL=https://127.0.0.1:8443/health

# Optional webhook for alerts (Slack/Discord/custom)
ALERT_WEBHOOK_URL=

# Set to 1 if you want service failures when alerts occur
FAIL_ON_ALERT=0
EOF
  chmod 600 "${ENV_FILE}"
fi

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Luuniensuki Resource Monitor
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
Environment=APP_DIR=${APP_DIR}
Environment=ENV_PATH=${ENV_FILE}
ExecStart=${MONITOR_SCRIPT}
SuccessExitStatus=1
EOF

cat > "${TIMER_FILE}" <<'EOF'
[Unit]
Description=Run Luuniensuki Resource Monitor every 5 minutes

[Timer]
OnBootSec=2m
OnUnitActiveSec=5m
AccuracySec=30s
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now luuniensuki-monitor.timer
systemctl start luuniensuki-monitor.service || true

echo "Installed monitor service + timer."
systemctl status luuniensuki-monitor.timer --no-pager
