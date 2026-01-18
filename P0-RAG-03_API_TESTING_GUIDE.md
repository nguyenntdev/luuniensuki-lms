# P0-RAG-03: API Testing Guide

## Prerequisites

1. **Admin Access**: You need an admin user account
2. **Authentication**: Valid JWT access token
3. **API Running**: Backend API must be running
4. **Documents**: At least one RAG document in the database

## Setup

### 1. Get Admin Token

```bash
# Login as admin
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin_password"
  }'
```

Save the `access_token` from the response:
```bash
export TOKEN="eyJhbGc..."
```

### 2. Verify Admin Access

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

Ensure `role` is `admin` or `super_admin`.

## Test Cases

### Test 1: Start Rebuild Job (Normal Mode)

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/rag/rebuild \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

**Expected Response (202):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "total_documents": 0,
  "processed_documents": 0,
  "started_at": null,
  "completed_at": null,
  "error_message": null,
  "created_by_id": "admin-user-uuid",
  "created_at": "2025-01-16T10:30:00Z",
  "progress_percent": 0.0
}
```

**Validation:**
- Status code is 202
- Job has valid UUID
- status is "pending", "running", or "completed"
- created_by_id matches your user ID
- progress_percent is between 0 and 100

### Test 2: Start Rebuild Job (Force Mode)

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/rag/rebuild \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": true}'
```

**Expected Response:** Same as Test 1

**Validation:**
- Job should rebuild all embeddings even if they exist
- total_documents should match all active RAG documents

### Test 3: Get Latest Job Status

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/admin/rag/rebuild/status \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "total_documents": 10,
  "processed_documents": 10,
  "started_at": "2025-01-16T10:30:01Z",
  "completed_at": "2025-01-16T10:30:15Z",
  "error_message": null,
  "created_by_id": "admin-user-uuid",
  "created_at": "2025-01-16T10:30:00Z",
  "progress_percent": 100.0
}
```

**Validation:**
- Status code is 200
- Returns most recent job
- If status is "completed", completed_at should be set
- progress_percent should be 100.0 for completed jobs

### Test 4: Get Specific Job by ID

First, get a job ID from Test 1 or Test 3:
```bash
JOB_ID="123e4567-e89b-12d3-a456-426614174000"
```

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/admin/rag/rebuild/$JOB_ID \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200):** Same structure as Test 3

**Validation:**
- Status code is 200
- Returned job ID matches requested ID

### Test 5: Get Non-Existent Job

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/admin/rag/rebuild/00000000-0000-0000-0000-000000000000 \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (404):**
```json
{
  "detail": "Job not found"
}
```

**Validation:**
- Status code is 404
- Error message is clear

### Test 6: Unauthorized Access (Non-Admin)

Create or use a non-admin user token:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "learner@example.com",
    "password": "learner_password"
  }'

export LEARNER_TOKEN="..."
```

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/rag/rebuild \
  -H "Authorization: Bearer $LEARNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

**Expected Response (403):**
```json
{
  "detail": "Not authorized"
}
```

**Validation:**
- Status code is 403
- Non-admin users cannot access endpoint

### Test 7: Missing Authentication

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/rag/rebuild \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

**Expected Response (401):**
```json
{
  "detail": "Not authenticated"
}
```

**Validation:**
- Status code is 401

### Test 8: Monitor Job Progress

This test monitors a job from start to completion:

```bash
#!/bin/bash

# Start rebuild
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/admin/rag/rebuild \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}')

JOB_ID=$(echo $RESPONSE | jq -r '.id')
echo "Started job: $JOB_ID"

# Poll until complete
while true; do
  STATUS_RESPONSE=$(curl -s -X GET \
    http://localhost:8000/api/v1/admin/rag/rebuild/$JOB_ID \
    -H "Authorization: Bearer $TOKEN")
  
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  PROGRESS=$(echo $STATUS_RESPONSE | jq -r '.progress_percent')
  PROCESSED=$(echo $STATUS_RESPONSE | jq -r '.processed_documents')
  TOTAL=$(echo $STATUS_RESPONSE | jq -r '.total_documents')
  
  echo "Status: $STATUS | Progress: $PROGRESS% | Processed: $PROCESSED/$TOTAL"
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    echo "Job finished with status: $STATUS"
    if [ "$STATUS" = "failed" ]; then
      ERROR=$(echo $STATUS_RESPONSE | jq -r '.error_message')
      echo "Error: $ERROR"
    fi
    break
  fi
  
  sleep 2
done
```

**Validation:**
- Progress increases from 0% to 100%
- processed_documents increments
- Status transitions: pending → running → completed

## Manual Testing Checklist

- [ ] Start rebuild with force=false
- [ ] Start rebuild with force=true
- [ ] Get latest job status
- [ ] Get specific job by ID
- [ ] Attempt to get non-existent job (404)
- [ ] Try access as non-admin (403)
- [ ] Try access without token (401)
- [ ] Monitor job progress from start to finish
- [ ] Verify progress_percent calculation
- [ ] Verify status transitions
- [ ] Check database for created job records
- [ ] Verify embeddings are actually updated in RAG documents

## Automated Testing Script

Save as `test_embedding_rebuild.sh`:

```bash
#!/bin/bash
set -e

# Configuration
API_URL="http://localhost:8000"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="admin_password"

echo "=== P0-RAG-03 API Testing ==="

# Login
echo "1. Logging in as admin..."
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}")
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ]; then
  echo "❌ Failed to login"
  exit 1
fi
echo "✅ Login successful"

# Test 1: Start rebuild
echo ""
echo "2. Starting rebuild job..."
REBUILD_RESPONSE=$(curl -s -X POST $API_URL/api/v1/admin/rag/rebuild \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}')
JOB_ID=$(echo $REBUILD_RESPONSE | jq -r '.id')

if [ "$JOB_ID" = "null" ]; then
  echo "❌ Failed to start rebuild"
  exit 1
fi
echo "✅ Rebuild started: $JOB_ID"

# Test 2: Get job status
echo ""
echo "3. Getting job status..."
STATUS_RESPONSE=$(curl -s -X GET \
  $API_URL/api/v1/admin/rag/rebuild/$JOB_ID \
  -H "Authorization: Bearer $TOKEN")
STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
echo "✅ Job status: $STATUS"

# Test 3: Get latest job
echo ""
echo "4. Getting latest job..."
LATEST_RESPONSE=$(curl -s -X GET \
  $API_URL/api/v1/admin/rag/rebuild/status \
  -H "Authorization: Bearer $TOKEN")
LATEST_ID=$(echo $LATEST_RESPONSE | jq -r '.id')

if [ "$LATEST_ID" != "$JOB_ID" ]; then
  echo "❌ Latest job ID doesn't match"
  exit 1
fi
echo "✅ Latest job matches"

echo ""
echo "=== All tests passed! ==="
```

Make executable and run:
```bash
chmod +x test_embedding_rebuild.sh
./test_embedding_rebuild.sh
```

## Expected Database State

After running tests, check the database:

```sql
-- View all embedding jobs
SELECT id, status, total_documents, processed_documents, 
       started_at, completed_at, created_by_id, created_at
FROM embedding_jobs
ORDER BY created_at DESC;

-- View job with user info
SELECT ej.id, ej.status, ej.progress, u.email as created_by
FROM embedding_jobs ej
JOIN users u ON ej.created_by_id = u.id
ORDER BY ej.created_at DESC;

-- Count jobs by status
SELECT status, COUNT(*) 
FROM embedding_jobs 
GROUP BY status;
```

## Troubleshooting

### Issue: 500 Internal Server Error
- Check API logs for detailed error
- Verify database connection
- Ensure embedding API credentials are configured

### Issue: All documents skipped
- Normal if embeddings already exist
- Use force=true to rebuild all

### Issue: Job stuck in "pending"
- Check if API crashed during execution
- Look for errors in logs

### Issue: Progress doesn't update
- Ensure database commits are working
- Check for transaction issues

