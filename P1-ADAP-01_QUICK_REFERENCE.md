# P1-ADAP-01: Spaced Repetition Quick Reference

## Quick Start

### 1. Run Migration
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
alembic upgrade head
```

### 2. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/review/due` | Get cards due for review |
| POST | `/api/v1/review/{card_id}` | Submit review result |
| GET | `/api/v1/review/stats` | Get review statistics |
| POST | `/api/v1/review/cards` | Add motif to review deck |

### 3. Quality Scale

| 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Blackout | Wrong | Wrong (Easy) | Hard | Good | Perfect |

## File Changes

### Created Files
- ✅ `backend/services/spaced_repetition.py` - Service implementation
- ✅ `migrations/versions/0024_spaced_repetition.py` - Database migration
- ✅ `P1-ADAP-01_SPACED_REPETITION_IMPLEMENTATION.md` - Full documentation
- ✅ `P1-ADAP-01_API_REFERENCE.md` - API documentation
- ✅ `P1-ADAP-01_QUICK_REFERENCE.md` - This file

### Modified Files
- ✅ `backend/models.py` - Added `SpacedRepetitionCard` model
- ✅ `backend/schemas.py` - Added review schemas
- ✅ `backend/main.py` - Added API endpoints

## Database Schema

```sql
CREATE TABLE spaced_repetition_cards (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    motif_id UUID NOT NULL REFERENCES motifs(id) ON DELETE CASCADE,
    ease_factor FLOAT NOT NULL DEFAULT 2.5,
    interval_days INTEGER NOT NULL DEFAULT 0,
    repetitions INTEGER NOT NULL DEFAULT 0,
    next_review_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_reviewed_at TIMESTAMP WITH TIME ZONE,
    review_history JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, motif_id)
);

CREATE INDEX idx_sr_cards_user ON spaced_repetition_cards(user_id);
CREATE INDEX idx_sr_cards_motif ON spaced_repetition_cards(motif_id);
CREATE INDEX idx_sr_cards_next_review ON spaced_repetition_cards(next_review_at);
CREATE INDEX idx_sr_cards_user_next_review ON spaced_repetition_cards(user_id, next_review_at);
```

## SM-2 Algorithm Flow

```
New Card
    ↓ (Review immediately)
Quality ≥ 3? → NO → Reset: 1 day, repetitions=0
    ↓ YES
Repetition 1 → 1 day
    ↓ (Quality ≥ 3)
Repetition 2 → 6 days
    ↓ (Quality ≥ 3)
Repetition 3+ → interval × ease_factor days
```

## API Examples

### Get Due Cards
```bash
curl http://localhost:8000/api/v1/review/due?limit=10 \
  -H "Authorization: Bearer TOKEN"
```

### Submit Review
```bash
curl -X POST http://localhost:8000/api/v1/review/CARD_ID \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quality": 4}'
```

### Get Stats
```bash
curl http://localhost:8000/api/v1/review/stats \
  -H "Authorization: Bearer TOKEN"
```

### Add Card
```bash
curl -X POST http://localhost:8000/api/v1/review/cards \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"motif_id": "MOTIF_UUID"}'
```

## Service Functions

```python
from backend.services.spaced_repetition import (
    get_due_cards,
    process_review,
    add_card_to_deck,
    get_user_review_stats,
    calculate_sm2_parameters,
)

# Get cards for user
cards = get_due_cards(db, user_id, limit=20)

# Process review
card = process_review(db, card_id, quality=4)

# Add motif to deck
card = add_card_to_deck(db, user_id, motif_id)

# Get statistics
stats = get_user_review_stats(db, user_id)
# Returns: {total_cards, due_cards, reviewed_today, mastered_cards, learning_cards, total_reviews}
```

## Integration Points

### 1. Auto-add after lesson completion
```python
# In lesson completion handler
from backend.services.spaced_repetition import add_card_to_deck

# After user completes lesson
card = add_card_to_deck(db, user.id, lesson.motif_id)
```

### 2. Dashboard widget
```python
# Show review stats on dashboard
from backend.services.spaced_repetition import get_user_review_stats

stats = get_user_review_stats(db, current_user.id)
# Display: {due_cards} cards due, {reviewed_today} reviewed today
```

### 3. Daily notification
```python
# Send notification if cards are due
from backend.services.spaced_repetition import get_due_cards

due = get_due_cards(db, user.id, limit=1)
if due:
    send_notification(user, f"{len(due)} cards ready for review")
```

## Testing Checklist

- [ ] Run migration successfully
- [ ] GET `/review/due` returns empty list for new user
- [ ] POST `/review/cards` adds card successfully
- [ ] GET `/review/due` now returns the added card
- [ ] POST `/review/{card_id}` with quality=5 updates card
- [ ] Card next_review_at is 1 day in future
- [ ] POST `/review/{card_id}` with quality=5 again
- [ ] Card next_review_at is 6 days in future
- [ ] POST `/review/{card_id}` with quality=2 (fail)
- [ ] Card resets to 1 day interval
- [ ] GET `/review/stats` returns accurate counts

## Key Metrics to Track

- **Total Cards**: Total in review deck
- **Due Cards**: Cards ready now
- **Reviewed Today**: Daily activity
- **Mastered Cards**: Repetitions ≥ 3, Ease ≥ 2.5
- **Learning Cards**: Repetitions < 3
- **Total Reviews**: All-time review count

## Common Issues

### Migration fails
- Check database connection
- Ensure previous migrations are applied
- Verify PostgreSQL is running

### Cards not appearing as due
- Check `next_review_at` is in the past
- Verify timezone handling
- Ensure composite index exists

### Review history not updating
- Check JSONB column type
- Verify serialization of datetime
- Ensure commit after update

## Performance Tips

1. **Composite Index**: `(user_id, next_review_at)` makes queries fast
2. **Limit Due Cards**: Don't fetch more than needed
3. **Batch Reviews**: Process multiple cards in one session
4. **Cache Stats**: Cache review statistics with TTL

## Next Steps

1. ✅ Implementation complete
2. 🔄 Run migration
3. 🔄 Test API endpoints
4. 🔄 Integrate with lesson completion
5. 🔄 Add to user dashboard
6. 🔄 Create mobile UI
7. 🔄 Add daily notifications
8. 🔄 Track analytics

## Support

For issues or questions:
- See: `P1-ADAP-01_SPACED_REPETITION_IMPLEMENTATION.md` for details
- See: `P1-ADAP-01_API_REFERENCE.md` for API docs
- Check: `backend/services/spaced_repetition.py` for implementation

