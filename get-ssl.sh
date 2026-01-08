#!/bin/bash
set -e

# =============================================================================
# SSL Certificate Script for Luuniensuki LMS
# Run this script ON THE SERVER after the main setup is complete
# =============================================================================

DOMAIN="lms.histolab.icu"
APP_DIR="/opt/luuniensuki-lms"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"

echo "=========================================="
echo "  Let's Encrypt SSL Certificate Setup"
echo "  Domain: $DOMAIN"
echo "=========================================="

cd "$APP_DIR"

# Check if containers are running
if ! docker compose -f "$COMPOSE_FILE" -f docker-compose.override.yml --env-file "$ENV_FILE" ps | grep -q "nginx"; then
    echo "ERROR: Nginx container is not running!"
    echo "Please run ./remote-setup.sh first"
    exit 1
fi

# Prompt for email
read -p "Enter your email for Let's Encrypt notifications: " CERT_EMAIL

if [ -z "$CERT_EMAIL" ]; then
    echo "ERROR: Email is required for Let's Encrypt"
    exit 1
fi

echo ""
echo "Requesting SSL certificate from Let's Encrypt..."
echo ""

# Request certificate using certbot
docker run --rm \
    -v "$APP_DIR/certbot/www:/var/www/certbot" \
    -v "$APP_DIR/certbot/conf:/etc/letsencrypt" \
    certbot/certbot certonly --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    --email "$CERT_EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal

# Restart nginx to use the new certificate
echo ""
echo "Restarting Nginx with new certificate..."
docker compose -f "$COMPOSE_FILE" -f docker-compose.override.yml --env-file "$ENV_FILE" restart nginx

sleep 5

# Verify SSL
echo ""
echo "Verifying SSL certificate..."
if curl -s "https://$DOMAIN/health" > /dev/null 2>&1; then
    echo "✓ SSL certificate is working!"
else
    echo "SSL verification pending. It may take a moment to propagate."
fi

echo ""
echo "=========================================="
echo "  SSL Certificate Installed!"
echo "=========================================="
echo ""
echo "Your site is now available at: https://$DOMAIN"
echo ""
echo "Certificate auto-renewal:"
echo "Add this to crontab (crontab -e):"
echo ""
echo "0 0 1 * * cd $APP_DIR && docker run --rm -v \"$APP_DIR/certbot/www:/var/www/certbot\" -v \"$APP_DIR/certbot/conf:/etc/letsencrypt\" certbot/certbot renew --quiet && docker compose -f $COMPOSE_FILE restart nginx"
echo ""
