# P0-ANA-01: Event Taxonomy Implementation Summary

## Overview
This implementation defines a comprehensive event taxonomy for the Luuniensuki LMS analytics system, organized by category (activation, lesson, quiz, streak, discovery, engagement) with proper validation and schema definitions.

## Changes Made

### 1. New File: `backend/services/analytics.py`
Created a comprehensive analytics service module with:

#### Event Taxonomy Constants
- **EventCategory**: Categories for organizing events
  - ACTIVATION, LESSON, QUIZ, STREAK, DISCOVERY, ENGAGEMENT

- **EventType**: All event type constants organized by category
  - **Activation**: app_opened, onboarding_started, onboarding_completed, first_lesson_started, first_quiz_completed
  - **Lesson**: lesson_viewed, lesson_started, lesson_completed, lesson_time_spent
  - **Quiz**: quiz_started, quiz_submitted, quiz_passed, quiz_failed, question_answered
  - **Streak**: streak_continued, streak_broken, streak_freeze_used, streak_milestone_reached
  - **Discovery**: motif_discovered, motif_learned, motif_mastered
  - **Engagement**: session_started, session_ended, daily_mission_completed, badge_earned

- **EVENT_CATEGORY_MAP**: Dictionary mapping event types to their categories

#### Event Schema Definitions (Pydantic Models)
- `BaseEventPayload`: Base payload with common fields (source, timestamp)
- `ActivationEventPayload`: For activation events (screen, step)
- `LessonEventPayload`: For lesson events (motif_id, urn_id, duration_seconds, completion_percentage)
- `QuizEventPayload`: For quiz events (motif_id, urn_id, score, max_score, percentage, passed, time_taken_seconds, question_id, answer, correct)
- `StreakEventPayload`: For streak events (current_streak, previous_streak, milestone, freeze_count)
- `DiscoveryEventPayload`: For discovery events (motif_id, urn_id, status, xp_awarded)
- `EngagementEventPayload`: For engagement events (session_id, duration_seconds, badge_slug, badge_name, mission_type, xp_awarded)
- `DeviceInfo`: Device metadata schema (platform, os_version, app_version, device_model, screen_width, screen_height, language)

#### Utility Functions
- `get_event_category(event_name: str)`: Returns the category for an event type
- `validate_event_payload(event_name: str, payload: Dict)`: Validates and normalizes event payload based on type
- `create_event_record(...)`: Creates a validated event record for database insertion

### 2. Updated: `backend/models.py`
Extended the `AnalyticsEvent` model with new fields:

```python
class AnalyticsEvent(Base):
    # Existing fields
    id: UUID
    user_id: UUID
    event_name: str
    path: Optional[str]
    payload: Optional[Any]
    created_at: datetime
    
    # NEW FIELDS
    session_id: Optional[UUID]      # For session tracking
    cohort: Optional[str]            # For user cohort tracking (e.g., "2024-W01")
    event_category: Optional[str]    # Auto-categorized from event_name
    device_info: Optional[Any]       # JSONB for device metadata
```

Added new indexes for performance:
- `idx_analytics_session` on `session_id`
- `idx_analytics_category` on `event_category`
- `idx_analytics_cohort` on `cohort`

### 3. Updated: `backend/schemas.py`
Enhanced analytics schemas:

```python
class AnalyticsEventIn(BaseModel):
    name: str                        # Event name (validated, max 100 chars)
    payload: Optional[dict]          # Event payload
    path: Optional[str]              # URL path or screen name
    session_id: Optional[UUID]       # NEW: Session tracking
    cohort: Optional[str]            # NEW: User cohort
    device_info: Optional[dict]      # NEW: Device metadata

class AnalyticsEventOut(BaseModel):
    id: UUID
    name: str
    payload: dict
    path: Optional[str]
    session_id: Optional[UUID]       # NEW
    cohort: Optional[str]            # NEW
    event_category: Optional[str]    # NEW: Auto-populated
    device_info: Optional[dict]      # NEW
    created_at: datetime
```

### 4. Updated: `backend/main.py`

Modified analytics endpoints to use the new taxonomy validation:

#### Updated `_record_analytics_event()` helper function:
```python
def _record_analytics_event(
    session: Session,
    *,
    user_id: UUID,
    name: str,
    payload: Optional[dict[str, Any]] = None,
    path: Optional[str] = None,
    session_id: Optional[UUID] = None,      # NEW
    cohort: Optional[str] = None,           # NEW
    device_info: Optional[dict] = None,     # NEW
) -> None:
    # Now uses services.analytics.create_event_record for validation
```

#### Updated analytics endpoint schema:
```python
class AnalyticsEventIn(BaseModel):
    name: str
    payload: Optional[dict]
    path: Optional[str]
    session_id: Optional[UUID]      # NEW
    cohort: Optional[str]           # NEW
    device_info: Optional[dict]     # NEW
```

#### Updated `POST /api/v1/analytics/events` endpoint:
- Now imports and uses `services.analytics.create_event_record`
- Validates event payloads based on event category
- Auto-populates `event_category` field
- Validates device_info against DeviceInfo schema

### 5. New Migration: `migrations/versions/0012_analytics_taxonomy.py`

Database migration to add new columns and indexes:

```python
# New Columns:
- session_id: UUID (nullable)
- cohort: VARCHAR(50) (nullable)
- event_category: VARCHAR(50) (nullable)
- device_info: JSONB (nullable)

# New Indexes:
- idx_analytics_session on session_id
- idx_analytics_category on event_category
- idx_analytics_cohort on cohort
```

## Usage Examples

### 1. Recording an Activation Event (Backend)
```python
from services.analytics import create_event_record

event_data = create_event_record(
    user_id=user.id,
    event_name="onboarding_completed",
    payload={
        "source": "mobile",
        "step": 3,
    },
    cohort="2024-W01",
    device_info={
        "platform": "ios",
        "app_version": "1.5.0",
    }
)
db.add(AnalyticsEvent(**event_data))
```

### 2. Recording a Lesson Event
```python
event_data = create_event_record(
    user_id=user.id,
    event_name="lesson_completed",
    payload={
        "motif_id": str(motif.id),
        "urn_id": str(urn.id),
        "duration_seconds": 120,
    },
    session_id=session_id,
)
```

### 3. Recording a Quiz Event
```python
event_data = create_event_record(
    user_id=user.id,
    event_name="quiz_passed",
    payload={
        "motif_id": str(motif.id),
        "score": 8,
        "max_score": 10,
        "percentage": 80,
        "passed": True,
    },
)
```

### 4. From Mobile/Frontend (API Call)
```javascript
POST /api/v1/analytics/events
{
  "events": [
    {
      "name": "lesson_started",
      "payload": {
        "motif_id": "uuid-here",
        "source": "mobile"
      },
      "path": "/lesson/uuid",
      "session_id": "session-uuid",
      "cohort": "2024-W01",
      "device_info": {
        "platform": "android",
        "app_version": "1.5.0",
        "os_version": "14"
      }
    }
  ]
}
```

## Benefits

1. **Type Safety**: Pydantic models ensure payload validation
2. **Auto-categorization**: Events are automatically categorized
3. **Cohort Analysis**: Track user cohorts for retention analysis
4. **Session Tracking**: Link events to user sessions
5. **Device Insights**: Understand platform-specific behavior
6. **Query Performance**: Indexed fields for fast analytics queries
7. **Backwards Compatible**: Optional fields don't break existing code

## Migration Instructions

To apply the database migration:
```bash
cd /path/to/luuniensuki-lms
alembic upgrade head
```

## Testing

All Python files compile successfully:
- ✅ `backend/services/analytics.py`
- ✅ `backend/models.py`
- ✅ `backend/schemas.py`
- ✅ `backend/main.py`
- ✅ `migrations/versions/0012_analytics_taxonomy.py`

## Next Steps

1. Run database migration: `alembic upgrade head`
2. Update mobile app to send new analytics fields
3. Update analytics dashboards to use event_category
4. Create cohort analysis queries
5. Build session-based analytics reports


