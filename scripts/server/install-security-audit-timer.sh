#!/usr/bin/env bash
set -Eeuo pipefail

# Install systemd timer for scripts/server/security-ioc-audit.sh
# Run as root on target server.

APP_DIR="${APP_DIR:-/opt/luuniensuki-lms}"
AUDIT_SCRIPT="${APP_DIR}/scripts/server/security-ioc-audit.sh"
SERVICE_FILE="/etc/systemd/system/luuniensuki-security-audit.service"
TIMER_FILE="/etc/systemd/system/luuniensuki-security-audit.timer"

[[ "${EUID}" -eq 0 ]] || { echo "Run as root."; exit 1; }
[[ -f "${AUDIT_SCRIPT}" ]] || { echo "Missing ${AUDIT_SCRIPT}"; exit 1; }

chmod +x "${AUDIT_SCRIPT}"

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Luuniensuki IOC Security Audit
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
Environment=APP_DIR=${APP_DIR}
ExecStart=${AUDIT_SCRIPT}
SuccessExitStatus=2
EOF

cat > "${TIMER_FILE}" <<'EOF'
[Unit]
Description=Run Luuniensuki IOC Security Audit daily

[Timer]
OnBootSec=10m
OnCalendar=daily
RandomizedDelaySec=20m
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now luuniensuki-security-audit.timer
systemctl start luuniensuki-security-audit.service || true

echo "Installed security audit service + timer."
systemctl status luuniensuki-security-audit.timer --no-pager
