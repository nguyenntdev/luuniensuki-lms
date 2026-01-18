# P1-ADAP-01: Spaced Repetition Scheduler - Documentation Index

## Overview

Complete implementation of a spaced repetition scheduler for motif review using the SuperMemo-2 (SM-2) algorithm.

**Status:** ✅ Implementation Complete  
**Date:** January 17, 2025  
**Version:** 1.0.0

---

## Documentation Files

### 1. Implementation Guide
**File:** `P1-ADAP-01_SPACED_REPETITION_IMPLEMENTATION.md`

Complete technical implementation details including:
- Database model specifications
- Service layer architecture
- SM-2 algorithm implementation
- API endpoint specifications
- Integration recommendations
- Future enhancement ideas

**Use this for:** Understanding the full technical implementation and architecture decisions.

---

### 2. API Reference
**File:** `P1-ADAP-01_API_REFERENCE.md`

Complete REST API documentation including:
- Endpoint specifications
- Request/response formats
- Authentication requirements
- Error handling
- Data models
- Common use cases
- Code examples

**Use this for:** Integrating the spaced repetition API into frontend applications.

---

### 3. Quick Reference
**File:** `P1-ADAP-01_QUICK_REFERENCE.md`

One-page quick reference including:
- Quick start commands
- Endpoint summary table
- Database schema
- SM-2 algorithm flow diagram
- API examples
- Integration snippets
- Testing checklist

**Use this for:** Quick lookups during development.

---

### 4. Testing Script
**File:** `test_spaced_repetition.sh`

Automated testing script for all endpoints:
- Tests all CRUD operations
- Validates SM-2 algorithm behavior
- Checks error handling
- Verifies review history tracking
- Outputs detailed test results

**Use this for:** Validating the implementation works correctly.

---

## Implementation Files

### Backend Service
**File:** `backend/services/spaced_repetition.py`

Core service layer implementing:
- `calculate_sm2_parameters()` - SM-2 algorithm
- `get_due_cards()` - Fetch cards for review
- `process_review()` - Process review submissions
- `add_card_to_deck()` - Add motifs to review
- `get_user_review_stats()` - Retrieve statistics

---

### Database Model
**File:** `backend/models.py` (modified)

Added `SpacedRepetitionCard` model:
- UUID primary key
- Foreign keys to users and motifs
- SM-2 parameters (ease_factor, interval_days, repetitions)
- Review scheduling (next_review_at, last_reviewed_at)
- JSONB review_history
- Proper indexes for query performance

---

### API Schemas
**File:** `backend/schemas.py` (modified)

Added schemas:
- `SpacedRepetitionCardOut` - Card output
- `ReviewSubmitIn` - Review submission input
- `ReviewStatsOut` - Statistics output
- `AddCardIn` - Add card input
- `DueCardsOut` - Due cards list output
- `ReviewHistoryEntry` - History entry model

---

### API Endpoints
**File:** `backend/main.py` (modified)

Added 4 endpoints:
- `GET /api/v1/review/due` - Get due cards
- `POST /api/v1/review/{card_id}` - Submit review
- `GET /api/v1/review/stats` - Get statistics
- `POST /api/v1/review/cards` - Add card to deck

---

### Database Migration
**File:** `migrations/versions/0024_spaced_repetition.py`

Alembic migration:
- Creates `spaced_repetition_cards` table
- Creates indexes for performance
- Includes upgrade and downgrade functions

---

## Quick Start

### 1. Apply Database Migration
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
alembic upgrade head
```

### 2. Test the API
```bash
# Set your auth token
export AUTH_TOKEN="your_jwt_token_here"

# Run automated tests
./test_spaced_repetition.sh
```

### 3. Use the API

**Get due cards:**
```bash
curl "http://localhost:8000/api/v1/review/due?limit=10" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

**Add a card:**
```bash
curl -X POST "http://localhost:8000/api/v1/review/cards" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"motif_id": "YOUR_MOTIF_UUID"}'
```

**Submit review:**
```bash
curl -X POST "http://localhost:8000/api/v1/review/CARD_UUID" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quality": 4}'
```

**Get stats:**
```bash
curl "http://localhost:8000/api/v1/review/stats" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

---

## Key Features

### ✅ SM-2 Algorithm Implementation
- Quality-based review scheduling (0-5 scale)
- Adaptive ease factor (minimum 1.3)
- Progressive intervals: 1 day → 6 days → exponential

### ✅ Comprehensive API
- Get due cards with limit
- Submit reviews with quality ratings
- Track statistics (total, due, mastered, learning)
- Add/manage review cards

### ✅ Review History
- JSONB storage for complete history
- Tracks quality, ease factor, interval per review
- Enables analytics and progress tracking

### ✅ Performance Optimized
- Composite index on (user_id, next_review_at)
- Efficient JSONB queries
- Proper foreign key constraints

### ✅ Error Handling
- Input validation (quality 0-5)
- Authorization checks
- Clear error messages

---

## SM-2 Algorithm Summary

### Quality Scale
| Quality | Meaning | Effect |
|---------|---------|--------|
| 0 | Complete blackout | Reset to day 1 |
| 1 | Incorrect (recalled) | Reset to day 1 |
| 2 | Incorrect (seemed easy) | Reset to day 1 |
| 3 | Correct (hard) | Interval increases |
| 4 | Correct (good) | Interval increases |
| 5 | Perfect | Interval increases |

### Review Schedule
```
New Card → Review now
    ↓ (Quality ≥ 3)
First Success → Review in 1 day
    ↓ (Quality ≥ 3)
Second Success → Review in 6 days
    ↓ (Quality ≥ 3)
Third+ Success → Review in (interval × ease_factor) days
```

---

## Integration Recommendations

### 1. Auto-add After Lesson
```python
from backend.services.spaced_repetition import add_card_to_deck

# When user completes a lesson
card = add_card_to_deck(db, user.id, motif.id)
```

### 2. Dashboard Widget
Show review statistics on user dashboard:
- Cards due today
- Cards reviewed today
- Mastery progress

### 3. Daily Notifications
Send push notification when cards are due:
```python
from backend.services.spaced_repetition import get_due_cards

due = get_due_cards(db, user.id, limit=1)
if due:
    send_notification(user, f"{len(due)} cards ready for review")
```

### 4. Quiz Integration
Use quiz results as quality ratings:
- Perfect score (100%) → Quality 5
- Good score (80-99%) → Quality 4
- Pass (60-79%) → Quality 3
- Fail (<60%) → Quality 0-2

---

## Testing Checklist

- [ ] Migration runs successfully
- [ ] Can add card to review deck
- [ ] Card appears in due cards
- [ ] Can submit review with quality 0-5
- [ ] Review updates card parameters correctly
- [ ] Failed review resets card (quality < 3)
- [ ] Successful review increases interval
- [ ] Review history is tracked in JSONB
- [ ] Statistics are accurate
- [ ] Error handling works (invalid quality, non-existent card)
- [ ] Authorization is enforced

---

## Performance Metrics

### Expected Performance
- Get due cards: <50ms (with index)
- Submit review: <100ms
- Get statistics: <100ms
- Add card: <50ms

### Database Indexes
- `idx_sr_cards_user` - User's cards
- `idx_sr_cards_motif` - Motif references
- `idx_sr_cards_next_review` - Due card queries
- `idx_sr_cards_user_next_review` - Composite for optimal performance

---

## Next Steps

### Immediate
1. Run database migration
2. Test all endpoints
3. Verify SM-2 algorithm behavior

### Short-term
1. Integrate with lesson completion
2. Add to user dashboard
3. Implement daily notifications

### Long-term
1. Create mobile UI for reviews
2. Add review analytics dashboard
3. Implement practice mode
4. Build retention curves
5. Add gamification (streaks, XP, badges)

---

## Support & Troubleshooting

### Common Issues

**Migration fails:**
- Ensure database is running
- Check previous migrations are applied
- Verify PostgreSQL connection

**Cards not showing as due:**
- Check `next_review_at` is in past
- Verify timezone handling
- Ensure indexes are created

**Review history not saving:**
- Check JSONB column type
- Verify datetime serialization
- Ensure transaction commits

### Getting Help

1. Check implementation guide for details
2. Review API reference for endpoint specs
3. Run test script to validate setup
4. Check service code for algorithm details

---

## License & Credits

**Algorithm:** SuperMemo-2 (SM-2)  
**Implementation:** Custom for Luuniensuki LMS  
**Date:** January 17, 2025

---

**End of Documentation Index**
