# P0-RAG-03: Rebuild Embeddings - Quick Reference

## API Endpoints

### 1. Start Rebuild Job
**POST** `/api/v1/admin/rag/rebuild`

**Request:**
```json
{
  "force": false  // Optional: true to rebuild all, false to skip existing
}
```

**Response (202 Accepted):**
```json
{
  "id": "uuid",
  "status": "running",
  "total_documents": 100,
  "processed_documents": 45,
  "started_at": "2025-01-16T10:30:00Z",
  "completed_at": null,
  "error_message": null,
  "created_by_id": "uuid",
  "created_at": "2025-01-16T10:29:55Z",
  "progress_percent": 45.0
}
```

### 2. Get Latest Job Status
**GET** `/api/v1/admin/rag/rebuild/status`

**Response:**
```json
{
  "id": "uuid",
  "status": "completed",
  "total_documents": 100,
  "processed_documents": 100,
  "started_at": "2025-01-16T10:30:00Z",
  "completed_at": "2025-01-16T10:35:00Z",
  "error_message": null,
  "created_by_id": "uuid",
  "created_at": "2025-01-16T10:29:55Z",
  "progress_percent": 100.0
}
```

### 3. Get Specific Job
**GET** `/api/v1/admin/rag/rebuild/{job_id}`

**Response:** Same as above

## Status Values
- `pending`: Job created but not started
- `running`: Job is currently processing
- `completed`: Job finished successfully
- `failed`: Job encountered an error

## Database Schema

### Table: embedding_jobs
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| status | VARCHAR(20) | pending, running, completed, failed |
| total_documents | INTEGER | Total docs to process |
| processed_documents | INTEGER | Docs processed so far |
| started_at | TIMESTAMP | When job started |
| completed_at | TIMESTAMP | When job finished |
| error_message | TEXT | Error details if failed |
| created_by_id | UUID | Admin who started job |
| created_at | TIMESTAMP | When job was created |

### Indexes
- `idx_embedding_jobs_status` on status
- `idx_embedding_jobs_created_by` on created_by_id

## Service Functions

### embeddings.py
```python
# Generate embedding for text
embedding = call_embedding("text content")

# Update single document
success = update_document_embedding(session, doc, force=False)

# Rebuild all embeddings with progress tracking
result = rebuild_all_embeddings(session, job, force=False)

# Get job by ID
job = get_job_by_id(session, job_id)

# Get latest job
job = get_latest_job(session)
```

## Usage Examples

### Start Rebuild (Python)
```python
from uuid import UUID
import requests

response = requests.post(
    "https://api.example.com/api/v1/admin/rag/rebuild",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={"force": False}
)
job = response.json()
print(f"Job started: {job['id']}, Progress: {job['progress_percent']}%")
```

### Poll Job Status (Python)
```python
import time

job_id = "123e4567-e89b-12d3-a456-426614174000"
while True:
    response = requests.get(
        f"https://api.example.com/api/v1/admin/rag/rebuild/{job_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    job = response.json()
    print(f"Status: {job['status']}, Progress: {job['progress_percent']}%")
    
    if job['status'] in ['completed', 'failed']:
        break
    
    time.sleep(2)  # Poll every 2 seconds
```

### Start Rebuild (cURL)
```bash
curl -X POST https://api.example.com/api/v1/admin/rag/rebuild \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

### Check Status (cURL)
```bash
curl -X GET https://api.example.com/api/v1/admin/rag/rebuild/status \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Migration Commands

### Apply Migration
```bash
# Using Docker
docker-compose exec api alembic upgrade head

# Local
cd /Users/nguyennt/Documents/luuniensuki-lms
alembic upgrade head
```

### Rollback Migration
```bash
# Using Docker
docker-compose exec api alembic downgrade -1

# Local
alembic downgrade -1
```

### Check Current Version
```bash
docker-compose exec api alembic current
```

## Error Codes

| Code | Description |
|------|-------------|
| 202 | Rebuild job accepted and started |
| 404 | Job not found |
| 403 | Not authorized (admin only) |
| 401 | Not authenticated |

## Force Rebuild vs Normal Rebuild

### Normal Rebuild (force=false)
- Skips documents that already have embeddings
- Only updates documents without embeddings
- Faster for incremental updates
- Default behavior

### Force Rebuild (force=true)
- Rebuilds ALL embeddings regardless of existing state
- Useful when embedding model changes
- Useful when embeddings are corrupted
- Slower but ensures consistency

## Files Created/Modified

### New Files
- `backend/services/embeddings.py`
- `migrations/versions/0015_embedding_jobs.py`
- `P0-RAG-03_IMPLEMENTATION_SUMMARY.md`
- `P0-RAG-03_QUICK_REFERENCE.md` (this file)

### Modified Files
- `backend/models.py` - Added EmbeddingJob model
- `backend/main.py` - Added endpoints and schemas

## Admin Requirements

All endpoints require:
- Valid JWT token
- User role: `admin` or `super_admin`

## Best Practices

1. **Monitor Progress**: Poll status endpoint to track progress
2. **Handle Errors**: Check error_message field when status is 'failed'
3. **Use Force Sparingly**: Only use force=true when necessary
4. **Check Existing Jobs**: Get latest job status before starting new one
5. **Schedule Wisely**: Run during low-traffic periods for large rebuilds

## Common Issues

### Issue: 404 on status endpoint
**Solution**: No jobs have been created yet. Start a rebuild job first.

### Issue: Job stuck in "running"
**Solution**: Check API logs for errors. Job may have crashed without updating status.

### Issue: Slow rebuild
**Solution**: 
- Embedding API may be slow
- Check network connectivity
- Consider using force=false to skip existing embeddings

### Issue: All documents skipped
**Solution**: Documents already have embeddings. Use force=true to rebuild anyway.

