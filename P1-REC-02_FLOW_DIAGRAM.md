# P1-REC-02: Flow Diagrams

## Next Lesson Recommendation Flow

```
┌─────────────────────────────────────────────────────────────┐
│  User requests next lesson                                  │
│  GET /api/v1/lessons/next?urn_id={optional}                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Get user's progress                                        │
│  - Query UserProgress table                                 │
│  - Build map of motif_id -> progress status                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STRATEGY 1: Check for in-progress lessons                 │
│  Status = discovered OR learned                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                ┌──────┴──────┐
                │             │
            Found?          No lessons
                │             │
                ▼             ▼
        ┌───────────┐   ┌──────────────────────────────┐
        │  Return   │   │  STRATEGY 2: Find unlocked   │
        │  lesson   │   │  lesson by difficulty        │
        └───────────┘   └──────┬───────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Get published       │
                    │  lessons             │
                    │  - Filter by urn (if │
                    │    provided)         │
                    │  - Exclude mastered  │
                    │  - Order by          │
                    │    difficulty        │
                    └──────┬───────────────┘
                           │
                           ▼
                    ┌──────────────────────┐
                    │  For each lesson:    │
                    │  Check if unlocked   │
                    └──────┬───────────────┘
                           │
                    ┌──────┴───────┐
                    │              │
              Found unlocked?    All locked
                    │              │
                    ▼              ▼
            ┌───────────┐    ┌────────────┐
            │  Return   │    │  Return    │
            │  lesson   │    │  null      │
            └───────────┘    └────────────┘
```

## Lesson Unlock Check Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Check if lesson is unlocked                                │
│  GET /api/v1/lessons/{id}/is-unlocked                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Get prerequisites for lesson                               │
│  SELECT * FROM lesson_prerequisites                         │
│  WHERE lesson_id = {id}                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                ┌──────┴──────┐
                │             │
        No prerequisites   Has prerequisites
                │             │
                ▼             ▼
        ┌───────────┐   ┌──────────────────────────────┐
        │  UNLOCKED │   │  Get user's completed        │
        │  Return   │   │  lessons (status=mastered)   │
        │  true     │   └──────┬───────────────────────┘
        └───────────┘          │
                               ▼
                    ┌──────────────────────┐
                    │  For each prereq:    │
                    │  Check if completed  │
                    └──────┬───────────────┘
                           │
                           ▼
                    ┌──────────────────────┐
                    │  Split into:         │
                    │  - Missing strict    │
                    │  - Missing           │
                    │    recommended       │
                    └──────┬───────────────┘
                           │
                           ▼
                    ┌──────────────────────┐
                    │  If missing strict   │
                    │  prerequisites:      │
                    │    is_unlocked=false │
                    │  Else:               │
                    │    is_unlocked=true  │
                    └──────┬───────────────┘
                           │
                           ▼
                    ┌──────────────────────┐
                    │  Return unlock       │
                    │  status + missing    │
                    │  prerequisites       │
                    └──────────────────────┘
```

## Learning Sequence Generation Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Get learning sequence                                      │
│  GET /api/v1/lessons/sequence?urn_id={optional}            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Query all published lessons                                │
│  - Filter by urn (if provided)                             │
│  - Order by difficulty_level ASC, created_at ASC           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Get user's progress                                        │
│  Build map: motif_id -> UserProgress                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  For each lesson in order:                                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │  1. Check if completed (status=mastered)          │   │
│  │  2. Check if unlocked (prerequisites met)         │   │
│  │  3. Add to sequence with:                         │   │
│  │     - position (1-based)                          │   │
│  │     - is_unlocked                                 │   │
│  │     - is_completed                                │   │
│  │     - progress_status                             │   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Calculate summary:                                         │
│  - total_lessons = count(sequence)                         │
│  - completed_lessons = count(is_completed=true)            │
│  - current_position = max position with is_completed=true  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Return LessonSequenceOut                                   │
│  - urn_id, urn_name                                        │
│  - total_lessons, completed_lessons, current_position      │
│  - sequence (ordered list)                                 │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisite Relationship Diagram

```
                    Lesson A
                    (Basic)
                        │
                        │ is_strict=true
                        │
                        ▼
                    Lesson B
                (Intermediate)
                    ╱       ╲
    is_strict=true ╱         ╲ is_strict=false
                  ╱           ╲
                 ▼             ▼
            Lesson C      Lesson D
            (Advanced)    (Advanced)
                 │
                 │ is_strict=true
                 ▼
            Lesson E
            (Expert)

Legend:
────────────▶  Strict prerequisite (must complete)
- - - - - -▶  Recommended prerequisite (optional)
```

## User Journey: Learning Path

```
Start
  │
  ▼
┌─────────────────┐
│ User logs in    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ App calls GET /lessons/next     │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ System recommends:              │
│ "Rồng" (Dragon) - Lesson 1     │
│ Reason: next_in_sequence        │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ User completes lesson           │
│ Status → mastered               │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ App calls GET /lessons/next     │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ System recommends:              │
│ "Phượng" (Phoenix) - Lesson 2  │
│ Reason: next_in_sequence        │
│ (Unlocked: Dragon completed)    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ User starts but doesn't finish │
│ Status → discovered             │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ User logs in next day           │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ App calls GET /lessons/next     │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ System recommends:              │
│ "Phượng" (Phoenix) - Lesson 2  │
│ Reason: continue_learning       │
│ (Prioritizes in-progress)       │
└────────┬────────────────────────┘
         │
         ▼
     Continue...
```

## Database Query Flow

```
GET /lessons/next
    │
    ├─▶ SELECT * FROM user_progress 
    │   WHERE user_id = ?
    │
    ├─▶ SELECT * FROM lesson_content
    │   WHERE motif_id IN (discovered OR learned)
    │   LIMIT 1
    │
    └─▶ If none found:
        └─▶ SELECT * FROM lesson_content
            WHERE is_published = true
              AND difficulty_level IS NOT NULL
            ORDER BY difficulty_level ASC
            LIMIT 20
            └─▶ For each:
                └─▶ SELECT * FROM lesson_prerequisites
                    WHERE lesson_id = ?
                    └─▶ Check if unlocked
                        └─▶ Return first unlocked

GET /lessons/{id}/is-unlocked
    │
    ├─▶ SELECT * FROM lesson_prerequisites
    │   WHERE lesson_id = ?
    │
    ├─▶ SELECT motif_id FROM user_progress
    │   WHERE user_id = ? AND status = 'mastered'
    │
    └─▶ Check prerequisites against completed

GET /lessons/sequence
    │
    ├─▶ SELECT * FROM lesson_content
    │   WHERE is_published = true
    │     [AND motif.urn_id = ? if filtered]
    │   ORDER BY difficulty_level ASC
    │
    ├─▶ SELECT * FROM user_progress
    │   WHERE user_id = ?
    │
    └─▶ For each lesson:
        └─▶ Check unlock status
            (may query lesson_prerequisites)
```

