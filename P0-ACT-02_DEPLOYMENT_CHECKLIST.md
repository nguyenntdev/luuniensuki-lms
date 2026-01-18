# P0-ACT-02: Guest Preview - Deployment Checklist

## Pre-Deployment

### Code Review
- [ ] Review all model changes in `backend/models.py`
- [ ] Review all schema definitions in `backend/schemas.py`
- [ ] Review all API endpoints in `backend/main.py`
- [ ] Review migration file `migrations/versions/0022_guest_preview.py`
- [ ] Verify imports are correct in all files
- [ ] Check for any syntax errors or linting issues

### Testing
- [ ] Run test script: `./test_guest_preview.sh`
- [ ] Test GET `/api/v1/preview/lesson` endpoint
- [ ] Test POST `/api/v1/preview/start` endpoint
- [ ] Test POST `/api/v1/preview/complete` endpoint
- [ ] Test POST `/api/v1/preview/convert` endpoint
- [ ] Verify error handling for edge cases
- [ ] Test with invalid session IDs
- [ ] Test with missing authentication on `/convert`

### Database
- [ ] Backup production database
- [ ] Review migration SQL
- [ ] Test migration on development database
- [ ] Verify rollback migration works
- [ ] Check database performance impact
- [ ] Review index creation strategy

## Deployment Steps

### 1. Database Migration

```bash
# Connect to server
ssh your-server

# Navigate to project directory
cd /path/to/luuniensuki-lms

# Backup database
pg_dump -U postgres -d luuniensuki_lms > backup_before_p0_act_02.sql

# Run migration
alembic upgrade head

# Verify migration
alembic current
# Should show: 0022 (head)

# Check tables
psql -U postgres -d luuniensuki_lms -c "\d guest_previews"
psql -U postgres -d luuniensuki_lms -c "\d lesson_content"
```

### 2. Backend Deployment

```bash
# Pull latest code
git pull origin main

# Install any new dependencies (if any)
pip install -r backend/requirements.txt

# Restart backend service
sudo systemctl restart luuniensuki-backend

# Check status
sudo systemctl status luuniensuki-backend

# Check logs
sudo journalctl -u luuniensuki-backend -f
```

### 3. Smoke Tests

```bash
# Test preview endpoints
curl https://your-domain.com/api/v1/preview/lesson

# If you get 404, mark a lesson as preview-eligible (see below)
```

### 4. Mark Preview Lesson

```bash
# Connect to database
psql -U postgres -d luuniensuki_lms

# Find a good lesson to mark as preview
SELECT lc.id, m.name as motif_name, u.name as urn_name
FROM lesson_content lc
JOIN motifs m ON lc.motif_id = m.id
JOIN urns u ON m.urn_id = u.id
WHERE lc.is_published = true
ORDER BY lc.created_at
LIMIT 10;

# Mark lesson as preview-eligible
UPDATE lesson_content 
SET preview_eligible = true 
WHERE id = 'YOUR_CHOSEN_LESSON_ID';

# Verify
SELECT id, preview_eligible FROM lesson_content WHERE preview_eligible = true;
```

## Post-Deployment

### Verification
- [ ] Verify GET `/api/v1/preview/lesson` returns a lesson
- [ ] Verify can start a preview session
- [ ] Verify can complete a preview session
- [ ] Verify can convert after signup
- [ ] Check database for preview records
- [ ] Verify indexes were created correctly
- [ ] Test from production mobile app (if applicable)
- [ ] Test from production web app (if applicable)

### Monitoring
- [ ] Set up monitoring for preview endpoints
- [ ] Track preview start rate
- [ ] Track preview completion rate
- [ ] Track conversion rate
- [ ] Monitor API errors
- [ ] Monitor database performance
- [ ] Set up alerts for errors

### Analytics
- [ ] Create dashboard for preview metrics
- [ ] Track daily preview sessions
- [ ] Track conversion funnel
- [ ] Monitor device distribution
- [ ] Track time to complete
- [ ] Identify drop-off points

## Rollback Plan

If issues arise, rollback with:

```bash
# Rollback database migration
alembic downgrade -1

# This will:
# - Drop guest_previews table
# - Remove preview_eligible column from lesson_content
# - Drop all related indexes

# Revert code changes
git revert <commit-hash>

# Restart backend
sudo systemctl restart luuniensuki-backend
```

## Configuration

### Environment Variables

No new environment variables required.

### Rate Limiting (Optional)

If using nginx or API gateway, add rate limiting:

```nginx
# Example nginx rate limiting
limit_req_zone $binary_remote_addr zone=preview_lesson:10m rate=100r/h;
limit_req_zone $binary_remote_addr zone=preview_start:10m rate=20r/h;

location /api/v1/preview/lesson {
    limit_req zone=preview_lesson burst=10;
}

location /api/v1/preview/start {
    limit_req zone=preview_start burst=5;
}
```

## Documentation Updates

- [ ] Update API documentation
- [ ] Update mobile app documentation
- [ ] Update frontend documentation
- [ ] Add to changelog
- [ ] Update version number
- [ ] Notify team of new feature

## User Communication

- [ ] Prepare announcement for new preview feature
- [ ] Update marketing materials
- [ ] Create demo video/tutorial
- [ ] Update onboarding flow
- [ ] Prepare support documentation
- [ ] Train customer support team

## Success Metrics (First Week)

Monitor these KPIs:

- [ ] Total preview sessions started: Target > 100
- [ ] Preview completion rate: Target > 60%
- [ ] Preview-to-signup conversion rate: Target > 10%
- [ ] Average time to complete: Target 3-5 minutes
- [ ] Error rate: Target < 1%
- [ ] API response time: Target < 200ms

## Troubleshooting

### Issue: "No preview lesson available"

**Solution:** Mark at least one lesson as preview-eligible

```sql
UPDATE lesson_content SET preview_eligible = true 
WHERE is_published = true LIMIT 1;
```

### Issue: Migration fails

**Solution:** Check database connection and permissions

```bash
# Check connection
psql -U postgres -d luuniensuki_lms -c "SELECT version();"

# Check if tables already exist
psql -U postgres -d luuniensuki_lms -c "\dt guest_previews"
```

### Issue: Preview sessions not converting

**Solution:** Verify session_id is being passed correctly and user is authenticated

```bash
# Check preview sessions
psql -U postgres -d luuniensuki_lms -c "SELECT * FROM guest_previews ORDER BY created_at DESC LIMIT 5;"
```

## Support Contacts

- **Backend Team:** backend@example.com
- **DevOps Team:** devops@example.com
- **Product Team:** product@example.com

---

**Deployment Date:** _________________  
**Deployed By:** _________________  
**Version:** 1.0.0  
**Status:** [ ] Complete

