# P1-TEACH-01: System Architecture

## Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  Teacher App                    Student App                      │
│  - Create Classroom             - Join by Code                   │
│  - Manage Members               - View Enrollments               │
│  - Archive/Unarchive            - Access Materials               │
│  - Update Settings                                               │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTP/REST
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER (FastAPI)                      │
├─────────────────────────────────────────────────────────────────┤
│  Classroom Endpoints:                                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Teacher Routes (/api/v1/classrooms)                    │     │
│  │ - GET    /                 List all                    │     │
│  │ - POST   /                 Create new                  │     │
│  │ - GET    /{id}             Get details                 │     │
│  │ - PUT    /{id}             Update                      │     │
│  │ - DELETE /{id}             Delete                      │     │
│  │ - POST   /{id}/archive     Archive                     │     │
│  │ - POST   /{id}/unarchive   Unarchive                   │     │
│  │ - DELETE /{id}/members/{m} Remove member               │     │
│  └────────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Student Routes (/api/v1/classrooms)                    │     │
│  │ - POST   /join             Join by code                │     │
│  │ - GET    /enrolled         List enrollments            │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Authentication: JWT Bearer Token                               │
│  Authorization: Role-based (teacher/learner/admin)              │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  classroom_service.py                                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Core Functions:                                        │     │
│  │ • generate_unique_class_code()                         │     │
│  │ • create_classroom()                                   │     │
│  │ • update_classroom()                                   │     │
│  │ • archive_classroom()                                  │     │
│  │ • unarchive_classroom()                                │     │
│  │ • join_classroom_by_code()                             │     │
│  │ • remove_class_member()                                │     │
│  │ • get_enrolled_classrooms()                            │     │
│  │ • get_classroom_member_count()                         │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Business Logic:                                                │
│  • Unique code generation (excludes O/0/I/1)                    │
│  • Capacity validation (max_students)                           │
│  • Archive status checks                                        │
│  • Membership management                                        │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  │ SQLAlchemy ORM
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER (PostgreSQL)                    │
├─────────────────────────────────────────────────────────────────┤
│  Tables:                                                         │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ classes                                                │     │
│  │ ├─ id (UUID, PK)                                       │     │
│  │ ├─ name (VARCHAR)                                      │     │
│  │ ├─ description (TEXT)                                  │     │
│  │ ├─ teacher_id (UUID, FK → users)                       │     │
│  │ ├─ class_code (VARCHAR(8), UNIQUE) ★ NEW              │     │
│  │ ├─ max_students (INTEGER) ★ NEW                        │     │
│  │ ├─ is_archived (BOOLEAN) ★ NEW                         │     │
│  │ ├─ settings (JSONB) ★ NEW                              │     │
│  │ ├─ created_at (TIMESTAMP)                              │     │
│  │ └─ updated_at (TIMESTAMP) ★ NEW                        │     │
│  └────────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ class_members                                          │     │
│  │ ├─ id (UUID, PK)                                       │     │
│  │ ├─ class_id (UUID, FK → classes)                       │     │
│  │ ├─ user_id (UUID, FK → users)                          │     │
│  │ ├─ role (VARCHAR)                                      │     │
│  │ └─ joined_at (TIMESTAMP)                               │     │
│  └────────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ users                                                  │     │
│  │ ├─ id (UUID, PK)                                       │     │
│  │ ├─ email (VARCHAR, UNIQUE)                             │     │
│  │ ├─ display_name (VARCHAR)                              │     │
│  │ └─ role (ENUM: learner/teacher/admin)                  │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Indexes:                                                        │
│  • classes.class_code (UNIQUE)                                  │
│  • classes.teacher_id                                           │
│  • class_members.class_id                                       │
│  • class_members.user_id                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Teacher Creates Classroom

```
Teacher → POST /api/v1/classrooms
           ↓
    [Validate Input]
           ↓
    classroom_service.create_classroom()
           ↓
    generate_unique_class_code()
           ↓
    Save to Database
           ↓
    Return ClassroomSummaryOut
    (includes generated class_code)
```

### Student Joins Classroom

```
Student → POST /api/v1/classrooms/join
          {class_code: "ABC123XY"}
           ↓
    [Validate Input]
           ↓
    classroom_service.join_classroom_by_code()
           ↓
    ┌─────────────────────────┐
    │ 1. Find by class_code   │
    │ 2. Check if archived    │
    │ 3. Check max_students   │
    │ 4. Check existing member│
    │ 5. Create ClassMember   │
    └─────────────────────────┘
           ↓
    Return ClassroomJoinOut
    (includes full classroom details)
```

### Archive Classroom

```
Teacher → POST /api/v1/classrooms/{id}/archive
           ↓
    [Check Authorization]
           ↓
    classroom_service.archive_classroom()
           ↓
    Set is_archived = true
    Update updated_at
           ↓
    Save to Database
           ↓
    Return ClassroomDetailOut
```

## Schema Relationships

```
ClassroomCreateIn (Input)
    ↓
[Service Layer Processing]
    ↓
Classroom (Database Model)
    ↓
[Query & Transform]
    ↓
ClassroomSummaryOut (List Output)
ClassroomDetailOut (Detail Output)
```

## Code Organization

```
backend/
├── main.py                    # API endpoints
├── models.py                  # Database models (Classroom)
├── schemas.py                 # Pydantic schemas
├── services/
│   └── classroom.py          # Business logic
└── security.py               # Auth helpers

migrations/
└── versions/
    └── 0021_classroom_enhancements.py

tests/
└── test_classroom_api.sh     # Integration tests
```

## Security Flow

```
Request
  ↓
[JWT Validation]
  ↓
[Role Check]
  ├─ Teacher → Can manage own classrooms
  ├─ Admin → Can manage all classrooms
  └─ Learner → Can only join/view
  ↓
[Access Control]
  ├─ _ensure_class_access()
  └─ Check classroom.teacher_id == user.id
  ↓
[Execute Operation]
  ↓
Response
```

## Key Design Decisions

1. **Unique Code Generation**
   - 8 characters (short and memorable)
   - Excludes O/0/I/1 (prevents confusion)
   - Random generation with uniqueness check

2. **Archive vs Delete**
   - Archive preserves data
   - Prevents new enrollment
   - Can be reversed
   - Soft delete pattern

3. **Service Layer**
   - Separates business logic from API
   - Reusable across endpoints
   - Easier to test
   - Consistent error handling

4. **Backward Compatibility**
   - New routes: `/api/v1/classrooms`
   - Legacy routes: `/api/v1/classes`
   - Both work simultaneously
   - No breaking changes

5. **Capacity Management**
   - Optional limit (max_students)
   - Enforced during enrollment
   - Flexible for different needs

6. **Settings Field**
   - JSONB for flexibility
   - Future extensibility
   - No schema changes needed
   - Can store custom configs

