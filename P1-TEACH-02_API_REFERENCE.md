# P1-TEACH-02: Quest Assignment - API Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
All endpoints require authentication via Bearer token in the `Authorization` header.

---

## Teacher Endpoints

### 1. List Classroom Assignments

Get all quest assignments for a classroom with progress statistics.

**Endpoint:** `GET /classrooms/{classroom_id}/assignments`

**Authorization:** Teacher or Admin

**Path Parameters:**
- `classroom_id` (UUID) - The classroom ID

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "class_id": "660e8400-e29b-41d4-a716-446655440001",
    "quest": {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "slug": "discover-cao-dinh",
      "name": "Discover Cao Dinh",
      "description": "Explore the motifs of Cao Dinh"
    },
    "assigned_by_id": "880e8400-e29b-41d4-a716-446655440003",
    "assigned_by_name": "Teacher Name",
    "due_at": "2024-02-01T23:59:59Z",
    "assigned_at": "2024-01-15T10:00:00Z",
    "points_override": 200,
    "notes": "Complete all lessons and quiz",
    "total_students": 25,
    "completed_count": 15,
    "in_progress_count": 8,
    "assigned_count": 2,
    "completion_rate": 60.0
  }
]
```

---

### 2. Create Assignment

Assign a quest to the entire classroom or to an individual student.

**Endpoint:** `POST /classrooms/{classroom_id}/assignments`

**Authorization:** Teacher or Admin

**Path Parameters:**
- `classroom_id` (UUID) - The classroom ID

**Request Body:**
```json
{
  "quest_id": "770e8400-e29b-41d4-a716-446655440002",
  "due_at": "2024-02-01T23:59:59Z",
  "points_override": 200,
  "notes": "Complete all lessons and quiz",
  "student_id": null
}
```

**Fields:**
- `quest_id` (UUID, required) - The quest to assign
- `due_at` (datetime, optional) - Due date for the assignment
- `points_override` (int, optional) - Custom points (overrides quest default)
- `notes` (string, optional, max 1000 chars) - Teacher notes for students
- `student_id` (UUID, optional) - If provided, assigns only to this student

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "class_id": "660e8400-e29b-41d4-a716-446655440001",
  "quest": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "slug": "discover-cao-dinh",
    "name": "Discover Cao Dinh",
    "description": "Explore the motifs of Cao Dinh"
  },
  "assigned_by_id": "880e8400-e29b-41d4-a716-446655440003",
  "assigned_by_name": "Teacher Name",
  "due_at": "2024-02-01T23:59:59Z",
  "assigned_at": "2024-01-15T10:00:00Z",
  "points_override": 200,
  "notes": "Complete all lessons and quiz",
  "total_students": 25,
  "completed_count": 0,
  "in_progress_count": 0,
  "assigned_count": 25,
  "completion_rate": 0.0
}
```

**Error Responses:**
- `400 Bad Request` - Quest not found, already assigned, or inactive
- `404 Not Found` - Classroom not found
- `403 Forbidden` - Not a teacher of this classroom

---

### 3. Update Assignment

Update an existing assignment's due date, points, or notes.

**Endpoint:** `PUT /classrooms/{classroom_id}/assignments/{assignment_id}`

**Authorization:** Teacher or Admin

**Path Parameters:**
- `classroom_id` (UUID) - The classroom ID
- `assignment_id` (UUID) - The assignment ID

**Request Body:**
```json
{
  "due_at": "2024-02-15T23:59:59Z",
  "points_override": 250,
  "notes": "Extended deadline - complete by mid-February"
}
```

**Fields:** (all optional)
- `due_at` (datetime, optional) - New due date
- `points_override` (int, optional) - Updated custom points
- `notes` (string, optional, max 1000 chars) - Updated notes

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "class_id": "660e8400-e29b-41d4-a716-446655440001",
  "quest": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "slug": "discover-cao-dinh",
    "name": "Discover Cao Dinh",
    "description": "Explore the motifs of Cao Dinh"
  },
  "assigned_by_id": "880e8400-e29b-41d4-a716-446655440003",
  "assigned_by_name": "Teacher Name",
  "due_at": "2024-02-15T23:59:59Z",
  "assigned_at": "2024-01-15T10:00:00Z",
  "points_override": 250,
  "notes": "Extended deadline - complete by mid-February",
  "total_students": 25,
  "completed_count": 15,
  "in_progress_count": 8,
  "assigned_count": 2,
  "completion_rate": 60.0
}
```

**Error Responses:**
- `404 Not Found` - Assignment or classroom not found
- `403 Forbidden` - Not a teacher of this classroom

---

### 4. Delete Assignment

Delete an assignment. This will remove all student progress entries for this assignment.

**Endpoint:** `DELETE /classrooms/{classroom_id}/assignments/{assignment_id}`

**Authorization:** Teacher or Admin

**Path Parameters:**
- `classroom_id` (UUID) - The classroom ID
- `assignment_id` (UUID) - The assignment ID

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found` - Assignment or classroom not found
- `403 Forbidden` - Not a teacher of this classroom

---

## Student Endpoints

### 5. Get My Assignments

Get all quest assignments for the current student across all classrooms or filtered by classroom.

**Endpoint:** `GET /assignments/mine`

**Authorization:** Any authenticated user

**Query Parameters:**
- `classroom_id` (UUID, optional) - Filter by specific classroom

**Response:** `200 OK`
```json
[
  {
    "assignment_id": "550e8400-e29b-41d4-a716-446655440000",
    "quest_id": "770e8400-e29b-41d4-a716-446655440002",
    "quest_name": "Discover Cao Dinh",
    "quest_description": "Explore the motifs of Cao Dinh",
    "classroom_id": "660e8400-e29b-41d4-a716-446655440001",
    "classroom_name": "Vietnamese History Class",
    "due_at": "2024-02-01T23:59:59Z",
    "assigned_at": "2024-01-15T10:00:00Z",
    "points_override": 200,
    "notes": "Complete all lessons and quiz",
    "status": "assigned",
    "completed_at": null,
    "is_overdue": false
  }
]
```

**Field Descriptions:**
- `status` - One of: "assigned", "in_progress", "completed"
- `is_overdue` - `true` if past due date and not completed
- `points_override` - Custom points for this assignment (if set)
- `notes` - Teacher notes about the assignment

---

### 6. Submit Assignment

Mark an assignment as complete. The quest must be actually completed first.

**Endpoint:** `POST /assignments/{assignment_id}/submit`

**Authorization:** Any authenticated user

**Path Parameters:**
- `assignment_id` (UUID) - The assignment ID

**Response:** `200 OK`
```json
{
  "assignment_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "completed_at": "2024-01-20T15:30:00Z",
  "message": "Assignment completed!"
}
```

**Possible Statuses:**
- `in_progress` - Quest not yet completed, marked as started
- `completed` - Quest completed, assignment marked as done

**Error Responses:**
- `400 Bad Request` - Assignment not found, already completed, or other validation error

---

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Resource deleted successfully
- `400 Bad Request` - Invalid request data or business logic error
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - User lacks permission for this resource
- `404 Not Found` - Resource not found

---

## Assignment Status Flow

```
1. Teacher assigns quest
   ↓
2. Student receives assignment (status: "assigned")
   ↓
3. Student starts quest (status: "in_progress")
   ↓
4. Student completes quest
   ↓
5. Student submits assignment (status: "completed")
```

---

## Examples

### Example 1: Assign Quest to Entire Class

```bash
curl -X POST http://localhost:8000/api/v1/classrooms/660e8400-e29b-41d4-a716-446655440001/assignments \
  -H "Authorization: Bearer YOUR_TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quest_id": "770e8400-e29b-41d4-a716-446655440002",
    "due_at": "2024-02-01T23:59:59Z",
    "points_override": 200,
    "notes": "Complete all lessons and pass the quiz"
  }'
```

### Example 2: Assign Quest to One Student

```bash
curl -X POST http://localhost:8000/api/v1/classrooms/660e8400-e29b-41d4-a716-446655440001/assignments \
  -H "Authorization: Bearer YOUR_TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quest_id": "770e8400-e29b-41d4-a716-446655440002",
    "student_id": "990e8400-e29b-41d4-a716-446655440004",
    "due_at": "2024-02-01T23:59:59Z",
    "notes": "Extra practice assignment"
  }'
```

### Example 3: Student Views Assignments

```bash
curl -X GET http://localhost:8000/api/v1/assignments/mine \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN"
```

### Example 4: Student Submits Assignment

```bash
curl -X POST http://localhost:8000/api/v1/assignments/550e8400-e29b-41d4-a716-446655440000/submit \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN"
```

