# P0-MOB-01: Offline Lesson Caching - Quick Reference

## API Endpoints

### 1. Get Cache Manifest
```
GET /api/v1/lessons/cache-manifest
Auth: Required
Returns: CacheManifestOut
```

Gets all cacheable lessons with file URLs, sizes, and priorities.

**Response:**
```json
{
  "lessons": [
    {
      "lesson_id": "uuid",
      "motif_id": "uuid",
      "motif_name": "Rồng",
      "title": "Rồng",
      "version": 1,
      "file_urls": [{"url": "...", "type": "audio", "size_bytes": 500000}],
      "total_size_bytes": 535000,
      "priority": 1
    }
  ],
  "total_size_bytes": 5350000,
  "recommended_cache_size_bytes": 52428800
}
```

### 2. Cache Lesson
```
POST /api/v1/lessons/{lesson_id}/cache
Auth: Required
Body: {"file_size_bytes": 535000, "cache_version": 1}
Returns: LessonCacheOut
```

Marks a lesson as cached by the user.

### 3. Remove Cached Lesson
```
DELETE /api/v1/lessons/{lesson_id}/cache
Auth: Required
Returns: 204 No Content
```

Removes a lesson from user's cache.

### 4. Get Cached Lessons
```
GET /api/v1/lessons/cached
Auth: Required
Returns: list[LessonCacheOut]
```

Gets all lessons cached by the current user.

## Priority Levels

- **1 (High):** Discovered or learned lessons - download first
- **2 (Medium):** Not yet discovered - download on WiFi
- **3 (Low):** Mastered lessons - download only if space available

## Cache Policy

- **Expiration:** 30 days from cache time
- **Recommended Size:** 50MB total
- **Versioning:** Re-download when lesson version changes

## File Types in Manifest

- `content` - Lesson text content
- `image` - Images, thumbnails, silhouettes
- `audio` - Audio narration files
- `video` - Video content

## Size Estimates

| Content Type | Estimated Size |
|--------------|----------------|
| Lesson text | 5KB |
| Audio narration | 500KB |
| Video | 5MB |
| Image | 100KB |
| Thumbnail | 50KB |
| Silhouette | 30KB |

## Database Schema

```sql
CREATE TABLE lesson_cache (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES lesson_content(id) ON DELETE CASCADE,
    cached_at TIMESTAMP WITH TIME ZONE NOT NULL,
    cache_version INTEGER NOT NULL DEFAULT 1,
    file_size_bytes INTEGER NOT NULL DEFAULT 0,
    is_valid BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE (user_id, lesson_id)
);
```

## Migration Command

```bash
# Development
python3 -m alembic upgrade head

# Production
docker-compose exec backend alembic upgrade head
```

## Mobile Caching Flow

```
1. Fetch cache manifest on app launch
2. Filter by priority (1 = high priority)
3. Download files from file_urls array
4. Store locally by lesson_id
5. Call POST /cache endpoint with total size
6. Use cached content when offline
7. Check expiration and re-download if needed
```

## Testing Checklist

- [ ] GET manifest returns lessons with priorities
- [ ] POST cache creates/updates entry
- [ ] GET cached returns user's cache
- [ ] DELETE cache removes entry
- [ ] Cache expires after 30 days
- [ ] Version changes trigger re-cache
- [ ] Offline mode uses cached content

## Common Use Cases

### Download high-priority lessons
```bash
curl "https://api.example.com/api/v1/lessons/cache-manifest" \
  -H "Authorization: Bearer TOKEN" | \
  jq '.lessons[] | select(.priority == 1)'
```

### Mark lesson as cached
```bash
curl -X POST "https://api.example.com/api/v1/lessons/{id}/cache" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_size_bytes": 535000}'
```

### Clear all cached lessons
```bash
for id in $(curl "https://api.example.com/api/v1/lessons/cached" \
  -H "Authorization: Bearer TOKEN" | jq -r '.[].lesson_id'); do
  curl -X DELETE "https://api.example.com/api/v1/lessons/$id/cache" \
    -H "Authorization: Bearer TOKEN"
done
```

## Error Codes

- `404` - Lesson not found
- `401` - Unauthorized (no token)
- `403` - Forbidden (invalid token)
- `409` - Conflict (if unique constraint violated)

