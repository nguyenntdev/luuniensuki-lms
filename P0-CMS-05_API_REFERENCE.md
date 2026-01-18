# P0-CMS-05: Content Tagging - API Reference

## Table of Contents
- [Authentication](#authentication)
- [Schemas](#schemas)
- [Endpoints](#endpoints)
- [Error Codes](#error-codes)

## Authentication

Admin endpoints require JWT authentication:
```
Authorization: Bearer {access_token}
```

Public endpoints (search, list tags) do not require authentication.

## Schemas

### TagOut
Response schema for tag objects.

```json
{
  "id": "uuid",
  "slug": "string (1-100 chars)",
  "name": "string (1-200 chars)",
  "tag_type": "topic|difficulty|audience|era|style",
  "description": "string|null",
  "is_active": "boolean",
  "created_at": "datetime"
}
```

### TagCreateIn
Request schema for creating tags.

```json
{
  "slug": "string (required, 1-100 chars)",
  "name": "string (required, 1-200 chars)",
  "tag_type": "topic|difficulty|audience|era|style (required)",
  "description": "string (optional)",
  "is_active": "boolean (optional, default: true)"
}
```

**Field Validations:**
- `slug`: Lowercase, alphanumeric with hyphens, unique
- `tag_type`: Must be one of: topic, difficulty, audience, era, style

### ContentTagOut
Response schema for content tag associations.

```json
{
  "id": "uuid",
  "tag_id": "uuid",
  "content_type": "lesson|motif|quiz|quest",
  "content_id": "uuid",
  "created_at": "datetime",
  "tag": {
    // TagOut object
  }
}
```

### ContentTagCreateIn
Request schema for adding tags to content.

```json
{
  "tag_slugs": ["string"] // At least 1 tag slug required
}
```

### SearchRequest
Query parameters for search endpoint.

```
q: string (optional) - Search query
tags: string (optional) - Comma-separated tag slugs
content_types: string (optional) - Comma-separated content types
limit: integer (optional, 1-100, default: 20)
```

### SearchResponse
Response schema for search results.

```json
{
  "results": [
    {
      "content_type": "lesson|motif|quiz|quest",
      "content_id": "uuid",
      "title": "string",
      "description": "string|null",
      "tags": [
        // Array of TagOut objects
      ],
      "relevance_score": "float"
    }
  ],
  "total": "integer",
  "query": "string|null",
  "applied_tags": ["string"]
}
```

---

## Endpoints

### 1. GET /api/v1/tags

List all active tags, optionally filtered by type.

**Authentication:** None (public)

**Query Parameters:**
- `tag_type` (optional): Filter by tag type (topic, difficulty, audience, era, style)

**Response:** 200 OK
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "slug": "architecture",
    "name": "Architecture",
    "tag_type": "topic",
    "description": "Architectural elements and structures",
    "is_active": true,
    "created_at": "2025-01-16T10:00:00Z"
  }
]
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/tags?tag_type=topic"
```

---

### 2. POST /api/v1/admin/tags

Create a new tag.

**Authentication:** Required (admin role)

**Request Body:**
```json
{
  "slug": "vietnamese-culture",
  "name": "Vietnamese Culture",
  "tag_type": "topic",
  "description": "Content related to Vietnamese cultural elements",
  "is_active": true
}
```

**Response:** 201 Created
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "slug": "vietnamese-culture",
  "name": "Vietnamese Culture",
  "tag_type": "topic",
  "description": "Content related to Vietnamese cultural elements",
  "is_active": true,
  "created_at": "2025-01-16T10:00:00Z"
}
```

**Errors:**
- `400 Bad Request`: Tag with this slug already exists
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: User is not an admin
- `422 Unprocessable Entity`: Invalid request body

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "vietnamese-culture",
    "name": "Vietnamese Culture",
    "tag_type": "topic"
  }'
```

---

### 3. POST /api/v1/admin/content/{content_type}/{content_id}/tags

Add tags to content.

**Authentication:** Required (admin role)

**Path Parameters:**
- `content_type`: Type of content (lesson, motif, quiz, quest)
- `content_id`: UUID of the content

**Request Body:**
```json
{
  "tag_slugs": ["architecture", "beginner", "19th-century"]
}
```

**Response:** 200 OK
```json
[
  {
    "id": "456e7890-e89b-12d3-a456-426614174002",
    "tag_id": "123e4567-e89b-12d3-a456-426614174000",
    "content_type": "motif",
    "content_id": "123e4567-e89b-12d3-a456-426614174001",
    "created_at": "2025-01-16T10:05:00Z",
    "tag": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "slug": "architecture",
      "name": "Architecture",
      "tag_type": "topic",
      "description": "Architectural elements and structures",
      "is_active": true,
      "created_at": "2025-01-16T10:00:00Z"
    }
  }
]
```

**Errors:**
- `400 Bad Request`: Invalid content type
- `404 Not Found`: Content not found or tags not found
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: User is not an admin

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/content/motif/123e4567-e89b-12d3-a456-426614174001/tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tag_slugs": ["architecture", "beginner"]}'
```

---

### 4. DELETE /api/v1/admin/content/{content_type}/{content_id}/tags/{tag_slug}

Remove a tag from content.

**Authentication:** Required (admin role)

**Path Parameters:**
- `content_type`: Type of content (lesson, motif, quiz, quest)
- `content_id`: UUID of the content
- `tag_slug`: Slug of the tag to remove

**Response:** 204 No Content

**Errors:**
- `400 Bad Request`: Invalid content type
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: User is not an admin

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/admin/content/motif/123e4567-e89b-12d3-a456-426614174001/tags/architecture \
  -H "Authorization: Bearer $TOKEN"
```

---

### 5. GET /api/v1/search

Search content by query and/or tags.

**Authentication:** None (public)

**Query Parameters:**
- `q` (optional): Search query string
- `tags` (optional): Comma-separated list of tag slugs to filter by
- `content_types` (optional): Comma-separated list of content types (default: all)
- `limit` (optional): Maximum results (1-100, default: 20)

**Response:** 200 OK
```json
{
  "results": [
    {
      "content_type": "motif",
      "content_id": "123e4567-e89b-12d3-a456-426614174001",
      "title": "Dragon Motif",
      "description": "Traditional Vietnamese dragon symbolism",
      "tags": [
        {
          "id": "123e4567-e89b-12d3-a456-426614174000",
          "slug": "mythology",
          "name": "Mythology",
          "tag_type": "topic",
          "description": null,
          "is_active": true,
          "created_at": "2025-01-16T10:00:00Z"
        }
      ],
      "relevance_score": 1.0
    }
  ],
  "total": 1,
  "query": "dragon",
  "applied_tags": ["mythology"]
}
```

**Errors:**
- `400 Bad Request`: Invalid content type specified

**Examples:**

Search by text query:
```bash
curl "http://localhost:8000/api/v1/search?q=dragon&limit=10"
```

Search by tags:
```bash
curl "http://localhost:8000/api/v1/search?tags=architecture,beginner"
```

Combined search:
```bash
curl "http://localhost:8000/api/v1/search?q=temple&tags=architecture&content_types=motif,lesson"
```

Search specific content types:
```bash
curl "http://localhost:8000/api/v1/search?tags=mythology&content_types=motif"
```

---

## Error Codes

### Standard HTTP Status Codes

| Code | Description | When it occurs |
|------|-------------|----------------|
| 200 | OK | Successful GET/POST request |
| 201 | Created | Successfully created tag |
| 204 | No Content | Successfully deleted content tag |
| 400 | Bad Request | Invalid input or duplicate slug |
| 401 | Unauthorized | Missing or invalid auth token |
| 403 | Forbidden | User doesn't have required role |
| 404 | Not Found | Content or tag not found |
| 422 | Unprocessable Entity | Invalid request body format |
| 500 | Internal Server Error | Server-side error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Messages

**Tag Creation:**
- "Tag with this slug already exists" (400)
- "Not authorized" (403)

**Content Tagging:**
- "Invalid content type. Must be one of: lesson, motif, quiz, quest" (400)
- "Lesson not found" / "Motif not found" / etc. (404)
- "Tags not found: tag1, tag2" (404)

**Search:**
- "Invalid content type 'xyz'. Must be one of: lesson, motif, quiz, quest" (400)

---

## Rate Limiting

Currently, no rate limiting is implemented. For production deployments, consider:
- 100 requests/minute for authenticated users
- 30 requests/minute for anonymous users
- Higher limits for admin users

## Best Practices

1. **Tag Slugs:**
   - Use lowercase letters, numbers, and hyphens only
   - Keep slugs short and descriptive (e.g., "19th-century", not "the-nineteenth-century-period")
   - Use consistent naming conventions

2. **Search:**
   - Combine text query with tags for better results
   - Use specific content_types to improve performance
   - Keep limit reasonable (20-50) for responsive UI

3. **Error Handling:**
   - Always check for 404 when tagging content
   - Handle duplicate tag creation gracefully
   - Validate tag slugs before making requests

4. **Performance:**
   - Cache frequently accessed tags
   - Implement pagination for large result sets
   - Consider debouncing search queries in UI

