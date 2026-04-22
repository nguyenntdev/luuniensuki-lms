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
