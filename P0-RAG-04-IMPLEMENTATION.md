# P0-RAG-04: RAG Health Panel Implementation

## Summary
Added a comprehensive RAG health monitoring endpoint that provides detailed statistics about the RAG document system, including coverage metrics, embedding status, and system health indicators.

## API Endpoint

### GET /api/v1/admin/rag/health
**Authentication:** Admin only (requires `get_admin_user`)

**Response Schema: RagHealthOut**
```python
{
    "total_documents": int,              # Total number of RAG documents
    "active_documents": int,             # Number of active documents
    "documents_with_embeddings": int,    # Documents with generated embeddings
    "documents_without_embeddings": int, # Documents missing embeddings
    "coverage_percent": float,           # Percentage of docs with embeddings (0-100)
    "last_embedding_updated_at": datetime | null,  # Most recent embedding update
    "oldest_embedding_at": datetime | null,        # Oldest embedding timestamp
    "embedding_model": str,              # Current embedding model name
    "settings_status": {                 # Summary of RAG settings
        "embedding_enabled": bool,
        "max_documents": int,
        "hybrid_alpha": float,
        "model_override": str | null,
        "temperature": float | null
    },
    "status": str,                       # Overall health: "healthy", "degraded", "unhealthy"
    "issues": list[str]                  # List of detected issues
}
```

## Health Status Logic

### Status Levels
1. **healthy**: 
   - Coverage >= 90%
   - No issues detected

2. **degraded**: 
   - Coverage 50-90%, OR
   - One or more non-critical issues detected

3. **unhealthy**: 
   - Coverage < 50%, OR
   - No documents available, OR
   - Critical configuration issues

### Issue Detection
The endpoint checks for the following issues:
- Missing embedding API key configuration
- Embeddings disabled in settings
- Documents missing embeddings (when embeddings are enabled)
- Inactive documents present
- No RAG documents available

## Implementation Details

### Location
- **Schema:** `backend/main.py` lines 4009-4020 (RagHealthOut)
- **Endpoint:** `backend/main.py` lines 4314-4413

### Key Features
1. **Comprehensive Metrics**: Tracks total, active, and embedded documents
2. **Coverage Calculation**: Percentage of documents with embeddings
3. **Timestamp Tracking**: Last and oldest embedding update times
4. **Settings Overview**: Quick view of current RAG configuration
5. **Issue Detection**: Automatic identification of common problems
6. **Health Status**: Clear overall status indicator

### Example Response
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

## Testing
The implementation has been validated with unit tests covering:
- ✅ Healthy system (100% coverage)
- ✅ Degraded system (75% coverage with issues)
- ✅ Unhealthy system (0% coverage)
- ✅ Empty system (no documents)

## Integration Notes
This endpoint can be used by admin dashboards to:
- Display RAG system health at a glance
- Alert on coverage degradation
- Monitor embedding generation progress
- Identify configuration issues
- Track embedding update timestamps

## Frontend Integration

### API Client Function
The frontend API function has been added to `frontend/src/lib/api.js`:

```javascript
export function getRagHealth() {
  return apiRequest(`/api/v1/admin/rag/health`);
}
```

### Import Added
The function is now imported in `frontend/src/app/admin/page.jsx` for use in the admin panel.

### Example Usage in React Component

```javascript
import { getRagHealth } from "@/lib/api";

function RagHealthPanel() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadHealth() {
      setLoading(true);
      try {
        const data = await getRagHealth();
        setHealth(data);
      } catch (err) {
        console.error("Failed to load RAG health:", err);
      } finally {
        setLoading(false);
      }
    }
    loadHealth();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!health) return null;

  const statusColor = {
    healthy: "text-green-600",
    degraded: "text-yellow-600",
    unhealthy: "text-red-600",
  }[health.status];

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h3 className="font-semibold mb-2">RAG System Health</h3>

      <div className={`text-lg font-bold ${statusColor}`}>
        Status: {health.status.toUpperCase()}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="text-muted-foreground">Total Documents</div>
          <div className="font-semibold">{health.total_documents}</div>
        </div>
        <div>
          <div className="text-muted-foreground">Active Documents</div>
          <div className="font-semibold">{health.active_documents}</div>
        </div>
        <div>
          <div className="text-muted-foreground">Coverage</div>
          <div className="font-semibold">{health.coverage_percent}%</div>
        </div>
        <div>
          <div className="text-muted-foreground">With Embeddings</div>
          <div className="font-semibold">{health.documents_with_embeddings}</div>
        </div>
      </div>

      {health.issues.length > 0 && (
        <div className="mt-4 rounded bg-yellow-50 p-3">
          <div className="font-semibold text-yellow-800 mb-2">Issues:</div>
          <ul className="text-sm text-yellow-700 space-y-1">
            {health.issues.map((issue, i) => (
              <li key={i}>• {issue}</li>
            ))}
          </ul>
        </div>
      )}

      {health.last_embedding_updated_at && (
        <div className="mt-4 text-xs text-muted-foreground">
          Last updated: {new Date(health.last_embedding_updated_at).toLocaleString()}
        </div>
      )}
    </div>
  );
}
```


