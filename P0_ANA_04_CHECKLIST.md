# P0-ANA-04: Testing & Deployment Checklist

## Pre-Deployment Testing

### ✅ Unit Tests

#### Service Layer Tests
- [ ] Test `calculate_overall_retention` with no users
- [ ] Test `calculate_overall_retention` with users but no events
- [ ] Test `calculate_overall_retention` with mix of retained/not retained users
- [ ] Test `calculate_overall_retention` with days_ago filter
- [ ] Test `calculate_cohort_retention` with week period
- [ ] Test `calculate_cohort_retention` with month period
- [ ] Test `calculate_cohort_retention` with limit parameter
- [ ] Test `calculate_retention_curve` with various day ranges
- [ ] Test `_check_user_active_on_day` with events in/out of window
- [ ] Test `_get_cohort_from_date` for week and month formats

#### Edge Cases
- [ ] Users who signed up < 1 day ago (D1 not eligible)
- [ ] Users who signed up < 7 days ago (D7 not eligible)
- [ ] Users who signed up < 30 days ago (D30 not eligible)
- [ ] Events exactly at window boundaries (±12 hours)
- [ ] Multiple events on same day
- [ ] No events for any users
- [ ] Timezone edge cases (UTC consistency)

### ✅ API Endpoint Tests

#### Authentication & Authorization
- [ ] Test with valid admin token → 200 OK
- [ ] Test with valid learner token → 403 Forbidden
- [ ] Test with invalid token → 401 Unauthorized
- [ ] Test without token → 401 Unauthorized

#### Overall Retention Endpoint
```bash
GET /api/v1/admin/analytics/retention
```
- [ ] Test without parameters (all users)
- [ ] Test with `days_ago=30`
- [ ] Test with `days_ago=90`
- [ ] Verify response schema matches `RetentionMetricsOut`
- [ ] Verify percentages are correctly calculated
- [ ] Verify eligible_users counts are accurate

#### Cohort Retention Endpoint
```bash
GET /api/v1/admin/analytics/retention/cohorts
```
- [ ] Test with `period=week` (default)
- [ ] Test with `period=month`
- [ ] Test with `limit=6`
- [ ] Test with `limit=52` (max)
- [ ] Test with invalid period → 422 Validation Error
- [ ] Test with `limit > 52` → 422 Validation Error
- [ ] Verify cohort identifiers are correctly formatted
- [ ] Verify retention rates match manual calculations

#### Retention Curve Endpoint
```bash
GET /api/v1/admin/analytics/retention/curve
```
- [ ] Test with default parameters (days=30)
- [ ] Test with `days=60`
- [ ] Test with `days=90` (max)
- [ ] Test with `days > 90` → 422 Validation Error
- [ ] Test with `cohort_days_ago=180`
- [ ] Verify data_points array length matches days + 1
- [ ] Verify day 0 retention is 100% (or close to it)
- [ ] Verify retention decreases over time (generally)

### ✅ Performance Tests

- [ ] Test with 100 users
- [ ] Test with 1,000 users
- [ ] Test with 10,000 users
- [ ] Test with 100,000 analytics events
- [ ] Measure query execution time (<5s acceptable)
- [ ] Test concurrent requests (10 simultaneous)
- [ ] Monitor database query count (N+1 queries?)

### ✅ Data Integrity Tests

- [ ] Manually calculate retention for sample data
- [ ] Verify API results match manual calculations
- [ ] Cross-check cohort totals with user counts
- [ ] Verify eligible_users never exceeds total_users
- [ ] Verify retention rates are between 0-100%

## Database Optimization

### Recommended Indexes
```sql
-- Index for user cohort queries
CREATE INDEX idx_users_created_at ON users(created_at);

-- Index for retention activity checks
CREATE INDEX idx_analytics_events_user_created 
  ON analytics_events(user_id, created_at);

-- Composite index for faster lookups
CREATE INDEX idx_analytics_events_user_created_name 
  ON analytics_events(user_id, created_at, event_name);
```

- [ ] Create indexes in development
- [ ] Test query performance improvement
- [ ] Create indexes in staging
- [ ] Create indexes in production

### Query Analysis
- [ ] Run EXPLAIN ANALYZE on retention queries
- [ ] Identify slow queries
- [ ] Optimize WHERE clauses
- [ ] Consider materialized views for expensive queries

## Deployment Steps

### Pre-Deployment
- [ ] Code review completed
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Changelog updated

### Staging Deployment
1. [ ] Deploy code to staging
2. [ ] Run database migrations (if any)
3. [ ] Create database indexes
4. [ ] Run manual API tests
5. [ ] Run automated test suite
6. [ ] Performance testing with production-like data
7. [ ] Verify no regressions in existing features

### Production Deployment
1. [ ] Schedule maintenance window (if needed)
2. [ ] Backup database
3. [ ] Deploy code to production
4. [ ] Run database migrations
5. [ ] Create database indexes (during low-traffic period)
6. [ ] Smoke test endpoints
7. [ ] Monitor error rates
8. [ ] Monitor API response times
9. [ ] Monitor database load

### Post-Deployment
- [ ] Test all three endpoints in production
- [ ] Verify admin dashboard integration
- [ ] Check logs for errors
- [ ] Monitor performance metrics
- [ ] Gather initial retention data
- [ ] Share results with stakeholders

## Monitoring

### Metrics to Track
- [ ] API response times (p50, p95, p99)
- [ ] Error rates (4xx, 5xx)
- [ ] Database query times
- [ ] Cache hit rates (if caching implemented)
- [ ] Endpoint usage frequency

### Alerts
- [ ] Alert if response time > 10s
- [ ] Alert if error rate > 5%
- [ ] Alert if database queries timeout
- [ ] Alert if no requests for 24h (possible integration issue)

## Documentation

### User Documentation
- [ ] Add to admin dashboard docs
- [ ] Create user guide with screenshots
- [ ] Add to API documentation
- [ ] Update OpenAPI/Swagger specs

### Developer Documentation
- [ ] Code comments complete
- [ ] Service layer documented
- [ ] API endpoints documented
- [ ] Example usage provided
- [ ] Architecture diagrams created

## Rollback Plan

### If Issues Arise
1. [ ] Document the issue
2. [ ] Assess severity (critical, major, minor)
3. [ ] If critical: Revert deployment immediately
4. [ ] If major: Schedule fix within 24h
5. [ ] If minor: Schedule fix in next release

### Rollback Steps
1. [ ] Revert code to previous version
2. [ ] Drop new indexes (if they cause issues)
3. [ ] Restore database from backup (if needed)
4. [ ] Verify system stability
5. [ ] Communicate status to stakeholders

## Sign-Off

### Completed By
- [ ] Developer: _________________ Date: _______
- [ ] QA: _______________________ Date: _______
- [ ] DevOps: ___________________ Date: _______
- [ ] Product Owner: _____________ Date: _______

### Production Deployment
- [ ] Deployed by: _______________ Date: _______
- [ ] Verified by: _______________ Date: _______

---

**Version**: 1.0  
**Last Updated**: December 20, 2024  
**Feature**: P0-ANA-04 Retention Analytics
