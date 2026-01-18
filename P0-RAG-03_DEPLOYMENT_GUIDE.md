# P0-RAG-03: Deployment Guide

## Pre-Deployment Checklist

- [ ] Code review completed
- [ ] All files committed to version control
- [ ] Database backup created
- [ ] Deployment window scheduled
- [ ] Stakeholders notified

## Deployment Steps

### 1. Backup Database

**Production:**
```bash
# Create backup
docker-compose exec db pg_dump -U postgres luuniensuki > backup_$(date +%Y%m%d_%H%M%S)_pre_rag03.sql

# Verify backup
ls -lh backup_*_pre_rag03.sql
```

**Development:**
```bash
docker-compose exec db pg_dump -U postgres luuniensuki > dev_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Pull Latest Code

```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
git pull origin main  # or your branch name
```

### 3. Rebuild Docker Images (if needed)

```bash
docker-compose build api
```

### 4. Apply Database Migration

```bash
# Check current migration version
docker-compose exec api alembic current

# Run migration
docker-compose exec api alembic upgrade head

# Verify migration applied
docker-compose exec api alembic current
# Should show: 0015_embedding_jobs (head)
```

### 5. Verify Database Schema

```bash
docker-compose exec db psql -U postgres -d luuniensuki -c "
  SELECT column_name, data_type, is_nullable 
  FROM information_schema.columns 
  WHERE table_name = 'embedding_jobs' 
  ORDER BY ordinal_position;
"
```

Expected output:
```
     column_name      |          data_type          | is_nullable 
----------------------+-----------------------------+-------------
 id                   | uuid                        | NO
 status               | character varying           | NO
 total_documents      | integer                     | NO
 processed_documents  | integer                     | NO
 started_at           | timestamp with time zone    | YES
 completed_at         | timestamp with time zone    | YES
 error_message        | text                        | YES
 created_by_id        | uuid                        | NO
 created_at           | timestamp with time zone    | NO
```

### 6. Restart API Service

```bash
docker-compose restart api

# Wait for service to be ready
sleep 5

# Check logs
docker-compose logs --tail=50 api
```

### 7. Verify API Health

```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}

curl http://localhost:8000/docs
# Should show OpenAPI documentation
```

### 8. Test New Endpoints

#### 8.1 Get Admin Token

```bash
# Login as admin
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"your_password"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

#### 8.2 Test Rebuild Endpoint

```bash
# Start a rebuild job
curl -X POST http://localhost:8000/api/v1/admin/rag/rebuild \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}' \
  | jq .
```

Expected response (202):
```json
{
  "id": "uuid",
  "status": "pending" or "running" or "completed",
  "total_documents": 0,
  "processed_documents": 0,
  ...
}
```

#### 8.3 Test Status Endpoint

```bash
# Get latest job status
curl -X GET http://localhost:8000/api/v1/admin/rag/rebuild/status \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
```

### 9. Verify Data Integrity

```bash
# Check if jobs are being created
docker-compose exec db psql -U postgres -d luuniensuki -c "
  SELECT id, status, total_documents, processed_documents, created_at 
  FROM embedding_jobs 
  ORDER BY created_at DESC 
  LIMIT 5;
"
```

### 10. Monitor Logs

```bash
# Watch logs in real-time
docker-compose logs -f api

# Look for:
# - No error messages
# - Successful job creation
# - Progress updates
```

## Post-Deployment Verification

### Functional Tests

- [ ] POST /api/v1/admin/rag/rebuild returns 202
- [ ] GET /api/v1/admin/rag/rebuild/status returns 200 or 404
- [ ] GET /api/v1/admin/rag/rebuild/{job_id} returns 200 or 404
- [ ] Non-admin users get 403 error
- [ ] Unauthenticated requests get 401 error
- [ ] Progress percentage is calculated correctly
- [ ] Job status transitions correctly
- [ ] Embeddings are actually updated

### Database Tests

```bash
# Verify foreign key constraint
docker-compose exec db psql -U postgres -d luuniensuki -c "
  SELECT conname, contype 
  FROM pg_constraint 
  WHERE conrelid = 'embedding_jobs'::regclass;
"

# Verify indexes
docker-compose exec db psql -U postgres -d luuniensuki -c "
  SELECT indexname, indexdef 
  FROM pg_indexes 
  WHERE tablename = 'embedding_jobs';
"
```

### Performance Tests

```bash
# Test with small dataset
curl -X POST http://localhost:8000/api/v1/admin/rag/rebuild \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'

# Monitor response time (should be < 30s for 100 documents)
time curl -X POST http://localhost:8000/api/v1/admin/rag/rebuild \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": true}'
```

## Rollback Procedure

If issues are encountered:

### 1. Rollback Migration

```bash
# Downgrade to previous version
docker-compose exec api alembic downgrade -1

# Verify
docker-compose exec api alembic current
```

### 2. Restore Database (if needed)

```bash
# Stop services
docker-compose stop api

# Restore from backup
docker-compose exec -T db psql -U postgres luuniensuki < backup_*_pre_rag03.sql

# Restart services
docker-compose start api
```

### 3. Revert Code Changes

```bash
git revert <commit-hash>
# or
git reset --hard <previous-commit>
```

## Troubleshooting

### Issue: Migration fails

**Symptoms:** `alembic upgrade head` returns error

**Solution:**
```bash
# Check current version
docker-compose exec api alembic current

# Check migration history
docker-compose exec api alembic history

# Try manual migration
docker-compose exec db psql -U postgres -d luuniensuki
# Run SQL from migration file manually
```

### Issue: API won't start after deployment

**Symptoms:** `docker-compose logs api` shows import errors

**Solution:**
```bash
# Check syntax errors
docker-compose exec api python -m py_compile backend/services/embeddings.py

# Rebuild image
docker-compose build --no-cache api
docker-compose up -d api
```

### Issue: Endpoints return 500 error

**Symptoms:** API returns Internal Server Error

**Solution:**
```bash
# Check logs
docker-compose logs --tail=100 api

# Check database connection
docker-compose exec api python -c "from backend.config import settings; print(settings.database_url)"

# Test database connection
docker-compose exec db psql -U postgres -d luuniensuki -c "SELECT 1;"
```

### Issue: Jobs stuck in "running" status

**Symptoms:** Job never completes

**Solution:**
```bash
# Check logs for errors
docker-compose logs api | grep -i "embedding"

# Manually update job status
docker-compose exec db psql -U postgres -d luuniensuki -c "
  UPDATE embedding_jobs 
  SET status = 'failed', 
      error_message = 'Manually failed - stuck in running',
      completed_at = NOW()
  WHERE status = 'running' AND started_at < NOW() - INTERVAL '1 hour';
"
```

## Monitoring

### Key Metrics to Watch

1. **API Response Times**: Should remain < 200ms for status checks
2. **Database Connections**: Monitor connection pool usage
3. **Memory Usage**: Watch for memory leaks during rebuild
4. **Error Rate**: Monitor 500 errors in logs

### Monitoring Commands

```bash
# Watch API logs
docker-compose logs -f api | grep -E "ERROR|WARNING|embedding"

# Monitor database connections
docker-compose exec db psql -U postgres -c "
  SELECT count(*) as connections 
  FROM pg_stat_activity 
  WHERE datname = 'luuniensuki';
"

# Check job statistics
docker-compose exec db psql -U postgres -d luuniensuki -c "
  SELECT status, COUNT(*) 
  FROM embedding_jobs 
  GROUP BY status;
"
```

## Success Criteria

- ✅ Migration applied successfully
- ✅ No errors in API logs
- ✅ All endpoints return expected responses
- ✅ Database schema matches specification
- ✅ Jobs are created and tracked correctly
- ✅ Embeddings are updated as expected
- ✅ Performance is acceptable
- ✅ No data loss or corruption

## Sign-Off

- [ ] Deployment completed successfully
- [ ] All tests passed
- [ ] Monitoring in place
- [ ] Documentation updated
- [ ] Team notified
- [ ] Deployment notes recorded

## Contact

For issues during deployment, contact:
- DevOps Team: [contact info]
- Backend Team: [contact info]
- On-Call Engineer: [contact info]

