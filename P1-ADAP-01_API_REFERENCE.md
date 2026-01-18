# P1-ADAP-01: Spaced Repetition API Reference

## Overview

REST API endpoints for the spaced repetition review system.

Base URL: `http://localhost:8000/api/v1`

All endpoints require authentication via Bearer token unless specified otherwise.

## Endpoints

### 1. Get Due Cards

Get cards that are due for review based on the spaced repetition schedule.

**Endpoint:** `GET /review/due`

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | integer | No | 20 | Maximum number of cards to return (1-100) |

**Response:** `200 OK`

```json
{
  "cards": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "motif_id": "550e8400-e29b-41d4-a716-446655440002",
      "ease_factor": 2.5,
      "interval_days": 1,
      "repetitions": 0,
      "next_review_at": "2025-01-17T10:00:00Z",
      "last_reviewed_at": null,
      "review_history": [],
      "created_at": "2025-01-17T09:00:00Z",
      "updated_at": "2025-01-17T09:00:00Z",
      "motif": {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "Rồng",
        "name_han": "龍",
        "thumbnail_url": "https://example.com/thumbnails/dragon.jpg",
        "category": "linh_thu"
      }
    }
  ],
  "total_due": 1
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/review/due?limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 2. Submit Review Result

Submit a review result for a specific card.

**Endpoint:** `POST /review/{card_id}`

**Authentication:** Required

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| card_id | UUID | Yes | ID of the card to review |

**Request Body:**

```json
{
  "quality": 4
}
```

**Body Parameters:**
| Field | Type | Required | Range | Description |
|-------|------|----------|-------|-------------|
| quality | integer | Yes | 0-5 | Quality rating of recall |

**Quality Scale:**
- 0: Complete blackout (no recall)
- 1: Incorrect response; correct one recalled
- 2: Incorrect response; correct one seemed easy to recall
- 3: Correct response recalled with serious difficulty
- 4: Correct response after hesitation
- 5: Perfect response

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "motif_id": "550e8400-e29b-41d4-a716-446655440002",
  "ease_factor": 2.6,
  "interval_days": 1,
  "repetitions": 1,
  "next_review_at": "2025-01-18T10:00:00Z",
  "last_reviewed_at": "2025-01-17T10:00:00Z",
  "review_history": [
    {
      "quality": 4,
      "reviewed_at": "2025-01-17T10:00:00Z",
      "ease_factor": 2.6,
      "interval_days": 1,
      "repetitions": 1
    }
  ],
  "created_at": "2025-01-17T09:00:00Z",
  "updated_at": "2025-01-17T10:00:00Z",
  "motif": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "Rồng",
    "name_han": "龍",
    "thumbnail_url": "https://example.com/thumbnails/dragon.jpg",
    "category": "linh_thu"
      }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid quality value (must be 0-5)
- `403 Forbidden`: Card does not belong to the authenticated user
- `404 Not Found`: Card not found

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/review/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quality": 4
  }'
```

---

### 3. Get Review Statistics

Get comprehensive statistics about the user's review deck.

**Endpoint:** `GET /review/stats`

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "total_cards": 50,
  "due_cards": 10,
  "reviewed_today": 5,
  "mastered_cards": 20,
  "learning_cards": 30,
  "total_reviews": 250
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| total_cards | integer | Total number of cards in review deck |
| due_cards | integer | Number of cards due for review right now |
| reviewed_today | integer | Number of cards reviewed today |
| mastered_cards | integer | Cards with 3+ successful reviews and ease ≥ 2.5 |
| learning_cards | integer | Cards with less than 3 successful reviews |
| total_reviews | integer | Total number of reviews across all cards |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/review/stats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 4. Add Card to Review Deck

Add a motif to the user's review deck.

**Endpoint:** `POST /review/cards`

**Authentication:** Required

**Request Body:**

```json
{
  "motif_id": "550e8400-e29b-41d4-a716-446655440002"
}
```

**Body Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| motif_id | UUID | Yes | ID of the motif to add to review deck |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "motif_id": "550e8400-e29b-41d4-a716-446655440002",
  "ease_factor": 2.5,
  "interval_days": 0,
  "repetitions": 0,
  "next_review_at": "2025-01-17T10:00:00Z",
  "last_reviewed_at": null,
  "review_history": [],
  "created_at": "2025-01-17T10:00:00Z",
  "updated_at": "2025-01-17T10:00:00Z",
  "motif": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "Rồng",
    "name_han": "龍",
    "thumbnail_url": "https://example.com/thumbnails/dragon.jpg",
    "category": "linh_thu"
  }
}
```

**Behavior:**
- If card already exists for this user and motif, returns the existing card
- If card is new, creates with default SM-2 parameters (ease=2.5, interval=0, repetitions=0)
- New cards are immediately available for review (next_review_at = now)

**Error Responses:**

- `400 Bad Request`: Motif not found

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/review/cards" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "motif_id": "550e8400-e29b-41d4-a716-446655440002"
  }'
```

---

## Data Models

### SpacedRepetitionCard

```typescript
interface SpacedRepetitionCard {
  id: string;                    // UUID
  user_id: string;               // UUID
  motif_id: string;              // UUID
  ease_factor: number;           // Float, minimum 1.3, default 2.5
  interval_days: number;         // Integer, days until next review
  repetitions: number;           // Integer, count of successful reviews
  next_review_at: string;        // ISO 8601 datetime
  last_reviewed_at: string | null; // ISO 8601 datetime
  review_history: ReviewHistoryEntry[];
  created_at: string;            // ISO 8601 datetime
  updated_at: string;            // ISO 8601 datetime
  motif?: MotifSummary;          // Optional motif details
}
```

### ReviewHistoryEntry

```typescript
interface ReviewHistoryEntry {
  quality: number;               // 0-5
  reviewed_at: string;           // ISO 8601 datetime
  ease_factor: number;           // Ease factor after this review
  interval_days: number;         // Interval calculated for next review
  repetitions: number;           // Repetition count after this review
}
```

### MotifSummary

```typescript
interface MotifSummary {
  id: string;                    // UUID
  name: string;
  name_han: string | null;
  thumbnail_url: string | null;
  category: string;              // "linh_thu" | "dong_vat" | "thao_moc" | etc.
}
```

---

## Common Use Cases

### 1. Daily Review Session

```javascript
// 1. Get due cards
const dueResponse = await fetch('/api/v1/review/due?limit=20', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { cards } = await dueResponse.json();

// 2. For each card, show motif and get user's quality rating
for (const card of cards) {
  const quality = await showMotifAndGetRating(card.motif);

  // 3. Submit review
  await fetch(`/api/v1/review/${card.id}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ quality })
  });
}

// 4. Get updated stats
const statsResponse = await fetch('/api/v1/review/stats', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const stats = await statsResponse.json();
console.log(`Reviewed: ${stats.reviewed_today}, Remaining: ${stats.due_cards}`);
```

### 2. Add Motif After Lesson Completion

```javascript
// When user completes a lesson, add motif to review deck
async function onLessonComplete(motifId) {
  const response = await fetch('/api/v1/review/cards', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ motif_id: motifId })
  });

  const card = await response.json();
  console.log('Added to review deck:', card.motif.name);
}
```

### 3. Dashboard Widget

```javascript
// Display review stats on user dashboard
async function loadReviewWidget() {
  const response = await fetch('/api/v1/review/stats', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const stats = await response.json();

  return {
    dueCount: stats.due_cards,
    reviewedToday: stats.reviewed_today,
    masteryProgress: Math.round(
      (stats.mastered_cards / stats.total_cards) * 100
    )
  };
}
```

---

## SM-2 Algorithm Explanation

The system uses the SuperMemo-2 (SM-2) algorithm for optimal spacing:

### Quality Ratings

| Quality | Result | Effect |
|---------|--------|--------|
| 0-2 | Failed | Reset to day 1, ease factor decreased |
| 3-5 | Passed | Interval increases, ease factor adjusted |

### Review Schedule

1. **New Card:** Review immediately (interval = 0)
2. **After First Success:** Review in 1 day
3. **After Second Success:** Review in 6 days
4. **After Third+ Success:** Review in (previous interval × ease factor) days

### Ease Factor

- Starts at 2.5
- Adjusted based on quality: `EF' = EF + (0.1 - (5-q) × (0.08 + (5-q) × 0.02))`
- Minimum value: 1.3
- Higher ease = longer intervals = easier recall

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid input (e.g., quality out of range, invalid UUID)
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: User not authorized to access resource
- `404 Not Found`: Resource not found (card, motif)
- `500 Internal Server Error`: Server error

Error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

