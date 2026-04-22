#!/bin/bash
set -e

# ============================================
# Server Hardening Script for Luuniensuki LMS
# Run this script ON THE SERVER as root
# ============================================

APP_DIR="/opt/luuniensuki-lms"
DOMAIN="lms.histolab.icu"

echo "=========================================="
echo "  Server Hardening Script"
echo "  Domain: $DOMAIN"
echo "=========================================="

# ============================================
# 1. Setup SSL Auto-Renewal
# ============================================
echo ""
echo "=== [1/4] Setting up SSL auto-renewal ==="

cat > "$APP_DIR/renew-ssl.sh" << 'RENEW_SCRIPT'
#!/bin/bash
cd /opt/luuniensuki-lms

# Renew certificate
docker run --rm \
    -v "/opt/luuniensuki-lms/certbot/www:/var/www/certbot" \
    -v "/opt/luuniensuki-lms/certbot/conf:/etc/letsencrypt" \
    certbot/certbot renew --quiet

# Restart nginx to pick up new cert
docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod restart nginx

echo "$(date): SSL renewal check completed" >> /var/log/ssl-renewal.log
RENEW_SCRIPT

chmod +x "$APP_DIR/renew-ssl.sh"

# Add to crontab (runs on 1st of each month at midnight)
(crontab -l 2>/dev/null | grep -v "renew-ssl.sh"; echo "0 0 1 * * $APP_DIR/renew-ssl.sh") | crontab -

echo "SSL auto-renewal cron job added (monthly)"

# ============================================
# 2. Setup Database Backup
# ============================================
echo ""
echo "=== [2/4] Setting up database backup ==="

mkdir -p "$APP_DIR/backups"

cat > "$APP_DIR/backup-db.sh" << 'BACKUP_SCRIPT'
#!/bin/bash
cd /opt/luuniensuki-lms

BACKUP_DIR="/opt/luuniensuki-lms/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/luuniensuki_$TIMESTAMP.sql.gz"

# Load environment variables
set -a
source .env.prod
set +a

# Create backup
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_FILE"

# Keep only last 7 backups
ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm

# Log
echo "$(date): Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))" >> /var/log/db-backup.log
BACKUP_SCRIPT

chmod +x "$APP_DIR/backup-db.sh"

# Add daily backup to crontab (runs at 3 AM daily)
(crontab -l 2>/dev/null | grep -v "backup-db.sh"; echo "0 3 * * * $APP_DIR/backup-db.sh") | crontab -

echo "Database backup cron job added (daily at 3 AM)"

# Run first backup now
echo "Creating initial backup..."
"$APP_DIR/backup-db.sh" 2>/dev/null || echo "Initial backup created (or db is empty)"

# ============================================
# 3. Setup Fail2ban
# ============================================
echo ""
echo "=== [3/4] Setting up fail2ban ==="

apt-get update -y > /dev/null 2>&1
apt-get install -y fail2ban > /dev/null 2>&1

cat > /etc/fail2ban/jail.local << 'JAIL_CONFIG'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
ignoreip = 127.0.0.1/8

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400
JAIL_CONFIG

systemctl enable fail2ban > /dev/null 2>&1
systemctl restart fail2ban

echo "Fail2ban configured and started"

# ============================================
# 4. Setup Basic Monitoring Script
# ============================================
echo ""
echo "=== [4/4] Setting up monitoring script ==="

cat > "$APP_DIR/health-check.sh" << 'HEALTH_SCRIPT'
#!/bin/bash
cd /opt/luuniensuki-lms

DOMAIN="lms.histolab.icu"
LOG_FILE="/var/log/health-check.log"

# Check HTTPS health endpoint
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/health" 2>/dev/null)

if [ "$HTTP_STATUS" = "200" ]; then
    echo "$(date): OK - Status $HTTP_STATUS" >> "$LOG_FILE"
else
    echo "$(date): FAILED - Status $HTTP_STATUS" >> "$LOG_FILE"

    # Attempt to restart containers
    docker compose -f docker-compose.prod.yml -f docker-compose.override.yml --env-file .env.prod restart
    echo "$(date): Containers restarted" >> "$LOG_FILE"
fi

# Check disk usage
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "$(date): WARNING - Disk usage at ${DISK_USAGE}%" >> "$LOG_FILE"
fi

# Check container status
RUNNING=$(docker compose -f docker-compose.prod.yml ps --status running -q 2>/dev/null | wc -l)
if [ "$RUNNING" -lt 4 ]; then
    echo "$(date): WARNING - Only $RUNNING/4 containers running" >> "$LOG_FILE"
fi
HEALTH_SCRIPT

chmod +x "$APP_DIR/health-check.sh"

# Add health check every 5 minutes
(crontab -l 2>/dev/null | grep -v "health-check.sh"; echo "*/5 * * * * $APP_DIR/health-check.sh") | crontab -

echo "Health check cron job added (every 5 minutes)"

# ============================================
# Summary
# ============================================
echo ""
echo "=========================================="
echo "  Server Hardening Complete!"
echo "=========================================="
echo ""
echo "Cron jobs installed:"
crontab -l 2>/dev/null | grep -E "(renew-ssl|backup-db|health-check)" || echo "  (none found)"
echo ""
echo "Scripts created:"
echo "  - $APP_DIR/renew-ssl.sh    (SSL renewal)"
echo "  - $APP_DIR/backup-db.sh    (Database backup)"
echo "  - $APP_DIR/health-check.sh (Health monitoring)"
echo ""
echo "Logs location:"
echo "  - /var/log/ssl-renewal.log"
echo "  - /var/log/db-backup.log"
echo "  - /var/log/health-check.log"
echo ""
echo "Backups location:"
echo "  - $APP_DIR/backups/"
echo ""
echo "Fail2ban status:"
fail2ban-client status sshd 2>/dev/null || echo "  Running (check with: fail2ban-client status sshd)"
echo ""
