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
