# P0-CMS-03 Quick Reference Card

## 🚀 Quick Start

### Run Migration
```bash
alembic upgrade head
```

### Test Endpoints
```bash
# 1. List versions
GET /api/v1/admin/content/lesson/{id}/versions

# 2. Get version details
GET /api/v1/admin/content/lesson/{id}/versions/1

# 3. Revert to version
POST /api/v1/admin/content/lesson/{id}/revert/1
```

---

## 📊 Database Schema

### LessonContent (Extended)
```sql
ALTER TABLE lesson_content ADD COLUMN
  version INTEGER DEFAULT 1,
  last_editor_id UUID REFERENCES users(id),
  published_at TIMESTAMP WITH TIME ZONE,
  publish_note TEXT;
```

### ContentVersion (New)
```sql
CREATE TABLE content_versions (
  id UUID PRIMARY KEY,
  content_type VARCHAR(50),
  content_id UUID,
  version INTEGER,
  data JSONB,
  editor_id UUID REFERENCES users(id),
  change_note TEXT,
  created_at TIMESTAMP WITH TIME ZONE
);
```

---

## 🔑 Key Files

| File | Purpose |
|------|---------|
| `backend/models.py` | Extended LessonContent, added ContentVersion |
| `backend/schemas.py` | Added versioning schemas |
| `backend/main.py` | Added 3 endpoints, updated CRUD |
| `migrations/versions/0012_content_versioning.py` | Migration |

---

## 📝 How It Works

1. **Create lesson** → version = 1, no snapshot yet
2. **First update** → creates v1 snapshot, version = 2
3. **Second update** → creates v2 snapshot, version = 3
4. **Revert to v1** → creates v3 snapshot, applies v1 data, version = 4

---

## 🔒 Security

- All endpoints require JWT authentication
- Staff roles only (teacher/admin/super_admin)
- Teachers can't publish
- Version history is immutable

---

## 🎯 API Response Examples

### List Versions
```json
[
  {
    "id": "uuid",
    "version": 2,
    "editor_name": "John Doe",
    "change_note": "Updated content",
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

### Get Version
```json
{
  "version": 2,
  "data": {
    "description": "Full content snapshot",
    "historical_context": "..."
  },
  "editor_name": "John Doe",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### Revert Response
```json
{
  "message": "Content reverted to version 2",
  "new_version": 4
}
```

---

## 📚 Documentation Files

1. **P0-CMS-03_IMPLEMENTATION_SUMMARY.md** - Overview & status
2. **P0-CMS-03_CONTENT_VERSIONING_IMPLEMENTATION.md** - Full details
3. **P0-CMS-03_API_REFERENCE.md** - API examples
4. **P0-CMS-03_CHECKLIST.md** - Implementation checklist
5. **P0-CMS-03_FLOW_DIAGRAM.md** - Visual diagrams
6. **test_versioning.sh** - Test script

---

## 🧪 Testing

### Manual Test
```bash
# Set your token
export TOKEN="your_jwt_token"

# Create lesson
curl -X POST http://localhost:8000/api/v1/admin/lessons \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"motif_id":"...", "description":"Test"}'

# Update lesson (creates first snapshot)
curl -X PATCH http://localhost:8000/api/v1/admin/lessons/{id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"Updated"}'

# List versions
curl -X GET http://localhost:8000/api/v1/admin/content/lesson/{id}/versions \
  -H "Authorization: Bearer $TOKEN"
```

### Automated Test
```bash
./test_versioning.sh
```

### Unit Tests
```bash
pytest tests/backend/test_content_versioning.py -v
```

---

## ⚠️ Important Notes

- Version numbers never decrease
- Reverting creates new version with old data
- Snapshots are JSONB (complete state)
- created_at is auto-set on snapshot
- last_editor_id tracks who made each change
- published_at only set when is_published changes to true

---

## 🔄 Rollback Plan

```bash
# Downgrade migration
alembic downgrade -1

# Or restore from backup
psql database < backup.sql
```

---

## ✅ Success Criteria

- [x] Models extended with versioning fields
- [x] ContentVersion model tracks history
- [x] Migration created and tested
- [x] API endpoints functional
- [x] Role-based access enforced
- [x] Documentation complete
- [x] Tests written

---

## 🎓 Example Workflow

**Scenario:** Content Editor fixes a typo, then realizes they removed important info

1. Editor updates lesson → v2 created
2. Another edit → v3 created
3. Realizes mistake → lists versions
4. Reviews v1 content → sees complete data
5. Reverts to v1 → v4 created with v1 data
6. History preserved: v1, v2, v3, v4 all in database

---

## 💡 Tips

- Always provide `change_note` for better audit trail
- Use `publish_note` when publishing lessons
- Version numbers show edit frequency
- Filter versions by `editor_name` to see who changed what
- JSONB data field allows querying specific changes in future

---

**Implementation Status:** ✅ COMPLETE
**Migration Status:** ⏳ PENDING (run `alembic upgrade head`)
**Test Status:** ✅ TESTS WRITTEN

