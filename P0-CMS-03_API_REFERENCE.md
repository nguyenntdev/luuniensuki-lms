# Content Versioning API Reference

## Quick Reference for P0-CMS-03 Content Versioning Endpoints

### Authentication
All endpoints require authentication with a staff user (teacher, admin, or super_admin).

Header required:
```
Authorization: Bearer {your_jwt_token}
```

---

## Endpoints

### 1. List Content Versions

**Endpoint:** `GET /api/v1/admin/content/{content_type}/{content_id}/versions`

**Parameters:**
- `content_type`: Type of content (currently supports: "lesson", "quiz")
- `content_id`: UUID of the content item

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "version": 3,
    "editor_id": "uuid",
    "editor_name": "John Doe",
    "change_note": "Updated historical context",
    "created_at": "2025-01-15T10:30:00Z"
  },
  {
    "id": "uuid",
    "version": 2,
    "editor_id": "uuid",
    "editor_name": "Jane Smith",
    "change_note": "Fixed typos",
    "created_at": "2025-01-14T15:20:00Z"
  }
]
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/content/lesson/abc123.../versions" \
  -H "Authorization: Bearer eyJ..."
```

---

### 2. Get Specific Version

**Endpoint:** `GET /api/v1/admin/content/{content_type}/{content_id}/versions/{version}`

**Parameters:**
- `content_type`: Type of content (e.g., "lesson")
- `content_id`: UUID of the content item
- `version`: Version number to retrieve

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "content_type": "lesson",
  "content_id": "uuid",
  "version": 2,
  "data": {
    "intro_text": "...",
    "description": "...",
    "historical_context": "...",
    "symbolism": "...",
    "fun_fact": "...",
    "is_published": true
  },
  "editor_id": "uuid",
  "editor_name": "Jane Smith",
  "change_note": "Fixed typos",
  "created_at": "2025-01-14T15:20:00Z"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/content/lesson/abc123.../versions/2" \
  -H "Authorization: Bearer eyJ..."
```

---

### 3. Revert to Version

**Endpoint:** `POST /api/v1/admin/content/{content_type}/{content_id}/revert/{version}`

**Parameters:**
- `content_type`: Type of content (e.g., "lesson")
- `content_id`: UUID of the content item
- `version`: Version number to revert to

**Request Body:**
```json
{
  "change_note": "Reverting due to incorrect information" 
}
```
Note: `change_note` is optional but recommended.

**Response:** `200 OK`
```json
{
  "message": "Content reverted to version 2",
  "new_version": 4
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/admin/content/lesson/abc123.../revert/2" \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"change_note": "Reverting to previous version"}'
```

---

## Lesson Update with Versioning

### Update Lesson (with automatic versioning)

**Endpoint:** `PATCH /api/v1/admin/lessons/{lesson_id}`

**Request Body:**
```json
{
  "description": "Updated description",
  "historical_context": "New historical context",
  "is_published": true,
  "publish_note": "Ready for production"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "motif_id": "uuid",
  "description": "Updated description",
  "historical_context": "New historical context",
  "is_published": true,
  "version": 3,
  "last_editor_id": "uuid",
  "published_at": "2025-01-15T10:30:00Z",
  "publish_note": "Ready for production",
  "created_at": "2025-01-10T09:00:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

Note: The system automatically:
- Creates a snapshot of the current version before updating
- Increments the version number
- Sets the last_editor_id to the current user
- Sets published_at timestamp if publishing

---

## Workflow Examples

### Example 1: Review Version History
```bash
# 1. Get all versions
GET /api/v1/admin/content/lesson/{lesson_id}/versions

# 2. View specific version
GET /api/v1/admin/content/lesson/{lesson_id}/versions/2

# 3. Compare with current (manually or via UI)
```

### Example 2: Rollback Mistake
```bash
# 1. Discover error in latest version
# 2. Review previous versions
GET /api/v1/admin/content/lesson/{lesson_id}/versions

# 3. Revert to good version
POST /api/v1/admin/content/lesson/{lesson_id}/revert/3
{
  "change_note": "Reverting incorrect historical context"
}
```

### Example 3: Publish with Note
```bash
PATCH /api/v1/admin/lessons/{lesson_id}
{
  "is_published": true,
  "publish_note": "v1.0 - Initial release"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid content type"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized"
}
```

### 404 Not Found
```json
{
  "detail": "Version not found"
}
```

---

## Notes

- All timestamps are in UTC with timezone
- Version numbers start at 1 and increment with each change
- Reverting creates TWO new versions: one before revert, one after
- Only staff users (teacher/admin/super_admin) can access versioning endpoints
- Teachers can only edit unpublished content
- Only admins can publish content

