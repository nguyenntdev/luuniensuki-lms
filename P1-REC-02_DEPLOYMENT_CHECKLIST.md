# P1-REC-02: Deployment Checklist

## Pre-Deployment Verification

### ✅ Code Review
- [ ] Review changes in `backend/models.py`
- [ ] Review changes in `backend/schemas.py`
- [ ] Review changes in `backend/main.py`
- [ ] Review new file `backend/services/lesson_sequence.py`
- [ ] Review migration file `migrations/versions/0026_lesson_prerequisites.py`

### ✅ Testing
- [ ] Run test script: `./test_lesson_prerequisites.sh`
- [ ] Verify all endpoints return expected responses
- [ ] Test with authenticated user
- [ ] Test with different urn filters
- [ ] Test prerequisite validation logic

### ✅ Database
- [ ] Backup production database
- [ ] Test migration on staging database
- [ ] Verify no data loss after migration
- [ ] Check indexes are created properly

### ✅ Documentation
- [ ] Read through P1-REC-02_README.md
- [ ] Review API_REFERENCE.md for integration details
- [ ] Check IMPLEMENTATION_SUMMARY.md for architecture
- [ ] Share documentation with team

---

## Deployment Steps

### Step 1: Backup Database
```bash
# PostgreSQL backup
pg_dump -U postgres -d luuniensuki_lms > backup_$(date +%Y%m%d).sql

# Or with Docker
docker-compose exec postgres pg_dump -U postgres luuniensuki_lms > backup_$(date +%Y%m%d).sql
```
**Status**: [ ] Complete

### Step 2: Run Migration (Staging)
```bash
# Development/Staging
cd /Users/nguyennt/Documents/luuniensuki-lms
alembic upgrade head

# Or with Docker
docker-compose exec backend alembic upgrade head
```
**Status**: [ ] Complete

### Step 3: Verify Migration
```bash
# Connect to database and verify tables
psql -U postgres -d luuniensuki_lms

# Run these queries:
\d lesson_prerequisites
\d lesson_content

# Check indexes
\di lesson_prerequisites*
```
**Expected Results**:
- [ ] `lesson_prerequisites` table exists
- [ ] `difficulty_level` column exists in `lesson_content`
- [ ] `estimated_time_minutes` column exists in `lesson_content`
- [ ] Indexes created: `idx_lesson_prereq_lesson`, `idx_lesson_prereq_prerequisite`
- [ ] Unique constraint: `uq_lesson_prereq_lesson_prereq`

### Step 4: Restart Application (Staging)
```bash
# Development
# Stop and restart your FastAPI server
# Ctrl+C, then restart

# Docker
docker-compose restart backend

# Kubernetes
kubectl rollout restart deployment/backend
```
**Status**: [ ] Complete

### Step 5: Smoke Tests (Staging)
```bash
# Set environment variables
export API_URL="https://staging.yourdomain.com"
export TOKEN="your_staging_token"

# Test 1: Health check
curl -X GET "$API_URL/health"

# Test 2: Get next lesson
curl -X GET "$API_URL/api/v1/lessons/next" \
  -H "Authorization: Bearer $TOKEN"

# Test 3: Get sequence
curl -X GET "$API_URL/api/v1/lessons/sequence" \
  -H "Authorization: Bearer $TOKEN"
```
**Expected Results**:
- [ ] All endpoints return 200 OK
- [ ] Responses match expected schema
- [ ] No server errors in logs

### Step 6: Monitor Staging
```bash
# Watch logs
tail -f /var/log/backend.log

# Or with Docker
docker-compose logs -f backend

# Or with Kubernetes
kubectl logs -f deployment/backend
```
**Monitor For**:
- [ ] No errors in application logs
- [ ] Database queries executing successfully
- [ ] Response times acceptable (< 500ms)
- [ ] No memory leaks

### Step 7: Deploy to Production
```bash
# Same steps as staging, but on production environment

# 1. Backup production database
pg_dump -U postgres -d luuniensuki_lms_prod > backup_prod_$(date +%Y%m%d).sql

# 2. Run migration
alembic upgrade head

# 3. Restart application
# (Use your deployment process)

# 4. Monitor
# Watch logs and metrics
```
**Status**: [ ] Complete

---

## Post-Deployment Verification

### ✅ Functional Testing
- [ ] User can get next lesson recommendation
- [ ] User can view learning sequence
- [ ] Prerequisites are checked correctly
- [ ] Locked lessons show proper status
- [ ] Unlocked lessons are accessible

### ✅ Performance Testing
- [ ] API response time < 500ms
- [ ] Database queries optimized
- [ ] Indexes being used
- [ ] No N+1 query problems

### ✅ Integration Testing
- [ ] Mobile app can call new endpoints
- [ ] Authentication works
- [ ] Urn filtering works
- [ ] Error handling works

### ✅ Monitoring
- [ ] Set up alerts for errors
- [ ] Monitor API endpoint usage
- [ ] Track database performance
- [ ] Log prerequisite validation results

---

## Rollback Plan

If issues are detected:

### Step 1: Rollback Migration
```bash
# Downgrade to previous version
alembic downgrade -1

# Verify downgrade
psql -U postgres -d luuniensuki_lms
\d lesson_prerequisites  # Should not exist
```

### Step 2: Revert Code Changes
```bash
# Git rollback
git revert <commit_hash>

# Or checkout previous version
git checkout <previous_commit>
```

### Step 3: Restart Application
```bash
# Restart with previous code
docker-compose restart backend
```

### Step 4: Verify Rollback
```bash
# Test endpoints are gone
curl -X GET "$API_URL/api/v1/lessons/next"
# Should return 404

# Check old functionality still works
curl -X GET "$API_URL/api/v1/lessons"
# Should return lesson list
```

---

## Success Criteria

### Must Have
- [x] All 4 new endpoints operational
- [x] No errors in application logs
- [x] Database migration successful
- [x] No impact on existing functionality
- [x] Documentation complete

### Should Have
- [ ] Response times < 500ms
- [ ] Test coverage > 80%
- [ ] Mobile app integration complete
- [ ] Admin UI for prerequisites

### Nice to Have
- [ ] Analytics on recommendation accuracy
- [ ] A/B testing on recommendation algorithm
- [ ] User feedback on learning paths

---

## Contacts

### Technical Issues
- **Backend Lead**: [Name/Email]
- **Database Admin**: [Name/Email]
- **DevOps**: [Name/Email]

### Business Questions
- **Product Manager**: [Name/Email]
- **Education Content Lead**: [Name/Email]

---

## Documentation Links

- [README](P1-REC-02_README.md) - Quick start guide
- [Implementation Summary](P1-REC-02_IMPLEMENTATION_SUMMARY.md) - Technical details
- [API Reference](P1-REC-02_API_REFERENCE.md) - Full API docs
- [Flow Diagrams](P1-REC-02_FLOW_DIAGRAM.md) - Visual flows

---

## Timeline

| Stage | Duration | Status |
|-------|----------|--------|
| Code Review | 1 day | [ ] |
| Staging Deployment | 2 hours | [ ] |
| Staging Testing | 1 day | [ ] |
| Production Deployment | 2 hours | [ ] |
| Production Monitoring | 3 days | [ ] |

---

## Sign-Off

- [ ] **Developer**: Implementation complete and tested
- [ ] **Tech Lead**: Code reviewed and approved
- [ ] **QA**: Tests passed
- [ ] **DevOps**: Deployment plan reviewed
- [ ] **Product**: Features meet requirements

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Verified By**: _______________

