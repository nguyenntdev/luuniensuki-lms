# P0-HAB-04: Hearts System - API Quick Reference

## Endpoints

### 1. GET /api/v1/hearts
**Get current hearts status**

**Authentication**: Required

**Response** (`HeartsStatusOut`):
```json
{
  "current_hearts": 5,
  "max_hearts": 5,
  "last_heart_lost_at": "2025-01-16T12:00:00Z",
  "hearts_refill_at": "2025-01-16T16:00:00Z",
  "unlimited_until": null,
  "streak_freezes": 2,
  "is_unlimited": false,
  "time_until_refill_seconds": 14400,
  "updated_at": "2025-01-16T12:00:00Z"
}
```

**Auto-refills hearts** based on time passed before returning status.

---

### 2. POST /api/v1/hearts/use
**Use a heart (e.g., on wrong quiz answer)**

**Authentication**: Required

**Request** (`UseHeartIn`):
```json
{
  "reason": "quiz_wrong",  // or "practice"
  "metadata": {
    "quiz_id": "uuid",
    "question_id": "uuid"
  }
}
```

**Response** (`UseHeartOut`):
```json
{
  "success": true,
  "current_hearts": 4,
  "hearts_refill_at": "2025-01-16T16:00:00Z",
  "message": "Heart used. 4 hearts remaining."
}
```

**Error Response** (no hearts):
```json
{
  "success": false,
  "current_hearts": 0,
  "hearts_refill_at": "2025-01-16T16:00:00Z",
  "message": "No hearts available. Wait for refill or purchase more hearts."
}
```

---

### 3. POST /api/v1/hearts/refill
**Refill hearts (purchase, ad watch, reward, admin)**

**Authentication**: Required

**Request** (`RefillHeartsIn`):
```json
{
  "method": "ad_watch",  // purchase, ad_watch, reward, admin
  "amount": 1,  // optional, null = refill to max
  "metadata": {
    "transaction_id": "xyz",
    "ad_id": "abc"
  }
}
```

**Response** (`RefillHeartsOut`):
```json
{
  "success": true,
  "current_hearts": 5,
  "hearts_added": 1,
  "message": "Successfully added 1 hearts!"
}
```

**Error Response** (already full):
```json
{
  "success": false,
  "current_hearts": 5,
  "hearts_added": 0,
  "message": "Hearts are already full."
}
```

---

### 4. POST /api/v1/hearts/use-streak-freeze
**Use a streak freeze to restore all hearts**

**Authentication**: Required

**Request** (`UseStreakFreezeIn`):
```json
{}
```

**Response** (`UseStreakFreezeForHeartsOut`):
```json
{
  "success": true,
  "current_hearts": 5,
  "remaining_freezes": 1,
  "message": "Streak freeze used! All hearts restored."
}
```

**Error Response** (no freezes):
```json
{
  "success": false,
  "current_hearts": 0,
  "remaining_freezes": 0,
  "message": "No streak freezes available."
}
```

---

### 5. GET /api/v1/hearts/transactions
**Get heart transaction history**

**Authentication**: Required

**Query Parameters**:
- `page` (int, default=1): Page number
- `page_size` (int, default=20, max=100): Items per page

**Response** (`HeartTransactionListOut`):
```json
{
  "transactions": [
    {
      "id": "uuid",
      "amount": -1,
      "reason": "quiz_wrong",
      "balance_after": 4,
      "metadata": {
        "quiz_id": "uuid",
        "question_id": "uuid"
      },
      "created_at": "2025-01-16T12:00:00Z"
    },
    {
      "id": "uuid",
      "amount": 5,
      "reason": "daily_refill",
      "balance_after": 5,
      "metadata": null,
      "created_at": "2025-01-16T08:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

## Transaction Reasons

| Reason | Description | Amount |
|--------|-------------|---------|
| `quiz_wrong` | Wrong quiz answer | -1 |
| `practice_complete` | Practice mode | -1 |
| `heart_purchase` | Purchased with gems/coins | +1 to +5 |
| `daily_refill` | Automatic time-based refill | +1 to +5 |
| `streak_freeze_used` | Used streak freeze | +5 (all) |
| `reward` | Reward from quest/achievement | +1 to +5 |
| `admin_grant` | Admin gave hearts | +1 to +5 |
| `ad_watch` | Watched an ad | +1 |

---

## Heart Mechanics

### Refill Timeline
- **1 heart lost**: 4 hours to refill
- **2 hearts lost**: 8 hours to refill
- **3 hearts lost**: 12 hours to refill
- **4 hearts lost**: 16 hours to refill  
- **5 hearts lost**: 20 hours to refill

### Maximum Hearts
- Default: **5 hearts**
- Configurable per user via `max_hearts` field

### Unlimited Hearts
- Can be granted for premium/events via `unlimited_until` timestamp
- When active, hearts don't decrease and refill is bypassed

### Streak Freezes
- Restore **all hearts** immediately
- Deduct 1 streak freeze from user
- Sync with `users.streak_freezes` field

---

## Integration Examples

### Check Hearts Before Quiz
```python
from .services.hearts import has_hearts

if not has_hearts(db, current_user, now):
    raise HTTPException(
        status_code=403,
        detail="Out of hearts"
    )
```

### Deduct Heart on Wrong Answer
```python
from .services.hearts import use_heart

success, user_hearts = use_heart(
    db, 
    current_user, 
    now,
    reason=HeartTransactionReason.quiz_wrong,
    metadata={"quiz_id": str(quiz_id)}
)

if not success:
    # User has no hearts
    pass
```

### Give Hearts as Reward
```python
from .services.hearts import refill_hearts

hearts_added, user_hearts = refill_hearts(
    db,
    current_user,
    now,
    amount=2,
    reason=HeartTransactionReason.reward,
    metadata={"quest_id": str(quest_id)}
)
```

---

## Error Codes

| Status | Error | Reason |
|--------|-------|--------|
| 401 | Unauthorized | No valid authentication |
| 403 | Forbidden | Out of hearts (cannot take quiz) |
| 404 | Not Found | User hearts record not found |
| 422 | Validation Error | Invalid request body |

---

## Migration

Run migration to create tables:
```bash
cd /path/to/luuniensuki-lms
alembic upgrade head
```

This creates:
- `user_hearts` table
- `heart_transactions` table  
- `heart_transaction_reason` enum
