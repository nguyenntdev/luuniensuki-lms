# P0-MOB-01: Offline Lesson Caching

## 🎯 Feature Overview

Offline lesson caching allows mobile users to download and cache lessons for offline viewing. This feature provides intelligent caching with priority-based recommendations and comprehensive cache management.

## ✨ Key Features

- **📱 Smart Caching:** Priority-based lesson recommendations
- **📊 Size Estimation:** Accurate cache size planning
- **🔄 Version Tracking:** Automatic cache invalidation on updates
- **⏰ Expiration:** 30-day cache validity
- **🗂️ File Management:** Track all cacheable assets (text, audio, video, images)

## 🚀 Quick Start

### 1. Run Migration
```bash
python3 -m alembic upgrade head
```

### 2. Test Endpoints
```bash
./test_cache_api.sh
```

### 3. Integrate in Mobile App
```typescript
// Get cacheable lessons
const manifest = await api.get('/api/v1/lessons/cache-manifest');

// Cache a lesson
await api.post(`/api/v1/lessons/${lessonId}/cache`, {
  file_size_bytes: totalSize,
  cache_version: 1
});

// Get cached lessons
const cached = await api.get('/api/v1/lessons/cached');
```

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [P0-MOB-01_INDEX.md](./P0-MOB-01_INDEX.md) | Complete documentation index | All |
| [P0-MOB-01_SUMMARY.md](./P0-MOB-01_SUMMARY.md) | Implementation summary | Developers, DevOps |
| [P0-MOB-01_QUICK_REFERENCE.md](./P0-MOB-01_QUICK_REFERENCE.md) | API quick reference | Developers |
| [P0-MOB-01_IMPLEMENTATION.md](./P0-MOB-01_IMPLEMENTATION.md) | Technical details | Backend developers |
| [P0-MOB-01_API_TESTING.md](./P0-MOB-01_API_TESTING.md) | Testing guide | QA engineers |
| [test_cache_api.sh](./test_cache_api.sh) | Automated test script | All |

## 🔌 API Endpoints

### Get Cache Manifest
```http
GET /api/v1/lessons/cache-manifest
Authorization: Bearer {token}
```

Returns all cacheable lessons with priorities and file information.

### Cache Lesson
```http
POST /api/v1/lessons/{lesson_id}/cache
Authorization: Bearer {token}
Content-Type: application/json

{
  "file_size_bytes": 535000,
  "cache_version": 1
}
```

Marks a lesson as cached by the user.

### Get Cached Lessons
```http
GET /api/v1/lessons/cached
Authorization: Bearer {token}
```

Returns all lessons cached by the current user.

### Remove Cached Lesson
```http
DELETE /api/v1/lessons/{lesson_id}/cache
Authorization: Bearer {token}
```

Removes a lesson from the user's cache.

## 🎨 Priority System

Lessons are prioritized based on user progress:

| Priority | Status | When to Cache |
|----------|--------|---------------|
| 1 (High) | Discovered/Learned | Download immediately |
| 2 (Medium) | Not discovered | Download on WiFi |
| 3 (Low) | Mastered | Download if space available |

## 📦 File Types

Each lesson may include:
- **Content:** Lesson text (5KB)
- **Audio:** Narration files (500KB)
- **Video:** Lesson videos (5MB)
- **Images:** Additional images (100KB each)
- **Thumbnails:** Motif thumbnails (50KB)
- **Silhouettes:** Motif silhouettes (30KB)

## 🗄️ Database Schema

```sql
CREATE TABLE lesson_cache (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES lesson_content(id) ON DELETE CASCADE,
    cached_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    cache_version INTEGER NOT NULL DEFAULT 1,
    file_size_bytes INTEGER NOT NULL DEFAULT 0,
    is_valid BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE (user_id, lesson_id)
);
```

## 🧪 Testing

Run the automated test script:
```bash
./test_cache_api.sh
```

Or test manually:
```bash
# Get token
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' | \
  jq -r '.access_token')

# Get manifest
curl "http://localhost:8000/api/v1/lessons/cache-manifest" \
  -H "Authorization: Bearer $TOKEN" | jq

# Cache a lesson
curl -X POST "http://localhost:8000/api/v1/lessons/{id}/cache" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_size_bytes": 535000}'
```

## 📱 Mobile Integration

### Recommended Flow

1. **On App Launch (WiFi):**
   - Fetch cache manifest
   - Download high-priority lessons
   - Mark as cached

2. **Background Sync:**
   - Check for cache expiration
   - Update outdated caches
   - Download medium-priority lessons

3. **Offline Mode:**
   - Check local cache first
   - Fall back to network if available
   - Show cache status to user

4. **Storage Management:**
   - Monitor total cache size
   - Respect user preferences
   - Clean up expired/low-priority caches

## ⚙️ Configuration

### Cache Settings
- **Default Expiration:** 30 days
- **Recommended Size:** 50MB
- **Cache Version:** Tracks lesson updates

### Customization
Edit these values in `backend/main.py`:
```python
# Cache expiration
expires = now + timedelta(days=30)  # Change days value

# Recommended size
recommended_cache_size_bytes=50 * 1024 * 1024  # Change MB value
```

## 🔍 Monitoring

Track these metrics:
- Cache API request volume
- Average manifest size
- Cache hit rate
- Most cached lessons
- Cache size distribution
- Error rates

## 🐛 Troubleshooting

### Migration Fails
```bash
# Check database connection
python3 -c "from backend.config import settings; print(settings.database_url)"

# Check migration status
python3 -m alembic current

# Retry migration
python3 -m alembic upgrade head
```

### Endpoint Returns 404
- Verify lesson exists
- Check user has access
- Confirm authentication token

### Large Response Time
- Add database indexes (already included)
- Consider caching manifest
- Implement pagination if needed

## 📈 Future Enhancements

- [ ] Smart pre-caching based on user behavior
- [ ] Compression for faster downloads
- [ ] Delta updates for changed content
- [ ] P2P cache sharing
- [ ] Analytics dashboard
- [ ] Cache quality metrics

## 🤝 Contributing

When extending this feature:
1. Update relevant documentation
2. Add tests to `test_cache_api.sh`
3. Update API_TESTING.md with new scenarios
4. Increment cache_version if schema changes

## 📞 Support

- **Documentation:** See P0-MOB-01_INDEX.md
- **API Reference:** See P0-MOB-01_QUICK_REFERENCE.md
- **Testing:** See P0-MOB-01_API_TESTING.md
- **Implementation:** See P0-MOB-01_IMPLEMENTATION.md

## ✅ Checklist

Before deployment:
- [ ] Run migration in staging
- [ ] Test all endpoints
- [ ] Verify priority calculation
- [ ] Check cache expiration
- [ ] Test error scenarios
- [ ] Monitor database performance
- [ ] Update mobile app
- [ ] Document any changes

## 📄 License

Part of the Luuniensuki LMS project.

---

**Status:** ✅ Ready for Production  
**Version:** 1.0  
**Last Updated:** 2025-01-18

