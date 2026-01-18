# P0-RAG-01 API Reference

## Overview

Three endpoints for managing RAG (Retrieval Augmented Generation) settings in the admin panel.

**Base Path:** `/api/v1/admin/rag/settings`

**Authentication:** Required (Admin or Super Admin role)

---

## Endpoints

### 1. Get RAG Settings

Retrieve the current RAG configuration.

**Endpoint:** `GET /api/v1/admin/rag/settings`

**Authentication:** Bearer token (admin/super_admin)

**Request Headers:**
```http
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "system_instruction": "You are a helpful assistant for the Lưu Niên Sử Kí...",
  "prompt_prefix": "Based on the following context from the Cửu Đỉnh learning materials:\n\n{context}\n\nPlease answer the following question:",
  "model_override": null,
  "temperature": 0.7,
  "max_documents": 6,
  "embedding_enabled": true,
  "hybrid_alpha": 0.6
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: User is not admin/super_admin

---

### 2. Update RAG Settings

Update one or more RAG settings. Performs partial update - only provided fields are changed.

**Endpoint:** `PUT /api/v1/admin/rag/settings`

**Authentication:** Bearer token (admin/super_admin)

**Request Headers:**
```http
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:** (all fields optional)
```json
{
  "system_instruction": "Custom system instruction",
  "prompt_prefix": "Custom prompt prefix",
  "model_override": "gemini-1.5-pro",
  "temperature": 0.8,
  "max_documents": 10,
  "embedding_enabled": true,
  "hybrid_alpha": 0.7
}
```

**Field Specifications:**

| Field | Type | Min | Max | Description |
|-------|------|-----|-----|-------------|
| `system_instruction` | string | - | 5000 chars | AI's personality and instructions |
| `prompt_prefix` | string | - | 2000 chars | Template for wrapping questions |
| `model_override` | string | - | 100 chars | Override model name (optional) |
| `temperature` | float | 0.0 | 2.0 | Creativity/randomness (0=focused, 2=creative) |
| `max_documents` | integer | 1 | 20 | Number of RAG docs to retrieve |
| `embedding_enabled` | boolean | - | - | Enable semantic search |
| `hybrid_alpha` | float | 0.0 | 1.0 | Search balance (0=keyword, 1=semantic) |

**Response:** `200 OK`
```json
{
  "system_instruction": "Custom system instruction",
  "prompt_prefix": "Custom prompt prefix",
  "model_override": "gemini-1.5-pro",
  "temperature": 0.8,
  "max_documents": 10,
  "embedding_enabled": true,
  "hybrid_alpha": 0.7
}
```

**Error Responses:**

`401 Unauthorized`: Missing or invalid token
```json
{
  "detail": "Not authenticated"
}
```

`403 Forbidden`: User is not admin/super_admin
```json
{
  "detail": "Not authorized"
}
```

`422 Unprocessable Entity`: Validation error
```json
{
  "detail": [
    {
      "loc": ["body", "temperature"],
      "msg": "ensure this value is less than or equal to 2.0",
      "type": "value_error.number.not_le",
      "ctx": {"limit_value": 2.0}
    }
  ]
}
```

**Validation Examples:**

Temperature out of range:
```json
// Request
{"temperature": 3.0}

// Response 422
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

System instruction too long:
```json
// Request
{"system_instruction": "x".repeat(5001)}

// Response 422
{
  "detail": [
    {
      "loc": ["body", "system_instruction"],
      "msg": "ensure this value has at most 5000 characters",
      "type": "value_error.any_str.max_length"
    }
  ]
}
```

---

### 3. Reset RAG Settings

Reset all RAG settings to their default values.

**Endpoint:** `POST /api/v1/admin/rag/settings/reset`

**Authentication:** Bearer token (admin/super_admin)

**Request Headers:**
```http
Authorization: Bearer <token>
```

**Request Body:** None

**Response:** `200 OK`
```json
{
  "system_instruction": "You are a helpful assistant for the Lưu Niên Sử Kí (Cửu Đỉnh Chronicles) learning platform.\n\nYour role is to help learners understand Vietnamese history and culture through the lens of the nine dynastic urns (Cửu Đỉnh).\n\nGuidelines:\n- Provide clear, accurate information based on the provided context\n- Use simple, accessible language appropriate for learners\n- Connect historical concepts to the specific motifs and urns being studied\n- Encourage curiosity and deeper exploration\n- When uncertain, acknowledge limitations rather than speculating\n- Relate information back to the learning objectives when relevant",
  "prompt_prefix": "Based on the following context from the Cửu Đỉnh learning materials:\n\n{context}\n\nPlease answer the following question:",
  "model_override": null,
  "temperature": 0.7,
  "max_documents": 6,
  "embedding_enabled": true,
  "hybrid_alpha": 0.6
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: User is not admin/super_admin

---

## Default Values

Defined in `/backend/rag_defaults.py`:

```python
RAG_DEFAULT_SYSTEM_INSTRUCTION = """You are a helpful assistant for the Lưu Niên Sử Kí (Cửu Đỉnh Chronicles) learning platform.

Your role is to help learners understand Vietnamese history and culture through the lens of the nine dynastic urns (Cửu Đỉnh).

Guidelines:
- Provide clear, accurate information based on the provided context
- Use simple, accessible language appropriate for learners
- Connect historical concepts to the specific motifs and urns being studied
- Encourage curiosity and deeper exploration
- When uncertain, acknowledge limitations rather than speculating
- Relate information back to the learning objectives when relevant"""

RAG_DEFAULT_PROMPT_PREFIX = """Based on the following context from the Cửu Đỉnh learning materials:

{context}

Please answer the following question:"""

RAG_DEFAULT_MODEL_OVERRIDE = None
RAG_DEFAULT_TEMPERATURE = 0.7
RAG_DEFAULT_MAX_DOCUMENTS = 6
RAG_DEFAULT_EMBEDDING_ENABLED = True
RAG_DEFAULT_HYBRID_ALPHA = 0.6
```

---

## Access Control

All endpoints require:
1. Valid JWT token in `Authorization` header
2. User role must be `admin` or `super_admin`

Implementation uses `get_admin_user` dependency:
```python
def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user
```

Where:
```python
ADMIN_ROLES = {UserRole.admin, UserRole.super_admin}
```

---

## Common Use Cases

### Adjust AI Temperature

**More Conservative (Factual):**
```bash
curl -X PUT "$API/admin/rag/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 0.3}'
```

**More Creative:**
```bash
curl -X PUT "$API/admin/rag/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 1.2}'
```

### Adjust Search Strategy

**Pure Keyword Search:**
```bash
curl -X PUT "$API/admin/rag/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hybrid_alpha": 0.0}'
```

**Pure Semantic Search:**
```bash
curl -X PUT "$API/admin/rag/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hybrid_alpha": 1.0}'
```

**Balanced (Default):**
```bash
curl -X PUT "$API/admin/rag/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hybrid_alpha": 0.6}'
```

### Change Context Size

**More Context:**
```bash
curl -X PUT "$API/admin/rag/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"max_documents": 15}'
```

**Less Context (Faster):**
```bash
curl -X PUT "$API/admin/rag/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"max_documents": 3}'
```

---

## Implementation Details

**Backend Files:**
- `/backend/main.py` - Endpoint implementations (lines 4338-4407)
- `/backend/schemas.py` - Request/response schemas (lines 1151-1189)
- `/backend/rag_defaults.py` - Default values and constants
- `/backend/models.py` - RagSettings database model (lines 1227-1255)

**Database:**
- Table: `rag_settings`
- Model: `RagSettings` (SQLAlchemy)
- Single row stores current configuration
- Auto-created on first access if doesn't exist

**Validation:**
- Powered by Pydantic Field validators
- Automatic type checking and coercion
- Range validation for numeric fields
- Length validation for string fields
- Returns 422 with detailed error messages

