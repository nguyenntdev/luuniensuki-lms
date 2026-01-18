# P1-TEACH-01: Classroom Management CRUD Implementation

## Overview

This implementation provides comprehensive classroom management functionality for teachers, including:
- Creating and managing classrooms
- Generating unique class codes for student enrollment
- Managing student members
- Archiving/unarchiving classrooms
- Viewing enrolled classrooms (for students)

## Database Changes

### Enhanced Classroom Model

Added new fields to the `Classroom` model:

```python
class Classroom(Base):
    # Existing fields
    id: UUID
    name: str
    description: Optional[str]
    teacher_id: UUID
    created_at: datetime
    
    # New fields
    class_code: str              # Unique 8-character code for joining
    max_students: Optional[int]  # Maximum number of students allowed
    is_archived: bool            # Archive status (default: false)
    settings: Optional[dict]     # JSONB field for additional settings
    updated_at: datetime         # Last update timestamp
```

### Migration

- **File**: `migrations/versions/0021_classroom_enhancements.py`
- **Revision ID**: `0021_classroom_enhancements`
- **Features**:
  - Adds new columns to `classes` table
  - Generates unique class codes for existing classrooms
  - Creates unique constraint and index on `class_code`

## Service Layer

### Classroom Service (`backend/services/classroom.py`)

#### Functions

1. **`generate_unique_class_code(db, length=8)`**
   - Generates a unique 8-character code
   - Uses uppercase letters and numbers (excluding O, 0, I, 1)
   - Ensures uniqueness in database

2. **`create_classroom(db, teacher, name, description, max_students, settings)`**
   - Creates a new classroom with auto-generated code
   - Returns Classroom instance

3. **`update_classroom(db, classroom, name, description, max_students, settings)`**
   - Updates classroom details
   - Updates `updated_at` timestamp

4. **`archive_classroom(db, classroom)`**
   - Sets `is_archived` to True
   - Prevents new student enrollment

5. **`unarchive_classroom(db, classroom)`**
   - Sets `is_archived` to False
   - Re-enables student enrollment

6. **`join_classroom_by_code(db, user, class_code)`**
   - Allows students to join using class code
   - Checks for archived status and max_students limit
   - Returns (Classroom, ClassMember) tuple

7. **`remove_class_member(db, classroom, member_id)`**
   - Removes a member from classroom

8. **`get_enrolled_classrooms(db, user)`**
   - Returns list of classrooms where user is enrolled

9. **`get_classroom_member_count(db, classroom_id)`**
   - Returns member count for a classroom

## API Schemas

### Input Schemas

```python
# Create classroom
ClassroomCreateIn:
    name: str (1-255 chars)
    description: Optional[str]
    max_students: Optional[int] (1-1000)
    settings: Optional[dict]

# Update classroom
ClassroomUpdateIn:
    name: Optional[str] (1-255 chars)
    description: Optional[str]
    max_students: Optional[int] (1-1000)
    settings: Optional[dict]

# Join classroom
ClassroomJoinIn:
    class_code: str (6-10 chars, uppercase + numbers)
```

### Output Schemas

```python
# Member information
ClassMemberOut:
    id: UUID
    user_id: UUID
    display_name: str
    email: str
    role: str
    joined_at: datetime

# Classroom summary (list view)
ClassroomSummaryOut:
    id: UUID
    name: str
    description: Optional[str]
    teacher_id: UUID
    class_code: str
    max_students: Optional[int]
    is_archived: bool
    member_count: int
    assignment_count: int
    created_at: datetime
    updated_at: datetime

# Classroom details (full view)
ClassroomDetailOut:
    id: UUID
    name: str
    description: Optional[str]
    teacher_id: UUID
    teacher_name: str
    class_code: str
    max_students: Optional[int]
    is_archived: bool
    settings: Optional[dict]
    members: list[ClassMemberOut]
    member_count: int
    assignment_count: int
    created_at: datetime
    updated_at: datetime

# Join response
ClassroomJoinOut:
    classroom: ClassroomDetailOut
    message: str
```

## API Endpoints

### Teacher Endpoints

#### 1. List Classrooms
```
GET /api/v1/classrooms?include_archived=false
Authorization: Bearer {teacher_token}
```
- Lists all classrooms for the current teacher
- Optional query param: `include_archived` (default: false)
- Returns: `list[ClassroomSummaryOut]`

#### 2. Create Classroom
```
POST /api/v1/classrooms
Authorization: Bearer {teacher_token}
Content-Type: application/json

{
    "name": "Vietnamese Pottery Class",
    "description": "Learn about ancient pottery",
    "max_students": 30,
    "settings": {
        "allow_self_paced": true
    }
}
```
- Creates a new classroom
- Auto-generates unique class code
- Returns: `ClassroomSummaryOut`

#### 3. Get Classroom Details
```
GET /api/v1/classrooms/{classroom_id}
Authorization: Bearer {teacher_token}
```
- Returns detailed classroom information
- Includes members and assignments
- Returns: `ClassroomDetailOut`

#### 4. Update Classroom
```
PUT /api/v1/classrooms/{classroom_id}
Authorization: Bearer {teacher_token}
Content-Type: application/json

{
    "name": "Advanced Pottery",
    "max_students": 25
}
```
- Updates classroom details
- All fields optional
- Returns: `ClassroomDetailOut`

#### 5. Delete Classroom
```
DELETE /api/v1/classrooms/{classroom_id}
Authorization: Bearer {teacher_token}
```
- Permanently deletes classroom
- Also deletes members and assignments
- Returns: 204 No Content

#### 6. Archive Classroom
```
POST /api/v1/classrooms/{classroom_id}/archive
Authorization: Bearer {teacher_token}
```
- Archives classroom
- Prevents new enrollment
- Returns: `ClassroomDetailOut`

#### 7. Unarchive Classroom
```
POST /api/v1/classrooms/{classroom_id}/unarchive
Authorization: Bearer {teacher_token}
```
- Unarchives classroom
- Re-enables enrollment
- Returns: `ClassroomDetailOut`

#### 8. Remove Member
```
DELETE /api/v1/classrooms/{classroom_id}/members/{member_id}
Authorization: Bearer {teacher_token}
```
- Removes a student from classroom
- Returns: 204 No Content

### Student Endpoints

#### 9. Join Classroom
```
POST /api/v1/classrooms/join
Authorization: Bearer {learner_token}
Content-Type: application/json

{
    "class_code": "ABC123XY"
}
```
- Joins classroom using class code
- Only for learners
- Returns: `ClassroomJoinOut`

#### 10. Get Enrolled Classrooms
```
GET /api/v1/classrooms/enrolled
Authorization: Bearer {learner_token}
```
- Lists classrooms where user is enrolled
- Returns: `list[ClassroomSummaryOut]`

## Error Handling

### Common Error Responses

```json
{
    "detail": "Classroom not found"
}
```

```json
{
    "detail": "Not authorized"
}
```

```json
{
    "detail": "Only learners can join classrooms"
}
```

```json
{
    "detail": "This classroom is archived and cannot accept new students"
}
```

```json
{
    "detail": "This classroom has reached its maximum student capacity"
}
```

## Testing

Run the comprehensive test script:

```bash
./test_classroom_api.sh
```

The script tests:
1. ✅ Teacher login
2. ✅ Create classroom
3. ✅ List classrooms
4. ✅ Get classroom details
5. ✅ Update classroom
6. ✅ Student login
7. ✅ Join classroom by code
8. ✅ Get enrolled classrooms
9. ✅ View members
10. ✅ Remove member
11. ✅ Archive classroom
12. ✅ Unarchive classroom
13. ✅ List with archived filter
14. ✅ Delete classroom

## Migration Instructions

1. **Apply the migration**:
   ```bash
   cd /path/to/luuniensuki-lms
   alembic upgrade head
   ```

2. **Restart the backend**:
   ```bash
   docker-compose restart backend
   ```

3. **Run tests**:
   ```bash
   ./test_classroom_api.sh
   ```

## Files Modified/Created

### Created
- `migrations/versions/0021_classroom_enhancements.py` - Database migration
- `backend/services/classroom.py` - Classroom service layer
- `test_classroom_api.sh` - API testing script
- `P1-TEACH-01_IMPLEMENTATION.md` - This documentation

### Modified
- `backend/models.py` - Enhanced Classroom model
- `backend/schemas.py` - Added classroom schemas
- `backend/main.py` - Added/enhanced classroom endpoints

## Usage Examples

### Teacher Workflow

1. Create a new classroom:
   ```python
   POST /api/v1/classrooms
   {
       "name": "Pottery 101",
       "max_students": 20
   }
   # Response includes class_code: "ABC123XY"
   ```

2. Share class code with students
3. View enrolled students:
   ```python
   GET /api/v1/classrooms/{id}
   ```

### Student Workflow

1. Get class code from teacher
2. Join classroom:
   ```python
   POST /api/v1/classrooms/join
   {
       "class_code": "ABC123XY"
   }
   ```

3. View enrolled classrooms:
   ```python
   GET /api/v1/classrooms/enrolled
   ```

## Security & Permissions

- **Teachers**: Can create, update, delete, archive their own classrooms
- **Admins**: Can manage all classrooms
- **Learners**: Can join classrooms and view their enrollments
- **Class codes**: Unique, random, excludes ambiguous characters
- **Max students**: Enforced during enrollment

## Future Enhancements

Potential improvements for future iterations:
- Classroom invitations via email
- Bulk student import
- Classroom analytics dashboard
- Assignment creation and grading
- Classroom announcements
- Discussion forums per classroom

## Backward Compatibility

Legacy endpoints maintained for backward compatibility:
- `GET /api/v1/classes`
- `POST /api/v1/classes`
- `GET /api/v1/classes/{id}`
- `POST /api/v1/classes/{id}/members`
- `DELETE /api/v1/classes/{id}/members/{user_id}`
- `POST /api/v1/classes/{id}/assignments`

New applications should use `/api/v1/classrooms` endpoints.

