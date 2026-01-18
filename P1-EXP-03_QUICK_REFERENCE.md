# P1-EXP-03 Quick Reference Guide

## Overview
Track experiment metric events to measure and analyze key performance metrics across variants.

## API Endpoints

### 1. Record Metric Event (User)
```
POST /api/v1/experiments/{experiment_id}/metrics
```

**Authentication**: Required (any authenticated user assigned to experiment)

**Request Body**:
```json
{
  "metric_name": "conversion",
  "metric_value": 1.0,
  "metadata": {"source": "homepage", "time_on_page": 45}
}
```

**Common Metric Names**:
- `conversion` - Binary conversion (0 or 1)
- `retention` - Retention rate (0-100)
- `engagement_score` - Engagement metrics (0-100)
- `session_duration` - Time spent in seconds
- `clicks` - Number of clicks
- `revenue` - Revenue generated

**Response** (201 Created):
```json
{
  "id": "uuid",
  "experiment_id": "uuid",
  "user_id": "uuid",
  "variant": "variant_a",
  "metric_name": "conversion",
  "metric_value": 1.0,
  "metadata": {"source": "homepage"},
  "created_at": "2025-01-18T10:30:00Z"
}
```

**Error Responses**:
- `404`: Experiment not found
- `400`: User not assigned to experiment

---

### 2. Get Metrics Summary (Admin)
```
GET /api/v1/admin/experiments/{experiment_id}/metrics
```

**Authentication**: Admin only

**Response**:
```json
{
  "experiment_id": "uuid",
  "experiment_key": "homepage_test",
  "experiment_name": "Homepage Layout Test",
  "metrics": ["conversion", "engagement_score", "retention"]
}
```

---

### 3. Get Metric Comparison (Admin)
```
GET /api/v1/admin/experiments/{experiment_id}/metrics/{metric_name}
  ?control_variant_key=control
```

**Authentication**: Admin only

**Query Parameters**:
- `control_variant_key` (optional): Control variant key for comparison (default: "control")

**Response**:
```json
{
  "metric_name": "engagement_score",
  "control_variant": "control",
  "variants": {
    "control": {
      "count": 150,
      "sum": 12750.5,
      "avg": 85.0,
      "min": 20.0,
      "max": 100.0,
      "improvement_pct": 0.0,
      "is_better": false,
      "has_sufficient_data": true
    },
    "variant_a": {
      "count": 145,
      "sum": 13225.75,
      "avg": 91.2,
      "min": 25.0,
      "max": 100.0,
      "improvement_pct": 7.29,
      "is_better": true,
      "has_sufficient_data": true
    },
    "variant_b": {
      "count": 48,
      "sum": 3850.0,
      "avg": 80.2,
      "min": 15.0,
      "max": 98.0,
      "improvement_pct": -5.65,
      "is_better": false,
      "has_sufficient_data": true
    }
  }
}
```

**Metric Fields**:
- `count`: Number of metric events recorded
- `sum`: Total sum of all metric values
- `avg`: Average (mean) metric value
- `min`: Minimum metric value observed
- `max`: Maximum metric value observed
- `improvement_pct`: Percentage improvement vs control (only for non-control variants)
- `is_better`: Boolean indicating if this variant outperforms control
- `has_sufficient_data`: Boolean indicating if sample size >= 30 (statistical significance threshold)

---

## Usage Examples

### Track Conversion
```bash
curl -X POST "http://localhost:8000/api/v1/experiments/uuid/metrics" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "conversion",
    "metric_value": 1.0
  }'
```

### Track Engagement Score
```bash
curl -X POST "http://localhost:8000/api/v1/experiments/uuid/metrics" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "engagement_score",
    "metric_value": 87.5,
    "metadata": {"session_duration": 450, "interactions": 12}
  }'
```

### View Metrics List
```bash
curl "http://localhost:8000/api/v1/admin/experiments/uuid/metrics" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Analyze Specific Metric
```bash
curl "http://localhost:8000/api/v1/admin/experiments/uuid/metrics/engagement_score?control_variant_key=control" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Best Practices

### 1. Metric Naming Conventions
- Use lowercase with underscores: `engagement_score`, `session_duration`
- Be consistent across experiments
- Use descriptive names that indicate what is measured

### 2. Metric Value Ranges
- **Binary metrics** (conversion): Use 0 or 1
- **Percentages**: Use 0-100 scale
- **Time metrics**: Use seconds for consistency
- **Counts**: Use natural numbers (1, 2, 3, ...)
- **Scores**: Define and document your scale (e.g., 0-100)

### 3. When to Record Metrics
- Record metrics when the measured action completes
- For engagement: Record at session end or periodic intervals
- For conversion: Record immediately upon conversion
- For retention: Record based on time-based criteria

### 4. Using Metadata
Store additional context that might be useful later:
```json
{
  "metric_name": "conversion",
  "metric_value": 1.0,
  "metadata": {
    "source": "email_campaign",
    "campaign_id": "summer_2025",
    "device": "mobile",
    "time_to_convert_seconds": 120
  }
}
```

### 5. Statistical Significance
- Ensure `has_sufficient_data: true` before making decisions
- Minimum recommended sample size: 30 events per variant
- Higher sample sizes provide more reliable results
- Consider using P1-EXP-02 chi-square tests for conversion metrics

---

## Data Model

### ExperimentMetricEvent
```typescript
{
  id: UUID
  experiment_id: UUID (FK to experiments)
  user_id: UUID (FK to users)
  variant: string (variant key)
  metric_name: string (e.g., "conversion", "engagement")
  metric_value: float (numeric value)
  metadata: object | null (JSONB)
  created_at: datetime
}
```

### Indexes
Optimized for fast querying:
- `experiment_id` - For filtering by experiment
- `user_id` - For user-specific queries
- `variant` - For per-variant aggregations
- `metric_name` - For metric-specific queries
- `created_at` - For time-based analysis

---

## Complementary with P1-EXP-02

**P1-EXP-02 (Event Tracking)**:
- Track discrete events (impressions, clicks, conversions)
- Used for conversion rate calculations
- Chi-square statistical tests

**P1-EXP-03 (Metric Tracking)**:
- Track numeric metrics with aggregations
- Used for any measurable KPI
- Statistical comparisons based on averages

**Use Both Together**:
```javascript
// Track impression event (P1-EXP-02)
POST /api/v1/experiments/{key}/events
{
  "event_type": "impression",
  "event_name": "viewed_pricing_page"
}

// Track engagement metric (P1-EXP-03)
POST /api/v1/experiments/{id}/metrics
{
  "metric_name": "time_on_pricing_page",
  "metric_value": 45.3
}

// Track conversion event (P1-EXP-02)
POST /api/v1/experiments/{key}/events
{
  "event_type": "conversion",
  "event_name": "purchased_subscription"
}

// Track revenue metric (P1-EXP-03)
POST /api/v1/experiments/{id}/metrics
{
  "metric_name": "revenue",
  "metric_value": 49.99
}
```

