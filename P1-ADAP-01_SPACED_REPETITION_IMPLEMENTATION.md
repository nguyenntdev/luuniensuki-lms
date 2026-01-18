# P1-ADAP-01: Spaced Repetition Scheduler Implementation

## Overview

This document describes the implementation of a spaced repetition scheduler for motif review using the SuperMemo-2 (SM-2) algorithm.

## Implementation Summary

### 1. Database Model

**Table:** `spaced_repetition_cards`

Created a new `SpacedRepetitionCard` model in `backend/models.py` with the following fields:

- `id`: UUID primary key
- `user_id`: Foreign key to users
- `motif_id`: Foreign key to motifs
- `ease_factor`: Float (default 2.5, SM-2 algorithm parameter)
- `interval_days`: Integer (current interval in days)
- `repetitions`: Integer (successful reviews count)
- `next_review_at`: DateTime (when the card is due for review)
- `last_reviewed_at`: DateTime (nullable, last review timestamp)
- `review_history`: JSONB (list of past reviews with quality, date, interval, ease_factor)
- `created_at`: DateTime
- `updated_at`: DateTime

**Indexes:**
- `idx_sr_cards_user` on `user_id`
- `idx_sr_cards_motif` on `motif_id`
- `idx_sr_cards_next_review` on `next_review_at`
- `idx_sr_cards_user_next_review` on `(user_id, next_review_at)` (composite index for efficient queries)

**Constraints:**
- Unique constraint on `(user_id, motif_id)` to prevent duplicate cards

### 2. Service Layer

**File:** `backend/services/spaced_repetition.py`

Implemented the following functions:

#### `calculate_sm2_parameters(quality, current_ease, current_interval, current_repetitions)`
Implements the SM-2 algorithm to calculate next review parameters.

**Quality Scale (0-5):**
- 0: Complete blackout
- 1: Incorrect response; correct one recalled
- 2: Incorrect response; correct one seemed easy to recall
- 3: Correct response recalled with serious difficulty
- 4: Correct response after hesitation
- 5: Perfect response

**Algorithm Logic:**
- Quality >= 3 is considered successful
- Ease factor adjusts based on quality (minimum 1.3)
- Failed reviews (quality < 3) reset to day 1
- Successful reviews follow: 1 day → 6 days → interval * ease_factor

#### `get_due_cards(db, user_id, limit, now)`
Returns cards due for review ordered by `next_review_at`.

#### `process_review(db, card_id, quality, now)`
Processes a review submission:
- Calculates new SM-2 parameters
- Updates card fields
- Adds entry to review history
- Schedules next review

#### `add_card_to_deck(db, user_id, motif_id, now)`
Adds a motif to the user's review deck:
- Creates new card or returns existing
- Initializes with default SM-2 parameters
- Sets next review to immediate

#### `get_user_review_stats(db, user_id, now)`
Returns comprehensive review statistics:
- Total cards in deck
- Cards due for review
- Cards reviewed today
- Mastered cards (repetitions >= 3, ease >= 2.5)
- Learning cards (repetitions < 3)
- Total reviews count

### 3. API Schemas

**File:** `backend/schemas.py`

Added the following schemas:

- `ReviewHistoryEntry`: Single review history entry
- `SpacedRepetitionCardOut`: Card output with motif details
- `ReviewSubmitIn`: Input for submitting review (quality 0-5)
- `ReviewStatsOut`: User review statistics
- `AddCardIn`: Input for adding card (motif_id)
- `DueCardsOut`: List of due cards

### 4. API Endpoints

**File:** `backend/main.py`

#### `GET /api/v1/review/due`
Get cards due for review.

**Query Parameters:**
- `limit`: Max cards to return (default 20, max 100)

**Response:** `DueCardsOut`
```json
{
  "cards": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "motif_id": "uuid",
      "ease_factor": 2.5,
      "interval_days": 1,
      "repetitions": 0,
      "next_review_at": "2025-01-17T00:00:00Z",
      "last_reviewed_at": null,
      "review_history": [],
      "created_at": "2025-01-17T00:00:00Z",
      "updated_at": "2025-01-17T00:00:00Z",
      "motif": {
        "id": "uuid",
        "name": "Motif Name",
        "name_han": "漢字",
        "thumbnail_url": "https://...",
        "category": "linh_thu"
      }
    }
  ],
  "total_due": 1
}
```

#### `POST /api/v1/review/{card_id}`
Submit review result for a card.

**Path Parameters:**
- `card_id`: UUID of the card to review

**Request Body:**
```json
{
  "quality": 4
}
```

**Response:** `SpacedRepetitionCardOut` (updated card)

#### `GET /api/v1/review/stats`
Get user's review statistics.

**Response:** `ReviewStatsOut`
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

#### `POST /api/v1/review/cards`
Add a motif to the review deck.

**Request Body:**
```json
{
  "motif_id": "uuid"
}
```

**Response:** `SpacedRepetitionCardOut` (created or existing card)

### 5. Database Migration

**File:** `migrations/versions/0024_spaced_repetition.py`

- Creates `spaced_repetition_cards` table
- Creates all necessary indexes
- Includes upgrade and downgrade functions

### 6. Model Import

Updated `backend/main.py` to import `SpacedRepetitionCard` from models.

## SM-2 Algorithm Details

The SuperMemo-2 algorithm is a well-established spaced repetition algorithm:

1. **Initial State:**
   - Ease Factor (EF) = 2.5
   - Interval = 0 days
   - Repetitions = 0

2. **After Each Review:**
   - Calculate new EF: `EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))`
   - Minimum EF = 1.3

3. **Interval Calculation:**
   - If quality < 3 (failed): Reset to interval = 1, repetitions = 0
   - If quality >= 3 (passed):
     - First repetition: interval = 1 day
     - Second repetition: interval = 6 days
     - Third+ repetition: interval = previous_interval * EF

4. **Next Review:**
   - next_review_at = current_time + interval (in days)

## Files Modified/Created

### Created:
1. `backend/services/spaced_repetition.py` - Service layer implementation
2. `migrations/versions/0024_spaced_repetition.py` - Database migration

### Modified:
1. `backend/models.py` - Added `SpacedRepetitionCard` model
2. `backend/schemas.py` - Added review-related schemas
3. `backend/main.py` - Added API endpoints and imports

## Next Steps

### 1. Run the Migration
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
alembic upgrade head
```

### 2. Test the API

Test getting due cards:
```bash
curl -X GET "http://localhost:8000/api/v1/review/due?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Test adding a card:
```bash
curl -X POST "http://localhost:8000/api/v1/review/cards" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"motif_id": "MOTIF_UUID"}'
```

Test submitting a review:
```bash
curl -X POST "http://localhost:8000/api/v1/review/CARD_UUID" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quality": 4}'
```

Test getting statistics:
```bash
curl -X GET "http://localhost:8000/api/v1/review/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Integration Points

The spaced repetition system can be integrated with:

1. **Lesson Completion:**
   - Auto-add motifs to review deck when lessons are completed
   - Trigger: After user completes a motif lesson

2. **Quiz Results:**
   - Use quiz performance as quality rating
   - Trigger: After quiz completion

3. **User Dashboard:**
   - Show due cards count
   - Display review statistics
   - Prompt users to review

4. **Notifications:**
   - Daily reminder for due reviews
   - Milestone achievements (100 reviews, etc.)

5. **Progress Tracking:**
   - Include review stats in user progress
   - Track mastery level based on ease factor and repetitions

## Quality Rating Guidelines

Provide these to users when reviewing:

| Rating | Label | Description |
|--------|-------|-------------|
| 0 | Complete Blackout | No recollection at all |
| 1 | Incorrect | Incorrect answer, but correct answer was familiar |
| 2 | Incorrect (Easy) | Incorrect answer, but correct answer seemed easy |
| 3 | Correct (Hard) | Correct answer with serious difficulty |
| 4 | Correct (Good) | Correct answer with slight hesitation |
| 5 | Perfect | Perfect recall, no hesitation |

## Performance Considerations

1. **Indexes:** Composite index on `(user_id, next_review_at)` ensures fast queries for due cards
2. **JSONB:** Review history stored as JSONB for flexibility and PostgreSQL's efficient JSONB handling
3. **Batch Processing:** Consider implementing batch review sessions for mobile offline mode
4. **Caching:** Review statistics could be cached with invalidation on review submission

## Future Enhancements

1. **Review Sessions:**
   - Group reviews into sessions
   - Track session completion time
   - Calculate average quality per session

2. **Adaptive Scheduling:**
   - Adjust intervals based on motif difficulty
   - Consider user's historical performance
   - Time-of-day optimization

3. **Review Modes:**
   - Practice mode (doesn't affect schedule)
   - Cram mode (accelerated reviews)
   - Mastery challenge (only mature cards)

4. **Analytics:**
   - Review heatmap
   - Retention curves
   - Difficulty distribution

5. **Gamification:**
   - Review streaks
   - XP rewards for reviews
   - Badges for milestones

