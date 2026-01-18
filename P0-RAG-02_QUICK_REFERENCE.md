# P0-RAG-02: Quick Reference Guide

## API Endpoints Quick Reference

### 📋 List Documents (Paginated)
```
GET /api/v1/admin/rag/documents?page=1&page_size=20
```
Returns: `RagDocumentListOut` with pagination metadata

### 🔍 Get Single Document
```
GET /api/v1/admin/rag/documents/{document_id}
```
Returns: `RagDocumentOut`

### ➕ Create Document
```
POST /api/v1/admin/rag/documents
Body: RagDocumentCreateIn
```
Returns: `RagDocumentOut` (201 Created)

### 📤 Upload File
```
POST /api/v1/admin/rag/documents/upload
Form: file (txt/md/json), title (optional)
```
Returns: `RagDocumentOut` (201 Created)
Max size: 5MB

### ✏️ Update Document
```
PUT /api/v1/admin/rag/documents/{document_id}
Body: RagDocumentUpdateIn (partial)
```
Returns: `RagDocumentOut`
Note: Clears embedding on content change

### 🗑️ Delete Document
```
DELETE /api/v1/admin/rag/documents/{document_id}
```
Returns: 204 No Content

### ✅ Activate Document
```
POST /api/v1/admin/rag/documents/{document_id}/activate
```
Returns: `RagDocumentOut` with is_active=true

### ❌ Deactivate Document
```
POST /api/v1/admin/rag/documents/{document_id}/deactivate
```
Returns: `RagDocumentOut` with is_active=false

---

## Schemas Reference

### RagDocumentOut
```python
{
    "id": UUID,
    "title": str,
    "content": str,
    "source_type": str,  # "manual" or "file"
    "source_path": Optional[str],
    "is_active": bool,
    "embedding_model": Optional[str],
    "embedding_updated_at": Optional[datetime],
    "has_embedding": bool,
    "created_at": datetime,
    "updated_at": datetime
}
```

### RagDocumentListOut
```python
{
    "documents": list[RagDocumentOut],
    "total": int,
    "page": int,
    "page_size": int,
    "total_pages": int
}
```

### RagDocumentCreateIn
```python
{
    "title": str,        # 1-255 chars, required
    "content": str,      # min 1 char, required
    "is_active": bool    # optional, default: true
}
```

### RagDocumentUpdateIn
```python
{
    "title": Optional[str],      # 1-255 chars
    "content": Optional[str],    # min 1 char
    "is_active": Optional[bool]  # true/false
}
```
Note: All fields are optional - only send what you want to update

---

## Key Features

✅ **Pagination** - List endpoint supports page and page_size params
✅ **File Upload** - Accepts .txt, .md, .json files up to 5MB
✅ **Embedding Management** - Auto-clears and regenerates on content change
✅ **Activate/Deactivate** - Separate endpoints for toggling document status
✅ **Admin Only** - All endpoints require admin role
✅ **Validation** - File type and size validation with clear error messages

---

## Common Operations

### Creating a Document
```bash
# Manual text
curl -X POST http://localhost:8000/api/v1/admin/rag/documents \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Doc", "content": "Text"}'

# File upload
curl -X POST http://localhost:8000/api/v1/admin/rag/documents/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@doc.txt"
```

### Updating a Document
```bash
# Partial update (only content)
curl -X PUT http://localhost:8000/api/v1/admin/rag/documents/UUID \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "New content"}'
```

### Toggling Active Status
```bash
# Deactivate
curl -X POST http://localhost:8000/api/v1/admin/rag/documents/UUID/deactivate \
  -H "Authorization: Bearer TOKEN"

# Activate
curl -X POST http://localhost:8000/api/v1/admin/rag/documents/UUID/activate \
  -H "Authorization: Bearer TOKEN"
```

---

## Error Codes

| Code | Endpoint | Reason |
|------|----------|--------|
| 400 | Upload | Unsupported file type or size > 5MB |
| 401 | All | Not authenticated |
| 403 | All | Not admin user |
| 404 | Get/Update/Activate/Deactivate | Document not found |
| 422 | Create/Update | Validation error (invalid fields) |

---

## Files Modified

1. **backend/schemas.py**
   - Added `RagDocumentOut`
   - Added `RagDocumentListOut`
   - Added `RagDocumentCreateIn`
   - Added `RagDocumentUpdateIn`

2. **backend/main.py**
   - Updated list endpoint with pagination
   - Added get single document endpoint
   - Changed PATCH to PUT for update
   - Added activate/deactivate endpoints
   - Improved file upload validation
   - Removed old inline schemas

---

## Testing Checklist

- [ ] Create document with manual text
- [ ] Upload .txt file
- [ ] Upload .md file
- [ ] Upload .json file
- [ ] Try uploading file > 5MB (should fail)
- [ ] Try uploading .pdf file (should fail)
- [ ] List documents (verify pagination)
- [ ] Get single document by ID
- [ ] Update document content
- [ ] Update document title
- [ ] Deactivate document
- [ ] Activate document
- [ ] Delete document
- [ ] Try operations as non-admin (should fail 403)
- [ ] Verify embedding clears on content update
- [ ] Verify embedding regenerates (if enabled)

---

**Quick Start**: See API Reference section in P0-RAG-02_IMPLEMENTATION_SUMMARY.md
**Full Docs**: See P0-RAG-02_API_REFERENCE.md (to be created)

