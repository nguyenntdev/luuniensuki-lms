# P1-ADAP-03: Learning Path Architecture Diagram

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATION                        │
│                    (Mobile App / Web Frontend)                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ HTTP/REST API (JWT Auth)
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                         API ENDPOINTS                            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ GET  /api/v1/learning-path/today                       │    │
│  │ POST /api/v1/learning-path/generate                    │    │
│  │ POST /api/v1/learning-path/complete-item              │    │
│  │ GET  /api/v1/learning-path/history                     │    │
│  │ GET  /api/v1/learning-path/stats                       │    │
│  └────────────────────────────────────────────────────────┘    │
│                      (backend/main.py)                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Function Calls
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                    LEARNING PATH SERVICE                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ • get_todays_learning_path()                           │    │
│  │ • generate_learning_path()                             │    │
│  │ • complete_path_item()                                 │    │
│  │ • get_path_history()                                   │    │
│  │ • get_path_statistics()                                │    │
│  │                                                         │    │
│  │ Private Functions:                                      │    │
│  │ • _get_due_reviews()      ← Spaced Repetition         │    │
│  │ • _get_recommended_lessons() ← User Progress           │    │
│  │ • _get_recommended_quizzes() ← Performance             │    │
│  └────────────────────────────────────────────────────────┘    │
│              (backend/services/learning_path.py)                 │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Database Queries
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  TABLE: user_learning_paths                            │    │
│  │  ┌──────────────────────────────────────────────┐     │    │
│  │  │ id, user_id, path_date                       │     │    │
│  │  │ recommended_lessons (JSONB)                  │     │    │
│  │  │ recommended_reviews (JSONB)                  │     │    │
│  │  │ recommended_quizzes (JSONB)                  │     │    │
│  │  │ completed_items (JSONB)                      │     │    │
│  │  │ is_completed, timestamps...                  │     │    │
│  │  └──────────────────────────────────────────────┘     │    │
│  │                                                         │    │
│  │  Related Tables:                                        │    │
│  │  • users (user info, goals)                            │    │
│  │  • user_progress (motif learning status)              │    │
│  │  • quiz_attempts (performance data)                    │    │
│  │  • lesson_content (available lessons)                  │    │
│  │  • motifs (content items)                              │    │
│  └────────────────────────────────────────────────────────┘    │
│                    (PostgreSQL Database)                         │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow: Generate Daily Path

```
1. User Request
   └─→ GET /api/v1/learning-path/today
       │
       ▼
2. API Layer (main.py)
   └─→ Call: get_todays_learning_path(db, user, now)
       │
       ▼
3. Service Layer (learning_path.py)
   ├─→ Check: Path exists for today?
   │   ├─→ YES: Return existing path
   │   └─→ NO: Generate new path
   │       │
   │       ├─→ _get_due_reviews()
   │       │   ├─→ Query user_progress
   │       │   ├─→ Query quiz_attempts
   │       │   ├─→ Calculate intervals (1/3/7/14 days)
   │       │   ├─→ Assign priorities (high/med/low)
   │       │   └─→ Return review list
   │       │
   │       ├─→ _get_recommended_lessons()
   │       │   ├─→ Query discovered motifs
   │       │   ├─→ Query undiscovered motifs
   │       │   ├─→ Consider onboarding goals
   │       │   └─→ Return lesson list
   │       │
   │       ├─→ _get_recommended_quizzes()
   │       │   ├─→ Query learned motifs
   │       │   ├─→ Filter by score < 90%
   │       │   ├─→ Adapt difficulty
   │       │   └─→ Return quiz list
   │       │
   │       ├─→ Calculate estimated time
   │       └─→ Create UserLearningPath record
       │
       ▼
4. Database Layer
   └─→ INSERT INTO user_learning_paths
       │
       ▼
5. Response
   └─→ Return formatted JSON to client
```

## 📊 Spaced Repetition Algorithm Flow

```
Review Scheduling Logic:

┌─────────────────────┐
│ User Takes Quiz     │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ Calculate    │
    │ Performance  │
    └──────┬───────┘
           │
           ├─→ Score ≥ 90%  ───→ Interval: 14 days  ───┐
           │                                            │
           ├─→ Score 80-89% ───→ Interval: 7 days   ───┤
           │                                            │
           ├─→ Score 60-79% ───→ Interval: 3 days   ───┤
           │                                            │
           └─→ Score < 60%  ───→ Interval: 1 day    ───┤
                                                        │
                                                        ▼
                                              ┌──────────────────┐
                                              │ Schedule Next    │
                                              │ Review Date      │
                                              └────────┬─────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ Review Appears   │
                                              │ in Daily Path    │
                                              │ on Due Date      │
                                              └──────────────────┘
```

## 🎯 Path Item Completion Flow

```
1. User Completes Item (lesson/review/quiz)
   │
   ├─→ POST /api/v1/learning-path/complete-item
   │   Body: { "item_type": "lesson", "item_id": "uuid" }
   │
   ▼
2. API Layer Validates
   ├─→ Check: Valid item_type? (lesson/review/quiz)
   ├─→ Check: Valid UUID format?
   └─→ Check: Path exists for today?
       │
       ▼
3. Service Layer: complete_path_item()
   ├─→ Check: Already completed?
   │   └─→ YES: Return already_completed=true
   │
   ├─→ Add to completed_items array
   │   └─→ { "item_type": "...", "item_id": "...", "completed_at": "..." }
   │
   ├─→ Check: All items completed?
   │   └─→ YES: Set is_completed=true, completed_at=now
   │
   └─→ COMMIT to database
       │
       ▼
4. Response
   └─→ {
       "success": true,
       "path_completed": false/true,
       "progress": 3,
       "total": 8
       }
```

## 📈 Statistics Calculation Flow

```
GET /api/v1/learning-path/stats?days=30
│
├─→ Query: All paths for user in last 30 days
│
├─→ Aggregate:
│   ├─→ total_paths_generated
│   ├─→ completed_paths (where is_completed=true)
│   ├─→ completion_rate (completed/total * 100)
│   │
│   ├─→ For Lessons:
│   │   ├─→ Sum: length(recommended_lessons) → total_recommended
│   │   ├─→ Count: completed items where type="lesson" → completed
│   │   └─→ Calculate: completion_rate
│   │
│   ├─→ For Reviews:
│   │   ├─→ Same calculation as lessons
│   │
│   └─→ For Quizzes:
│       └─→ Same calculation as lessons
│
└─→ Return statistics JSON
```

## 🗂️ Component Relationships

```
┌────────────────────────────────────────────────────────┐
│                   USER JOURNEY                          │
└────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌────────┐      ┌──────────┐    ┌──────────┐
   │Onboard-│      │ User     │    │  Quiz    │
   │ing     │──┬──→│ Progress │←───│ Attempts │
   │Goals   │  │   │          │    │          │
   └────────┘  │   └──────────┘    └──────────┘
               │         │
               │         └───────────┐
               │                     │
               ▼                     ▼
        ┌──────────────────────────────────┐
        │     LEARNING PATH GENERATOR      │
        │  • Considers goals               │
        │  • Analyzes progress             │
        │  • Reviews performance           │
        │  • Schedules reviews             │
        └──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │      DAILY LEARNING PATH          │
        │  • 3 Lessons                      │
        │  • 10 Reviews                     │
        │  • 5 Quizzes                      │
        └──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │      USER COMPLETES ITEMS         │
        └──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │   PROGRESS TRACKING & ANALYTICS   │
        └──────────────────────────────────┘
```

## 🔐 Security Layer

```
Every API Request:
│
├─→ Extract JWT Token from Authorization header
│
├─→ Validate Token
│   ├─→ Valid signature?
│   ├─→ Not expired?
│   └─→ Contains user_id?
│
├─→ Load User from Database
│
├─→ Verify User Owns Resource
│   └─→ learning_path.user_id == current_user.id
│
└─→ Process Request
```

## 📊 Performance Optimizations

```
Database Indexes:
├─→ idx_learning_path_user (user_id)
│   └─→ Fast lookup: "Get my paths"
│
├─→ idx_learning_path_date (path_date)
│   └─→ Fast lookup: "Get today's path"
│
└─→ idx_learning_path_completed (is_completed)
    └─→ Fast analytics: "Completion rates"

JSONB Fields:
├─→ recommended_lessons
├─→ recommended_reviews
├─→ recommended_quizzes
└─→ completed_items
    └─→ Flexible schema, no joins needed

Unique Constraint:
└─→ (user_id, path_date)
    └─→ Prevents duplicate paths per day
```

---

This architecture ensures:
- ✅ Scalability (indexed queries)
- ✅ Flexibility (JSONB for items)
- ✅ Security (JWT + ownership checks)
- ✅ Performance (efficient algorithms)
- ✅ Maintainability (clear separation of concerns)

