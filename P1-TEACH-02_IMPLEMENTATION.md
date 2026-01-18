# P1-TEACH-02: Quest Assignment Implementation

## Overview

Implemented quest assignment feature allowing teachers to assign quests to students in their classrooms. Teachers can assign quests to entire classrooms or individual students, set due dates, customize points, and add notes.

## Changes Summary

### 1. **Model Enhancements** (`backend/models.py`)

Enhanced `QuestAssignment` model with new fields:
- `points_override: Optional[int]` - Custom points for this assignment (overrides quest default)
- `notes: Optional[str]` - Teacher notes for students about the assignment

Existing fields already present:
- `due_at: Optional[datetime]` - Due date for the assignment
- `assigned_at: datetime` - When the assignment was created (auto-set)

### 2. **Database Migration** (`migrations/versions/0029_quest_assignment_enhancements.py`)

Created migration to add new columns to `quest_assignments` table:
- `points_override` (nullable integer)
- `notes` (nullable text)

### 3. **Service Layer** (`backend/services/quest_assignments.py`)

Created comprehensive service with the following functions:

#### Assignment Management
- `assign_quest_to_classroom()` - Assign quest to entire classroom
  - Creates assignment record
  - Auto-creates progress entries for all current members
  - Validates quest is active and not already assigned
  
- `assign_quest_to_student()` - Assign quest to individual student
  - Verifies student is classroom member
  - Creates or reuses classroom assignment
  - Creates progress entry for specific student

#### Querying
- `get_classroom_assignments()` - List all assignments for a classroom
  - Eager loads quest and progress data
  - Returns assignments ordered by assigned_at desc

- `get_student_assignments()` - Get student's assigned quests
  - Returns assignment details with progress
  - Optional classroom filter
  - Includes quest and classroom context

- `get_classroom_assignment_progress()` - Get statistics for an assignment
  - Total students, assigned, in progress, completed counts
  - Completion rate percentage

#### Updates & Submission
- `update_assignment()` - Update due date, points, or notes
- `delete_assignment()` - Delete assignment (cascades to progress)
- `submit_assignment()` - Submit as complete
  - Verifies quest is actually completed
  - Updates status to "in_progress" or "completed"

### 4. **Schemas** (`backend/schemas.py`)

Added comprehensive schemas for quest assignments:

#### Input Schemas
- `QuestAssignmentCreateIn` - Create assignment
  - quest_id, due_at, points_override, notes
  - Optional student_id for individual assignment
  
- `QuestAssignmentUpdateIn` - Update assignment
  - Optional due_at, points_override, notes

#### Output Schemas
- `QuestBriefOut` - Brief quest info for listings
- `QuestAssignmentOut` - Assignment with progress summary
  - Includes completion statistics
  - Teacher and quest details
  
- `QuestAssignmentDetailOut` - Detailed with student progress
  - Full student progress list
  
- `StudentAssignmentOut` - Student view of assignment
  - Quest details, classroom context
  - Status, due date, overdue flag
  
- `AssignmentProgressBriefOut` - Student progress summary
- `AssignmentSubmitOut` - Submission response

### 5. **API Endpoints** (`backend/main.py`)

Added 6 new endpoints under `/api/v1`:

#### Teacher Endpoints (require staff permissions)
1. **GET `/classrooms/{classroom_id}/assignments`**
   - List all assignments for classroom
   - Returns completion statistics

2. **POST `/classrooms/{classroom_id}/assignments`**
   - Create new assignment
   - Supports classroom-wide or individual student
   - Returns created assignment with stats

3. **PUT `/classrooms/{classroom_id}/assignments/{assignment_id}`**
   - Update assignment details
   - Can modify due date, points, notes

4. **DELETE `/classrooms/{classroom_id}/assignments/{assignment_id}`**
   - Delete assignment
   - Cascades to all progress entries

#### Student Endpoints (authenticated users)
5. **GET `/assignments/mine`**
   - Get all assigned quests for current student
   - Optional classroom filter
   - Shows due dates and overdue status

6. **POST `/assignments/{assignment_id}/submit`**
   - Submit assignment as complete
   - Validates quest is actually completed
   - Returns updated status

## Usage Examples

### Teacher: Assign Quest to Classroom

```bash
POST /api/v1/classrooms/{classroom_id}/assignments
Authorization: Bearer {teacher_token}
Content-Type: application/json

{
  "quest_id": "550e8400-e29b-41d4-a716-446655440000",
  "due_at": "2024-02-01T23:59:59Z",
  "points_override": 150,
  "notes": "Complete this quest to learn about Cao Dinh motifs"
}
```

### Teacher: Assign to Individual Student

```bash
POST /api/v1/classrooms/{classroom_id}/assignments
Authorization: Bearer {teacher_token}
Content-Type: application/json

{
  "quest_id": "550e8400-e29b-41d4-a716-446655440000",
  "student_id": "660e8400-e29b-41d4-a716-446655440001",
  "due_at": "2024-02-01T23:59:59Z",
  "notes": "Extra practice assignment"
}
```

### Student: View My Assignments

```bash
GET /api/v1/assignments/mine?classroom_id={classroom_id}
Authorization: Bearer {student_token}
```

### Student: Submit Assignment

```bash
POST /api/v1/assignments/{assignment_id}/submit
Authorization: Bearer {student_token}
```

## Architecture

```
┌─────────────┐
│   Teacher   │
└──────┬──────┘
       │ POST /classrooms/{id}/assignments
       ▼
┌─────────────────────────┐
│   API Endpoint Layer    │
│   (main.py)             │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│   Service Layer         │
│   (quest_assignments)   │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐      ┌────────────────┐
│   QuestAssignment       │──────│ Quest          │
│   - class_id            │      │ - name         │
│   - quest_id            │      │ - description  │
│   - assigned_by_id      │      │ - is_active    │
│   - due_at              │      └────────────────┘
│   - points_override     │
│   - notes               │      ┌────────────────┐
└──────────┬──────────────┘      │ Classroom      │
           │                     │ - name         │
           │                     │ - teacher_id   │
           │                     └────────────────┘
           ▼
┌─────────────────────────┐
│ AssignmentProgress      │
│ - assignment_id         │
│ - user_id               │
│ - status                │
│ - completed_at          │
└─────────────────────────┘
```

## Key Features

✅ **Classroom-wide assignment** - Assign to all students at once
✅ **Individual assignment** - Target specific students
✅ **Custom due dates** - Set deadlines per assignment
✅ **Points override** - Customize points for specific assignments
✅ **Teacher notes** - Add instructions or context
✅ **Progress tracking** - Real-time completion statistics
✅ **Student view** - Students see all their assignments
✅ **Overdue detection** - Automatic overdue flagging
✅ **Quest validation** - Ensures quest completion before marking done
✅ **Auto-progress creation** - New classroom members auto-get existing assignments

## Database Schema

```sql
-- QuestAssignment table enhancements
ALTER TABLE quest_assignments ADD COLUMN points_override INTEGER NULL;
ALTER TABLE quest_assignments ADD COLUMN notes TEXT NULL;

-- Existing structure:
-- id: UUID PRIMARY KEY
-- class_id: UUID FOREIGN KEY → classes(id)
-- quest_id: UUID FOREIGN KEY → quests(id)
-- assigned_by_id: UUID FOREIGN KEY → users(id)
-- due_at: TIMESTAMP WITH TIME ZONE NULL
-- assigned_at: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
```

## Testing Guide

### 1. Create Assignment
```bash
# Assign to classroom
curl -X POST http://localhost:8000/api/v1/classrooms/{classroom_id}/assignments \
  -H "Authorization: Bearer {teacher_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "quest_id": "{quest_id}",
    "due_at": "2024-02-01T23:59:59Z",
    "points_override": 200,
    "notes": "Complete by end of month"
  }'
```

### 2. List Assignments
```bash
# Teacher view
curl -X GET http://localhost:8000/api/v1/classrooms/{classroom_id}/assignments \
  -H "Authorization: Bearer {teacher_token}"
```

### 3. Update Assignment
```bash
curl -X PUT http://localhost:8000/api/v1/classrooms/{classroom_id}/assignments/{assignment_id} \
  -H "Authorization: Bearer {teacher_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "due_at": "2024-02-15T23:59:59Z",
    "notes": "Extended deadline"
  }'
```

### 4. Student View
```bash
curl -X GET http://localhost:8000/api/v1/assignments/mine \
  -H "Authorization: Bearer {student_token}"
```

### 5. Submit Assignment
```bash
curl -X POST http://localhost:8000/api/v1/assignments/{assignment_id}/submit \
  -H "Authorization: Bearer {student_token}"
```

## Security

- **Teacher endpoints** require `get_staff_user` (teacher or admin role)
- **Classroom access check** via `_ensure_class_access()` helper
- **Student endpoints** accessible by authenticated users
- **Assignment submission** validates user has the assignment
- **Quest validation** ensures only active quests can be assigned

## Next Steps

1. Run migration: `alembic upgrade head`
2. Test endpoints with teacher and student accounts
3. Integrate with frontend classroom management UI
4. Add email notifications for new assignments
5. Implement assignment reminders for approaching due dates

## Files Changed

- `backend/models.py` - Enhanced QuestAssignment model
- `backend/schemas.py` - Added assignment schemas
- `backend/services/quest_assignments.py` - New service file
- `backend/main.py` - Added 6 new API endpoints
- `migrations/versions/0029_quest_assignment_enhancements.py` - Database migration

## Status

✅ **COMPLETE** - All tasks implemented and ready for testing.

