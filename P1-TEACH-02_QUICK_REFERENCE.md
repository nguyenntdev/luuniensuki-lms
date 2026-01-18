# P1-TEACH-02: Quest Assignment - Quick Reference

## 📋 Overview

Teachers assign quests to students. Students complete and submit them.

## 🎯 Key Features

✅ Assign to entire classroom or individual students
✅ Set custom due dates and points
✅ Add teacher notes
✅ Track completion progress
✅ Auto-detect overdue assignments
✅ Validate quest completion before submission

## 🔗 API Endpoints

### Teacher Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/classrooms/{id}/assignments` | List all assignments |
| POST | `/classrooms/{id}/assignments` | Create new assignment |
| PUT | `/classrooms/{id}/assignments/{id}` | Update assignment |
| DELETE | `/classrooms/{id}/assignments/{id}` | Delete assignment |

### Student Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/assignments/mine` | Get my assignments |
| POST | `/assignments/{id}/submit` | Submit assignment |

## 📊 Data Models

### QuestAssignment
```python
{
  "id": UUID,
  "class_id": UUID,
  "quest_id": UUID,
  "assigned_by_id": UUID,
  "due_at": datetime,        # Optional
  "assigned_at": datetime,   # Auto-set
  "points_override": int,    # Optional custom points
  "notes": str,              # Optional teacher notes
}
```

### AssignmentProgress
```python
{
  "id": UUID,
  "assignment_id": UUID,
  "user_id": UUID,
  "status": str,  # assigned, in_progress, completed
  "completed_at": datetime,  # When submitted
}
```

## 🚀 Quick Start

### 1. Assign Quest to Classroom

```bash
POST /api/v1/classrooms/{classroom_id}/assignments
{
  "quest_id": "...",
  "due_at": "2024-02-01T23:59:59Z",
  "points_override": 200,
  "notes": "Complete by end of month"
}
```

### 2. Student Views Assignments

```bash
GET /api/v1/assignments/mine?classroom_id={id}
```

### 3. Student Submits Assignment

```bash
POST /api/v1/assignments/{assignment_id}/submit
```

## 📁 Files Modified

- `backend/models.py` - Enhanced QuestAssignment model
- `backend/schemas.py` - Added assignment schemas  
- `backend/services/quest_assignments.py` - New service
- `backend/main.py` - Added 6 API endpoints
- `migrations/versions/0029_quest_assignment_enhancements.py` - Migration

## 🗄️ Database Changes

```sql
ALTER TABLE quest_assignments 
  ADD COLUMN points_override INTEGER,
  ADD COLUMN notes TEXT;
```

## 🔐 Permissions

- **Teacher endpoints**: Require teacher/admin role + classroom ownership
- **Student endpoints**: Require authentication only

## 📈 Progress Tracking

Teachers see:
- Total students
- Assigned count
- In progress count  
- Completed count
- Completion rate (%)

Students see:
- Assignment status
- Due date
- Overdue flag
- Teacher notes

## ⚠️ Business Rules

1. Quest must be **active** to be assigned
2. Cannot assign same quest to classroom twice
3. Student must **complete quest** before marking assignment done
4. Deleting assignment **cascades** to all progress entries
5. New classroom members **auto-get** existing assignments

## 🧪 Testing Checklist

- [ ] Create classroom assignment
- [ ] Create individual assignment
- [ ] Update assignment (due date, points, notes)
- [ ] Delete assignment
- [ ] Student views assignments
- [ ] Student submits before quest complete (should fail)
- [ ] Student submits after quest complete (should succeed)
- [ ] Check completion statistics
- [ ] Test overdue detection
- [ ] Verify new members get existing assignments

## 📚 Related Documentation

- [Full Implementation Guide](./P1-TEACH-02_IMPLEMENTATION.md)
- [API Reference](./P1-TEACH-02_API_REFERENCE.md)
- [P1-TEACH-01: Classroom Management](./P1-TEACH-01_README.md)

## 🔄 Status Flow

```
Teacher assigns → Student receives (assigned)
                      ↓
                Student works (in_progress)
                      ↓
                Student submits (completed)
```

## 💡 Usage Examples

### Assign to Classroom
```json
{
  "quest_id": "abc-123",
  "due_at": "2024-02-01T23:59:59Z",
  "notes": "Complete all lessons"
}
```

### Assign to Student
```json
{
  "quest_id": "abc-123",
  "student_id": "def-456",
  "due_at": "2024-02-01T23:59:59Z",
  "notes": "Extra practice"
}
```

### Update Assignment
```json
{
  "due_at": "2024-02-15T23:59:59Z",
  "notes": "Extended deadline"
}
```

## ✅ Implementation Complete

All features implemented and ready for testing!

