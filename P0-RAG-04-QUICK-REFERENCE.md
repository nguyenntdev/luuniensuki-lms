# P0-RAG-04 Quick Reference Card

## API Endpoint
```
GET /api/v1/admin/rag/health
Authorization: Admin only
```

## Response Fields
| Field | Type | Description |
|-------|------|-------------|
| `total_documents` | int | Total number of RAG documents |
| `active_documents` | int | Number of active documents |
| `documents_with_embeddings` | int | Documents with embeddings |
| `documents_without_embeddings` | int | Documents missing embeddings |
| `coverage_percent` | float | Percentage with embeddings (0-100) |
| `last_embedding_updated_at` | datetime\|null | Most recent embedding update |
| `oldest_embedding_at` | datetime\|null | Oldest embedding timestamp |
| `embedding_model` | string | Current embedding model name |
| `settings_status` | object | RAG settings summary |
| `status` | string | Health status: `healthy`, `degraded`, `unhealthy` |
| `issues` | array | List of detected issues |

## Health Status
- **healthy**: Coverage ≥ 90%, no issues
- **degraded**: Coverage 50-90% OR has issues
- **unhealthy**: Coverage < 50% OR no documents

## Frontend Usage
```javascript
import { getRagHealth } from "@/lib/api";

const health = await getRagHealth();
console.log(health.status); // "healthy" | "degraded" | "unhealthy"
```

## Example Response
```json
{
  "total_documents": 25,
  "active_documents": 23,
  "documents_with_embeddings": 22,
  "documents_without_embeddings": 3,
  "coverage_percent": 88.0,
  "last_embedding_updated_at": "2024-01-20T10:30:00Z",
  "oldest_embedding_at": "2024-01-10T08:15:00Z",
  "embedding_model": "text-embedding-3-small",
  "settings_status": {
    "embedding_enabled": true,
    "max_documents": 6,
    "hybrid_alpha": 0.6,
    "model_override": null,
    "temperature": null
  },
  "status": "degraded",
  "issues": [
    "3 document(s) missing embeddings",
    "2 inactive document(s)"
  ]
}
```

## Implementation Files
- Backend: `backend/main.py` (lines 3965-3976, 4535-4634)
- Frontend: `frontend/src/lib/api.js` (line 685)
- Import: `frontend/src/app/admin/page.jsx` (line 34)

## Testing
✅ All syntax checks passed
✅ Logic validation complete
✅ 4/4 test scenarios passed

