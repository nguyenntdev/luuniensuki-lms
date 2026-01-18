# P0-CMS-05: Content Tagging - Quick Reference

## Quick Start

### 1. Run Migration
```bash
alembic upgrade head
# or
docker-compose exec backend alembic upgrade head
```

### 2. Create Tags (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/admin/tags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "architecture",
    "name": "Architecture",
    "tag_type": "topic"
  }'
```

### 3. Tag Content (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/admin/content/motif/$MOTIF_ID/tags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tag_slugs": ["architecture", "beginner"]}'
```

### 4. Search Content
```bash
# Search by text
curl "http://localhost:8000/api/v1/search?q=dragon"

# Search by tags
curl "http://localhost:8000/api/v1/search?tags=architecture,beginner"

# Combined search
curl "http://localhost:8000/api/v1/search?q=temple&tags=architecture&content_types=motif"
```

## Tag Types

| Type | Description | Examples |
|------|-------------|----------|
| `topic` | Subject matter | architecture, mythology, nature |
| `difficulty` | Complexity level | beginner, intermediate, advanced |
| `audience` | Target audience | students, researchers, general |
| `era` | Historical period | nguyen-dynasty, 19th-century |
| `style` | Artistic style | ornate, minimalist, traditional |

## Content Types

- `lesson` - Lesson content
- `motif` - Motif patterns
- `quiz` - Quiz questions
- `quest` - Quest activities

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/tags` | None | List all active tags |
| POST | `/api/v1/admin/tags` | Admin | Create new tag |
| POST | `/api/v1/admin/content/{type}/{id}/tags` | Admin | Add tags to content |
| DELETE | `/api/v1/admin/content/{type}/{id}/tags/{slug}` | Admin | Remove tag from content |
| GET | `/api/v1/search` | None | Search content by query/tags |

## Example Tag Hierarchy

```
Topic Tags:
  - architecture
  - mythology
  - nature
  - history
  - culture

Difficulty Tags:
  - beginner
  - intermediate
  - advanced
  - expert

Audience Tags:
  - students
  - teachers
  - researchers
  - general-public

Era Tags:
  - nguyen-dynasty
  - 19th-century
  - 20th-century
  - ancient
  - medieval

Style Tags:
  - ornate
  - minimalist
  - traditional
  - modern
```

## Database Schema

```
┌─────────────────┐
│      tags       │
├─────────────────┤
│ id (PK)         │
│ slug (unique)   │
│ name            │
│ tag_type        │
│ description     │
│ is_active       │
│ created_at      │
└─────────────────┘
        │
        │ 1:N
        ▼
┌─────────────────┐
│  content_tags   │
├─────────────────┤
│ id (PK)         │
│ tag_id (FK)     │
│ content_type    │
│ content_id      │
│ created_at      │
└─────────────────┘
```

## Typical Workflow

1. **Admin creates tags** → POST /api/v1/admin/tags
2. **Admin tags content** → POST /api/v1/admin/content/{type}/{id}/tags
3. **Users search/browse** → GET /api/v1/search
4. **System recommends** → Based on user's tag preferences

## Common Queries

### List all topic tags
```bash
curl "http://localhost:8000/api/v1/tags?tag_type=topic"
```

### Search beginner architecture content
```bash
curl "http://localhost:8000/api/v1/search?tags=architecture,beginner&content_types=lesson,motif"
```

### Find all mythology motifs
```bash
curl "http://localhost:8000/api/v1/search?tags=mythology&content_types=motif"
```

### Search by era
```bash
curl "http://localhost:8000/api/v1/search?tags=nguyen-dynasty"
```

## Performance Tips

- Tags are indexed for fast lookup
- Search is case-insensitive
- Use specific content_types to narrow results
- Limit results with `limit` parameter (max 100)
- Tags are eagerly loaded to avoid N+1 queries

## Files Modified

- `backend/models.py` - Tag and ContentTag models
- `backend/schemas.py` - Tag schemas
- `backend/main.py` - Tag endpoints
- `migrations/versions/0013_content_tagging.py` - Migration

## Next Steps

1. Apply migration
2. Seed initial tags
3. Tag existing content
4. Update frontend UI
5. Add tag-based recommendations

