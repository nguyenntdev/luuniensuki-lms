# P0-ANA-04: Retention Analytics Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Admin Dashboard UI                          │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────────┐   │
│  │  D1/D7/D30 │  │   Cohort   │  │   Retention Curve       │   │
│  │   Metrics  │  │  Heatmap   │  │    Line Chart           │   │
│  └─────┬──────┘  └──────┬─────┘  └───────────┬─────────────┘   │
└────────┼─────────────────┼──────────────────────┼───────────────┘
         │                 │                      │
         │                 │                      │
         ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Endpoints                            │
│                                                                   │
│  GET /api/v1/admin/analytics/retention                           │
│  GET /api/v1/admin/analytics/retention/cohorts                   │
│  GET /api/v1/admin/analytics/retention/curve                     │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              Admin Access Control                      │     │
│  │  (get_admin_user dependency - checks role)             │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Retention Service (business logic)                  │
│                                                                   │
│  calculate_overall_retention(session, days_ago)                  │
│  ├─ Get all eligible users                                       │
│  ├─ Check activity for D1, D7, D30                               │
│  └─ Calculate retention percentages                              │
│                                                                   │
│  calculate_cohort_retention(session, period, limit)              │
│  ├─ Group users by signup week/month                             │
│  ├─ Calculate retention for each cohort                          │
│  └─ Return cohort metrics                                        │
│                                                                   │
│  calculate_retention_curve(session, days, cohort_days_ago)       │
│  ├─ Get users in cohort period                                   │
│  ├─ Calculate daily retention (day 0-N)                          │
│  └─ Return data points for visualization                         │
│                                                                   │
│  Helper: _check_user_active_on_day(session, user_id, date)       │
│  └─ Checks for events within ±12 hour window                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database Layer                              │
│                                                                   │
│  ┌──────────────────┐          ┌─────────────────────┐          │
│  │  users           │          │  analytics_events   │          │
│  ├──────────────────┤          ├─────────────────────┤          │
│  │ id               │          │ id                  │          │
│  │ created_at  ─────┼──────┐   │ user_id ────────────┼───┐      │
│  │ ...              │      │   │ created_at          │   │      │
│  └──────────────────┘      │   │ event_name          │   │      │
│                            │   │ ...                 │   │      │
│                            │   └─────────────────────┘   │      │
│                            └──────────────────────────────┘      │
│                                                                   │
│  Indexes:                                                        │
│  - users(created_at) for cohort queries                          │
│  - analytics_events(user_id, created_at) for retention checks    │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: Overall Retention

```
1. Request
   GET /api/v1/admin/analytics/retention?days_ago=30
   Headers: Authorization: Bearer <admin_token>

2. Middleware & Auth
   ├─ Verify JWT token
   ├─ Load user from database
   └─ Check user.role in ADMIN_ROLES

3. Service Layer
   calculate_overall_retention(db, days_ago=30)
   
   ├─ Query users created ≥30 days ago
   │  SELECT id, created_at FROM users
   │  WHERE created_at >= NOW() - INTERVAL '30 days'
   │
   ├─ For each retention day (1, 7, 30):
   │  ├─ Filter eligible users (created ≥N days ago)
   │  ├─ For each user:
   │  │  ├─ Calculate target_date = created_at + N days
   │  │  ├─ Check for events within ±12 hours
   │  │  │  SELECT 1 FROM analytics_events
   │  │  │  WHERE user_id = ? 
   │  │  │    AND created_at BETWEEN (target - 12h) AND (target + 12h)
   │  │  │  LIMIT 1
   │  │  └─ Count as retained if event exists
   │  └─ Calculate: (retained / eligible) × 100
   │
   └─ Return metrics

4. Response
   {
     "d1_retention": 45.5,
     "d7_retention": 28.3,
     "d30_retention": 15.7,
     "total_users": 1000,
     "eligible_users": {"1": 980, "7": 950, "30": 850},
     "date_range": {"start": "...", "end": "..."}
   }
```

## Retention Calculation Example

```
User Signup Timeline:

Day 0: User signs up (2024-01-01 10:00 AM)
       └─ 100% retention (by definition)

Day 1: Target = 2024-01-02 10:00 AM
       Window = [2024-01-01 10:00 PM - 2024-01-02 10:00 PM]
       └─ Has event in window? → D1 Retained ✓

Day 7: Target = 2024-01-08 10:00 AM
       Window = [2024-01-07 10:00 PM - 2024-01-08 10:00 PM]
       └─ Has event in window? → D7 Retained ✓

Day 30: Target = 2024-01-31 10:00 AM
        Window = [2024-01-30 10:00 PM - 2024-01-31 10:00 PM]
        └─ No event in window → D30 Not Retained ✗

Result for this user:
- D1: Retained (counts toward numerator)
- D7: Retained (counts toward numerator)
- D30: Not retained (doesn't count)
```

## Cohort Analysis Example

```
Cohort: 2024-W50 (Week 50 of 2024)
Period: Dec 11-17, 2024
Users: 45 signups

Retention Calculation:
┌──────┬─────────┬─────────┬──────────┐
│ Day  │ Eligible│ Retained│ Rate (%) │
├──────┼─────────┼─────────┼──────────┤
│ D1   │   45    │   25    │  55.6    │
│ D7   │   45    │   15    │  33.3    │
│ D30  │   0     │   0     │   0.0    │
└──────┴─────────┴─────────┴──────────┘

Note: D30 = 0% because not enough time has passed

