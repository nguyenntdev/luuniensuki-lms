# Analytics Funnel API Quick Reference

## Endpoints

### 1. List Available Funnels

```
GET /api/v1/admin/analytics/funnels
```

**Authentication**: Admin only

**Response**: Array of funnel metadata

```json
[
  {
    "funnel_type": "onboarding",
    "name": "Onboarding Funnel",
    "description": "User journey from first app open to first lesson completion",
    "stage_count": 5,
    "stages": ["App Opened", "Onboarding Started", "Goal Selected", "First Lesson Started", "First Lesson Completed"]
  },
  {
    "funnel_type": "lesson",
    "name": "Lesson Funnel",
    "description": "User journey through lesson content",
    "stage_count": 4,
    "stages": ["Lesson Viewed", "Lesson Started", "50% Progress", "Lesson Completed"]
  },
  {
    "funnel_type": "quiz",
    "name": "Quiz Funnel",
    "description": "User journey through quiz attempts",
    "stage_count": 3,
    "stages": ["Quiz Started", "Quiz Submitted", "Quiz Passed"]
  }
]
```

### 2. Get Funnel Data

```
GET /api/v1/admin/analytics/funnels/{funnel_type}
```

**Authentication**: Admin only

**Path Parameters**:
- `funnel_type`: One of "onboarding", "lesson", or "quiz"

**Query Parameters** (all optional):
- `start_date`: ISO 8601 datetime (e.g., "2024-01-01T00:00:00Z")
- `end_date`: ISO 8601 datetime (e.g., "2024-12-31T23:59:59Z")
- `cohort`: Cohort identifier (e.g., "2024-W01")

**Response**: Detailed funnel data with conversion metrics

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

## Curl Examples

### List all funnels
```bash
curl -X GET "http://localhost:8000/api/v1/admin/analytics/funnels" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Get onboarding funnel (all time)
```bash
curl -X GET "http://localhost:8000/api/v1/admin/analytics/funnels/onboarding" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Get lesson funnel for Q1 2024
```bash
curl -X GET "http://localhost:8000/api/v1/admin/analytics/funnels/lesson?start_date=2024-01-01T00:00:00Z&end_date=2024-03-31T23:59:59Z" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Get quiz funnel for specific cohort
```bash
curl -X GET "http://localhost:8000/api/v1/admin/analytics/funnels/quiz?cohort=2024-W01" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Funnel Definitions

### Onboarding Funnel
Tracks user activation from app open to first lesson completion.

| Stage | Event Name | Description |
|-------|------------|-------------|
| app_opened | app_opened | User opened the app |
| onboarding_started | onboarding_started | User began onboarding |
| goal_selected | onboarding_completed | User selected learning goal |
| first_lesson_started | first_lesson_started | User started first lesson |
| first_lesson_completed | lesson_completed | User completed first lesson |

### Lesson Funnel
Tracks user progression through lesson content.

| Stage | Event Name | Description |
|-------|------------|-------------|
| lesson_viewed | lesson_viewed | User viewed lesson |
| lesson_started | lesson_started | User started lesson |
| lesson_50_percent | lesson_time_spent | User reached 50% completion |
| lesson_completed | lesson_completed | User completed lesson |

### Quiz Funnel
Tracks user progression through quiz attempts.

| Stage | Event Name | Description |
|-------|------------|-------------|
| quiz_started | quiz_started | User started quiz |
| quiz_submitted | quiz_submitted | User submitted quiz |
| quiz_passed | quiz_passed | User passed quiz |

## Response Fields Explained

- **funnel_type**: Identifier for the funnel ("onboarding", "lesson", or "quiz")
- **funnel_name**: Display name of the funnel
- **description**: Explanation of what the funnel tracks
- **date_range**: Time period for the analysis (null values = all time)
- **cohort**: User cohort filter (null = all users)
- **total_users**: Number of users who entered the funnel (first stage count)
- **stages**: Array of stage data
  - **stage**: Stage identifier
  - **display_name**: Human-readable stage name
  - **count**: Number of unique users who reached this stage
  - **conversion_from_previous**: Percentage of users from previous stage who reached this stage
- **overall_conversion**: Percentage of users who completed the entire funnel (first to last stage)

