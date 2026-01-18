# P0-SEC-01: Age-Appropriate Content Flags - API Reference

## Overview

This implementation adds age-based content rating and filtering to protect younger users and comply with content safety requirements.

## Content Rating System

### Rating Levels

| Rating | Label | Description | Min Age |
|--------|-------|-------------|---------|
| `everyone` | Everyone | Suitable for all ages | None |
| `teen` | Teen | Suitable for ages 13+ | 13 |
| `mature` | Mature | Suitable for ages 18+ | 18 |

### Access Rules

1. **Not Age Verified or Under 13**: Only `everyone` content
2. **Age 13-17**: `everyone` and `teen` content
3. **Age 18+**: All content (`everyone`, `teen`, `mature`)

## API Endpoints

### 1. Verify User Age

Allows users to verify their age by submitting their birth year.

**Endpoint**: `POST /api/v1/users/me/age-verify`

**Authentication**: Required (JWT token)

**Request Body**:
```json
{
  "birth_year": 1990
}
```

**Response** (200 OK):
```json
{
  "age_verified": true,
  "age_verified_at": "2025-01-08T12:00:00Z",
  "birth_year": 1990,
  "current_age": 35,
  "allowed_ratings": ["everyone", "teen", "mature"]
}
```

**Error Responses**:
- `400 Bad Request`: Invalid birth year
- `401 Unauthorized`: Not authenticated

**Example**:
```bash
curl -X POST https://api.example.com/api/v1/users/me/age-verify \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"birth_year": 1990}'
```

---

### 2. Get Content Ratings

Returns information about all available content ratings and their age requirements.

**Endpoint**: `GET /api/v1/content/ratings`

**Authentication**: Not required

**Response** (200 OK):
```json
{
  "ratings": [
    {
      "rating": "everyone",
      "label": "Everyone",
      "description": "Suitable for all ages",
      "min_age": null
    },
    {
      "rating": "teen",
      "label": "Teen",
      "description": "Suitable for ages 13 and up",
      "min_age": 13
    },
    {
      "rating": "mature",
      "label": "Mature",
      "description": "Suitable for ages 18 and up",
      "min_age": 18
    }
  ]
}
```

**Example**:
```bash
curl https://api.example.com/api/v1/content/ratings
```

---

## Modified Endpoints

The following endpoints now filter content based on user age verification:

### 1. Get Motifs by Urn

**Endpoint**: `GET /motifs/{urn_name}`

**Changes**: Only returns motifs with content ratings the user can access.

**Example**: User with age 15 will only see motifs rated `everyone` or `teen`.

---

### 2. Get Motif Detail

**Endpoint**: `GET /api/v1/motifs/{motif_id}`

**Changes**: Returns `403 Forbidden` if user doesn't have access to the motif's content rating.

**Error Response** (403):
```json
{
  "detail": "You do not have access to this content. Please verify your age."
}
```

---

### 3. List Quests

**Endpoint**: `GET /api/v1/quests`

**Changes**: Only returns quests with content ratings the user can access.

---

### 4. Get Quest Detail

**Endpoint**: `GET /api/v1/quests/{quest_slug}`

**Changes**: Returns `403 Forbidden` if user doesn't have access to the quest's content rating.

**Error Response** (403):
```json
{
  "detail": "You do not have access to this content. Please verify your age."
}
```

---

## Database Schema Changes

### Users Table

New fields added:

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `birth_year` | INTEGER | Yes | NULL | User's birth year |
| `age_verified` | BOOLEAN | No | false | Whether age has been verified |
| `age_verified_at` | TIMESTAMP | Yes | NULL | When age was verified |

### Motifs Table

New field added:

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `content_rating` | ENUM | No | 'everyone' | Content rating for motif |

### Lesson Content Table

New field added:

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `content_rating` | ENUM | No | 'everyone' | Content rating for lesson |

### Quests Table

New field added:

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `content_rating` | ENUM | No | 'everyone' | Content rating for quest |

---

## Content Rating Enum

PostgreSQL ENUM type with values:
- `everyone`
- `teen`
- `mature`

---

## Migration

**File**: `migrations/versions/0020_content_rating_age_verification.py`

**To apply**:
```bash
cd backend
alembic upgrade head
```

**To rollback**:
```bash
alembic downgrade -1
```

---

## Security Considerations

1. **Age Verification is Optional**: Users can use the platform without age verification but will only see `everyone` content.

2. **Birth Year Privacy**: Birth year is stored but full birth date is not required for privacy.

3. **No Age Bypass**: Content filtering is enforced server-side and cannot be bypassed client-side.

4. **Staff Override**: Staff members (teachers/admins) can see all content regardless of rating for content management purposes (to be implemented if needed).

---

## Next Steps

1. Add content rating field to admin content creation/editing interfaces
2. Add age verification prompt in mobile/web app onboarding
3. Add content rating badges/indicators in UI
4. Consider adding parental controls for underage accounts

