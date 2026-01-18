# P0-ACT-03: Push Notification Permission Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Mobile App                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ JWT Auth
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Endpoints                              │
│                                                                 │
│  GET  /api/v1/notifications/settings                           │
│  PUT  /api/v1/notifications/settings                           │
│  POST /api/v1/notifications/register-push                      │
│  DEL  /api/v1/notifications/unregister-push                    │
│  GET  /api/v1/notifications/should-prompt-permission           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database Models                              │
│                                                                 │
│  ┌────────────────┐         ┌─────────────────────────┐        │
│  │     users      │ 1───1   │ user_notification_      │        │
│  │                │◄───────►│       settings          │        │
│  │ - id           │         │ - id                    │        │
│  │ - email        │         │ - user_id (FK, unique)  │        │
│  │ - push_        │         │ - push_enabled          │        │
│  │   permission_  │         │ - push_token            │        │
│  │   prompted     │         │ - push_platform         │        │
│  └────────────────┘         │ - email_enabled         │        │
│                             │ - streak_reminders      │        │
│                             │ - daily_mission_        │        │
│                             │   reminders             │        │
│                             │ - quiet_hours_start     │        │
│                             │ - quiet_hours_end       │        │
│                             └─────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Permission Prompt Flow

```
┌─────────────────────┐
│  User Starts App    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ User Completes      │
│ First Lesson        │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ App Calls:                                   │
│ GET /api/v1/notifications/                   │
│     should-prompt-permission                 │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ Backend Checks:                              │
│ 1. push_permission_prompted == false?        │
│ 2. Completed lessons count >= 1?             │
└──────────┬───────────────────────────────────┘
           │
           ├─────────────────┬─────────────────┐
           │ NO              │ YES             │
           ▼                 ▼                 ▼
┌─────────────────┐   ┌─────────────────────────────┐
│ Return:         │   │ Return:                     │
│ should_prompt:  │   │ should_prompt: true         │
│    false        │   │ reason: "User is eligible"  │
└─────────────────┘   └───────────┬─────────────────┘
                                  │
                                  ▼
                      ┌───────────────────────────┐
                      │ App Shows Native          │
                      │ Permission Dialog         │
                      └───────────┬───────────────┘
                                  │
                      ┌───────────┴───────────┐
                      │                       │
                      ▼                       ▼
          ┌────────────────────┐   ┌────────────────────┐
          │ User GRANTS        │   │ User DENIES        │
          │ Permission         │   │ Permission         │
          └─────────┬──────────┘   └─────────┬──────────┘
                    │                        │
                    ▼                        ▼
    ┌───────────────────────────┐   ┌────────────────────┐
    │ Get FCM/APNS Token        │   │ Optional: Update   │
    │ from Device               │   │ Settings to Mark   │
    └────────┬──────────────────┘   │ as Declined        │
             │                       └────────────────────┘
             ▼
    ┌─────────────────────────────────────┐
    │ POST /api/v1/notifications/         │
    │      register-push                  │
    │ {                                   │
    │   "token": "fcm-token",            │
    │   "platform": "ios"                │
    │ }                                   │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ Backend:                            │
    │ 1. Stores token & platform          │
    │ 2. Sets push_enabled = true         │
    │ 3. Sets push_permission_prompted    │
    │    = true                           │
    └─────────────────────────────────────┘
```

## Settings Update Flow

```
┌─────────────────────┐
│ User Opens          │
│ Settings Screen     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│ GET /api/v1/notifications/      │
│     settings                    │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Display Current Settings:       │
│ - Push Enabled                  │
│ - Streak Reminders              │
│ - Daily Mission Reminders       │
│ - Quiet Hours                   │
│ - etc.                          │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ User Toggles a Setting          │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ PUT /api/v1/notifications/      │
│     settings                    │
│ {                               │
│   "streak_reminders": false,    │
│   "quiet_hours_start": 22       │
│ }                               │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Backend Updates Settings        │
│ (Partial Update)                │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Return Updated Settings         │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ UI Reflects New Settings        │
└─────────────────────────────────┘
```

## Database Schema Relationships

```
users
├── id (PK)
├── email
├── push_permission_prompted (NEW)
└── ... (other fields)
    │
    │ 1:1 relationship
    ▼
user_notification_settings
├── id (PK)
├── user_id (FK → users.id, UNIQUE)
├── push_enabled
├── push_token
├── push_platform
├── email_enabled
├── streak_reminders
├── daily_mission_reminders
├── weekly_digest
├── marketing_enabled
├── quiet_hours_start
├── quiet_hours_end
├── created_at
└── updated_at

user_progress
├── id (PK)
├── user_id (FK → users.id)
├── motif_id
├── lesson_viewed_at (Used to check lesson completion)
└── ...
```

## API Decision Tree

### Should Prompt Permission?

```
GET /api/v1/notifications/should-prompt-permission
│
├─► Check: user.push_permission_prompted == false?
│   │
│   ├─► NO → Return {should_prompt: false, reason: "Already prompted"}
│   │
│   └─► YES → Continue
│       │
│       └─► Check: COUNT(user_progress WHERE lesson_viewed_at != NULL) >= 1?
│           │
│           ├─► NO → Return {should_prompt: false, reason: "No lessons completed"}
│           │
│           └─► YES → Return {should_prompt: true, reason: "Eligible"}
```

### Register Push Token

```
POST /api/v1/notifications/register-push
│
├─► Validate platform ∈ {ios, android, web}
│   │
│   ├─► INVALID → Return 422 Validation Error
│   │
│   └─► VALID → Continue
│       │
│       ├─► Get or Create user_notification_settings
│       │
│       ├─► Set push_token = request.token
│       ├─► Set push_platform = request.platform
│       ├─► Set push_enabled = true
│       │
│       ├─► Set user.push_permission_prompted = true
│       │
│       └─► Return success response
```

## State Transitions

### User States

```
┌───────────────────────┐
│ New User              │
│ - No lessons done     │
│ - Not prompted        │
└───────┬───────────────┘
        │ Complete 1st lesson
        ▼
┌───────────────────────┐
│ Eligible User         │
│ - Has lessons         │
│ - Not prompted        │
│ - should_prompt=true  │
└───────┬───────────────┘
        │ Grant/Deny permission
        ▼
┌───────────────────────┐
│ Decided User          │
│ - Has lessons         │
│ - Already prompted    │
│ - should_prompt=false │
└───────────────────────┘
```

### Notification Settings States

```
┌──────────────────┐
│ Not Registered   │
│ - No token       │
│ - push_enabled=  │
│   false          │
└────────┬─────────┘
         │ Register token
         ▼
┌──────────────────┐
│ Registered       │
│ - Has token      │
│ - push_enabled=  │
│   true           │
└────────┬─────────┘
         │ Unregister
         ▼
┌──────────────────┐
│ Unregistered     │
│ - No token       │
│ - push_enabled=  │
│   false          │
└──────────────────┘
```

## Integration Sequence

```
Mobile App                    Backend                     Database
    │                            │                            │
    │  Complete lesson           │                            │
    ├───────────────────────────►│                            │
    │                            │  Update user_progress      │
    │                            ├───────────────────────────►│
    │                            │◄───────────────────────────┤
    │  Should prompt?            │                            │
    ├───────────────────────────►│                            │
    │                            │  Check prompted flag       │
    │                            ├───────────────────────────►│
    │                            │  Count completed lessons   │
    │                            ├───────────────────────────►│
    │                            │◄───────────────────────────┤
    │  {should_prompt: true}     │                            │
    │◄───────────────────────────┤                            │
    │                            │                            │
    │  Show permission dialog    │                            │
    │                            │                            │
    │  Register token            │                            │
    ├───────────────────────────►│                            │
    │                            │  Create/Update settings    │
    │                            ├───────────────────────────►│
    │                            │  Set prompted = true       │
    │                            ├───────────────────────────►│
    │                            │◄───────────────────────────┤
    │  {success: true}           │                            │
    │◄───────────────────────────┤                            │
```

