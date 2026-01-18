# Analytics Funnel Visualization - P0-ANA-02

## Overview

This implementation provides funnel visualization endpoints for analyzing user journeys through the LMS. It tracks conversion rates across different stages of onboarding, lesson completion, and quiz attempts.

## Implementation Summary

### 1. Analytics Funnel Service (`backend/services/analytics_funnels.py`)

**Purpose**: Core business logic for calculating funnel metrics from analytics events.

**Key Components**:

- **FUNNEL_DEFINITIONS**: Dictionary defining three funnel types:
  - `onboarding`: User activation journey (5 stages)
  - `lesson`: Lesson engagement journey (4 stages)
  - `quiz`: Quiz completion journey (3 stages)

- **Functions**:
  - `_count_users_in_stage()`: Counts unique users who reached a specific funnel stage
  - `calculate_funnel_data()`: Calculates complete funnel metrics with conversion rates
  - `list_available_funnels()`: Returns metadata about available funnels

### 2. Schemas (`backend/schemas.py`)

**New Pydantic Models**:

- `FunnelStageOut`: Output schema for individual funnel stages
  - Fields: stage, display_name, count, conversion_from_previous

- `FunnelDataOut`: Output schema for complete funnel data
  - Fields: funnel_type, funnel_name, description, date_range, cohort, total_users, stages, overall_conversion

- `FunnelListItemOut`: Output schema for available funnel types
  - Fields: funnel_type, name, description, stage_count, stages

### 3. API Endpoints (`backend/main.py`)

**New Admin Endpoints**:

#### GET `/api/v1/admin/analytics/funnels`
- **Purpose**: List all available funnel types
- **Access**: Admin only
- **Response**: List of `FunnelListItemOut`
- **Example Response**:
```json
[
  {
    "funnel_type": "onboarding",
    "name": "Onboarding Funnel",
    "description": "User journey from first app open to first lesson completion",
    "stage_count": 5,
    "stages": [
      "App Opened",
      "Onboarding Started",
      "Goal Selected",
      "First Lesson Started",
      "First Lesson Completed"
    ]
  }
]
```

#### GET `/api/v1/admin/analytics/funnels/{funnel_type}`
- **Purpose**: Get detailed funnel data with conversion rates
- **Access**: Admin only
- **Path Parameters**:
  - `funnel_type`: One of "onboarding", "lesson", or "quiz"
- **Query Parameters**:
  - `start_date` (optional): Filter events after this date
  - `end_date` (optional): Filter events before this date
  - `cohort` (optional): Filter by cohort identifier (e.g., "2024-W01")
- **Response**: `FunnelDataOut`
- **Example Response**:
```json
{
  "funnel_type": "onboarding",
  "funnel_name": "Onboarding Funnel",
  "description": "User journey from first app open to first lesson completion",
  "date_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-12-31T23:59:59Z"
  },
  "cohort": null,
  "total_users": 1000,
  "stages": [
    {
      "stage": "app_opened",
      "display_name": "App Opened",
      "count": 1000,
      "conversion_from_previous": 100.0
    },
    {
      "stage": "onboarding_started",
      "display_name": "Onboarding Started",
      "count": 850,
      "conversion_from_previous": 85.0
    },
    {
      "stage": "goal_selected",
      "display_name": "Goal Selected",
      "count": 750,
      "conversion_from_previous": 88.24
    },
    {
      "stage": "first_lesson_started",
      "display_name": "First Lesson Started",
      "count": 600,
      "conversion_from_previous": 80.0
    },
    {
      "stage": "first_lesson_completed",
      "display_name": "First Lesson Completed",
      "count": 450,
      "conversion_from_previous": 75.0
    }
  ],
  "overall_conversion": 45.0
}
```

## Funnel Definitions

### Onboarding Funnel
Tracks user activation from first app open to completing their first lesson.

**Stages**:
1. `app_opened` → App Opened
2. `onboarding_started` → Onboarding Started
3. `goal_selected` → Goal Selected (onboarding_completed event)
4. `first_lesson_started` → First Lesson Started
5. `first_lesson_completed` → First Lesson Completed

### Lesson Funnel
Tracks user engagement through lesson content.

**Stages**:
1. `lesson_viewed` → Lesson Viewed
2. `lesson_started` → Lesson Started
3. `lesson_50_percent` → 50% Progress (lesson_time_spent with completion_percentage >= 50)
4. `lesson_completed` → Lesson Completed

### Quiz Funnel
Tracks user progression through quiz attempts.

**Stages**:
1. `quiz_started` → Quiz Started
2. `quiz_submitted` → Quiz Submitted
3. `quiz_passed` → Quiz Passed

## Usage Examples

### List Available Funnels
```bash
curl -X GET "http://localhost:8000/api/v1/admin/analytics/funnels" \
  -H "Authorization: Bearer <admin_token>"
```

### Get Onboarding Funnel Data
```bash
curl -X GET "http://localhost:8000/api/v1/admin/analytics/funnels/onboarding" \
  -H "Authorization: Bearer <admin_token>"
```

### Get Lesson Funnel for Specific Date Range
```bash
curl -X GET "http://localhost:8000/api/v1/admin/analytics/funnels/lesson?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z" \
  -H "Authorization: Bearer <admin_token>"
```

### Get Quiz Funnel for Specific Cohort
```bash
curl -X GET "http://localhost:8000/api/v1/admin/analytics/funnels/quiz?cohort=2024-W01" \
  -H "Authorization: Bearer <admin_token>"
```

## Implementation Notes

1. **Admin Only Access**: All funnel endpoints require admin role authentication
2. **Event-Based Tracking**: Funnels are calculated from `AnalyticsEvent` records
3. **Unique User Counting**: Each stage counts distinct users who reached that stage
4. **Conversion Rates**: Calculated as percentage from previous stage
5. **Overall Conversion**: Percentage from first to last stage
6. **Date Filtering**: Optional start_date and end_date for time-bounded analysis
7. **Cohort Filtering**: Optional cohort parameter for cohort analysis

## Testing

The implementation has been validated with unit tests covering:
- Funnel definition structure
- Stage configuration validation
- Function signatures and return types

## Files Modified

1. `backend/services/analytics_funnels.py` - New file (251 lines)
2. `backend/schemas.py` - Added 3 new schemas (lines 1226-1258)
3. `backend/main.py` - Added 2 new endpoints (lines 9979-10029)

## Dependencies

- Existing analytics event infrastructure
- SQLAlchemy for database queries
- FastAPI for API endpoints
- Pydantic for schema validation

