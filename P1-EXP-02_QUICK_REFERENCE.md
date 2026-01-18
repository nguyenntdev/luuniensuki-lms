# P1-EXP-02 Quick Reference Guide

## Overview
Track experiment conversion events and analyze A/B test results with statistical significance.

## API Endpoints

### 1. Track Experiment Event (User)
```
POST /api/v1/experiments/{experiment_key}/events
```

**Request Body**:
```json
{
  "event_type": "conversion",
  "event_name": "completed_onboarding",
  "event_value": 1.0,
  "metadata": {"time_spent_seconds": 120}
}
```

**Event Types**: `impression`, `conversion`, `click`, `custom`

### 2. Get Experiment Results (Admin)
```
GET /api/v1/admin/experiments/{experiment_id}/results
  ?conversion_event_name=completed_onboarding
  &control_variant_key=control
  &significance_threshold=0.05
```

**Response**: Per-variant metrics, p-values, winner

### 3. List Experiment Events (Admin)
```
GET /api/v1/admin/experiments/{experiment_id}/events
  ?event_type=conversion
  &event_name=completed_onboarding
  &page=1
  &page_size=100
```

## Key Functions (backend/services/experiment_analytics.py)

| Function | Purpose |
|----------|---------|
| `track_experiment_event()` | Record an event for user's experiment assignment |
| `calculate_conversion_rates()` | Calculate conversion rate per variant |
| `calculate_chi_square_test()` | Statistical significance test |
| `generate_experiment_report()` | Complete analysis with winner |
| `get_experiment_events()` | Query events with filtering |

## Database Schema

### ExperimentEvent Table
- **id**: UUID primary key
- **experiment_id**: FK to experiments
- **user_id**: FK to users
- **assignment_id**: FK to user_experiment_assignments
- **event_type**: impression | conversion | click | custom
- **event_name**: Specific event identifier
- **event_value**: Optional numeric value
- **metadata**: JSONB for additional data
- **created_at**: Timestamp

### Indexes
- experiment_id, user_id, assignment_id, event_type, created_at

## Statistical Analysis

### Metrics
- **Impressions**: Number of users assigned to variant
- **Conversions**: Distinct users who triggered conversion event
- **Conversion Rate**: (conversions / impressions) × 100
- **Improvement**: % increase over control variant
- **P-Value**: Statistical significance (< 0.05 = significant)
- **Chi-Square**: Test statistic

### Winner Determination
A variant wins if:
1. Conversion rate > control conversion rate
2. P-value < significance threshold (default 0.05)

## Code Examples

### Track Event (Frontend/Mobile)
```typescript
const trackConversion = async (experimentKey: string) => {
  await api.post(`/api/v1/experiments/${experimentKey}/events`, {
    event_type: "conversion",
    event_name: "completed_lesson",
    event_value: 1.0,
    metadata: { lesson_id: lessonId }
  });
};
```

### Get Results (Admin Dashboard)
```typescript
const getResults = async (experimentId: string) => {
  const response = await api.get(
    `/api/v1/admin/experiments/${experimentId}/results`,
    {
      params: {
        conversion_event_name: "completed_lesson",
        control_variant_key: "control"
      }
    }
  );
  return response.data;
};
```

### Python Service Usage
```python
from backend.services import experiment_analytics

# Track event
event = experiment_analytics.track_experiment_event(
    db=db,
    experiment_key="onboarding_test",
    user_id=user.id,
    event_type="conversion",
    event_name="signup_completed",
)

# Generate report
report = experiment_analytics.generate_experiment_report(
    db=db,
    experiment_id=experiment.id,
    conversion_event_name="signup_completed",
    control_variant_key="control",
    significance_threshold=0.05,
)

if report["is_significant"] and report["winner"]:
    print(f"Winner: {report['winner']}")
```

## Migration

```bash
alembic upgrade head
```

## Files Modified/Created

| File | Status | Lines |
|------|--------|-------|
| `backend/models.py` | Modified | +48 |
| `backend/services/experiment_analytics.py` | Created | 392 |
| `backend/schemas.py` | Modified | +70 |
| `backend/main.py` | Modified | +179 |
| `migrations/versions/0033_*.py` | Created | 132 |

## Testing

### Basic Flow Test
1. Create experiment (admin)
2. User gets assigned to variant
3. Track impression event
4. User completes goal → track conversion
5. View results (admin)
6. Check if winner determined

### Statistical Test
- Create experiment with 2 variants
- Track 1000+ events per variant
- Verify chi-square p-value calculation
- Confirm winner only when p < 0.05

## Common Patterns

### Onboarding Experiment
```python
# Event names
- impression: "saw_onboarding"
- conversion: "completed_onboarding"
- click: "clicked_skip_button"
```

### Feature Adoption
```python
# Event names
- impression: "saw_new_feature"
- conversion: "used_new_feature"
- custom: "feature_interaction"
```

### Purchase Funnel
```python
# Event names
- impression: "viewed_pricing"
- click: "clicked_buy_button"
- conversion: "completed_purchase"
```

## Best Practices

1. **Event Naming**: Use descriptive, consistent names (snake_case)
2. **Sample Size**: Wait for 100+ conversions per variant before analyzing
3. **Significance Threshold**: Use 0.05 for 95% confidence
4. **Multiple Events**: Track multiple conversion events for comprehensive analysis
5. **Metadata**: Store contextual data in metadata field
6. **Deduplication**: System automatically deduplicates conversions per user

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Event not tracked | Check user is assigned to experiment |
| No winner despite difference | Increase sample size or lower threshold |
| P-value always 1.0 | No conversions recorded, check event_name |
| Wrong conversion rate | Verify event_name matches exactly |

## Related Documentation

- P1-EXP-01_QUICK_REFERENCE.md - Experiment setup
- P1-EXP-02_IMPLEMENTATION.md - Full implementation details

