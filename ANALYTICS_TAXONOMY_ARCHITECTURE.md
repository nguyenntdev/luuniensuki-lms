# Analytics Event Taxonomy - Visual Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Analytics Event System                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐
│  Mobile App     │      │   Web Frontend   │      │   Backend   │
│  (React Native) │      │   (Next.js)      │      │   (FastAPI) │
└────────┬────────┘      └────────┬─────────┘      └──────┬──────┘
         │                        │                       │
         │  POST /api/v1/analytics/events                │
         └────────────────────────┴───────────────────────┤
                                                          │
                         ┌────────────────────────────────▼───────┐
                         │  Analytics Endpoint                    │
                         │  (main.py)                             │
                         │  - Receives event batch                │
                         │  - Validates schema                    │
                         └────────────────┬───────────────────────┘
                                          │
                         ┌────────────────▼───────────────────────┐
                         │  Analytics Service                     │
                         │  (services/analytics.py)               │
                         │  - create_event_record()               │
                         │  - validate_event_payload()            │
                         │  - get_event_category()                │
                         └────────────────┬───────────────────────┘
                                          │
                         ┌────────────────▼───────────────────────┐
                         │  AnalyticsEvent Model                  │
                         │  (models.py)                           │
                         │                                        │
                         │  Fields:                               │
                         │  - id (UUID)                           │
                         │  - user_id (UUID)                      │
                         │  - event_name (str)                    │
                         │  - payload (JSONB)                     │
                         │  - path (str)                          │
                         │  - session_id (UUID) ⭐ NEW            │
                         │  - cohort (str) ⭐ NEW                 │
                         │  - event_category (str) ⭐ NEW         │
                         │  - device_info (JSONB) ⭐ NEW          │
                         │  - created_at (timestamp)              │
                         └────────────────┬───────────────────────┘
                                          │
                         ┌────────────────▼───────────────────────┐
                         │  PostgreSQL Database                   │
                         │  analytics_events table                │
                         │                                        │
                         │  Indexes:                              │
                         │  - idx_analytics_user                  │
                         │  - idx_analytics_event_name            │
                         │  - idx_analytics_created_at            │
                         │  - idx_analytics_session ⭐ NEW        │
                         │  - idx_analytics_category ⭐ NEW       │
                         │  - idx_analytics_cohort ⭐ NEW         │
                         └────────────────────────────────────────┘
```

## Event Flow Diagram

```
User Action → Event Triggered → Validation → Categorization → Storage
     │              │                │              │             │
     │              │                │              │             │
     ▼              ▼                ▼              ▼             ▼
┌─────────┐  ┌──────────┐    ┌──────────┐   ┌──────────┐  ┌──────────┐
│ User    │  │ Client   │    │ Backend  │   │ Analytics│  │ Database │
│ clicks  │  │ sends    │    │ receives │   │ service  │  │ stores   │
│ lesson  │→ │ event    │ → │ payload  │ → │ validates│ →│ record   │
│         │  │ data     │    │ + meta   │   │ & tags   │  │          │
└─────────┘  └──────────┘    └──────────┘   └──────────┘  └──────────┘
                                                   │
                                                   │ Auto-categorizes
                                                   ▼
                                            ┌──────────────┐
                                            │ event_name   │
                                            │   "lesson_   │
                                            │   started"   │
                                            ├──────────────┤
                                            │ category ⭐  │
                                            │   "lesson"   │
                                            └──────────────┘
```

## Event Taxonomy Tree

```
Analytics Events (24 total)
│
├─ 📱 ACTIVATION (5 events) - User onboarding journey
│  ├─ app_opened
│  ├─ onboarding_started
│  ├─ onboarding_completed
│  ├─ first_lesson_started
│  └─ first_quiz_completed
│
├─ 📚 LESSON (4 events) - Content engagement
│  ├─ lesson_viewed
│  ├─ lesson_started
│  ├─ lesson_completed
│  └─ lesson_time_spent
│
├─ ✅ QUIZ (5 events) - Assessment activities
│  ├─ quiz_started
│  ├─ quiz_submitted
│  ├─ quiz_passed
│  ├─ quiz_failed
│  └─ question_answered
│
├─ 🔥 STREAK (4 events) - Consistency tracking
│  ├─ streak_continued
│  ├─ streak_broken
│  ├─ streak_freeze_used
│  └─ streak_milestone_reached
│
├─ 🎯 DISCOVERY (3 events) - Learning progression
│  ├─ motif_discovered
│  ├─ motif_learned
│  └─ motif_mastered
│
└─ 💫 ENGAGEMENT (4 events) - General activity
   ├─ session_started
   ├─ session_ended
   ├─ daily_mission_completed
   └─ badge_earned
```

## Data Model Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                        AnalyticsEvent                            │
├─────────────────────────────────────────────────────────────────┤
│ id: UUID (PK)                                                    │
│ user_id: UUID (FK → users.id) ──┐                               │
│ event_name: str                  │                               │
│ event_category: str ⭐           │                               │
│ session_id: UUID ⭐             │                               │
│ cohort: str ⭐                   │                               │
│ payload: JSONB                   │                               │
│ device_info: JSONB ⭐            │                               │
│ path: str                        │                               │
│ created_at: timestamp            │                               │
└──────────────────────────────────┼──────────────────────────────┘
                                   │
                                   │ Foreign Key
                                   │
                    ┌──────────────▼─────────────┐
                    │         User               │
                    ├────────────────────────────┤
                    │ id: UUID (PK)              │
                    │ email: str                 │
                    │ display_name: str          │
                    │ ...                        │
                    └────────────────────────────┘
```

## Payload Validation Flow

```
Event Payload
     │
     ▼
┌────────────────────┐
│ validate_event_    ���
│ payload()          │
└─────┬──────────────┘
      │
      ├─ Get event_category from EVENT_CATEGORY_MAP
      │
      ▼
┌────────────────────┐
│ Select Schema:     │
├────────────────────┤
│ activation →       │──→ ActivationEventPayload
│ lesson →           │──→ LessonEventPayload
│ quiz →             │──→ QuizEventPayload
│ streak →           │──→ StreakEventPayload
│ discovery →        │──→ DiscoveryEventPayload
│ engagement →       │──→ EngagementEventPayload
│ unknown →          │──→ BaseEventPayload
└─────┬──────────────┘
      │
      ▼
┌────────────────────┐
│ Pydantic Model     │
│ Validation         │
└─────┬──────────────┘
      │
      ├─ Success → Return validated payload
      └─ Failure → Return original payload
```

## Query Optimization with Indexes

```sql
-- By User (existing)
SELECT * FROM analytics_events 
WHERE user_id = 'uuid'
-- Uses: idx_analytics_user

-- By Event Name (existing)
SELECT * FROM analytics_events 
WHERE event_name = 'lesson_completed'
-- Uses: idx_analytics_event_name

-- By Time Range (existing)
SELECT * FROM analytics_events 
WHERE created_at BETWEEN '2024-01-01' AND '2024-01-31'
-- Uses: idx_analytics_created_at

-- By Category ⭐ NEW
SELECT * FROM analytics_events 
WHERE event_category = 'lesson'
-- Uses: idx_analytics_category

-- By Session ⭐ NEW
SELECT * FROM analytics_events 
WHERE session_id = 'session-uuid'
-- Uses: idx_analytics_session

-- By Cohort ⭐ NEW  
SELECT * FROM analytics_events 
WHERE cohort = '2024-W01'
-- Uses: idx_analytics_cohort
```

## Example Event Journey

```
User Journey: First Lesson Completion
═════════════════════════════════════

1. App Launch
   ┌─────────────────────────────────┐
   │ Event: app_opened               │
   │ Category: activation            │
   │ Session: abc-123                │
   │ Cohort: 2024-W01               │
   └─────────────────────────────────┘

2. Navigate to Lesson
   ┌─────────────────────────────────┐
   │ Event: lesson_viewed            │
   │ Category: lesson                │
   │ Session: abc-123 (same)         │
   │ Payload: {motif_id: xyz}        │
   └─────────────────────────────────┘

3. Start Lesson
   ┌─────────────────────────────────┐
   │ Event: lesson_started           │
   │ Category: lesson                │
   │ Session: abc-123 (same)         │
   │ Payload: {motif_id: xyz}        │
   └─────────────────────────────────┘

4. Complete Lesson
   ┌─────────────────────────────────┐
   │ Event: lesson_completed         │
   │ Category: lesson                │
   │ Session: abc-123 (same)         │
   │ Payload: {                      │
   │   motif_id: xyz,                │
   │   duration_seconds: 180         │
   │ }                               │
   └─────────────────────────────────┘

5. First Lesson Milestone
   ┌─────────────────────────────────┐
   │ Event: first_lesson_started     │
   │ Category: activation            │
   │ Session: abc-123 (same)         │
   └─────────────────────────────────┘

All events share:
✓ Same user_id
✓ Same session_id (abc-123)
✓ Same cohort (2024-W01)
✓ Same device_info
✓ Sequential timestamps
```

