# Analytics Event Taxonomy - Quick Reference Guide

## Event Categories

| Category | Description | Use Case |
|----------|-------------|----------|
| `activation` | User onboarding and first-time actions | Track new user journey |
| `lesson` | Lesson viewing and learning activities | Measure content engagement |
| `quiz` | Quiz taking and assessment activities | Track learning outcomes |
| `streak` | Daily streak and consistency tracking | Monitor user retention |
| `discovery` | Motif discovery and mastery | Track learning progression |
| `engagement` | General engagement activities | Measure overall activity |

## Event Types Reference

### Activation Events
```python
from services.analytics import EventType

EventType.APP_OPENED              # User opens the app
EventType.ONBOARDING_STARTED      # User begins onboarding flow
EventType.ONBOARDING_COMPLETED    # User completes onboarding
EventType.FIRST_LESSON_STARTED    # User starts their first lesson
EventType.FIRST_QUIZ_COMPLETED    # User completes their first quiz
```

### Lesson Events
```python
EventType.LESSON_VIEWED           # User views a lesson
EventType.LESSON_STARTED          # User starts a lesson
EventType.LESSON_COMPLETED        # User completes a lesson
EventType.LESSON_TIME_SPENT       # Time spent on lesson
```

### Quiz Events
```python
EventType.QUIZ_STARTED            # User starts a quiz
EventType.QUIZ_SUBMITTED          # User submits quiz answers
EventType.QUIZ_PASSED             # User passes a quiz
EventType.QUIZ_FAILED             # User fails a quiz
EventType.QUESTION_ANSWERED       # User answers individual question
```

### Streak Events
```python
EventType.STREAK_CONTINUED        # User maintains daily streak
EventType.STREAK_BROKEN           # User's streak is broken
EventType.STREAK_FREEZE_USED      # User uses a streak freeze
EventType.STREAK_MILESTONE_REACHED # User hits streak milestone (7, 30, 100 days)
```

### Discovery Events
```python
EventType.MOTIF_DISCOVERED        # User discovers a new motif
EventType.MOTIF_LEARNED           # User learns a motif (completes lesson)
EventType.MOTIF_MASTERED          # User masters a motif (passes quiz)
```

### Engagement Events
```python
EventType.SESSION_STARTED         # User starts a session
EventType.SESSION_ENDED           # User ends a session
EventType.DAILY_MISSION_COMPLETED # User completes daily mission
EventType.BADGE_EARNED            # User earns a badge
```

## Common Payload Fields by Category

### Activation Payloads
```python
{
    "source": "mobile",      # "mobile", "web", "server"
    "screen": "welcome",     # Screen/page name
    "step": 1,              # Onboarding step number
}
```

### Lesson Payloads
```python
{
    "motif_id": "uuid",            # Motif UUID
    "urn_id": "uuid",              # Urn UUID
    "duration_seconds": 120,       # Time spent
    "completion_percentage": 100.0, # Progress percentage
    "source": "mobile",
}
```

### Quiz Payloads
```python
{
    "motif_id": "uuid",
    "urn_id": "uuid",
    "score": 8,
    "max_score": 10,
    "percentage": 80,
    "passed": True,
    "time_taken_seconds": 45,
    
    # For question_answered event:
    "question_id": "uuid",
    "answer": "...",
    "correct": True,
}
```

### Streak Payloads
```python
{
    "current_streak": 7,
    "previous_streak": 6,
    "milestone": 7,           # For milestone events
    "freeze_count": 2,        # Remaining freezes
}
```

### Discovery Payloads
```python
{
    "motif_id": "uuid",
    "urn_id": "uuid",
    "status": "mastered",    # "discovered", "learned", "mastered"
    "xp_awarded": 100,
}
```

### Engagement Payloads
```python
{
    "session_id": "uuid",
    "duration_seconds": 600,
    "badge_slug": "first_lesson",
    "badge_name": "First Steps",
    "mission_type": "daily_login",
    "xp_awarded": 50,
}
```

## Device Info Fields
```python
{
    "platform": "ios",           # "ios", "android", "web"
    "os_version": "17.2",
    "app_version": "1.5.0",
    "device_model": "iPhone 15",
    "screen_width": 1170,
    "screen_height": 2532,
    "language": "en",
}
```

## Code Examples

### Backend: Record Event with Full Context
```python
from services.analytics import create_event_record, EventType
from backend.models import AnalyticsEvent

# Create and save event
event_data = create_event_record(
    user_id=user.id,
    event_name=EventType.LESSON_COMPLETED,
    payload={
        "motif_id": str(motif.id),
        "urn_id": str(urn.id),
        "duration_seconds": 180,
        "source": "mobile",
    },
    path="/lesson/uuid",
    session_id=session_uuid,
    cohort="2024-W03",
    device_info={
        "platform": "ios",
        "app_version": "1.5.0",
    }
)

db.add(AnalyticsEvent(**event_data))
db.commit()
```

### Frontend: Send Analytics Events
```javascript
// Single event
await logAnalyticsEvent({
  name: 'lesson_started',
  payload: {
    motif_id: motifId,
    source: 'web'
  },
  path: window.location.pathname,
  session_id: sessionId,
  cohort: '2024-W03',
  device_info: {
    platform: 'web',
    screen_width: window.screen.width,
    screen_height: window.screen.height,
  }
});

// Batch events
await logAnalyticsEvents({
  events: [
    {
      name: 'session_started',
      session_id: sessionId,
      cohort: userCohort,
    },
    {
      name: 'lesson_viewed',
      payload: { motif_id: motifId },
      session_id: sessionId,
    }
  ]
});
```

## Querying Analytics Data

### Get events by category
```python
from sqlalchemy import select
from backend.models import AnalyticsEvent

# Get all lesson events
lesson_events = db.execute(
    select(AnalyticsEvent)
    .where(AnalyticsEvent.event_category == 'lesson')
).scalars().all()
```

### Cohort analysis
```python
# Get events for a specific cohort
cohort_events = db.execute(
    select(AnalyticsEvent)
    .where(AnalyticsEvent.cohort == '2024-W01')
).scalars().all()
```

### Session-based analytics
```python
# Get all events in a session
session_events = db.execute(
    select(AnalyticsEvent)
    .where(AnalyticsEvent.session_id == session_uuid)
    .order_by(AnalyticsEvent.created_at)
).scalars().all()
```

## Best Practices

1. **Always specify source**: Include `"source": "mobile"/"web"/"server"` in payload
2. **Use event constants**: Import from `services.analytics.EventType` instead of hardcoding strings
3. **Include session_id**: Link related events together for session analysis
4. **Set cohort on signup**: Assign users to cohorts (e.g., "2024-W01") for retention tracking
5. **Validate payloads**: The system auto-validates, but include expected fields for better data quality
6. **Track device info**: Helps identify platform-specific issues
7. **Use timestamps**: Include client-side timestamp in payload for accuracy

## Migration Status

- ✅ Database schema updated
- ✅ Models updated with new fields
- ✅ API endpoints support new fields
- ✅ Event taxonomy defined
- ✅ Validation schemas created
- ⏳ Run migration: `alembic upgrade head`
- ⏳ Update mobile app to send new fields
- ⏳ Update analytics dashboards

