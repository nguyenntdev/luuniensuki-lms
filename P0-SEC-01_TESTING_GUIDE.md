# P0-SEC-01: Age-Appropriate Content Flags - Testing Guide

## Quick Test Script

Save as `test_content_rating.sh` and run with `bash test_content_rating.sh`

```bash
#!/bin/bash

# Configuration
API_BASE="http://localhost:8000"
TOKEN=""  # Add your test user token here

echo "========================================="
echo "P0-SEC-01: Content Rating Testing"
echo "========================================="
echo ""

# Test 1: Get Content Ratings (Public Endpoint)
echo "Test 1: Get Content Ratings"
echo "GET /api/v1/content/ratings"
curl -s "${API_BASE}/api/v1/content/ratings" | jq
echo ""
echo "Expected: List of 3 content ratings (everyone, teen, mature)"
echo ""
read -p "Press Enter to continue..."
echo ""

# Test 2: Verify Age as Adult (18+)
echo "Test 2: Verify Age - Adult (Born 1990)"
echo "POST /api/v1/users/me/age-verify"
curl -s -X POST "${API_BASE}/api/v1/users/me/age-verify" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"birth_year": 1990}' | jq
echo ""
echo "Expected: age_verified=true, current_age=35, allowed_ratings=[everyone,teen,mature]"
echo ""
read -p "Press Enter to continue..."
echo ""

# Test 3: Verify Age as Teen (13-17)
echo "Test 3: Verify Age - Teen (Born 2008)"
echo "POST /api/v1/users/me/age-verify"
curl -s -X POST "${API_BASE}/api/v1/users/me/age-verify" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"birth_year": 2008}' | jq
echo ""
echo "Expected: age_verified=true, current_age=17, allowed_ratings=[everyone,teen]"
echo ""
read -p "Press Enter to continue..."
echo ""

# Test 4: Verify Age as Child (<13)
echo "Test 4: Verify Age - Child (Born 2015)"
echo "POST /api/v1/users/me/age-verify"
curl -s -X POST "${API_BASE}/api/v1/users/me/age-verify" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"birth_year": 2015}' | jq
echo ""
echo "Expected: age_verified=true, current_age=10, allowed_ratings=[everyone]"
echo ""
read -p "Press Enter to continue..."
echo ""

# Test 5: Invalid Birth Year (Future)
echo "Test 5: Invalid Birth Year - Future Year"
echo "POST /api/v1/users/me/age-verify"
curl -s -X POST "${API_BASE}/api/v1/users/me/age-verify" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"birth_year": 2030}' | jq
echo ""
echo "Expected: 400 Bad Request - Birth year validation error"
echo ""
read -p "Press Enter to continue..."
echo ""

# Test 6: Invalid Birth Year (Too Old)
echo "Test 6: Invalid Birth Year - Before 1900"
echo "POST /api/v1/users/me/age-verify"
curl -s -X POST "${API_BASE}/api/v1/users/me/age-verify" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"birth_year": 1899}' | jq
echo ""
echo "Expected: 400 Bad Request - Birth year validation error"
echo ""
read -p "Press Enter to continue..."
echo ""

# Test 7: Get Motifs (Should be filtered)
echo "Test 7: Get Motifs by URN (Content Filtered)"
echo "GET /motifs/cao-dinh"
curl -s "${API_BASE}/motifs/cao-dinh" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.motifs | length'
echo ""
echo "Expected: Only motifs with appropriate content rating"
echo ""
read -p "Press Enter to continue..."
echo ""

# Test 8: Get Quests (Should be filtered)
echo "Test 8: Get Quests List (Content Filtered)"
echo "GET /api/v1/quests"
curl -s "${API_BASE}/api/v1/quests" \
  -H "Authorization: Bearer ${TOKEN}" | jq 'length'
echo ""
echo "Expected: Only quests with appropriate content rating"
echo ""
read -p "Press Enter to continue..."
echo ""

echo "========================================="
echo "Testing Complete!"
echo "========================================="
```

---

## Manual Testing Scenarios

### Scenario 1: New User (No Age Verification)

1. Create a new test user
2. Try to access motifs: `GET /motifs/cao-dinh`
3. **Expected**: Only see motifs with `content_rating = 'everyone'`
4. Try to access a teen-rated motif directly
5. **Expected**: 403 Forbidden error

### Scenario 2: Adult User (18+)

1. Verify age with birth year 1990: `POST /api/v1/users/me/age-verify {"birth_year": 1990}`
2. **Expected**: `allowed_ratings: ["everyone", "teen", "mature"]`
3. Try to access any motif
4. **Expected**: Can access all motifs regardless of rating
5. Try to access any quest
6. **Expected**: Can access all quests regardless of rating

### Scenario 3: Teen User (13-17)

1. Verify age with birth year 2008: `POST /api/v1/users/me/age-verify {"birth_year": 2008}`
2. **Expected**: `allowed_ratings: ["everyone", "teen"]`
3. Access motifs list
4. **Expected**: See `everyone` and `teen` rated motifs, but not `mature`
5. Try to access a mature-rated motif directly
6. **Expected**: 403 Forbidden error

### Scenario 4: Child User (<13)

1. Verify age with birth year 2015: `POST /api/v1/users/me/age-verify {"birth_year": 2015}`
2. **Expected**: `allowed_ratings: ["everyone"]`
3. Access any content list
4. **Expected**: Only see `everyone` rated content
5. Try to access teen or mature content
6. **Expected**: 403 Forbidden error

---

## Database Testing

### Check Migration Status

```sql
-- Connect to database
psql luuniensuki_lms

-- Check alembic version
SELECT * FROM alembic_version;
-- Should show: 0020

-- Verify new columns exist in users table
\d users
-- Should show: birth_year, age_verified, age_verified_at

-- Verify new columns exist in content tables
\d motifs
\d lesson_content
\d quests
-- Should all show: content_rating

-- Verify enum type exists
\dT content_rating
-- Should show: everyone, teen, mature

-- Check indexes
\di idx_motifs_content_rating
\di idx_lesson_content_rating
\di idx_quests_content_rating
\di idx_users_age_verified
```

### Test Data Setup

```sql
-- Create test motifs with different ratings
UPDATE motifs SET content_rating = 'everyone' WHERE id = '...';
UPDATE motifs SET content_rating = 'teen' WHERE id = '...';
UPDATE motifs SET content_rating = 'mature' WHERE id = '...';

-- Create test quests with different ratings
UPDATE quests SET content_rating = 'everyone' WHERE slug = 'explore-cao-dinh';
UPDATE quests SET content_rating = 'teen' WHERE slug = 'master-techniques';
UPDATE quests SET content_rating = 'mature' WHERE slug = 'advanced-analysis';

-- Check user age verification
SELECT id, email, birth_year, age_verified, age_verified_at
FROM users
WHERE email = 'test@example.com';
```

---

## Integration Testing

### Python Test Example

```python
import requests

API_BASE = "http://localhost:8000"
TOKEN = "your_test_token"

def test_age_verification():
    """Test age verification endpoint"""
    # Verify as adult
    response = requests.post(
        f"{API_BASE}/api/v1/users/me/age-verify",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"birth_year": 1990}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["age_verified"] == True
    assert data["current_age"] == 35
    assert "mature" in data["allowed_ratings"]

def test_content_ratings():
    """Test content ratings endpoint"""
    response = requests.get(f"{API_BASE}/api/v1/content/ratings")
    assert response.status_code == 200
    data = response.json()
    assert len(data["ratings"]) == 3
    ratings = [r["rating"] for r in data["ratings"]]
    assert "everyone" in ratings
    assert "teen" in ratings
    assert "mature" in ratings

def test_content_filtering():
    """Test content is filtered by age"""
    # First, verify as teen
    requests.post(
        f"{API_BASE}/api/v1/users/me/age-verify",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"birth_year": 2008}
    )

    # Get quests - should only see everyone and teen
    response = requests.get(
        f"{API_BASE}/api/v1/quests",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    assert response.status_code == 200
    quests = response.json()
    for quest in quests:
        # All quests should be everyone or teen rated
        # (requires quest to have content_rating in response)
        pass

if __name__ == "__main__":
    test_age_verification()
    test_content_ratings()
    test_content_filtering()
    print("All tests passed!")
```

---

## Performance Testing

### Load Test Script

```bash
# Test concurrent age verifications
ab -n 100 -c 10 \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -p age_verify.json \
  http://localhost:8000/api/v1/users/me/age-verify

# age_verify.json contains:
# {"birth_year": 1990}
```

### Query Performance

```sql
-- Test query performance with content rating filter
EXPLAIN ANALYZE
SELECT * FROM motifs
WHERE is_active = true
  AND content_rating IN ('everyone', 'teen')
  AND urn_id = '...';

-- Should use idx_motifs_content_rating index
```

---

## Checklist

### Pre-Deployment
- [ ] Run migration on development database
- [ ] Verify all new columns created
- [ ] Verify all indexes created
- [ ] Test age verification endpoint
- [ ] Test content ratings endpoint
- [ ] Test content filtering for all age groups

### Post-Deployment
- [ ] Monitor API error rates
- [ ] Check for 403 errors on content endpoints
- [ ] Verify age verification working in production
- [ ] Monitor database performance
- [ ] Check user feedback

### Data Validation
- [ ] All existing content has default rating ('everyone')
- [ ] No NULL values in new non-nullable columns
- [ ] Enum values are correct
- [ ] Indexes are being used

---

## Troubleshooting

### Issue: Migration Fails

**Error**: `type "content_rating" already exists`

**Solution**:
```sql
-- Drop existing enum if needed
DROP TYPE IF EXISTS content_rating CASCADE;
-- Then rerun migration
```

### Issue: 403 Errors on All Content

**Check**:
1. User's age_verified status
2. User's birth_year value
3. Content's content_rating value

```python
# Debug helper
def debug_user_access(user_id):
    user = db.get(User, user_id)
    print(f"Age verified: {user.age_verified}")
    print(f"Birth year: {user.birth_year}")

    age = get_user_age(user)
    print(f"Current age: {age}")

    allowed = get_allowed_content_ratings(user)
    print(f"Allowed ratings: {[r.value for r in allowed]}")
```

### Issue: Content Not Filtered

**Check**:
1. Endpoint is using `get_allowed_content_ratings()`
2. Query includes `.where(content_rating.in_(allowed_ratings))`
3. Enum values match exactly

---

## Success Criteria

✅ Age verification endpoint working
✅ Content ratings endpoint returning correct data
✅ Users under 13 only see 'everyone' content
✅ Teen users see 'everyone' and 'teen' content
✅ Adult users see all content
✅ 403 errors when accessing restricted content
✅ Database migration successful
✅ Indexes created and being used
✅ No performance degradation


