# P0-MOB-01: Offline Lesson Caching Implementation

## Overview

Implemented offline lesson caching functionality that allows mobile users to download and cache lessons for offline viewing. This feature provides a cache manifest endpoint, cache management endpoints, and tracks which lessons users have cached.

## Implementation Summary

### 1. Database Changes

#### New Model: `LessonCache`
**File:** `backend/models.py`

Added new table to track cached lessons:
```python
class LessonCache(Base):
    __tablename__ = "lesson_cache"
    
    id: UUID - Primary key
    user_id: UUID - FK to users (CASCADE delete)
    lesson_id: UUID - FK to lesson_content (CASCADE delete)
    cached_at: datetime - When lesson was cached
    cache_version: int - Version of cached content (default: 1)
    file_size_bytes: int - Size of cached files (default: 0)
    is_valid: bool - Whether cache is still valid (default: true)
    expires_at: datetime - Optional expiration timestamp
```

**Indexes:**
- `uq_lesson_cache_user_lesson` - Unique constraint on (user_id, lesson_id)
- `idx_lesson_cache_user` - Index on user_id
- `idx_lesson_cache_lesson` - Index on lesson_id
- `idx_lesson_cache_cached_at` - Index on cached_at

**Relationships:**
- Added `lesson_caches` relationship to User model
- Bidirectional relationships with User and LessonContent

#### Migration
**File:** `migrations/versions/0018_lesson_cache.py`
- Creates `lesson_cache` table with all columns and constraints
- Creates indexes for efficient querying
- Includes upgrade/downgrade functions

### 2. API Schemas

**File:** `backend/schemas.py`

Added schemas for cache operations:

```python
class CacheFileInfo(BaseModel):
    url: str
    type: str  # 'content', 'image', 'audio', 'video'
    size_bytes: int

class CacheManifestItemOut(BaseSchema):
    lesson_id: UUID
    motif_id: UUID
    motif_name: str
    title: str
    version: int
    file_urls: list[CacheFileInfo]
    total_size_bytes: int
    priority: int  # 1=high, 2=medium, 3=low

class CacheManifestOut(BaseModel):
    lessons: list[CacheManifestItemOut]
    total_size_bytes: int
    recommended_cache_size_bytes: int

class LessonCacheIn(BaseModel):
    file_size_bytes: int
    cache_version: int = 1

class LessonCacheOut(BaseSchema):
    id: UUID
    user_id: UUID
    lesson_id: UUID
    cached_at: datetime
    cache_version: int
    file_size_bytes: int
    is_valid: bool
    expires_at: Optional[datetime]
```

### 3. API Endpoints

**File:** `backend/main.py`

#### GET `/api/v1/lessons/cache-manifest`
**Purpose:** Get cacheable lessons with metadata
**Auth:** Required (current user)
**Returns:** `CacheManifestOut`

**Features:**
- Lists all published lessons with their associated files
- Calculates priority based on user progress:
  - Priority 1 (High): Discovered or learned lessons
  - Priority 2 (Medium): Hidden/not discovered lessons
  - Priority 3 (Low): Mastered lessons
- Includes file URLs for:
  - Lesson content
  - Audio narration
  - Video content
  - Additional images
  - Motif thumbnails and silhouettes
- Estimates file sizes for cache planning
- Returns recommended cache size (50MB)

**Size Estimates:**
- Lesson content: 5KB
- Audio narration: 500KB
- Video: 5MB
- Images: 100KB each
- Thumbnails: 50KB
- Silhouettes: 30KB

#### POST `/api/v1/lessons/{lesson_id}/cache`
**Purpose:** Mark a lesson as cached by user
**Auth:** Required (current user)
**Body:** `LessonCacheIn`
**Returns:** `LessonCacheOut`

**Features:**
- Creates or updates cache entry for a lesson
- Sets cache expiration to 30 days from caching
- Updates existing entries if already cached
- Validates lesson exists before caching
- Returns cache entry details

#### DELETE `/api/v1/lessons/{lesson_id}/cache`
**Purpose:** Remove lesson from user's cache
**Auth:** Required (current user)
**Returns:** 204 No Content

**Features:**
- Deletes cache entry for specified lesson
- Returns 404 if cache entry doesn't exist
- Cascading delete handled by database constraints

#### GET `/api/v1/lessons/cached`
**Purpose:** Get all cached lessons for current user
**Auth:** Required (current user)
**Returns:** `list[LessonCacheOut]`

**Features:**
- Lists all lessons cached by the user
- Ordered by most recently cached first
- Includes cache validity and expiration info

## Database Migration

Run the migration to create the `lesson_cache` table:

```bash
# Development
cd /path/to/luuniensuki-lms
python3 -m alembic upgrade head

# Production (via Docker)
docker-compose exec backend alembic upgrade head
```

## API Usage Examples

### 1. Get Cache Manifest

```bash
curl -X GET "https://api.luuniensuki.com/api/v1/lessons/cache-manifest" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

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
      "file_urls": [
        {
          "url": "https://...",
          "type": "audio",
          "size_bytes": 500000
        }
      ],
      "total_size_bytes": 535000,
      "priority": 1
    }
  ],
  "total_size_bytes": 5350000,
  "recommended_cache_size_bytes": 52428800
}
```

### 2. Mark Lesson as Cached

```bash
curl -X POST "https://api.luuniensuki.com/api/v1/lessons/{lesson_id}/cache" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_size_bytes": 535000,
    "cache_version": 1
  }'
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "lesson_id": "uuid",
  "cached_at": "2025-01-18T12:00:00Z",
  "cache_version": 1,
  "file_size_bytes": 535000,
  "is_valid": true,
  "expires_at": "2025-02-17T12:00:00Z"
}
```

### 3. Get Cached Lessons

```bash
curl -X GET "https://api.luuniensuki.com/api/v1/lessons/cached" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Remove Cached Lesson

```bash
curl -X DELETE "https://api.luuniensuki.com/api/v1/lessons/{lesson_id}/cache" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Mobile Integration

### Recommended Caching Strategy

1. **On App Launch:**
   - Fetch cache manifest
   - Check for high-priority lessons (priority=1)
   - Download and cache high-priority lessons in background

2. **On WiFi Connection:**
   - Check for medium-priority lessons (priority=2)
   - Cache additional lessons up to recommended size

3. **Cache Invalidation:**
   - Check `expires_at` on app launch
   - Re-download lessons with `is_valid=false`
   - Update cache when lesson version changes

4. **Storage Management:**
   - Monitor total cache size
   - Remove low-priority cached lessons when storage is low
   - Respect user preferences for cache size limits

### Implementation Notes

1. **File Downloads:**
   - Download files from URLs in `file_urls` array
   - Store locally with lesson_id as directory structure
   - Track total size and report back to API

2. **Cache Versioning:**
   - Compare lesson `version` from manifest with cached version
   - Re-download if versions differ
   - Update cache entry after successful download

3. **Offline Availability:**
   - Check cache before fetching from network
   - Fall back to cached content when offline
   - Display cache age/expiration to user

## Testing Checklist

- [ ] Migration runs successfully
- [ ] Cache manifest endpoint returns correct data
- [ ] Priority calculation works correctly
- [ ] Caching a lesson creates database entry
- [ ] Re-caching updates existing entry
- [ ] Deleting cache removes entry
- [ ] Getting cached lessons returns user's cache
- [ ] File size estimates are reasonable
- [ ] Cache expiration is set correctly
- [ ] Unique constraint prevents duplicate caches
- [ ] Foreign keys cascade delete properly

## Files Changed

1. `backend/models.py` - Added LessonCache model and relationship
2. `backend/schemas.py` - Added cache-related schemas
3. `backend/main.py` - Added cache API endpoints
4. `migrations/versions/0018_lesson_cache.py` - Database migration

## Future Enhancements

1. **Cache Analytics:**
   - Track cache hit/miss rates
   - Monitor cache usage patterns
   - Analyze which lessons are most cached

2. **Smart Caching:**
   - ML-based priority prediction
   - Automatic cache pre-loading
   - User-specific recommendations

3. **Cache Compression:**
   - Compress cached files
   - Delta updates for changed content
   - Bandwidth optimization

4. **Cache Sharing:**
   - P2P cache sharing between users
   - Classroom-based cache distribution
   - Offline-first sync strategies

## Notes

- Cache expires after 30 days by default
- Recommended cache size is 50MB
- File size estimates are conservative
- Priority is calculated per user based on their progress
- All endpoints require authentication
- Supports concurrent caching of multiple lessons

