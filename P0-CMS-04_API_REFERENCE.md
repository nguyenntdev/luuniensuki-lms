# P0-CMS-04: Review Workflow API Reference

## Base URL
```
Production: https://api.luuniensuki.com
Development: http://localhost:8000
```

## Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer {access_token}
```

---

## Lesson Workflow Endpoints

### 1. Submit Lesson for Review

**Endpoint**: `POST /api/v1/admin/lessons/{lesson_id}/submit-review`  
**Permission**: Teacher, Admin  
**Description**: Submit a draft lesson for admin review

#### Request

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body**: Empty object
```json
{}
```

#### Response

**Success (200)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "motif_id": "660e8400-e29b-41d4-a716-446655440000",
  "description": "Dragons symbolize power...",
  "status": "review",
  "submitted_for_review_at": "2024-12-01T10:30:00Z",
  "reviewed_by_id": null,
  "reviewed_at": null,
  "review_notes": null,
  "version": 1,
  "is_published": false,
  "created_at": "2024-12-01T09:00:00Z",
  "updated_at": "2024-12-01T10:30:00Z"
}
```

**Errors**:
- `400`: Can only submit draft lessons for review
- `403`: Not authorized
- `404`: Lesson not found

---

### 2. Approve Lesson

**Endpoint**: `POST /api/v1/admin/lessons/{lesson_id}/approve`  
**Permission**: Admin only  
**Description**: Approve and publish a lesson

#### Request

**Headers**:
```
Authorization: Bearer {admin_token}
Content-Type: application/json
```

**Body**:
```json
{
  "review_notes": "Content approved - excellent historical context"
}
```

**Fields**:
- `review_notes` (string, optional): Notes about the approval

#### Response

**Success (200)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "motif_id": "660e8400-e29b-41d4-a716-446655440000",
  "description": "Dragons symbolize power...",
  "status": "published",
  "submitted_for_review_at": "2024-12-01T10:30:00Z",
  "reviewed_by_id": "770e8400-e29b-41d4-a716-446655440000",
  "reviewed_at": "2024-12-01T11:00:00Z",
  "review_notes": "Content approved - excellent historical context",
  "version": 1,
  "is_published": true,
  "published_at": "2024-12-01T11:00:00Z",
  "created_at": "2024-12-01T09:00:00Z",
  "updated_at": "2024-12-01T11:00:00Z"
}
```

**Errors**:
- `400`: Can only approve lessons in review or draft status
- `403`: Admin access required
- `404`: Lesson not found

---

### 3. Reject Lesson

**Endpoint**: `POST /api/v1/admin/lessons/{lesson_id}/reject`  
**Permission**: Admin only  
**Description**: Reject a lesson and send back to draft with notes

#### Request

**Headers**:
```
Authorization: Bearer {admin_token}
Content-Type: application/json
```

**Body**:
```json
{
  "review_notes": "Needs more detail on historical context and symbolism"
}
```

**Fields**:
- `review_notes` (string, **required**): Reason for rejection

#### Response

**Success (200)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "motif_id": "660e8400-e29b-41d4-a716-446655440000",
  "description": "Dragons symbolize power...",
  "status": "draft",
  "submitted_for_review_at": "2024-12-01T10:30:00Z",
  "reviewed_by_id": "770e8400-e29b-41d4-a716-446655440000",
  "reviewed_at": "2024-12-01T11:00:00Z",
  "review_notes": "Needs more detail on historical context and symbolism",
  "version": 1,
  "is_published": false,
  "created_at": "2024-12-01T09:00:00Z",
  "updated_at": "2024-12-01T11:00:00Z"
}
```

**Errors**:
- `400`: Can only reject lessons in review status
- `403`: Admin access required
- `404`: Lesson not found
- `422`: review_notes field is required

---

## Quiz Question Workflow Endpoints

### 4. Submit Quiz Question for Review

**Endpoint**: `POST /api/v1/admin/quiz-questions/{question_id}/submit-review`  
**Permission**: Teacher, Admin  
**Description**: Submit a draft quiz question for admin review

#### Request

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body**: Empty object
```json
{}
```

#### Response

**Success (200)**:
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "motif_id": "660e8400-e29b-41d4-a716-446655440000",
  "question_type": "multiple_choice",
  "question_text": "What does the dragon symbolize?",
  "options": ["Power", "Weakness", "Sadness", "Fear"],
  "correct_answer": "Power",
  "difficulty": 2,
  "status": "review",
  "submitted_for_review_at": "2024-12-01T10:45:00Z",
  "reviewed_by_id": null,
  "reviewed_at": null,
  "review_notes": null,
  "created_by_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_published": false,
  "is_active": true,
  "created_at": "2024-12-01T10:00:00Z"
}
```

**Errors**: Same as lesson submit endpoint

---

### 5. Approve Quiz Question

**Endpoint**: `POST /api/v1/admin/quiz-questions/{question_id}/approve`
**Permission**: Admin only
**Description**: Approve and publish a quiz question

Request/Response format is identical to lesson approval, with quiz question fields.

---

### 6. Reject Quiz Question

**Endpoint**: `POST /api/v1/admin/quiz-questions/{question_id}/reject`
**Permission**: Admin only
**Description**: Reject a quiz question and send back to draft

Request/Response format is identical to lesson rejection, with quiz question fields.

---

## Pending Review List Endpoint

### 7. Get All Pending Reviews

**Endpoint**: `GET /api/v1/admin/content/pending-review`
**Permission**: Teacher, Admin
**Description**: Get all content items currently in review status

#### Request

**Headers**:
```
Authorization: Bearer {token}
```

**Query Parameters**: None

#### Response

**Success (200)**:
```json
{
  "lessons": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "content_type": "lesson",
      "title": "Lesson: Rồng",
      "motif_name": "Rồng",
      "submitted_by_id": "990e8400-e29b-41d4-a716-446655440000",
      "submitted_by_name": "John Teacher",
      "submitted_at": "2024-12-01T10:30:00Z",
      "version": 2
    }
  ],
  "quiz_questions": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "content_type": "quiz_question",
      "title": "What does the dragon symbolize...",
      "motif_name": "Rồng",
      "submitted_by_id": "990e8400-e29b-41d4-a716-446655440000",
      "submitted_by_name": "John Teacher",
      "submitted_at": "2024-12-01T10:45:00Z",
      "version": null
    }
  ],
  "total_count": 2
}
```

**Errors**:
- `403`: Not authorized

---

## Error Response Format

All endpoints return errors in this format:

```json
{
  "detail": "Error message here"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid status transition, validation error)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found (content doesn't exist)
- `422`: Unprocessable Entity (missing required field)

---

## Testing Examples

### cURL Examples

**Submit for Review**:
```bash
curl -X POST \
  'http://localhost:8000/api/v1/admin/lessons/{lesson_id}/submit-review' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Approve Lesson**:
```bash
curl -X POST \
  'http://localhost:8000/api/v1/admin/lessons/{lesson_id}/approve' \
  -H 'Authorization: Bearer {admin_token}' \
  -H 'Content-Type: application/json' \
  -d '{"review_notes": "Approved"}'
```

### Python Example

```python
import requests

response = requests.post(
    f"{BASE_URL}/api/v1/admin/lessons/{lesson_id}/submit-review",
    headers={"Authorization": f"Bearer {token}"},
    json={}
)
```

---

**For full documentation, see**: [P0-CMS-04_IMPLEMENTATION_SUMMARY.md](./P0-CMS-04_IMPLEMENTATION_SUMMARY.md)

