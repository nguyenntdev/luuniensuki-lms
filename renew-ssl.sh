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
