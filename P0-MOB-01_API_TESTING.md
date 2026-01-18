# P0-MOB-01: API Testing Guide

## Setup

### Prerequisites
- Backend server running
- Valid user authentication token
- Database migrated to include lesson_cache table

### Get Authentication Token

```bash
# Login to get token
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

## Test Suite

### Test 1: Get Cache Manifest

**Purpose:** Verify manifest endpoint returns lessons with priorities

```bash
curl -X GET "http://localhost:8000/api/v1/lessons/cache-manifest" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected Response:**
```json
{
  "lessons": [
    {
      "lesson_id": "...",
      "motif_id": "...",
      "motif_name": "...",
      "title": "...",
      "version": 1,
      "file_urls": [...],
      "total_size_bytes": 535000,
      "priority": 1
    }
  ],
  "total_size_bytes": 5350000,
  "recommended_cache_size_bytes": 52428800
}
```

**Verify:**
- [ ] Response contains lessons array
- [ ] Each lesson has lesson_id, motif_id, title
- [ ] priority is 1, 2, or 3
- [ ] file_urls is array with url, type, size_bytes
- [ ] total_size_bytes is sum of all lessons
- [ ] recommended_cache_size_bytes is 52428800 (50MB)

### Test 2: Filter High Priority Lessons

```bash
curl -X GET "http://localhost:8000/api/v1/lessons/cache-manifest" \
  -H "Authorization: Bearer $TOKEN" | \
  jq '.lessons[] | select(.priority == 1)'
```

**Verify:**
- [ ] Only returns lessons with priority=1
- [ ] These are discovered/learned lessons for the user

### Test 3: Cache a Lesson

**Get a lesson ID from manifest:**
```bash
LESSON_ID=$(curl -X GET "http://localhost:8000/api/v1/lessons/cache-manifest" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.lessons[0].lesson_id')

echo "Caching lesson: $LESSON_ID"
```

**Cache the lesson:**
```bash
curl -X POST "http://localhost:8000/api/v1/lessons/$LESSON_ID/cache" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_size_bytes": 535000,
    "cache_version": 1
  }' | jq
```

**Expected Response:**
```json
{
  "id": "...",
  "user_id": "...",
  "lesson_id": "...",
  "cached_at": "2025-01-18T12:00:00Z",
  "cache_version": 1,
  "file_size_bytes": 535000,
  "is_valid": true,
  "expires_at": "2025-02-17T12:00:00Z"
}
```

**Verify:**
- [ ] Response contains cache entry
- [ ] cached_at is current timestamp
- [ ] expires_at is 30 days from cached_at
- [ ] is_valid is true
- [ ] file_size_bytes matches request

### Test 4: Re-cache Same Lesson (Update)

```bash
curl -X POST "http://localhost:8000/api/v1/lessons/$LESSON_ID/cache" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_size_bytes": 600000,
    "cache_version": 2
  }' | jq
```

**Verify:**
- [ ] Same cache entry ID returned
- [ ] cached_at is updated to current time
- [ ] file_size_bytes is updated to 600000
- [ ] cache_version is updated to 2
- [ ] expires_at is updated to new 30-day period

### Test 5: Get Cached Lessons

```bash
curl -X GET "http://localhost:8000/api/v1/lessons/cached" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected Response:**
```json
[
  {
    "id": "...",
    "user_id": "...",
    "lesson_id": "...",
    "cached_at": "2025-01-18T12:00:00Z",
    "cache_version": 2,
    "file_size_bytes": 600000,
    "is_valid": true,
    "expires_at": "2025-02-17T12:00:00Z"
  }
]
```

**Verify:**
- [ ] Array contains cached lesson
- [ ] Ordered by cached_at DESC (most recent first)
- [ ] All cache fields are present

### Test 6: Cache Multiple Lessons

```bash
# Cache 3 lessons
for i in {0..2}; do
  LESSON_ID=$(curl -X GET "http://localhost:8000/api/v1/lessons/cache-manifest" \
    -H "Authorization: Bearer $TOKEN" | jq -r ".lessons[$i].lesson_id")
  
  curl -X POST "http://localhost:8000/api/v1/lessons/$LESSON_ID/cache" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"file_size_bytes\": $((500000 + i * 10000))}" | jq -c
  
  sleep 1
done
```

**Verify cached count:**
```bash
CACHED_COUNT=$(curl -X GET "http://localhost:8000/api/v1/lessons/cached" \
  -H "Authorization: Bearer $TOKEN" | jq 'length')

echo "Cached lessons: $CACHED_COUNT"
# Should be at least 3
```

### Test 7: Remove Cached Lesson

```bash
curl -X DELETE "http://localhost:8000/api/v1/lessons/$LESSON_ID/cache" \
  -H "Authorization: Bearer $TOKEN" -v
```

**Expected Response:**
- HTTP Status: 204 No Content
- Empty body

**Verify:**
```bash
# Should return fewer lessons now
curl -X GET "http://localhost:8000/api/v1/lessons/cached" \
  -H "Authorization: Bearer $TOKEN" | jq 'length'
```

**Verify:**
- [ ] 204 status code
- [ ] Lesson removed from cache
- [ ] GET /cached returns one less lesson

### Test 8: Remove Non-existent Cache

```bash
# Use a random UUID
curl -X DELETE "http://localhost:8000/api/v1/lessons/00000000-0000-0000-0000-000000000000/cache" \
  -H "Authorization: Bearer $TOKEN" -v
```

**Expected Response:**
- HTTP Status: 404 Not Found
- Body: `{"detail": "Cached lesson not found"}`

### Test 9: Cache Non-existent Lesson

```bash
curl -X POST "http://localhost:8000/api/v1/lessons/00000000-0000-0000-0000-000000000000/cache" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_size_bytes": 500000}' | jq
```

**Expected Response:**
- HTTP Status: 404 Not Found
- Body: `{"detail": "Lesson not found"}`

### Test 10: Unauthorized Access

```bash
# Without token
curl -X GET "http://localhost:8000/api/v1/lessons/cache-manifest" -v

# With invalid token
curl -X GET "http://localhost:8000/api/v1/lessons/cache-manifest" \
  -H "Authorization: Bearer invalid_token" -v
```

**Expected Response:**
- HTTP Status: 401 Unauthorized

## Complete Test Script

Save as `test_cache_api.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
EMAIL="test@example.com"
PASSWORD="password123"

# Login and get token
echo "=== Logging in ==="
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo "Failed to get token"
  exit 1
fi

echo "Token acquired: ${TOKEN:0:20}..."

# Test 1: Get manifest
echo -e "\n=== Test 1: Get cache manifest ==="
curl -s -X GET "$BASE_URL/api/v1/lessons/cache-manifest" \
  -H "Authorization: Bearer $TOKEN" | jq '.lessons | length'

# Test 2: Cache a lesson
echo -e "\n=== Test 2: Cache a lesson ==="
LESSON_ID=$(curl -s -X GET "$BASE_URL/api/v1/lessons/cache-manifest" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.lessons[0].lesson_id')

curl -s -X POST "$BASE_URL/api/v1/lessons/$LESSON_ID/cache" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_size_bytes": 535000}' | jq

# Test 3: Get cached lessons
echo -e "\n=== Test 3: Get cached lessons ==="
curl -s -X GET "$BASE_URL/api/v1/lessons/cached" \
  -H "Authorization: Bearer $TOKEN" | jq 'length'

# Test 4: Delete cache
echo -e "\n=== Test 4: Delete cached lesson ==="
curl -s -X DELETE "$BASE_URL/api/v1/lessons/$LESSON_ID/cache" \
  -H "Authorization: Bearer $TOKEN" -w "\nHTTP Status: %{http_code}\n"

echo -e "\n=== All tests complete ==="
```

Run with:
```bash
chmod +x test_cache_api.sh
./test_cache_api.sh
```

## Success Criteria

All tests should pass with:
- ✅ Correct HTTP status codes
- ✅ Valid JSON responses
- ✅ Correct data structure
- ✅ Proper authentication enforcement
- ✅ Database constraints working
- ✅ Cache expiration set correctly

