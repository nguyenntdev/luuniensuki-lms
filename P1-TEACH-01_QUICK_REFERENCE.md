# P1-TEACH-01: Classroom Management - Quick Reference

## API Endpoints Summary

### Teacher Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/classrooms` | List all classrooms |
| POST | `/api/v1/classrooms` | Create new classroom |
| GET | `/api/v1/classrooms/{id}` | Get classroom details |
| PUT | `/api/v1/classrooms/{id}` | Update classroom |
| DELETE | `/api/v1/classrooms/{id}` | Delete classroom |
| POST | `/api/v1/classrooms/{id}/archive` | Archive classroom |
| POST | `/api/v1/classrooms/{id}/unarchive` | Unarchive classroom |
| DELETE | `/api/v1/classrooms/{id}/members/{member_id}` | Remove member |

### Student Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/classrooms/join` | Join classroom by code |
| GET | `/api/v1/classrooms/enrolled` | List enrolled classrooms |

## Quick Examples

### Create Classroom
```bash
curl -X POST http://localhost:8000/api/v1/classrooms \
  -H "Authorization: Bearer {teacher_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vietnamese Pottery Class",
    "description": "Learn ancient pottery techniques",
    "max_students": 30
  }'
```

### Join Classroom
```bash
curl -X POST http://localhost:8000/api/v1/classrooms/join \
  -H "Authorization: Bearer {learner_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "class_code": "ABC123XY"
  }'
```

### List Classrooms
```bash
curl http://localhost:8000/api/v1/classrooms \
  -H "Authorization: Bearer {teacher_token}"
```

## Key Features

- ✅ Unique 8-character class codes
- ✅ Student capacity limits
- ✅ Archive/unarchive functionality
- ✅ JSONB settings field for extensibility
- ✅ Automatic code generation
- ✅ Teacher-only management
- ✅ Student enrollment via codes
- ✅ Backward compatible legacy endpoints

## Database Schema

```sql
-- New fields in classes table
class_code VARCHAR(8) UNIQUE NOT NULL
max_students INTEGER NULL
is_archived BOOLEAN DEFAULT false
settings JSONB NULL
updated_at TIMESTAMP DEFAULT NOW()
```

## Migration

```bash
# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Testing

```bash
# Run full test suite
./test_classroom_api.sh

# Manual testing
export API_URL=http://localhost:8000
./test_classroom_api.sh
```

## Service Functions

```python
from backend.services import classroom

# Generate code
code = classroom.generate_unique_class_code(db)

# Create classroom
room = classroom.create_classroom(db, teacher, "Class Name")

# Join classroom
room, member = classroom.join_classroom_by_code(db, user, "ABC123XY")

# Archive
classroom.archive_classroom(db, room)
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Classroom not found" | Invalid ID or code | Check classroom exists |
| "Not authorized" | Wrong user role | Use teacher account |
| "Maximum capacity reached" | Class full | Increase max_students |
| "Classroom is archived" | Trying to join archived | Unarchive first |
| "Only learners can join" | Teacher trying to join | Use learner account |

