# P0-ACT-02: Guest Preview - Visual Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         GUEST PREVIEW SYSTEM                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│  Database    │
│  (Web/Mobile)│     │  (FastAPI)   │     │ (PostgreSQL) │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                     │
       │                    │                     │
       ▼                    ▼                     ▼
  Session ID          API Endpoints         Tables:
  localStorage        /preview/*           - guest_previews
  Device Info         Validation          - lesson_content
                      Error Handling      
```

## Data Flow

### 1. Get Preview Lesson (No Auth)

```
Guest User
    │
    │ GET /api/v1/preview/lesson
    ▼
FastAPI Endpoint
    │
    │ SELECT lesson WHERE preview_eligible=true
    ▼
Database (lesson_content + motifs + urns)
    │
    │ Return lesson data
    ▼
Response: GuestPreviewLessonOut
    │
    ▼
Frontend displays lesson
```

### 2. Start Preview Session (No Auth)

```
Guest User (with session_id)
    │
    │ POST /api/v1/preview/start
    │ {session_id, device_info}
    ▼
FastAPI Endpoint
    │
    │ Find preview-eligible lesson
    ▼
Database Query
    │
    │ INSERT INTO guest_previews
    ▼
Create GuestPreview Record
    │
    │ Return preview details
    ▼
Response: GuestPreviewStartOut
    │
    ▼
Frontend tracks preview_id
```

### 3. Complete Preview (No Auth)

```
Guest User
    │
    │ POST /api/v1/preview/complete
    │ {session_id}
    ▼
FastAPI Endpoint
    │
    │ Find latest preview by session_id
    ▼
Database Query
    │
    │ UPDATE completed_at = NOW()
    ▼
Mark Preview Complete
    │
    │ Return success
    ▼
Response: GuestPreviewCompleteOut
    │
    ▼
Frontend shows signup CTA
```

### 4. Convert to User (Auth Required)

```
Registered User (authenticated)
    │
    │ POST /api/v1/preview/convert
    │ {session_id} + Bearer Token
    ▼
FastAPI Endpoint (with auth)
    │
    │ Find previews by session_id
    ▼
Database Query
    │
    │ UPDATE converted_to_user_id = current_user.id
    ▼
Link Previews to User
    │
    │ Return conversion count
    ▼
Response: GuestPreviewConvertOut
```

## Database Schema

```
┌─────────────────────────────────────────────────────┐
│                  guest_previews                      │
├──────────────────────┬─────────────┬────────────────┤
│ Field                │ Type        │ Description    │
├──────────────────────┼─────────────┼────────────────┤
│ id                   │ UUID        │ Primary Key    │
│ session_id           │ VARCHAR(255)│ Browser ID     │
│ preview_lesson_id    │ UUID        │ FK → lesson    │
│ started_at           │ TIMESTAMP   │ Start time     │
│ completed_at         │ TIMESTAMP   │ End time       │
│ converted_to_user_id │ UUID        │ FK → users     │
│ device_info          │ JSONB       │ Metadata       │
│ created_at           │ TIMESTAMP   │ Created        │
└──────────────────────┴─────────────┴────────────────┘
                         │       │
                ┌────────┘       └────────┐
                ▼                         ▼
    ┌───────────────────┐     ┌──────────────────┐
    │ lesson_content    │     │      users       │
    ├───────────────────┤     ├──────────────────┤
    │ id                │     │ id               │
    │ preview_eligible ◀│     │ email            │
    │ is_published      │     │ ...              │
    │ ...               │     └──────────────────┘
    └───────────────────┘
```

## API Endpoint Map

```
/api/v1/preview/
    │
    ├── GET  /lesson         [No Auth]  → Get demo lesson
    ├── POST /start          [No Auth]  → Start session
    ├── POST /complete       [No Auth]  → Mark complete
    └── POST /convert        [Auth]     → Link to user
```

## Analytics Funnel

```
 100% │ ████████████████████  Visitors
      │
  30% │ ██████                Preview Started
      │                       (guest_previews created)
      │
  18% │ ████                  Preview Completed
      │                       (completed_at NOT NULL)
      │
   2% │ █                     Converted to User
      │                       (converted_to_user_id NOT NULL)
      └─────────────────────────────────────────────
         Conversion Funnel
```

## Component Interactions

```
┌────────────────────────────────────────────────────────┐
│                    GUEST JOURNEY                       │
└────────────────────────────────────────────────────────┘

┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Landing   │──▶│   Preview   │──▶│   Signup    │
│    Page     │   │   Lesson    │   │    Form     │
└─────────────┘   └─────────────┘   └─────────────┘
       │                 │                   │
       │                 │                   │
       ▼                 ▼                   ▼
   No tracking      Track session        Link session
                    (session_id)         to user_id

                    ┌──────────┐
                    │ Database │
                    │ Records: │
                    │ - start  │
                    │ - finish │
                    │ - convert│
                    └──────────┘
```

## Security Model

```
Endpoint                  Auth Required    Rate Limit
─────────────────────────────────────────────────────
GET  /preview/lesson          NO           100/hour
POST /preview/start           NO            20/hour
POST /preview/complete        NO            10/hour
POST /preview/convert         YES            5/hour
                              ^^^
                              │
                    Bearer Token Required
```

## Success Metrics Dashboard (Conceptual)

```
┌──────────────────────────────────────────────────────┐
│              PREVIEW ANALYTICS DASHBOARD             │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Today's Stats:                                      │
│  ┌─────────┬─────────┬──────────┬─────────┐        │
│  │ Started │ Finished│ Converted│ Revenue │        │
│  │   342   │   206   │    28    │  $420   │        │
│  └─────────┴─────────┴──────────┴─────────┘        │
│                                                      │
│  Conversion Funnel:                                  │
│  Visitors: ████████████████████ 1,200               │
│  Started:  ██████              342 (28.5%)          │
│  Finished: ████                206 (60.2%)          │
│  Signed:   █                    28 (8.2%)           │
│                                                      │
│  Top Preview Lessons:                                │
│  1. Dragon Motif     - 156 views, 12% conversion    │
│  2. Phoenix Motif    - 98 views,  9% conversion     │
│  3. Lotus Motif      - 88 views,  7% conversion     │
│                                                      │
│  Device Breakdown:                                   │
│  Web:     68% ████████                              │
│  iOS:     20% ███                                   │
│  Android: 12% ██                                    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## File Structure

```
luuniensuki-lms/
│
├── backend/
│   ├── models.py          ← GuestPreview model added
│   ├── schemas.py         ← 7 new schemas added
│   └── main.py            ← 4 new endpoints added
│
├── migrations/
│   └── versions/
│       └── 0022_guest_preview.py   ← New migration
│
├── test_guest_preview.sh  ← Testing script
│
└── Documentation:
    ├── P0-ACT-02_COMPLETE.md
    ├── P0-ACT-02_GUEST_PREVIEW_IMPLEMENTATION.md
    ├── P0-ACT-02_API_REFERENCE.md
    ├── P0-ACT-02_QUICK_REFERENCE.md
    ├── P0-ACT-02_DEPLOYMENT_CHECKLIST.md
    ├── P0-ACT-02_INDEX.md
    └── P0-ACT-02_VISUAL_ARCHITECTURE.md (this file)
```

---

**Visual Guide Version:** 1.0.0  
**Last Updated:** 2025-01-16

