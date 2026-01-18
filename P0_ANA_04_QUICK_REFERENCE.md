# P0-ANA-04: Retention Analytics - Quick Reference

## API Endpoints

### 1. Overall Retention Metrics
```
GET /api/v1/admin/analytics/retention
```
**Auth**: Admin only  
**Query Params**:
- `days_ago` (optional): Filter users by cohort period

**Response**:
```json
{
  "d1_retention": 45.5,
  "d7_retention": 28.3,
  "d30_retention": 15.7,
  "total_users": 1000,
  "eligible_users": {"1": 980, "7": 950, "30": 850},
  "date_range": {"start": "...", "end": "..."}
}
```

### 2. Cohort Retention
```
GET /api/v1/admin/analytics/retention/cohorts
```
**Auth**: Admin only  
**Query Params**:
- `period`: "week" | "month" (default: "week")
- `limit`: 1-52 (default: 12)

**Response**:
```json
{
  "cohorts": [
    {
      "cohort": "2024-W50",
      "signup_count": 45,
      "d1_retention": 55.6,
      "d7_retention": 33.3,
      "d30_retention": 19.2,
      "eligible_d1": 45,
      "eligible_d7": 45,
      "eligible_d30": 45
    }
  ],
  "period": "week"
}
```

### 3. Retention Curve
```
GET /api/v1/admin/analytics/retention/curve
```
**Auth**: Admin only  
**Query Params**:
- `days`: 1-90 (default: 30)
- `cohort_days_ago`: 30-365 (default: 90)

**Response**:
```json
{
  "data_points": [
    {"day": 0, "retention_rate": 100.0, "retained_users": 500, "eligible_users": 500},
    {"day": 1, "retention_rate": 45.0, "retained_users": 225, "eligible_users": 500}
  ],
  "total_users": 500,
  "days": 30,
  "cohort_period": {"start": "...", "end": "..."}
}
```

## Retention Calculation

### Definition
A user is "retained" on day N if they have at least one `AnalyticsEvent` within a ±12 hour window of their signup date + N days.

### Retention Rates
- **D1**: % active 1 day after signup
- **D7**: % active 7 days after signup  
- **D30**: % active 30 days after signup

### Eligibility
Only users who have been registered for ≥N days are included in DN retention calculation.

## Service Functions

### `calculate_overall_retention(session, days_ago)`
Location: `backend/services/retention.py`

Calculates overall retention across all eligible users.

### `calculate_cohort_retention(session, period, limit)`
Groups users by signup week/month and calculates retention for each cohort.

### `calculate_retention_curve(session, days, cohort_days_ago)`
Returns daily retention rates from day 0 to specified day.

## Schemas

### `RetentionMetricsOut`
Overall retention response with D1/D7/D30 rates.

### `CohortRetentionOut`
List of cohorts with retention data.

### `RetentionCurveOut`
Data points for retention curve visualization.

## Usage Examples

### Python/Backend
```python
from services.retention import calculate_overall_retention

# Get overall retention
result = calculate_overall_retention(db, days_ago=30)
print(f"D7 Retention: {result['d7_retention']}%")
```

### cURL
```bash
# Overall retention
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/analytics/retention

# Cohort retention (monthly)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/admin/analytics/retention/cohorts?period=month&limit=6"

# Retention curve (60 days)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/admin/analytics/retention/curve?days=60"
```

## Files

### Created
- `backend/services/retention.py` - Service implementation

### Modified
- `backend/schemas.py` - Response schemas
- `backend/main.py` - API endpoints

## Performance Notes

- Cohort calculations are O(users × cohorts × retention_days)
- Recommend caching for production use
- Index on `analytics_events(user_id, created_at)` recommended
- Limit cohort count to prevent long queries

## Testing

```bash
# Test overall retention
pytest tests/test_retention.py::test_overall_retention

# Test cohort retention
pytest tests/test_retention.py::test_cohort_retention

# Test retention curve
pytest tests/test_retention.py::test_retention_curve
```

---

**Quick Start**: `GET /api/v1/admin/analytics/retention` for overall D1/D7/D30 metrics!
