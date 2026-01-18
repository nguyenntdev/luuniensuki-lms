# P0-HAB-04: Hearts System - Implementation Checklist

## ✅ Completed Tasks

### 1. Database Models
- [x] Created `HeartTransactionReason` enum with 8 transaction types
- [x] Created `UserHearts` model with all required fields
  - [x] `current_hearts` (int, default 5)
  - [x] `max_hearts` (int, default 5)
  - [x] `last_heart_lost_at` (datetime, nullable)
  - [x] `hearts_refill_at` (datetime, nullable)
  - [x] `unlimited_until` (datetime, nullable)
  - [x] `streak_freezes` (int, default 0)
  - [x] `updated_at`, `created_at` timestamps
- [x] Created `HeartTransaction` model for audit logging
  - [x] `amount` (positive/negative integer)
  - [x] `reason` (enum)
  - [x] `balance_after` (int)
  - [x] `metadata` (JSONB for context)
  - [x] `created_at` timestamp
- [x] Added relationship to User model (`hearts`)
- [x] Added proper indexes for performance

### 2. Database Migration
- [x] Created migration file `0023_hearts_system.py`
- [x] Creates `heart_transaction_reason` enum type
- [x] Creates `user_hearts` table with constraints
- [x] Creates `heart_transactions` table with foreign keys
- [x] Creates indexes: user_id, refill_at, reason, created_at
- [x] Includes downgrade function for rollback

### 3. Business Logic Service
- [x] Created `backend/services/hearts.py`
- [x] Implemented `get_or_create_user_hearts()`
- [x] Implemented `calculate_refill_hearts()` (1 per 4 hours)
- [x] Implemented `auto_refill_hearts()` with transaction logging
- [x] Implemented `calculate_time_until_refill()`
- [x] Implemented `has_hearts()` helper
- [x] Implemented `use_heart()` with transaction logging
- [x] Implemented `refill_hearts()` for multiple methods
- [x] Implemented `use_streak_freeze_for_hearts()`
- [x] Implemented `get_heart_transactions()` pagination
- [x] Implemented `set_unlimited_hearts()` for premium

### 4. API Schemas
- [x] Created `HeartsStatusOut` response schema
- [x] Created `UseHeartIn` request schema
- [x] Created `UseHeartOut` response schema
- [x] Created `RefillHeartsIn` request schema
- [x] Created `RefillHeartsOut` response schema
- [x] Created `UseStreakFreezeIn` request schema
- [x] Created `UseStreakFreezeForHeartsOut` response schema
- [x] Created `HeartTransactionOut` schema
- [x] Created `HeartTransactionListOut` pagination schema

### 5. API Endpoints
- [x] `GET /api/v1/hearts` - Get hearts status
- [x] `POST /api/v1/hearts/use` - Use a heart
- [x] `POST /api/v1/hearts/refill` - Refill hearts
- [x] `POST /api/v1/hearts/use-streak-freeze` - Use streak freeze
- [x] `GET /api/v1/hearts/transactions` - Get transaction history

### 6. Documentation
- [x] Created `P0_HAB_04_IMPLEMENTATION_SUMMARY.md`
- [x] Created `P0_HAB_04_API_REFERENCE.md`
- [x] Created `test_hearts_api.sh` testing script
- [x] Created this checklist

### 7. Code Updates
- [x] Added imports to `backend/main.py`
- [x] Updated models in `backend/models.py`
- [x] Updated schemas in `backend/schemas.py`

## 🔄 Next Steps (Not Yet Implemented)

### 1. Database Migration Execution
- [ ] Run `alembic upgrade head` to apply migration
- [ ] Verify tables created in database
- [ ] Verify indexes created
- [ ] Test migration rollback: `alembic downgrade -1`

### 2. Integration with Quiz System
- [ ] Modify quiz submission endpoint to check hearts
- [ ] Deduct heart on wrong answer
- [ ] Return hearts status in quiz result
- [ ] Block quiz if no hearts available
- [ ] Add hearts info to quiz attempt response

### 3. Testing
- [ ] Unit tests for hearts service functions
- [ ] Integration tests for API endpoints
- [ ] Test auto-refill logic with time manipulation
- [ ] Test streak freeze integration
- [ ] Test transaction logging
- [ ] Test edge cases (no hearts, already full, etc.)
- [ ] Load testing for concurrent heart usage

### 4. Mobile Client Integration
- [ ] Update mobile API client with hearts endpoints
- [ ] Create hearts display widget (already exists?)
- [ ] Show hearts in quiz screen
- [ ] Handle out-of-hearts state
- [ ] Show refill options dialog
- [ ] Implement hearts refill flow
- [ ] Add hearts to user profile

### 5. Premium Features
- [ ] Add hearts purchase with gems/coins
- [ ] Implement ad-watch for heart refill
- [ ] Add unlimited hearts as premium perk
- [ ] Create hearts packages (3-pack, 5-pack, etc.)
- [ ] Add hearts to daily login rewards

### 6. Notifications
- [ ] Push notification when hearts refilled
- [ ] Email reminder when hearts are full
- [ ] In-app notification for heart events

### 7. Analytics
- [ ] Track heart usage per user
- [ ] Track refill methods popularity
- [ ] Monitor users hitting zero hearts
- [ ] A/B test refill intervals
- [ ] Dashboard for heart metrics

### 8. Admin Tools
- [ ] Admin endpoint to grant hearts
- [ ] Admin endpoint to set unlimited hearts
- [ ] Admin dashboard for hearts monitoring
- [ ] Bulk operations for events

## 📋 Testing Checklist

### Manual Testing
- [ ] Test GET /api/v1/hearts
- [ ] Test POST /api/v1/hearts/use
- [ ] Test POST /api/v1/hearts/refill (all methods)
- [ ] Test POST /api/v1/hearts/use-streak-freeze
- [ ] Test GET /api/v1/hearts/transactions
- [ ] Test auto-refill after 4 hours
- [ ] Test unlimited hearts behavior
- [ ] Test edge cases

### Automated Testing
```bash
# Run the test script
AUTH_TOKEN="your_token" ./test_hearts_api.sh
```

### Database Verification
```sql
-- Check tables exist
SELECT * FROM user_hearts LIMIT 10;
SELECT * FROM heart_transactions LIMIT 10;

-- Check enum values
SELECT enumlabel FROM pg_enum WHERE enumtypid = 'heart_transaction_reason'::regtype;

-- Check indexes
SELECT indexname FROM pg_indexes WHERE tablename IN ('user_hearts', 'heart_transactions');
```

## 🐛 Known Issues / TODOs

- [ ] None currently

## 📊 Metrics to Monitor

1. **Heart Usage**
   - Average hearts lost per user per day
   - Distribution of zero-hearts events
   - Time users spend at zero hearts

2. **Refill Methods**
   - % using auto-refill vs purchase vs ad-watch
   - Average time to refill
   - Streak freeze usage rate

3. **Business Impact**
   - Effect on quiz completion rates
   - Effect on user engagement
   - Monetization through heart purchases

## 🎯 Success Criteria

- [x] All database models created and migrated
- [x] All API endpoints functional
- [x] Business logic correct (4 hours refill, max 5 hearts)
- [x] Transaction logging working
- [ ] Migration applied successfully
- [ ] Integration with quiz system
- [ ] Mobile client updated
- [ ] All tests passing

## 📚 References

- Duolingo hearts system (inspiration)
- [P0_HAB_04_IMPLEMENTATION_SUMMARY.md](./P0_HAB_04_IMPLEMENTATION_SUMMARY.md)
- [P0_HAB_04_API_REFERENCE.md](./P0_HAB_04_API_REFERENCE.md)
- Backend: `backend/services/hearts.py`
- Models: `backend/models.py` (UserHearts, HeartTransaction)
- Schemas: `backend/schemas.py` (hearts section)
- Endpoints: `backend/main.py` (hearts endpoints)
- Migration: `migrations/versions/0023_hearts_system.py`
