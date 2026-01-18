# P0-RAG-01 Quick Reference

## API Endpoints

### Get Current Settings
```bash
GET /api/v1/admin/rag/settings
Authorization: Bearer <admin_token>
```

### Update Settings (Partial)
```bash
PUT /api/v1/admin/rag/settings
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "temperature": 0.8,
  "max_documents": 10,
  "hybrid_alpha": 0.7
}
```

### Reset to Defaults
```bash
POST /api/v1/admin/rag/settings/reset
Authorization: Bearer <admin_token>
```

## Field Validation Rules

| Field | Type | Min | Max | Default |
|-------|------|-----|-----|---------|
| `system_instruction` | string | - | 5000 chars | See defaults |
| `prompt_prefix` | string | - | 2000 chars | See defaults |
| `model_override` | string | - | 100 chars | `null` |
| `temperature` | float | 0.0 | 2.0 | 0.7 |
| `max_documents` | int | 1 | 20 | 6 |
| `embedding_enabled` | bool | - | - | `true` |
| `hybrid_alpha` | float | 0.0 | 1.0 | 0.6 |

## Parameter Meanings

- **system_instruction**: AI's personality and guidelines
- **prompt_prefix**: Template for wrapping user questions with context
- **model_override**: Override the default model (optional)
- **temperature**: Higher = more creative, Lower = more focused (0.0-2.0)
- **max_documents**: How many RAG docs to retrieve per query (1-20)
- **embedding_enabled**: Use semantic search vs keyword only
- **hybrid_alpha**: 0.0 = pure keyword, 1.0 = pure semantic, 0.6 = balanced

## Access Control

**Required Role:** `admin` or `super_admin`

**Error Response (403):**
```json
{
  "detail": "Not authorized"
}
```

## Validation Errors (422)

```json
{
  "detail": [
    {
      "loc": ["body", "temperature"],
      "msg": "ensure this value is less than or equal to 2.0",
      "type": "value_error.number.not_le"
    }
  ]
}
```

## Code Examples

### Python (requests)
```python
import requests

API_URL = "https://your-domain.com/api/v1"
headers = {"Authorization": f"Bearer {admin_token}"}

# Get settings
response = requests.get(f"{API_URL}/admin/rag/settings", headers=headers)
settings = response.json()

# Update settings
update_data = {"temperature": 0.9, "max_documents": 8}
response = requests.put(
    f"{API_URL}/admin/rag/settings",
    headers=headers,
    json=update_data
)

# Reset to defaults
response = requests.post(f"{API_URL}/admin/rag/settings/reset", headers=headers)
```

### JavaScript (fetch)
```javascript
const API_URL = "https://your-domain.com/api/v1";
const headers = { 
  "Authorization": `Bearer ${adminToken}`,
  "Content-Type": "application/json"
};

// Get settings
const settings = await fetch(`${API_URL}/admin/rag/settings`, { headers })
  .then(r => r.json());

// Update settings
const updated = await fetch(`${API_URL}/admin/rag/settings`, {
  method: "PUT",
  headers,
  body: JSON.stringify({ temperature: 0.9, max_documents: 8 })
}).then(r => r.json());

// Reset to defaults
const defaults = await fetch(`${API_URL}/admin/rag/settings/reset`, {
  method: "POST",
  headers
}).then(r => r.json());
```

## Files Added/Modified

- ✅ `backend/rag_defaults.py` - Default values and validation constants
- ✅ `backend/schemas.py` - Added `RagSettingsOut` and `RagSettingsUpdateIn`
- ✅ `backend/main.py` - Updated endpoints, added reset endpoint

## Testing with curl

```bash
# Set your admin token
ADMIN_TOKEN="your-admin-jwt-token-here"
API="http://localhost:8000/api/v1"

# Get current settings
curl -X GET "$API/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Update temperature
curl -X PUT "$API/admin/rag/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 0.8}'

# Reset to defaults
curl -X POST "$API/admin/rag/settings/reset" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Common Use Cases

### Make AI More Creative
```json
{"temperature": 1.2}
```

### Make AI More Factual
```json
{"temperature": 0.3}
```

### Increase Context Size
```json
{"max_documents": 15}
```

### Pure Semantic Search
```json
{"hybrid_alpha": 1.0}
```

### Pure Keyword Search
```json
{"hybrid_alpha": 0.0}
```

### Balanced (Recommended)
```json
{"hybrid_alpha": 0.6}
```

