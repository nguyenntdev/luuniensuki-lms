# P0-ANA-03: Session Tracking Deployment Checklist

## Pre-Deployment

### Code Review
- [ ] Review `backend/models.py` changes
  - [ ] UserSession model added correctly
  - [ ] Indexes defined appropriately
  - [ ] Relationships configured

- [ ] Review `backend/schemas.py` changes
  - [ ] Request/response schemas validated
  - [ ] Field validations (regex patterns) correct
  - [ ] Documentation strings present

- [ ] Review `backend/main.py` changes
  - [ ] UserSession imported
  - [ ] All 4 endpoints implemented
  - [ ] Error handling in place
  - [ ] Authorization checks correct

- [ ] Review migration file
  - [ ] Migration version number correct (0017)
  - [ ] Up/down revision links correct
  - [ ] Idempotent (safe to run multiple times)
  - [ ] All indexes created

### Testing (Development)
- [ ] Run migration in dev environment
  ```bash
  docker compose exec api alembic upgrade head
  ```

- [ ] Verify table created
  ```bash
  docker compose exec db psql -U postgres -d luuniensuki -c "\d user_sessions"
  ```

- [ ] Run test script
  ```bash
  ./test_session_tracking.sh
  ```

- [ ] Manual endpoint testing
  - [ ] POST /api/v1/sessions/heartbeat (create)
  - [ ] POST /api/v1/sessions/heartbeat (update)
  - [ ] POST /api/v1/sessions/end
  - [ ] GET /api/v1/admin/analytics/sessions/active
  - [ ] GET /api/v1/admin/analytics/sessions/stats

- [ ] Edge case testing
  - [ ] Heartbeat with invalid session_id format
  - [ ] End non-existent session
  - [ ] Admin endpoints without admin role
  - [ ] Multiple concurrent sessions per user
  - [ ] Session expiration (wait 30+ min)

### Database Review
- [ ] Check index creation
  ```sql
  SELECT indexname, indexdef 
  FROM pg_indexes 
  WHERE tablename = 'user_sessions';
  ```

- [ ] Test query performance
  ```sql
  EXPLAIN ANALYZE 
  SELECT COUNT(*) FROM user_sessions 
  WHERE is_active = true 
    AND last_active_at > NOW() - INTERVAL '5 minutes';
  ```

- [ ] Verify foreign key constraint
  ```sql
  SELECT conname, conrelid::regclass, confrelid::regclass
  FROM pg_constraint 
  WHERE conname LIKE '%user_sessions%';
  ```

## Deployment

### Backup
- [ ] Backup production database
  ```bash
  # Create backup before migration
  docker compose exec db pg_dump -U postgres luuniensuki > backup_pre_sessions.sql
  ```

### Migration
- [ ] Check current migration version
  ```bash
  docker compose exec api alembic current
  ```

- [ ] Run migration
  ```bash
  docker compose exec api alembic upgrade head
  ```

- [ ] Verify migration succeeded
  ```bash
  docker compose exec api alembic current
  # Should show: 0017_user_sessions (head)
  ```

- [ ] Check table exists
  ```bash
  docker compose exec db psql -U postgres -d luuniensuki \
    -c "SELECT COUNT(*) FROM user_sessions;"
  ```

### Service Restart
- [ ] Restart API service
  ```bash
  docker compose restart api
  ```

- [ ] Check API logs
  ```bash
  docker compose logs -f api | grep -i "session"
  ```

- [ ] Verify API is healthy
  ```bash
  curl http://localhost/health
  ```

### Smoke Tests
- [ ] Test user login
  ```bash
  curl -X POST http://localhost/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"password"}'
  ```

- [ ] Test session heartbeat
  ```bash
  # Use token from login
  curl -X POST http://localhost/api/v1/sessions/heartbeat \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"session_id":"'$(uuidgen)'","device_type":"web","platform":"web"}'
  ```

- [ ] Test admin endpoints
  ```bash
  curl -X GET http://localhost/api/v1/admin/analytics/sessions/active \
    -H "Authorization: Bearer $ADMIN_TOKEN"
  ```

## Post-Deployment

### Monitoring
- [ ] Set up alerts for API errors
  - [ ] 500 errors on session endpoints
  - [ ] High response times (>1s)
  - [ ] Database connection errors

- [ ] Monitor database performance
  - [ ] Watch for slow queries
  - [ ] Monitor table size growth
  - [ ] Check index usage

- [ ] Create dashboards
  - [ ] Real-time active users
  - [ ] Session duration trends
  - [ ] Platform distribution
  - [ ] Peak concurrent users

### Documentation
- [ ] Update API documentation
  - [ ] Add new endpoints to OpenAPI/Swagger
  - [ ] Update internal API docs
  - [ ] Add examples to developer guide

- [ ] Update client integration docs
  - [ ] Mobile app integration guide
  - [ ] Web app integration guide
  - [ ] Example code snippets

- [ ] Update admin guide
  - [ ] How to view session analytics
  - [ ] How to interpret metrics
  - [ ] Troubleshooting guide

### Client Integration
- [ ] Mobile app changes
  - [ ] Implement session manager
  - [ ] Add heartbeat mechanism
  - [ ] Handle app lifecycle events
  - [ ] Test offline scenarios

- [ ] Web app changes
  - [ ] Implement session manager
  - [ ] Add heartbeat mechanism
  - [ ] Handle page unload
  - [ ] Test browser close scenarios

### Validation (1 week after)
- [ ] Check data quality
  ```sql
  -- Should have sessions
  SELECT COUNT(*) FROM user_sessions;
  
  -- Should have ended sessions
  SELECT COUNT(*) FROM user_sessions WHERE ended_at IS NOT NULL;
  
  -- Should have active sessions
  SELECT COUNT(*) FROM user_sessions WHERE is_active = true;
  ```

- [ ] Verify metrics
  - [ ] Active sessions count makes sense
  - [ ] Session durations are realistic
  - [ ] Platform distribution matches expectations

- [ ] Review logs
  - [ ] No repeated errors
  - [ ] Heartbeat frequency correct
  - [ ] Session creation/end flows working

## Rollback Plan

### If Critical Issues Found
1. **Immediate**: Disable endpoints
   ```python
   # Comment out session endpoints in main.py
   # @app.post("/api/v1/sessions/heartbeat", ...)
   # @app.post("/api/v1/sessions/end", ...)
   # @app.get("/api/v1/admin/analytics/sessions/active", ...)
   # @app.get("/api/v1/admin/analytics/sessions/stats", ...)
   ```

2. **Restart API**
   ```bash
   docker compose restart api
   ```

3. **Rollback Migration** (if needed)
   ```bash
   docker compose exec api alembic downgrade -1
   ```

4. **Restore Backup** (if data corrupted)
   ```bash
   docker compose exec -T db psql -U postgres luuniensuki < backup_pre_sessions.sql
   ```

## Success Criteria

### Technical Success
- [ ] Migration applied without errors
- [ ] All endpoints return 200/201 status codes
- [ ] No 500 errors in logs
- [ ] Database queries perform well (<100ms)
- [ ] Indexes are being used (check EXPLAIN)

### Business Success
- [ ] Active user count available in real-time
- [ ] Session analytics visible to admins
- [ ] Data matches expected patterns
- [ ] No performance degradation

## Sign-off

- [ ] **Backend Developer**: Code reviewed and tested
- [ ] **DevOps**: Migration applied successfully
- [ ] **QA**: All endpoints tested and verified
- [ ] **Product**: Metrics available and accurate
- [ ] **Frontend Team**: Integration planned/completed

## Timeline

```
Day 1: Code Review + Dev Testing
Day 2: Staging Deployment + Testing
Day 3: Production Deployment
Day 4-5: Monitor + Client Integration
Week 2: Validation + Optimization
```

## Notes

### Performance Expectations
- Heartbeat: <50ms response time
- Admin active sessions: <200ms response time
- Admin stats: <500ms response time
- Database inserts: <10ms

### Data Retention
- Active sessions: Indefinite
- Ended sessions: Consider archival after 90 days
- Anonymous sessions: Can be cleaned up after 7 days

### Scaling Considerations
- Indexes should handle 100k+ sessions
- Heartbeat endpoint must be fast (frequently called)
- Consider read replicas for admin analytics
- Monitor table bloat and vacuum regularly

---

**Last Updated**: 2025-01-17  
**Version**: 1.0  
**Status**: Ready for Deployment

