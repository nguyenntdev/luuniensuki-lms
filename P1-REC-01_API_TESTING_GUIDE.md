# P1-REC-01: Recommendation Engine API Testing Guide

## Prerequisites

1. Backend server running (http://localhost:8000)
2. Valid user account and authentication token
3. Some content (motifs/lessons) in the database

## Get Authentication Token

```bash
# Login to get token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

## Test 1: Get All Recommendations

Get personalized recommendations across all types.

```bash
curl -X GET "http://localhost:8000/api/v1/recommendations" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected Response:**
```json
{
  "continue_learning": [
    {
      "content_type": "lesson",
      "content_id": "uuid",
      "title": "Lesson Title",
      "description": "...",
      "status": "discovered",
      "reason": "continue_learning",
      "score": 1.0,
      "motif_id": "uuid"
    }
  ],
  "discover_new": [...],
  "review_needed": [...],
  "popular": [...]
}
```

## Test 2: Get Specific Recommendation Type

Get only "discover new" recommendations.

```bash
curl -X GET "http://localhost:8000/api/v1/recommendations?recommendation_type=discover_new&limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**All Types:**
- `continue_learning`
- `discover_new`
- `review_needed`
- `popular`

## Test 3: Get Similar Content

Get content similar to a specific motif.

```bash
# First, get a motif ID
MOTIF_ID=$(curl -X GET "http://localhost:8000/api/v1/urns" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].motifs[0].id')

echo "Testing with motif: $MOTIF_ID"

# Get similar content
curl -X GET "http://localhost:8000/api/v1/recommendations/similar/motif/$MOTIF_ID?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected Response:**
```json
{
  "similar_content": [
    {
      "content_type": "motif",
      "content_id": "uuid",
      "title": "Similar Motif",
      "description": "...",
      "similarity_score": 0.8,
      "reason": "similar_tags"
    }
  ],
  "total": 5
}
```

## Test 4: Record View Interaction

Track that a user viewed a piece of content.

```bash
# Get a motif to interact with
MOTIF_ID=$(curl -X GET "http://localhost:8000/api/v1/urns" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].motifs[0].id')

# Record view interaction
curl -X POST "http://localhost:8000/api/v1/recommendations/interaction" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "motif",
    "content_id": "'"$MOTIF_ID"'",
    "interaction_type": "view",
    "duration_seconds": 45,
    "metadata": {
      "source": "recommendation",
      "device": "web"
    }
  }' | jq
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Interaction recorded successfully",
  "interaction_id": "uuid"
}
```

## Test 5: Record Complete Interaction

Track that a user completed a lesson.

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/interaction" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "lesson",
    "content_id": "'"$MOTIF_ID"'",
    "interaction_type": "complete",
    "duration_seconds": 300,
    "metadata": {
      "completion_percentage": 100
    }
  }' | jq
```

## Test 6: Record Like Interaction

Track that a user liked/favorited content.

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/interaction" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "motif",
    "content_id": "'"$MOTIF_ID"'",
    "interaction_type": "like"
  }' | jq
```

## Test 7: Record Save Interaction

Track that a user saved/bookmarked content.

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/interaction" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "motif",
    "content_id": "'"$MOTIF_ID"'",
    "interaction_type": "save",
    "metadata": {
      "collection": "favorites"
    }
  }' | jq
```

## Test 8: Submit Helpful Feedback

Mark a recommendation as helpful.

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/feedback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "'"$MOTIF_ID"'",
    "content_type": "motif",
    "feedback_type": "helpful",
    "metadata": {
      "recommendation_type": "discover_new"
    }
  }' | jq
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Feedback recorded successfully"
}
```

## Test 9: Submit Not Helpful Feedback

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/feedback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "'"$MOTIF_ID"'",
    "content_type": "motif",
    "feedback_type": "not_helpful"
  }' | jq
```

## Test 10: Verify Recommendations Improve

After recording several interactions, verify that recommendations improve.

```bash
# Step 1: Record multiple interactions
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/v1/recommendations/interaction" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "content_type": "motif",
      "content_id": "'"$MOTIF_ID"'",
      "interaction_type": "view"
    }' -s > /dev/null
  echo "Recorded interaction $i"
done

# Step 2: Get updated recommendations
echo "\nGetting updated recommendations..."
curl -X GET "http://localhost:8000/api/v1/recommendations" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Error Testing

### Test Invalid Content Type
```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/interaction" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "invalid_type",
    "content_id": "'"$MOTIF_ID"'",
    "interaction_type": "view"
  }'
```

**Expected:** 422 Validation Error

### Test Invalid Interaction Type
```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/interaction" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "motif",
    "content_id": "'"$MOTIF_ID"'",
    "interaction_type": "invalid"
  }'
```

**Expected:** 422 Validation Error

### Test Missing Authentication
```bash
curl -X GET "http://localhost:8000/api/v1/recommendations"
```

**Expected:** 401 Unauthorized

## Complete Test Script

Save as `test_recommendations.sh`:

```bash
#!/bin/bash

# Configuration
BASE_URL="http://localhost:8000"
EMAIL="test@example.com"
PASSWORD="password123"

# Get token
echo "=== Getting authentication token ==="
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "Failed to get token. Please check credentials."
  exit 1
fi

echo "Token obtained: ${TOKEN:0:20}..."

# Get a motif ID
echo "\n=== Getting motif ID ==="
MOTIF_ID=$(curl -s -X GET "$BASE_URL/api/v1/urns" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].motifs[0].id')
echo "Using motif: $MOTIF_ID"

# Test 1: Get all recommendations
echo "\n=== Test 1: Get All Recommendations ==="
curl -s -X GET "$BASE_URL/api/v1/recommendations?limit=3" \
  -H "Authorization: Bearer $TOKEN" | jq '.discover_new | length'

# Test 2: Record view interaction
echo "\n=== Test 2: Record View Interaction ==="
curl -s -X POST "$BASE_URL/api/v1/recommendations/interaction" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"content_type\":\"motif\",\"content_id\":\"$MOTIF_ID\",\"interaction_type\":\"view\",\"duration_seconds\":60}" | jq '.success'

# Test 3: Get similar content
echo "\n=== Test 3: Get Similar Content ==="
curl -s -X GET "$BASE_URL/api/v1/recommendations/similar/motif/$MOTIF_ID?limit=3" \
  -H "Authorization: Bearer $TOKEN" | jq '.total'

# Test 4: Submit feedback
echo "\n=== Test 4: Submit Feedback ==="
curl -s -X POST "$BASE_URL/api/v1/recommendations/feedback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"content_id\":\"$MOTIF_ID\",\"content_type\":\"motif\",\"feedback_type\":\"helpful\"}" | jq '.success'

echo "\n=== All tests completed ===\"
```

Run with:
```bash
chmod +x test_recommendations.sh
./test_recommendations.sh
```

## Monitoring Interactions

Query the database to see recorded interactions:

```sql
-- View recent interactions
SELECT 
  u.email,
  uci.content_type,
  uci.interaction_type,
  uci.duration_seconds,
  uci.created_at
FROM user_content_interactions uci
JOIN users u ON u.id = uci.user_id
ORDER BY uci.created_at DESC
LIMIT 10;

-- Count interactions by type
SELECT 
  interaction_type,
  COUNT(*) as count
FROM user_content_interactions
GROUP BY interaction_type;

-- Most viewed content
SELECT 
  content_type,
  content_id,
  COUNT(*) as view_count
FROM user_content_interactions
WHERE interaction_type = 'view'
GROUP BY content_type, content_id
ORDER BY view_count DESC
LIMIT 10;
```

## Success Criteria

✅ All endpoints return 200 OK
✅ Recommendations returned in all 4 categories
✅ Similar content found for motifs with tags
✅ Interactions recorded successfully
✅ Feedback submitted successfully
✅ No authentication errors with valid token
✅ Proper validation errors for invalid input

