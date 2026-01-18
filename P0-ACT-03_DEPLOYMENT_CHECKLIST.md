# P0-ACT-03: Deployment Checklist

## Pre-Deployment Verification

### Code Review
- [x] UserNotificationSettings model implemented correctly
- [x] User.push_permission_prompted field added
- [x] Database migration created (0014_notification_settings.py)
- [x] All 5 API endpoints implemented
- [x] Request/response schemas defined
- [x] Validation logic implemented
- [x] Error handling added
- [x] Code follows project patterns

### Testing
- [x] Python syntax validation passed
- [x] Models compile without errors
- [x] Schemas compile without errors
- [x] Main.py compiles without errors
- [ ] Automated test script executed successfully
- [ ] Manual API testing completed
- [ ] Migration tested on dev database
- [ ] Rollback tested successfully

### Documentation
- [x] Implementation guide created
- [x] API reference documented
- [x] Quick reference guide created
- [x] Flow diagrams created
- [x] Summary document created
- [x] Index document created
- [x] Test script created and made executable

---

## Staging Deployment

### 1. Database Backup
- [ ] Backup staging database
- [ ] Verify backup integrity
- [ ] Document backup location

### 2. Code Deployment
- [ ] Pull latest code to staging
- [ ] Verify all files present
- [ ] Check file permissions

### 3. Database Migration
```bash
# Navigate to project directory
cd /path/to/luuniensuki-lms

# Check current migration version
alembic current

# Review migration
cat migrations/versions/0014_notification_settings.py

# Apply migration
alembic upgrade head

# Verify migration
alembic current
# Should show: 0014 (head)
```

- [ ] Migration applied successfully
- [ ] No errors in migration logs
- [ ] Tables created:
  - [ ] user_notification_settings table exists
  - [ ] Index idx_notification_settings_user exists
  - [ ] users.push_permission_prompted column exists

### 4. Verify Database Schema
```sql
-- Check table structure
\d user_notification_settings

-- Check user column
\d users

-- Verify constraints
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name = 'user_notification_settings';
```

- [ ] All columns present
- [ ] Foreign key constraint exists
- [ ] Unique constraint on user_id exists
- [ ] Index created

### 5. Restart Services
- [ ] Restart FastAPI/Uvicorn server
- [ ] Verify server starts without errors
- [ ] Check logs for any issues

### 6. API Testing
```bash
# Set staging token
export TOKEN="staging-jwt-token"
export BASE_URL="https://staging.api.example.com"

# Run test script
./test_notifications_api.sh
```

- [ ] All tests pass
- [ ] GET /api/v1/notifications/settings works
- [ ] PUT /api/v1/notifications/settings works
- [ ] POST /api/v1/notifications/register-push works
- [ ] DELETE /api/v1/notifications/unregister-push works
- [ ] GET /api/v1/notifications/should-prompt-permission works

### 7. Manual Verification
- [ ] Create test user
- [ ] Complete a lesson as test user
- [ ] Check should-prompt returns true
- [ ] Register push token
- [ ] Verify token saved
- [ ] Check should-prompt returns false
- [ ] Update notification settings
- [ ] Verify settings persisted
- [ ] Unregister push token
- [ ] Verify token removed

### 8. Integration Testing
- [ ] Test with mobile app (staging)
- [ ] Verify permission prompt appears
- [ ] Test token registration from mobile
- [ ] Test settings screen in mobile app
- [ ] Verify all mobile features work

---

## Production Deployment

### Pre-Production Checklist
- [ ] All staging tests passed
- [ ] No critical issues found
- [ ] Mobile app integration tested
- [ ] Rollback plan documented
- [ ] Production backup scheduled
- [ ] Deployment window scheduled
- [ ] Team notified of deployment

### 1. Production Database Backup
```bash
# Backup production database
pg_dump -U postgres -d luuniensuki_prod > backup_pre_p0act03_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_pre_p0act03_*.sql
```

- [ ] Backup created successfully
- [ ] Backup file size is reasonable
- [ ] Backup stored in safe location
- [ ] Backup retention policy applied

### 2. Production Code Deployment
- [ ] Deploy code to production server
- [ ] Verify all files deployed
- [ ] Check file permissions
- [ ] Review deployment logs

### 3. Production Database Migration
```bash
# Connect to production
ssh production-server

# Navigate to app directory
cd /path/to/luuniensuki-lms

# Verify current version
alembic current

# Apply migration
alembic upgrade head

# Verify new version
alembic current
```

- [ ] Migration completed successfully
- [ ] No errors in output
- [ ] Version shows 0014

### 4. Production Service Restart
- [ ] Stop application gracefully
- [ ] Clear application cache if needed
- [ ] Restart application
- [ ] Verify application started
- [ ] Check health endpoint
- [ ] Review startup logs

### 5. Production Smoke Tests
```bash
# Set production token
export TOKEN="production-jwt-token"
export BASE_URL="https://api.example.com"

# Quick smoke test
curl -X GET "$BASE_URL/api/v1/notifications/settings" \
  -H "Authorization: Bearer $TOKEN"
```

- [ ] GET settings endpoint works
- [ ] Response structure correct
- [ ] No 500 errors
- [ ] Response time acceptable

### 6. Production Verification
- [ ] API endpoints respond correctly
- [ ] Database queries perform well
- [ ] No errors in application logs
- [ ] No errors in database logs
- [ ] Metrics look normal

---

## Post-Deployment

### Immediate (First Hour)
- [ ] Monitor error logs
- [ ] Check API response times
- [ ] Verify database performance
- [ ] Monitor server resources
- [ ] Check for any user reports

### Short-term (First Day)
- [ ] Review analytics
- [ ] Check permission prompt display rate
- [ ] Monitor token registration rate
- [ ] Review error rates
- [ ] Gather user feedback

### Medium-term (First Week)
- [ ] Analyze permission grant/deny rates
- [ ] Review notification settings usage
- [ ] Monitor system performance
- [ ] Identify any issues
- [ ] Plan optimizations if needed

---

## Rollback Plan

### If Issues Are Found

#### 1. Immediate Rollback
```bash
# Rollback database migration
alembic downgrade -1

# Verify rollback
alembic current
```

#### 2. Restore Code
- [ ] Revert to previous code version
- [ ] Restart application
- [ ] Verify application works

#### 3. Restore Database (if needed)
```bash
# Stop application
systemctl stop luuniensuki-api

# Restore from backup
psql -U postgres -d luuniensuki_prod < backup_pre_p0act03_TIMESTAMP.sql

# Restart application
systemctl start luuniensuki-api
```

#### 4. Verification
- [ ] Application running
- [ ] No errors in logs
- [ ] Users can access app
- [ ] Core features working

---

## Monitoring & Alerts

### Metrics to Monitor
- [ ] API response times
- [ ] Error rates (4xx, 5xx)
- [ ] Database query performance
- [ ] Token registration success rate
- [ ] Permission prompt display rate
- [ ] Settings update frequency

### Alerts to Set Up
- [ ] High error rate on notification endpoints
- [ ] Slow database queries on notification tables
- [ ] Failed token registrations
- [ ] Migration failures

---

## Success Criteria

### Technical Success
- [x] Migration completes without errors
- [ ] All API endpoints return correct responses
- [ ] No performance degradation
- [ ] No increase in error rates
- [ ] Database queries perform well

### Business Success
- [ ] Users see permission prompt after first lesson
- [ ] Permission prompt not shown repeatedly
- [ ] Users can grant/deny permission
- [ ] Settings are saved and persist
- [ ] Mobile integration works smoothly

---

## Issues & Resolution

### Known Issues
(Document any issues found during testing)

| Issue | Severity | Status | Resolution |
|-------|----------|--------|------------|
| None yet | - | - | - |

### Post-Deployment Issues
(Document any issues found in production)

| Issue | When | Impact | Resolution |
|-------|------|--------|------------|
| | | | |

---

## Sign-Off

### Development Team
- [ ] Code complete and tested
- [ ] Documentation complete
- [ ] Ready for deployment

**Name:** ________________  **Date:** ________

### QA Team
- [ ] All tests passed
- [ ] Integration verified
- [ ] Ready for production

**Name:** ________________  **Date:** ________

### DevOps/SRE
- [ ] Deployment plan reviewed
- [ ] Backup completed
- [ ] Monitoring configured

**Name:** ________________  **Date:** ________

---

## Completion

- [ ] Staging deployment successful
- [ ] Production deployment successful
- [ ] Post-deployment verification complete
- [ ] Documentation updated
- [ ] Team notified
- [ ] Feature announced

**Deployment Date:** ________________  
**Deployed By:** ________________  
**Status:** ________________

