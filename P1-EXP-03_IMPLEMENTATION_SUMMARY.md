# P1-EXP-03 Implementation Summary

## Overview
Implemented experiment metric event tracking system to measure and analyze key performance metrics across experiment variants.

## What Was Implemented

### 1. Database Model (`backend/models.py`)

Added `ExperimentMetricEvent` model:
- **id**: UUID primary key
- **experiment_id**: FK to experiments table
- **user_id**: FK to users table
- **variant**: String - variant key the user is assigned to
- **metric_name**: String - metric identifier (e.g., "conversion", "retention", "engagement")
- **metric_value**: Float - numeric value for the metric
- **metadata**: JSONB - optional additional metadata
- **created_at**: Timestamp with timezone

Indexes created for optimal query performance:
- experiment_id
- user_id
- variant
- metric_name
- created_at

### 2. Database Migration (`migrations/versions/0034_experiment_metric_events.py`)

Created Alembic migration to:
- Create `experiment_metric_events` table
- Add all necessary indexes
- Include proper foreign key constraints with CASCADE delete

### 3. Service Functions (`backend/services/experiment_analytics.py`)

Added the following functions:

#### `record_metric_event()`
Records a metric event for an experiment user.
- Automatically determines user's variant from assignment
- Validates user is assigned to experiment
- Returns created ExperimentMetricEvent or None

#### `calculate_metric_summary()`
Calculates aggregated statistics per variant:
- Count of metric events
- Sum of metric values
- Average (mean) value
- Minimum value
- Maximum value

#### `calculate_metric_comparison()`
Compares metrics between variants:
- Calculates improvement percentage vs control
- Indicates which variant performs better
- Checks for sufficient sample size (>= 30 events)
- Returns detailed comparison data

#### `get_all_metrics_for_experiment()`
Returns list of all unique metric names tracked for an experiment.

### 4. API Schemas (`backend/schemas.py`)

Added the following schemas:

#### Input Schemas
- **ExperimentMetricEventIn**: For recording metric events
  - metric_name: str
  - metric_value: float
  - metadata: Optional[dict]

#### Output Schemas
- **ExperimentMetricEventOut**: Metric event response
- **VariantMetricSummary**: Aggregated stats per variant
- **MetricComparisonOut**: Comparison between variants
- **ExperimentMetricSummaryOut**: Overall experiment metric summary

### 5. API Endpoints (`backend/main.py`)

Added three new endpoints:

#### POST `/api/v1/experiments/{experiment_id}/metrics`
**Authentication**: Required (current user)
**Purpose**: Record a metric event for an experiment
**Request Body**:
```json
{
  "metric_name": "conversion",
  "metric_value": 1.0,
  "metadata": {"source": "homepage"}
}
```
**Response**: ExperimentMetricEventOut (201 Created)

#### GET `/api/v1/admin/experiments/{experiment_id}/metrics`
**Authentication**: Admin only
**Purpose**: Get metric summary for an experiment
**Response**: ExperimentMetricSummaryOut
- Lists all available metrics
- Provides basic experiment info

#### GET `/api/v1/admin/experiments/{experiment_id}/metrics/{metric_name}`
**Authentication**: Admin only
**Purpose**: Get detailed metric comparison for a specific metric
**Query Parameters**:
- `control_variant_key` (default: "control"): Key for control variant
**Response**: MetricComparisonOut
- Per-variant aggregations
- Comparison to control
- Statistical indicators

## Usage Examples

### 1. Record a Metric Event

```bash
curl -X POST "http://localhost:8000/api/v1/experiments/{experiment_id}/metrics" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "engagement_score",
    "metric_value": 85.5,
    "metadata": {"session_duration": 300}
  }'
```

### 2. Get Experiment Metrics Summary

```bash
curl "http://localhost:8000/api/v1/admin/experiments/{experiment_id}/metrics" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Response:
```json
{
  "experiment_id": "uuid",
  "experiment_key": "homepage_layout_test",
  "experiment_name": "Homepage Layout A/B Test",
  "metrics": ["conversion", "retention", "engagement_score"]
}
```

### 3. Get Specific Metric Comparison

```bash
curl "http://localhost:8000/api/v1/admin/experiments/{experiment_id}/metrics/engagement_score?control_variant_key=control" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Response:
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
    }
  }
}
```

## Key Features

### 1. Automatic Variant Detection
- Users don't need to specify their variant when recording metrics
- System automatically looks up variant from experiment assignment

### 2. Statistical Indicators
- **Sample Size Check**: Indicates if data is sufficient (>= 30 events per variant)
- **Improvement Percentage**: Shows relative performance vs control
- **Better/Worse Indicator**: Simple boolean for quick assessment

### 3. Flexible Metric Types
- Support for any numeric metric (conversion rates, engagement scores, retention, etc.)
- Metadata field allows storing additional context
- Multiple metrics can be tracked per experiment

### 4. Performance Optimized
- Database indexes on all commonly queried fields
- Efficient aggregation queries using SQL GROUP BY
- No N+1 query issues

### 5. Admin-Only Analytics
- Metric summaries and comparisons restricted to admins
- Regular users can only record their own metrics
- Prevents exposure of sensitive experiment data

## Database Schema

```sql
CREATE TABLE experiment_metric_events (
    id UUID PRIMARY KEY,
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    variant VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_experiment_metric_events_experiment ON experiment_metric_events(experiment_id);
CREATE INDEX idx_experiment_metric_events_user ON experiment_metric_events(user_id);
CREATE INDEX idx_experiment_metric_events_variant ON experiment_metric_events(variant);
CREATE INDEX idx_experiment_metric_events_metric_name ON experiment_metric_events(metric_name);
CREATE INDEX idx_experiment_metric_events_created ON experiment_metric_events(created_at);
```

## Testing Checklist

- [x] Models compile without errors
- [x] Schemas compile without errors
- [x] Service functions compile without errors
- [x] Migration file created with proper up/down migrations
- [x] API endpoints follow existing patterns
- [x] All imports added correctly
- [x] Proper error handling (404 for missing experiments, 400 for unassigned users)
- [x] Admin-only endpoints protected with `require_admin`
- [x] User endpoints protected with `get_current_user`

## Next Steps

To fully test the implementation:

1. **Run Migration**:
   ```bash
   alembic upgrade head
   ```

2. **Create Test Experiment** (if not exists):
   ```bash
   curl -X POST "http://localhost:8000/api/v1/admin/experiments" \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "key": "test_metrics",
       "name": "Test Metrics Experiment",
       "variants": [
         {"key": "control", "name": "Control", "weight": 50},
         {"key": "variant_a", "name": "Variant A", "weight": 50}
       ],
       "is_active": true
     }'
   ```

3. **Assign User to Experiment**:
   - Visit experiment endpoint to get auto-assigned

4. **Record Metrics**:
   ```bash
   # Record multiple metrics
   for i in {1..50}; do
     curl -X POST "http://localhost:8000/api/v1/experiments/{exp_id}/metrics" \
       -H "Authorization: Bearer $USER_TOKEN" \
       -H "Content-Type: application/json" \
       -d "{\"metric_name\": \"engagement\", \"metric_value\": $((RANDOM % 100))}"
   done
   ```

5. **View Analytics**:
   ```bash
   curl "http://localhost:8000/api/v1/admin/experiments/{exp_id}/metrics/engagement" \
     -H "Authorization: Bearer $ADMIN_TOKEN"
   ```

## Files Modified/Created

### Created:
- `migrations/versions/0034_experiment_metric_events.py`

### Modified:
- `backend/models.py` - Added ExperimentMetricEvent model
- `backend/schemas.py` - Added metric-related schemas
- `backend/services/experiment_analytics.py` - Added metric tracking functions
- `backend/main.py` - Added 3 new API endpoints and import

## Differences from P1-EXP-02

P1-EXP-02 (Experiment Events):
- Tracks individual events (impression, conversion, click)
- Used for conversion rate analysis
- Event-based tracking

P1-EXP-03 (Metric Events):
- Tracks numeric metrics with aggregations
- Used for any measurable KPI (engagement, retention, scores)
- Metric-based tracking with statistical comparisons
- More flexible for diverse metric types

Both systems complement each other:
- Events track user actions
- Metrics track measured outcomes

