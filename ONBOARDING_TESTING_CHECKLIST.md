# P0-ACT-01 Onboarding Implementation Checklist

## Pre-deployment Checklist

### Database Migration
- [ ] Review migration file: `migrations/versions/0012_onboarding_fields.py`
- [ ] Backup database before running migration
- [ ] Run migration: `alembic upgrade head`
- [ ] Verify migration success:
  ```sql
  SELECT column_name, data_type, is_nullable, column_default 
  FROM information_schema.columns 
  WHERE table_name = 'users' 
  AND column_name IN ('onboarding_goal', 'onboarding_completed', 'onboarding_completed_at');
  ```
- [ ] Test rollback: `alembic downgrade -1`
- [ ] Re-apply migration: `alembic upgrade head`

### Code Review
- [ ] Review `backend/models.py` changes (lines 128-134)
- [ ] Review `backend/schemas.py` changes (lines 673-706)
- [ ] Review `backend/main.py` changes (lines 1074-1165)
- [ ] Verify Python syntax with `python3 -m py_compile`

### API Testing

#### Test 1: Set Onboarding Goal
- [ ] Create test user or login as existing user
- [ ] Send POST request to `/api/v1/onboarding/goals`
  ```bash
  curl -X POST http://localhost:8000/api/v1/onboarding/goals \
    -H "Content-Type: application/json" \
    -b cookies.txt \
    -d '{"goal":"learn_culture"}'
  ```
- [ ] Verify response: `{"success": true, "goal": "learn_culture"}`
- [ ] Check database: User should have `onboarding_goal = 'learn_culture'`

#### Test 2: Invalid Goal
- [ ] Send invalid goal
  ```bash
  curl -X POST http://localhost:8000/api/v1/onboarding/goals \
    -H "Content-Type: application/json" \
    -b cookies.txt \
    -d '{"goal":"invalid_goal"}'
  ```
- [ ] Verify 400 error response with descriptive message

#### Test 3: Get Onboarding Status
- [ ] Send GET request to `/api/v1/onboarding/status`
  ```bash
  curl -X GET http://localhost:8000/api/v1/onboarding/status -b cookies.txt
  ```
- [ ] Verify response shows goal and `onboarding_completed: false`

#### Test 4: Complete Onboarding
- [ ] Send POST request to `/api/v1/onboarding/complete`
  ```bash
  curl -X POST http://localhost:8000/api/v1/onboarding/complete -b cookies.txt
  ```
- [ ] Verify response: `{"success": true, "onboarding_completed": true}`
- [ ] Check database: User should have `onboarding_completed = true` and timestamp
- [ ] Call endpoint again - should return "already completed" message

#### Test 5: Unauthenticated Access
- [ ] Try all endpoints without authentication
- [ ] Verify 401 Unauthorized responses

### Integration Testing

#### Full Onboarding Flow
- [ ] **Step 1:** Register new user
- [ ] **Step 2:** Check onboarding status (should be incomplete)
- [ ] **Step 3:** Set goal
- [ ] **Step 4:** Check status again (should show goal)
- [ ] **Step 5:** Complete onboarding
- [ ] **Step 6:** Verify completion in database
- [ ] **Step 7:** Check status final time (should be completed)

#### Edge Cases
- [ ] Complete onboarding without setting goal (should work)
- [ ] Set goal after completing onboarding (should work)
- [ ] Try all 5 valid goal values
- [ ] Test with special characters in goal (should fail validation)
- [ ] Test with existing user (should have `onboarding_completed = false`)

### Performance Testing
- [ ] Test with 100+ concurrent users
- [ ] Verify database query performance
- [ ] Check response times < 200ms

### Security Testing
- [ ] Verify JWT token validation
- [ ] Test CSRF protection
- [ ] Verify users can only access their own onboarding data
- [ ] Test SQL injection on goal field

## Post-deployment Checklist

### Monitoring
- [ ] Check application logs for errors
- [ ] Monitor database performance
- [ ] Track API response times
- [ ] Monitor error rates

### Data Verification
- [ ] Verify existing users have default values:
  ```sql
  SELECT 
    COUNT(*) as total_users,
    SUM(CASE WHEN onboarding_completed THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN onboarding_goal IS NOT NULL THEN 1 ELSE 0 END) as with_goal
  FROM users;
  ```
- [ ] Check for any NULL constraint violations

### Documentation
- [ ] Update API documentation with new endpoints
- [ ] Create frontend integration guide
- [ ] Update mobile app documentation
- [ ] Add to changelog

### Frontend/Mobile Integration
- [ ] Frontend: Add onboarding flow UI
- [ ] Frontend: Implement API calls
- [ ] Frontend: Add error handling
- [ ] Frontend: Test user flow
- [ ] Mobile: Update API client
- [ ] Mobile: Add onboarding screens
- [ ] Mobile: Test on iOS/Android

## Rollback Plan

If issues occur after deployment:

1. **Immediate:** Revert API changes
   ```bash
   git revert <commit-hash>
   ```

2. **Database:** Rollback migration
   ```bash
   alembic downgrade -1
   ```

3. **Verify:** Check that application works without new fields

4. **Debug:** Review logs and fix issues

5. **Re-deploy:** After fixes, re-apply changes

## Success Criteria

- [ ] All tests pass
- [ ] No errors in production logs
- [ ] Users can complete onboarding flow
- [ ] Database performance is acceptable
- [ ] Frontend/mobile integration works
- [ ] Analytics show onboarding completion rate

## Known Issues

None currently.

## Next Steps

1. Implement frontend onboarding UI
2. Add analytics tracking for onboarding events
3. Create A/B tests for different goal prompts
4. Add personalized content based on goal selection
5. Implement onboarding progress tracking (step by step)

## Support

For issues or questions:
- Check logs: `/var/log/luuniensuki/app.log`
- Review documentation: `P0-ACT-01_ONBOARDING_IMPLEMENTATION.md`
- API reference: `ONBOARDING_API_REFERENCE.md`

