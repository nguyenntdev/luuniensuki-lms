# P0-CMS-05: Content Tagging Implementation Summary

## Overview

This implementation adds a comprehensive content tagging system for recommendations and search functionality to the Luuniensuki LMS. The system allows admins to tag content (lessons, motifs, quizzes, quests) with categorized tags and enables users to search and filter content based on these tags.

## Database Schema

### Tag Model
- **id**: UUID primary key
- **slug**: str(100), unique - URL-friendly identifier
- **name**: str(200) - Human-readable name
- **tag_type**: enum (topic, difficulty, audience, era, style)
- **description**: text, nullable - Optional description
- **is_active**: boolean, default true
- **created_at**: datetime with timezone

**Indexes:**
- `idx_tags_slug` on slug
- `idx_tags_type` on tag_type  
- `idx_tags_active` on is_active

### ContentTag Model (Association Table)
- **id**: UUID primary key
- **tag_id**: UUID, foreign key to tags (CASCADE on delete)
- **content_type**: enum (lesson, motif, quiz, quest)
- **content_id**: UUID - ID of the tagged content
- **created_at**: datetime with timezone

**Constraints:**
- Unique constraint on (tag_id, content_type, content_id)

**Indexes:**
- `idx_content_tags_tag` on tag_id
- `idx_content_tags_content_type` on content_type
- `idx_content_tags_content` on (content_type, content_id)

## Tag Types

- **topic**: Subject matter (e.g., "architecture", "mythology", "nature")
- **difficulty**: Complexity level (e.g., "beginner", "intermediate", "advanced")
- **audience**: Target audience (e.g., "students", "researchers", "general")
- **era**: Historical period (e.g., "nguyen-dynasty", "19th-century")
- **style**: Artistic or presentation style (e.g., "ornate", "minimalist")

## API Endpoints

### 1. GET /api/v1/tags
**Description:** List all active tags, optionally filtered by type

**Query Parameters:**
- `tag_type` (optional): Filter by tag type (topic, difficulty, audience, era, style)

**Response:** Array of TagOut objects

**Example:**
```bash
curl http://localhost:8000/api/v1/tags?tag_type=topic
```

**Response:**
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

### 2. POST /api/v1/admin/tags
**Description:** Create a new tag (admin only)

**Authentication:** Requires admin role

**Request Body:**
```json
{
  "slug": "architecture",
  "name": "Architecture",
  "tag_type": "topic",
  "description": "Architectural elements and structures",
  "is_active": true
}
```

**Response:** TagOut object (201 Created)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/tags \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "architecture",
    "name": "Architecture",
    "tag_type": "topic",
    "description": "Architectural elements and structures"
  }'
```

### 3. POST /api/v1/admin/content/{content_type}/{content_id}/tags
**Description:** Add tags to content (admin only)

**Authentication:** Requires admin role

**Path Parameters:**
- `content_type`: Type of content (lesson, motif, quiz, quest)
- `content_id`: UUID of the content

**Request Body:**
```json
{
  "tag_slugs": ["architecture", "beginner", "19th-century"]
}
```

**Response:** Array of ContentTagOut objects with embedded tag details

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/content/motif/123e4567-e89b-12d3-a456-426614174001/tags \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tag_slugs": ["architecture", "beginner"]
  }'
```

**Response:**
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

### 4. DELETE /api/v1/admin/content/{content_type}/{content_id}/tags/{tag_slug}
**Description:** Remove a tag from content (admin only)

**Authentication:** Requires admin role

**Path Parameters:**
- `content_type`: Type of content (lesson, motif, quiz, quest)
- `content_id`: UUID of the content
- `tag_slug`: Slug of the tag to remove

**Response:** 204 No Content

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/admin/content/motif/123e4567-e89b-12d3-a456-426614174001/tags/architecture \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. GET /api/v1/search
**Description:** Search content by query and/or tags

**Query Parameters:**
- `q` (optional): Search query string
- `tags` (optional): Comma-separated list of tag slugs to filter by
- `content_types` (optional): Comma-separated list of content types to search (default: all)
- `limit` (optional): Maximum number of results (1-100, default: 20)

**Response:** SearchResponse object

**Example 1 - Search by query:**
```bash
curl "http://localhost:8000/api/v1/search?q=dragon"
```

**Example 2 - Search by tags:**
```bash
curl "http://localhost:8000/api/v1/search?tags=architecture,beginner"
```

**Example 3 - Combined search:**
```bash
curl "http://localhost:8000/api/v1/search?q=dragon&tags=mythology&content_types=motif,lesson&limit=10"
```

**Response:**
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

## Files Modified

1. **backend/models.py**
   - Added `TagType` enum (topic, difficulty, audience, era, style)
   - Added `ContentType` enum (lesson, motif, quiz, quest)
   - Added `Tag` model with indexes
   - Added `ContentTag` association model with unique constraint

2. **backend/schemas.py**
   - Added `TagOut`, `TagCreateIn` schemas
   - Added `ContentTagOut`, `ContentTagCreateIn` schemas
   - Added `SearchRequest`, `SearchResultItem`, `SearchResponse` schemas

3. **backend/main.py**
   - Added Tag and ContentTag imports
   - Added tag-related schemas inline (matching project pattern)
   - Added 5 new endpoints for tag management and search

4. **migrations/versions/0013_content_tagging.py**
   - Created migration for tags and content_tags tables
   - Added all necessary indexes for search performance

## Migration

To apply the migration:

```bash
# Using alembic directly
alembic upgrade head

# Or using docker-compose
docker-compose exec backend alembic upgrade head
```

## Usage Examples

### Step 1: Create Tags (Admin)

```python
import requests

# Admin authentication
headers = {"Authorization": "Bearer ADMIN_TOKEN"}

# Create topic tags
topics = [
    {"slug": "architecture", "name": "Architecture", "tag_type": "topic"},
    {"slug": "mythology", "name": "Mythology", "tag_type": "topic"},
    {"slug": "nature", "name": "Nature", "tag_type": "topic"},
]

for topic in topics:
    response = requests.post(
        "http://localhost:8000/api/v1/admin/tags",
        headers=headers,
        json=topic
    )
    print(f"Created tag: {response.json()['name']}")

# Create difficulty tags
difficulties = [
    {"slug": "beginner", "name": "Beginner", "tag_type": "difficulty"},
    {"slug": "intermediate", "name": "Intermediate", "tag_type": "difficulty"},
    {"slug": "advanced", "name": "Advanced", "tag_type": "difficulty"},
]

for diff in difficulties:
    response = requests.post(
        "http://localhost:8000/api/v1/admin/tags",
        headers=headers,
        json=diff
    )
    print(f"Created tag: {response.json()['name']}")
```

### Step 2: Tag Content (Admin)

```python
# Tag a motif
motif_id = "123e4567-e89b-12d3-a456-426614174001"
response = requests.post(
    f"http://localhost:8000/api/v1/admin/content/motif/{motif_id}/tags",
    headers=headers,
    json={"tag_slugs": ["architecture", "beginner", "19th-century"]}
)
print(f"Tagged motif with {len(response.json())} tags")

# Tag a lesson
lesson_id = "456e7890-e89b-12d3-a456-426614174002"
response = requests.post(
    f"http://localhost:8000/api/v1/admin/content/lesson/{lesson_id}/tags",
    headers=headers,
    json={"tag_slugs": ["mythology", "intermediate"]}
)
print(f"Tagged lesson with {len(response.json())} tags")
```

### Step 3: Search Content (All Users)

```python
# Search by text query
response = requests.get(
    "http://localhost:8000/api/v1/search",
    params={"q": "dragon", "limit": 10}
)
print(f"Found {response.json()['total']} results for 'dragon'")

# Search by tags
response = requests.get(
    "http://localhost:8000/api/v1/search",
    params={"tags": "architecture,beginner"}
)
print(f"Found {response.json()['total']} beginner architecture content")

# Combined search
response = requests.get(
    "http://localhost:8000/api/v1/search",
    params={
        "q": "temple",
        "tags": "architecture",
        "content_types": "motif,lesson"
    }
)
print(f"Found {response.json()['total']} temple-related architecture content")
```

### Step 4: List Tags

```python
# Get all tags
response = requests.get("http://localhost:8000/api/v1/tags")
print(f"Total tags: {len(response.json())}")

# Get tags by type
response = requests.get(
    "http://localhost:8000/api/v1/tags",
    params={"tag_type": "difficulty"}
)
print(f"Difficulty tags: {[tag['name'] for tag in response.json()]}")
```

## Testing Guide

### 1. Unit Tests

Create a test file `tests/backend/test_tags.py`:

```python
import pytest
from uuid import uuid4
from backend.models import Tag, ContentTag, TagType, ContentType

def test_create_tag(db_session, admin_client):
    """Test creating a new tag."""
    response = admin_client.post(
        "/api/v1/admin/tags",
        json={
            "slug": "test-topic",
            "name": "Test Topic",
            "tag_type": "topic",
            "description": "A test topic tag"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "test-topic"
    assert data["name"] == "Test Topic"
    assert data["tag_type"] == "topic"

def test_create_duplicate_tag(db_session, admin_client):
    """Test creating a tag with duplicate slug."""
    # Create first tag
    admin_client.post(
        "/api/v1/admin/tags",
        json={"slug": "duplicate", "name": "Duplicate", "tag_type": "topic"}
    )
    # Try to create duplicate
    response = admin_client.post(
        "/api/v1/admin/tags",
        json={"slug": "duplicate", "name": "Duplicate 2", "tag_type": "topic"}
    )
    assert response.status_code == 400

def test_list_tags(db_session, client):
    """Test listing tags."""
    # Create some tags
    tags = [
        Tag(id=uuid4(), slug="tag1", name="Tag 1", tag_type="topic", is_active=True),
        Tag(id=uuid4(), slug="tag2", name="Tag 2", tag_type="difficulty", is_active=True),
    ]
    db_session.add_all(tags)
    db_session.commit()

    response = client.get("/api/v1/tags")
    assert response.status_code == 200
    assert len(response.json()) >= 2

def test_list_tags_by_type(db_session, client):
    """Test filtering tags by type."""
    response = client.get("/api/v1/tags?tag_type=topic")
    assert response.status_code == 200
    data = response.json()
    for tag in data:
        assert tag["tag_type"] == "topic"

def test_add_content_tags(db_session, admin_client, sample_motif):
    """Test adding tags to content."""
    # Create tags
    tags = [
        Tag(id=uuid4(), slug="arch", name="Architecture", tag_type="topic", is_active=True),
        Tag(id=uuid4(), slug="easy", name="Easy", tag_type="difficulty", is_active=True),
    ]
    db_session.add_all(tags)
    db_session.commit()

    response = admin_client.post(
        f"/api/v1/admin/content/motif/{sample_motif.id}/tags",
        json={"tag_slugs": ["arch", "easy"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_remove_content_tag(db_session, admin_client, sample_motif):
    """Test removing a tag from content."""
    # Create and add tag
    tag = Tag(id=uuid4(), slug="test", name="Test", tag_type="topic", is_active=True)
    db_session.add(tag)
    db_session.commit()

    admin_client.post(
        f"/api/v1/admin/content/motif/{sample_motif.id}/tags",
        json={"tag_slugs": ["test"]}
    )

    # Remove tag
    response = admin_client.delete(
        f"/api/v1/admin/content/motif/{sample_motif.id}/tags/test"
    )
    assert response.status_code == 204

def test_search_by_query(db_session, client, sample_lesson):
    """Test searching content by text query."""
    response = client.get("/api/v1/search?q=dragon")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data

def test_search_by_tags(db_session, client, sample_motif):
    """Test searching content by tags."""
    # Add tag to motif
    tag = Tag(id=uuid4(), slug="arch", name="Architecture", tag_type="topic", is_active=True)
    db_session.add(tag)
    content_tag = ContentTag(
        id=uuid4(),
        tag_id=tag.id,
        content_type="motif",
        content_id=sample_motif.id
    )
    db_session.add(content_tag)
    db_session.commit()

    response = client.get("/api/v1/search?tags=arch")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
```

### 2. Integration Testing

```bash
# Run tests
cd /Users/nguyennt/Documents/luuniensuki-lms
pytest tests/backend/test_tags.py -v

# Run with coverage
pytest tests/backend/test_tags.py --cov=backend.models --cov=backend.main
```

### 3. Manual Testing with cURL

```bash
# 1. Login as admin
LOGIN_RESPONSE=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}')
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

# 2. Create a tag
curl -X POST http://localhost:8000/api/v1/admin/tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "vietnamese-culture",
    "name": "Vietnamese Culture",
    "tag_type": "topic",
    "description": "Content related to Vietnamese cultural elements"
  }'

# 3. List all tags
curl http://localhost:8000/api/v1/tags | jq

# 4. Tag a motif (replace MOTIF_ID with actual ID)
MOTIF_ID="your-motif-uuid-here"
curl -X POST http://localhost:8000/api/v1/admin/content/motif/$MOTIF_ID/tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tag_slugs": ["vietnamese-culture"]}'

# 5. Search by tag
curl "http://localhost:8000/api/v1/search?tags=vietnamese-culture" | jq

# 6. Remove a tag from content
curl -X DELETE http://localhost:8000/api/v1/admin/content/motif/$MOTIF_ID/tags/vietnamese-culture \
  -H "Authorization: Bearer $TOKEN"
```

## Performance Considerations

### Indexes for Search Performance

The implementation includes several indexes to optimize search queries:

1. **Tag Indexes:**
   - `idx_tags_slug`: Fast lookup by slug
   - `idx_tags_type`: Efficient filtering by tag type
   - `idx_tags_active`: Quick filtering of active tags

2. **ContentTag Indexes:**
   - `idx_content_tags_tag`: Fast lookup of all content with a specific tag
   - `idx_content_tags_content_type`: Efficient filtering by content type
   - `idx_content_tags_content`: Combined index for finding tags of specific content

### Query Optimization

- Uses `selectinload` to eagerly load tag relationships and avoid N+1 queries
- Filters inactive tags at the database level
- Limits result sets to prevent excessive memory usage
- Uses ILIKE for case-insensitive text search (consider full-text search for production)

### Scaling Recommendations

For production deployments with large datasets:

1. **Add Full-Text Search:**
   ```sql
   -- Add tsvector column to lessons
   ALTER TABLE lesson_content ADD COLUMN search_vector tsvector;
   CREATE INDEX idx_lesson_search ON lesson_content USING GIN(search_vector);
   ```

2. **Implement Caching:**
   - Cache frequently accessed tags with Redis
   - Cache popular search queries
   - Implement tag cloud with cached tag counts

3. **Add Pagination:**
   - Implement cursor-based pagination for search results
   - Add offset/limit parameters to all list endpoints

4. **Consider Elasticsearch:**
   - For advanced search features (fuzzy matching, relevance scoring)
   - Better performance for complex queries
   - Built-in analytics and aggregations

## Future Enhancements

1. **Tag Management UI:**
   - Admin interface for creating and managing tags
   - Bulk tag operations
   - Tag usage statistics

2. **Smart Recommendations:**
   - Use tags to power content recommendations
   - Track user tag preferences
   - Suggest related content based on tag similarity

3. **Tag Analytics:**
   - Track tag popularity
   - Identify trending topics
   - Analyze user search patterns

4. **Tag Hierarchy:**
   - Support parent-child tag relationships
   - Tag synonyms and aliases
   - Automatic tag suggestions

5. **Advanced Search:**
   - Boolean operators (AND, OR, NOT)
   - Tag weight/relevance scoring
   - Faceted search with tag counts
   - Auto-complete for tags

## Security Notes

- All tag creation, modification, and content tagging operations require admin authentication
- Tag listing and search are public (no authentication required)
- Input validation prevents SQL injection and XSS attacks
- Unique constraints prevent duplicate tags
- Foreign key constraints ensure data integrity

## Troubleshooting

### Common Issues

1. **Migration fails:**
   ```bash
   # Check current migration version
   alembic current

   # Try upgrading one step at a time
   alembic upgrade +1
   ```

2. **Tag slug conflicts:**
   - Ensure slugs are unique before creating
   - Use URL-friendly slugs (lowercase, hyphens, no spaces)

3. **Search returns no results:**
   - Check if content is properly tagged
   - Verify tag slugs are correct
   - Ensure tags are active (is_active=true)

4. **Performance issues:**
   - Add database indexes if missing
   - Enable query logging to identify slow queries
   - Consider implementing caching

## Checklist

- [x] Created Tag and ContentTag models in backend/models.py
- [x] Added TagType and ContentType enums
- [x] Created migration file 0013_content_tagging.py
- [x] Added tag schemas to backend/schemas.py
- [x] Implemented GET /api/v1/tags endpoint
- [x] Implemented POST /api/v1/admin/tags endpoint
- [x] Implemented POST /api/v1/admin/content/{type}/{id}/tags endpoint
- [x] Implemented DELETE /api/v1/admin/content/{type}/{id}/tags/{slug} endpoint
- [x] Implemented GET /api/v1/search endpoint
- [x] Added appropriate indexes for search performance
- [x] Created comprehensive documentation

## Next Steps

1. Apply the migration to the database
2. Seed initial tags for common categories
3. Tag existing content in the database
4. Update frontend to display tags
5. Add tag filtering to explore/browse pages
6. Implement tag-based recommendations
7. Create admin UI for tag management
8. Add analytics tracking for tag usage

## Related Documentation

- See `P0-CMS-03_CONTENT_VERSIONING_IMPLEMENTATION.md` for content versioning
- See `P0_ANA_01_IMPLEMENTATION_SUMMARY.md` for analytics integration
- See `TASK_CODEX.md` for overall project roadmap

