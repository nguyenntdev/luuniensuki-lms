# P1-ADAP-03: Learning Path Testing Checklist

## 🗄️ Database Setup

- [ ] Migration applied successfully
  ```bash
  cd backend
  alembic upgrade head
  ```

- [ ] Table `user_learning_paths` exists
  ```sql
  SELECT * FROM user_learning_paths LIMIT 1;
  ```

- [ ] Indexes created properly
  ```sql
  SELECT indexname FROM pg_indexes 
  WHERE tablename = 'user_learning_paths';
  ```

- [ ] Unique constraint on (user_id, path_date) works
  ```sql
  -- Should fail on duplicate insert
  INSERT INTO user_learning_paths (id, user_id, path_date) 
  VALUES (gen_random_uuid(), 'user-uuid', '2025-01-16');
  ```

## 🔧 Backend Service Tests

### Learning Path Generation

- [ ] New user (no progress) gets empty path
- [ ] User with discovered motifs gets lesson recommendations
- [ ] User with learned motifs gets review recommendations
- [ ] User with low quiz scores gets quiz recommendations
- [ ] Path respects max items per day (3 lessons, 10 reviews, 5 quizzes)
- [ ] Estimated time calculated correctly

### Spaced Repetition Logic

- [ ] 90%+ quiz score → 14 day interval
- [ ] 80-89% quiz score → 7 day interval
- [ ] 60-79% quiz score → 3 day interval
- [ ] <60% quiz score → 1 day interval
- [ ] Reviews sorted by priority (high → medium → low)
- [ ] Overdue reviews marked as high priority

### Lesson Recommendations

- [ ] Discovered motifs prioritized over new ones
- [ ] Lessons include reason for recommendation
- [ ] Onboarding goal influences recommendations
- [ ] Maximum 3 lessons per day enforced

### Progress Tracking

- [ ] Completing item adds to completed_items array
- [ ] Duplicate completion handled gracefully
- [ ] Path marked complete when all items done
- [ ] completed_at timestamp set correctly

## 🌐 API Endpoint Tests

### GET /api/v1/learning-path/today

- [ ] **Authentication**
  - [ ] Returns 401 without token
  - [ ] Returns 401 with invalid token
  - [ ] Works with valid token

- [ ] **First-time user**
  - [ ] Auto-generates path if none exists
  - [ ] Returns same path on subsequent calls same day
  - [ ] Contains expected fields (lessons, reviews, quizzes)

- [ ] **Path structure**
  - [ ] `lessons` array has correct schema
  - [ ] `reviews` array has correct schema  
  - [ ] `quizzes` array has correct schema
  - [ ] `progress` object calculates correctly
  - [ ] `estimated_time_minutes` is reasonable

### POST /api/v1/learning-path/generate

- [ ] **Authentication**
  - [ ] Returns 401 without token

- [ ] **Force regenerate**
  - [ ] Deletes existing path when force_regenerate=true
  - [ ] Creates new path with different recommendations
  - [ ] Works without force flag (creates if not exists)

- [ ] **Target date**
  - [ ] Can generate for past dates
  - [ ] Can generate for future dates
  - [ ] Defaults to today if not specified

### POST /api/v1/learning-path/complete-item

- [ ] **Authentication**
  - [ ] Returns 401 without token

- [ ] **Item types**
  - [ ] Works with item_type="lesson"
  - [ ] Works with item_type="review"
  - [ ] Works with item_type="quiz"
  - [ ] Rejects invalid item_type

- [ ] **Validation**
  - [ ] Returns 404 if no path exists for today
  - [ ] Returns 400 if item not in today's path
  - [ ] Handles already-completed items gracefully

- [ ] **Progress update**
  - [ ] Increments progress counter
  - [ ] Updates completed_items array
  - [ ] Marks path as complete when all items done
  - [ ] Returns correct progress/total counts

### GET /api/v1/learning-path/history

- [ ] **Authentication**
  - [ ] Returns 401 without token

- [ ] **Query parameters**
  - [ ] Respects days parameter
  - [ ] Returns max of specified days
  - [ ] Defaults to 30 days if not specified
  - [ ] Validates days is between 1 and 365

- [ ] **Response**
  - [ ] Paths sorted by date (newest first)
  - [ ] Each path has complete structure
  - [ ] total_paths count is accurate

### GET /api/v1/learning-path/stats

- [ ] **Authentication**
  - [ ] Returns 401 without token

- [ ] **Statistics accuracy**
  - [ ] total_paths_generated is correct
  - [ ] completed_paths count is accurate
  - [ ] completion_rate calculated correctly
  - [ ] Lesson stats match reality
  - [ ] Review stats match reality
  - [ ] Quiz stats match reality

- [ ] **Query parameters**
  - [ ] Respects days parameter
  - [ ] Validates days is between 1 and 365

## 🧪 Integration Tests

### Complete User Flow

1. **Morning** (Path Generation)
   - [ ] User logs in
   - [ ] GET /today creates new path
   - [ ] Path contains relevant recommendations
   - [ ] Estimated time is reasonable

2. **Learning** (Item Completion)
   - [ ] Complete first lesson
   - [ ] Progress updates correctly
   - [ ] Complete a review
   - [ ] Progress increments
   - [ ] Complete a quiz
   - [ ] All progress tracked

3. **Path Completion**
   - [ ] Complete all items
   - [ ] is_completed set to true
   - [ ] completed_at timestamp set
   - [ ] Completion message returned

4. **Next Day** (New Path)
   - [ ] New path generated for new day
   - [ ] Previous day's path in history
   - [ ] Stats include both days

### Spaced Repetition Integration

- [ ] Quiz at 95% → review in ~14 days
- [ ] Quiz at 85% → review in ~7 days
- [ ] Quiz at 70% → review in ~3 days
- [ ] Quiz at 50% → review in ~1 day
- [ ] Failed quiz → appears in next path

### Edge Cases

- [ ] **Empty states**
  - [ ] New user with no content
  - [ ] User who completed everything
  - [ ] No lessons available
  - [ ] No reviews due

- [ ] **Boundary conditions**
  - [ ] Exactly max lessons/reviews/quizzes
  - [ ] More items available than max
  - [ ] Path on first day of using app
  - [ ] Path after long absence

- [ ] **Concurrent operations**
  - [ ] Multiple complete-item calls
  - [ ] Regenerate while completing items
  - [ ] Two requests for today's path

## 🚀 Performance Tests

- [ ] **Query performance**
  - [ ] Today's path query < 100ms
  - [ ] History query < 200ms
  - [ ] Stats query < 300ms
  - [ ] Generation < 500ms

- [ ] **Scalability**
  - [ ] Works with 100+ learned motifs
  - [ ] Works with 30+ days of history
  - [ ] Multiple users don't interfere

## 📊 Data Validation

- [ ] **JSONB structure**
  - [ ] recommended_lessons has valid UUIDs
  - [ ] recommended_reviews has valid structure
  - [ ] recommended_quizzes has valid structure
  - [ ] completed_items has valid timestamps

- [ ] **Timestamps**
  - [ ] path_date is start of day (00:00:00)
  - [ ] generated_at is current time
  - [ ] completed_at only set when complete

## 🔒 Security Tests

- [ ] Users can't access other users' paths
- [ ] Can't complete items in other users' paths
- [ ] Can't regenerate for other users
- [ ] SQL injection protection in queries
- [ ] XSS protection in responses

## 📱 Test Script

Run automated tests:
```bash
./test_learning_path_api.sh
```

Expected output:
- ✅ All endpoints return 200/201
- ✅ Path generation works
- ✅ Item completion works
- ✅ History retrieval works
- ✅ Stats calculation works

## ✅ Sign-off Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] API documentation updated
- [ ] Migration applied to dev/staging
- [ ] Performance benchmarks acceptable
- [ ] Security review completed
- [ ] Code review approved
- [ ] Ready for production deployment

