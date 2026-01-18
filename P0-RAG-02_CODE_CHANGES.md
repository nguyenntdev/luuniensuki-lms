# P0-RAG-02: Detailed Code Changes

## Summary
Complete implementation of RAG document management system with CRUD operations, file upload, pagination, and activate/deactivate functionality.

---

## File Changes

### 1. backend/schemas.py

#### Line 14: Updated imports
```python
# BEFORE:
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

# AFTER:
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
```

#### Lines 1090-1148: Added RAG Document Schemas
```python
# NEW SECTION - RAG Document Schemas
# =============================================================================
# RAG Document Schemas
# =============================================================================


class RagDocumentOut(BaseSchema):
    """Output schema for RAG document."""
    
    id: UUID
    title: str
    content: str
    source_type: str
    source_path: Optional[str] = None
    is_active: bool
    embedding_model: Optional[str] = None
    embedding_updated_at: Optional[datetime] = None
    has_embedding: bool = False
    created_at: datetime
    updated_at: datetime


class RagDocumentListOut(BaseModel):
    """Output schema for paginated RAG document list."""
    
    documents: list[RagDocumentOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class RagDocumentCreateIn(BaseModel):
    """Input schema for creating a RAG document."""
    
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    content: str = Field(..., min_length=1, description="Document content")
    is_active: Optional[bool] = Field(
        default=True, description="Whether document is active"
    )


class RagDocumentUpdateIn(BaseModel):
    """Input schema for updating a RAG document."""
    
    title: Optional[str] = Field(
        default=None, min_length=1, max_length=255, description="Document title"
    )
    content: Optional[str] = Field(
        default=None, min_length=1, description="Document content"
    )
    is_active: Optional[bool] = Field(
        default=None, description="Whether document is active"
    )
```

---

### 2. backend/main.py

#### Lines 3957-3978: Removed Old Schemas
```python
# REMOVED:
class RagDocumentOut(BaseModel):
    id: UUID
    title: str
    content: str
    source_type: str
    source_path: Optional[str] = None
    is_active: bool
    embedding_model: Optional[str] = None
    embedding_updated_at: Optional[datetime] = None
    has_embedding: bool = False
    created_at: datetime
    updated_at: datetime


class RagDocumentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    is_active: Optional[bool] = True


class RagDocumentUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = None
    is_active: Optional[bool] = None

# These are now defined in schemas.py
```

#### Line 3993: Updated Helper Function
```python
# BEFORE:
def _rag_document_out(doc: RagDocument) -> RagDocumentOut:
    return RagDocumentOut(

# AFTER:
def _rag_document_out(doc: RagDocument) -> schemas.RagDocumentOut:
    return schemas.RagDocumentOut(
```

#### Lines 4084-4335: Replaced RAG Document Endpoints
Complete replacement of the RAG document endpoints section with enhanced implementation.

**OLD ENDPOINTS (Removed):**
```python
@app.get("/api/v1/admin/rag/documents", response_model=list[RagDocumentOut])
def list_rag_documents(...) -> list[RagDocumentOut]:
    # Simple list without pagination

@app.post("/api/v1/admin/rag/documents", ...)
def create_rag_document(payload: RagDocumentCreateRequest, ...) -> RagDocumentOut:
    # Used old schema

@app.post("/api/v1/admin/rag/documents/upload", ...)
async def upload_rag_document(...) -> RagDocumentOut:
    # Basic file validation

@app.patch("/api/v1/admin/rag/documents/{doc_id}", ...)
def update_rag_document(doc_id: UUID, payload: RagDocumentUpdateRequest, ...) -> RagDocumentOut:
    # PATCH method, didn't clear embedding

@app.delete("/api/v1/admin/rag/documents/{doc_id}", ...)
def delete_rag_document(doc_id: UUID, ...) -> Response:
    # Same implementation
```

**NEW ENDPOINTS (Added):**

1. **List with Pagination** (Enhanced)
```python
@app.get("/api/v1/admin/rag/documents", response_model=schemas.RagDocumentListOut)
def list_rag_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentListOut:
    """List all RAG documents with pagination."""
    # Count total, calculate pages, return paginated response
```

2. **Get Single Document** (NEW)
```python
@app.get("/api/v1/admin/rag/documents/{document_id}", response_model=schemas.RagDocumentOut)
def get_rag_document(
    document_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Get a single RAG document by ID."""
```

3. **Create Document** (Updated schema)
```python
@app.post("/api/v1/admin/rag/documents", response_model=schemas.RagDocumentOut, status_code=201)
def create_rag_document(
    payload: schemas.RagDocumentCreateIn,  # Changed from RagDocumentCreateRequest
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Create a new RAG document with manual text input."""
```

4. **Upload File** (Enhanced validation)
```python
@app.post("/api/v1/admin/rag/documents/upload", response_model=schemas.RagDocumentOut, status_code=201)
async def upload_rag_document(
    file: UploadFile = File(...),
    title: Optional[str] = Query(default=None),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Upload a RAG document from a file (.txt, .md, .json)."""
    # Enhanced: Check both content-type and file extension
    # Enhanced: 5MB limit (not settings.max_upload_size_mb)
    # Enhanced: Better error messages
```

5. **Update Document** (Changed from PATCH to PUT, clears embedding)
```python
@app.put("/api/v1/admin/rag/documents/{document_id}", response_model=schemas.RagDocumentOut)
def update_rag_document(
    document_id: UUID,  # Changed from doc_id
    payload: schemas.RagDocumentUpdateIn,  # Changed from RagDocumentUpdateRequest
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Update a RAG document. Clears embedding when content changes."""
    # Enhanced: Explicitly clears embedding before regenerating
```

6. **Delete Document** (Same implementation, updated parameter name)
```python
@app.delete("/api/v1/admin/rag/documents/{document_id}", status_code=204)
def delete_rag_document(
    document_id: UUID,  # Changed from doc_id for consistency
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a RAG document."""
```

7. **Activate Document** (NEW)
```python
@app.post("/api/v1/admin/rag/documents/{document_id}/activate", response_model=schemas.RagDocumentOut)
def activate_rag_document(
    document_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Activate a RAG document."""
    # Sets is_active = True
```

8. **Deactivate Document** (NEW)
```python
@app.post("/api/v1/admin/rag/documents/{document_id}/deactivate", response_model=schemas.RagDocumentOut)
def deactivate_rag_document(
    document_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> schemas.RagDocumentOut:
    """Deactivate a RAG document."""
    # Sets is_active = False
```

---

## Key Implementation Details

### Pagination Logic
```python
# Count total documents
total = db.execute(select(func.count()).select_from(RagDocument)).scalar_one()

# Calculate pagination
total_pages = math.ceil(total / page_size) if total > 0 else 1
offset = (page - 1) * page_size

# Get documents for current page
docs = (
    db.execute(
        select(RagDocument)
        .order_by(RagDocument.updated_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    .scalars()
    .all()
)

return schemas.RagDocumentListOut(
    documents=[_rag_document_out(doc) for doc in docs],
    total=total,
    page=page,
    page_size=page_size,
    total_pages=total_pages,
)
```

### Enhanced File Upload Validation
```python
# Validate file type by both content-type and extension
if file.content_type not in RAG_ALLOWED_FILE_TYPES:
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in {".txt", ".md", ".json"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: .txt, .md, .json",
            )

# Check file size (5MB limit)
max_bytes = 5 * 1024 * 1024
contents = await file.read(max_bytes + 1)
if len(contents) > max_bytes:
    raise HTTPException(
        status_code=400,
        detail=f"File too large. Maximum size: 5MB",
    )
```

### Embedding Clear and Regenerate
```python
# Clear and rebuild embedding if content or title changed
if "content" in updates or "title" in updates:
    doc.embedding = None
    doc.embedding_model = None
    doc.embedding_updated_at = None
    _maybe_update_rag_embedding(db, doc)
```

---

## Breaking Changes

1. **List Endpoint Response Format**
   - Before: `list[RagDocumentOut]`
   - After: `RagDocumentListOut` with pagination metadata

2. **Update Endpoint Method**
   - Before: `PATCH /api/v1/admin/rag/documents/{doc_id}`
   - After: `PUT /api/v1/admin/rag/documents/{document_id}`

3. **Schema Names**
   - Before: `RagDocumentCreateRequest`, `RagDocumentUpdateRequest`
   - After: `schemas.RagDocumentCreateIn`, `schemas.RagDocumentUpdateIn`

---

## Non-Breaking Changes

- New endpoints added (GET single, activate, deactivate)
- File upload size limit changed to 5MB (from config)
- Better error messages
- Consistent parameter naming (doc_id → document_id)
- Embedding is explicitly cleared before regeneration

---

## Testing Impact

All existing RAG functionality should continue to work, but API clients need to:
1. Update list endpoint to handle new response format
2. Change PATCH to PUT for updates
3. Update URL path parameter from `doc_id` to `document_id`

---

**Lines Changed**: ~350 lines
**Files Modified**: 2 (schemas.py, main.py)
**New Endpoints**: 3 (GET single, activate, deactivate)
**Enhanced Endpoints**: 3 (list, upload, update)
**Schemas Added**: 4


