# Production Deployment Checklist

## Environment Configuration
- [ ] **Environment Variables**: Ensure all variables in `.env.example` are set in the production environment.
- [ ] **Database URL**: Use a production-managed PostgreSQL instance (e.g., AWS RDS, DigitalOcean Managed DB) instead of a containerized DB if possible for reliability.
- [ ] **NEXT_PUBLIC_API_BASE_URL**: Point this to your production API domain (e.g., `https://api.histolab.icu`).

## Security
- [ ] **JWT Secret**: Generate a strong, random string for `JWT_SECRET_KEY`. Do not use the default "dev-insecure-change-me".
- [ ] **DB Password**: Ensure the database password is strong and rotated periodically.
- [ ] **HTTPS/SSL**: Ensure `certbot` is running and auto-renewing certificates. Verify SSL grades on SSL Labs.
- [ ] **CORS**: Configure CORS in `backend/main.py` to allow only your frontend domain.

## Performance & Reliability
- [ ] **Database Backups**: Configure automated daily/hourly backups.
- [ ] **CDN**: Serve static assets (images, GLB models) via a CDN (e.g., Cloudflare, AWS CloudFront) to reduce server load.
- [ ] **Gzip/Brotli**: Ensure Nginx is configured to compress responses.
- [ ] **Cache Headers**: Configure Nginx to serve static assets with long-expiry cache headers.

## Monitoring
- [ ] **Uptime Monitoring**: Set up a service like UptimeRobot or Better Stack to ping `/health`.
- [ ] **Error Tracking**: Integrate Sentry or similar for backend/frontend error tracking.
- [ ] **Logs**: Ensure logs are persisted and rotated (e.g., via Docker logging drivers or external service).

## CI/CD
- [ ] **CI Pipeline**: Ensure GitHub Actions is running tests on every PR.
- [ ] **Automatic Deployment**: Consider setting up a CD pipeline to deploy to your server on merge to `main`.
