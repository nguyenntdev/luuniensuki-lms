# P0-CMS-04: Review Workflow - Quick Reference

## Content Status Flow

```
┌──────────┐    submit-review     ┌──────────┐    approve      ┌───────────┐
│  DRAFT   │ ──────────────────> │  REVIEW  │ ─────────────> │ PUBLISHED │
└──────────┘    [Teacher/Admin]   └──────────┘   [Admin only]  └───────────┘
     ▲                                 │
     │                                 │
     └─────────────────────────────────┘
              reject [Admin only]
```

## API Endpoints Summary

| Endpoint | Method | Role | Action |
|----------|--------|------|--------|
| `/api/v1/admin/lessons/{id}/submit-review` | POST | Teacher/Admin | draft → review |
| `/api/v1/admin/lessons/{id}/approve` | POST | Admin | review/draft → published |
| `/api/v1/admin/lessons/{id}/reject` | POST | Admin | review → draft |
| `/api/v1/admin/quiz-questions/{id}/submit-review` | POST | Teacher/Admin | draft → review |
| `/api/v1/admin/quiz-questions/{id}/approve` | POST | Admin | review/draft → published |
| `/api/v1/admin/quiz-questions/{id}/reject` | POST | Admin | review → draft |
| `/api/v1/admin/content/pending-review` | GET | Teacher/Admin | List all pending |

## Role Permissions

### Teachers
- ✅ Create draft content
- ✅ Edit own draft content
- ✅ Submit for review
- ❌ Approve/reject
- ❌ Publish directly

### Admins
- ✅ All teacher permissions
- ✅ Approve/reject content
- ✅ Publish directly
- ✅ Edit any content

## Request Examples

### Submit for Review
```bash
curl -X POST \
  https://api.example.com/api/v1/admin/lessons/{lesson_id}/submit-review \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Approve Content
```bash
curl -X POST \
  https://api.example.com/api/v1/admin/lessons/{lesson_id}/approve \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "review_notes": "Content approved - great work!"
  }'
```

### Reject Content
```bash
curl -X POST \
  https://api.example.com/api/v1/admin/lessons/{lesson_id}/reject \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "review_notes": "Needs more historical context"
  }'
```

### Get Pending Reviews
```bash
curl -X GET \
  https://api.example.com/api/v1/admin/content/pending-review \
  -H "Authorization: Bearer {token}"
```

## Database Fields

### LessonContent
- `status`: content_status (draft/review/published/archived)
- `submitted_for_review_at`: timestamptz
- `reviewed_by_id`: uuid (FK to users)
- `reviewed_at`: timestamptz
- `review_notes`: text

### QuizQuestion
- Same as LessonContent, plus:
- `created_by_id`: uuid (FK to users)

## Migration

```bash
# Apply migration
docker compose exec backend alembic upgrade head

# Verify
docker compose exec backend alembic current
# Should show: 0013_review_workflow (head)
```

## Common Use Cases

### Teacher Workflow
1. Create lesson (status=draft)
2. Edit and refine
3. Submit for review (status=review)
4. Wait for admin approval
5. If rejected, edit and resubmit
6. If approved, content is published

### Admin Workflow
1. Check pending reviews: `GET /api/v1/admin/content/pending-review`
2. Review content details
3. Either:
   - Approve: `POST /lessons/{id}/approve` → published
   - Reject: `POST /lessons/{id}/reject` → back to draft with notes

### Direct Publish (Admin only)
1. Create lesson with `is_published: true`
2. Content goes directly to published status
3. Bypasses review workflow

## Status Checks

```sql
-- View all content by status
SELECT status, COUNT(*) 
FROM lesson_content 
GROUP BY status;

-- Find content pending review
SELECT id, status, submitted_for_review_at 
FROM lesson_content 
WHERE status = 'review' 
ORDER BY submitted_for_review_at DESC;

-- Check reviewer activity
SELECT u.display_name, COUNT(*) as reviewed_count
FROM lesson_content lc
JOIN users u ON lc.reviewed_by_id = u.id
WHERE lc.reviewed_at IS NOT NULL
GROUP BY u.display_name;
```

## Error Handling

| Status Code | Scenario |
|-------------|----------|
| 400 | Invalid status transition (e.g., submit non-draft) |
| 403 | Insufficient permissions (e.g., teacher trying to approve) |
| 404 | Content not found |

## Files Modified

- `backend/models.py` - ContentStatus enum, model fields
- `backend/schemas.py` - Request/response schemas
- `backend/main.py` - API endpoints
- `migrations/versions/0013_review_workflow.py` - Database migration

## Next Steps

1. ✅ Backend implementation complete
2. ⏳ Apply database migration
3. ⏳ Test all endpoints
4. ⏳ Build frontend UI for workflow
5. ⏳ Add notifications

---

**For detailed documentation, see**: [P0-CMS-04_IMPLEMENTATION_SUMMARY.md](./P0-CMS-04_IMPLEMENTATION_SUMMARY.md)

