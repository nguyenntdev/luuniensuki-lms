# P0-SEC-01: Content Rating - Quick Reference

## TL;DR

Age-based content filtering with 3 rating levels:
- **Everyone**: All ages (default)
- **Teen**: 13+ years
- **Mature**: 18+ years

## Quick Commands

### Run Migration
```bash
cd backend
alembic upgrade head
```

### Test Age Verification
```bash
curl -X POST http://localhost:8000/api/v1/users/me/age-verify \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"birth_year": 1990}'
```

### Get Content Ratings
```bash
curl http://localhost:8000/api/v1/content/ratings
```

---

## Content Rating Rules

| User Age | Allowed Ratings | Access Level |
|----------|----------------|--------------|
| Not verified | everyone | Basic |
| Under 13 | everyone | Basic |
| 13-17 | everyone, teen | Standard |
| 18+ | everyone, teen, mature | Full |

---

## Modified Models

### User
- `birth_year: int` (nullable)
- `age_verified: bool` (default: false)
- `age_verified_at: datetime` (nullable)

### Motif, LessonContent, Quest
- `content_rating: ContentRating` (default: 'everyone')

---

## New Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/users/me/age-verify` | Required | Verify user age |
| GET | `/api/v1/content/ratings` | None | Get rating info |

---

## Updated Endpoints (Now Filtered)

- `GET /motifs/{urn_name}`
- `GET /api/v1/motifs/{motif_id}`
- `GET /api/v1/quests`
- `GET /api/v1/quests/{quest_slug}`

---

## Helper Functions

```python
# Get user's current age
age = get_user_age(user)

# Get allowed content ratings
allowed_ratings = get_allowed_content_ratings(user)

# Filter content
.where(content_rating.in_(allowed_ratings))
```

---

## Common Tasks

### Set Content Rating (SQL)
```sql
UPDATE motifs SET content_rating = 'teen' WHERE id = '...';
UPDATE quests SET content_rating = 'mature' WHERE id = '...';
```

### Check User Age Status (SQL)
```sql
SELECT email, birth_year, age_verified, age_verified_at 
FROM users 
WHERE id = '...';
```

### Debug Access Issues
```python
user = db.get(User, user_id)
print(f"Verified: {user.age_verified}")
print(f"Age: {get_user_age(user)}")
print(f"Allowed: {get_allowed_content_ratings(user)}")
```

---

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Invalid birth year | Check year is 1900-current |
| 403 | Access denied | User doesn't have required rating |

---

## Files Changed

- `backend/models.py` - Added ContentRating enum, updated models
- `backend/schemas.py` - Added verification schemas
- `backend/main.py` - Added endpoints and filtering
- `migrations/versions/0020_content_rating_age_verification.py` - Migration

---

## Rollback

```bash
alembic downgrade -1
```

---

## Documentation

- API Reference: `P0-SEC-01_API_REFERENCE.md`
- Full Guide: `P0-SEC-01_IMPLEMENTATION_SUMMARY.md`
- Testing: `P0-SEC-01_TESTING_GUIDE.md`

