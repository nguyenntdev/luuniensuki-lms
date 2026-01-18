# Content Versioning Flow Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Content Versioning System                    │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   Admin/Teacher  │
│   Makes Edit     │
└────────┬─────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  PATCH /api/v1/admin/lessons/{id}          │
│  ─────────────────────────────────────     │
│  {                                         │
│    "description": "Updated content",       │
│    "publish_note": "Fixed typos"           │
│  }                                         │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  update_admin_lesson() Endpoint            │
│  ────────────────────────────────          │
│  1. Fetch current lesson                   │
│  2. Check permissions                      │
│  3. Create snapshot (before update) ◄──────┼─── _create_content_snapshot()
│  4. Apply changes                          │      │
│  5. Increment version                      │      ├─ Captures current state
│  6. Set last_editor_id                     │      ├─ Stores as JSONB
│  7. Set published_at (if publishing)       │      └─ Saves to content_versions
│  8. Save to database                       │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│         Database Tables                    │
│  ────────────────────────────────          │
│                                            │
│  ┌──────────────────────────────┐          │
│  │    lesson_content            │          │
│  ├──────────────────────────────┤          │
│  │ id: UUID                     │          │
│  │ description: Text            │          │
│  │ version: 3 ←────────────────┼─ Incremented
│  │ last_editor_id: UUID ←──────┼─ Current user
│  │ published_at: DateTime ←────┼─ Now (if publishing)
│  │ publish_note: Text ←────────┼─ From request
│  │ updated_at: DateTime         │          │
│  └──────────────────────────────┘          │
│                                            │
│  ┌──────────────────────────────┐          │
│  │   content_versions           │          │
│  ├──────────────────────────────┤          │
│  │ [Version 1]                  │          │
│  │ version: 1                   │          │
│  │ data: {original content}     │          │
│  │ editor_id: user_abc          │          │
│  │ created_at: 2025-01-10       │          │
│  ├──────────────────────────────┤          │
│  │ [Version 2]                  │          │
│  │ version: 2                   │          │
│  │ data: {first update}         │          │
│  │ editor_id: user_def          │          │
│  │ created_at: 2025-01-12       │          │
│  ├──────────────────────────────┤          │
│  │ [Version 3] ←───────────────┼─ Just created
│  │ version: 3                   │          │
│  │ data: {current update}       │          │
│  │ editor_id: current_user      │          │
│  │ created_at: 2025-01-15       │          │
│  └──────────────────────────────┘          │
└────────────────────────────────────────────┘
```

## Version History Flow

```
Time ─────────────────────────────────────────────────▶

Day 1               Day 2               Day 3
┌─────────┐        ┌─────────┐        ┌─────────┐
│ Create  │        │ Update  │        │ Update  │
│ Lesson  │        │ Content │        │ Content │
└────┬────┘        └────┬────┘        └────┬────┘
     │                  │                  │
     ▼                  ▼                  ▼
┌─────────┐        ┌─────────┐        ┌─────────┐
│Version 1│        │Version 2│        │Version 3│
│─────────│        │─────────│        │─────────│
│Initial  │        │Fixed    │        │Updated  │
│content  │        │typos    │        │context  │
└─────────┘        └─────────┘        └─────────┘
     │                  │                  │
     └──────────────────┴──────────────────┘
                    │
            ┌───────▼────────┐
            │ content_       │
            │ versions       │
            │ table          │
            └────────────────┘
```

## Revert Flow

```
Current State (Version 3)
┌────────────────────────┐
│ "Updated context"      │
│ version: 3             │
└────────┬───────────────┘
         │
         │ Admin wants to revert to Version 2
         │
         ▼
┌──────────────────────────────────────────────┐
│ POST /api/v1/admin/content/lesson/{id}/      │
│      revert/2                                │
└────────┬─────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│  revert_content_to_version()                 │
│  ──────────────────────────────              │
│  1. Get version 2 data                       │
│  2. Create snapshot of current (version 3)   │─┐
│  3. Apply version 2 data to lesson           │ │
│  4. Increment version to 4                   │ │
│  5. Create snapshot for version 4            │ │
└────────┬─────────────────────────────────────┘ │
         │                                       │
         ▼                                       │
┌──────────────────────────────────────────────┐│
│  Result: Version 4 (same content as v2)      ││
│  ──────────────────────────────────          ││
│  Current lesson now has:                     ││
│  - Content from version 2                    ││
│  - Version number: 4                         ││
│  - Complete audit trail:                     ││
│    • Version 1: Initial                      ││
│    • Version 2: Fixed typos                  ││
│    • Version 3: Updated context              ││
│    • Version 4: Reverted to v2  ◄────────────┘│
└──────────────────────────────────────────────┘
```

## API Interaction Flow

```
┌─────────────┐
│  Frontend   │
│  Admin UI   │
└──────┬──────┘
       │
       │ 1. View version history
       │
       ▼
GET /api/v1/admin/content/lesson/{id}/versions
       │
       ▼
┌──────────────────────────────────┐
│ [                                │
│   {version: 3, ...},             │
│   {version: 2, ...},             │
│   {version: 1, ...}              │
│ ]                                │
└──────┬───────────────────────────┘
       │
       │ 2. User selects version 2
       │
       ▼
GET /api/v1/admin/content/lesson/{id}/versions/2
       │
       ▼
┌──────────────────────────────────┐
│ {                                │
│   version: 2,                    │
│   data: {                        │
│     description: "...",          │
│     historical_context: "..."    │
│   },                             │
│   editor_name: "John Doe",       │
│   created_at: "..."              │
│ }                                │
└──────┬───────────────────────────┘
       │
       │ 3. User confirms revert
       │
       ▼
POST /api/v1/admin/content/lesson/{id}/revert/2
{
  "change_note": "Reverting incorrect info"
}
       │
       ▼
┌──────────────────────────────────┐
│ {                                │
│   message: "Content reverted...",│
│   new_version: 4                 │
│ }                                │
└──────────────────────────────────┘
```

## Data Model Relationship

```
┌─────────────────────┐
│       User          │
│─────────────────────│
│ id: UUID            │◄────┐
│ email: String       │     │ last_editor_id
│ display_name: String│     │
└─────────────────────┘     │
                            │
                            │
┌─────────────────────┐     │
│  LessonContent      │     │
│─────────────────────│     │
│ id: UUID            │     │
│ description: Text   │     │
│ version: Integer    │     │
│ last_editor_id ─────┼─────┘
│ published_at: DT    │
│ publish_note: Text  │
└──────────┬──────────┘
           │
           │ content_id
           │
           ▼
┌─────────────────────┐
│  ContentVersion     │
│─────────────────────│
│ id: UUID            │
│ content_type: String│ = "lesson"
│ content_id: UUID ───┼─ points to LessonContent.id
│ version: Integer    │
│ data: JSONB         │ = snapshot of lesson fields
│ editor_id: UUID ────┼─ points to User.id
│ change_note: Text   │
│ created_at: DT      │
└─────────────────────┘
     │
     │ Multiple versions per content
     │
     ├─ Version 1 (created_at: Day 1)
     ├─ Version 2 (created_at: Day 2)
     └─ Version 3 (created_at: Day 3)
```

## Permission Flow

```
┌──────────────────────┐
│   Request Received   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Check Authentication (JWT)      │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  get_staff_user() dependency     │
│  ──────────────────────────      │
│  Is user role in:                │
│  - teacher                       │
│  - admin                         │
│  - super_admin                   │
└──────────┬───────────────────────┘
           │
      Yes  │  No → 403 Forbidden
           ▼
┌──────────────────────────────────┐
│  Additional role checks          │
│  ──────────────────────────      │
│  If updating:                    │
│    - Teacher → Can't publish     │
│    - Admin → Full access         │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│     Execute Operation            │
└──────────────────────────────────┘
```

