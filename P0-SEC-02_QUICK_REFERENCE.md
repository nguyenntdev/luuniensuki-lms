# P0-SEC-02: Abuse Reporting - Quick Reference

## API Endpoints

### User Endpoints

#### Submit Report
```
POST /api/v1/reports/abuse
Auth: Required (any user)
Body: AbuseReportCreateIn
Response: AbuseReportOut (201)
```

#### Get My Reports
```
GET /api/v1/reports/abuse/mine?status={status}
Auth: Required (any user)
Response: AbuseReportOut[]
```

### Admin Endpoints

#### List All Reports
```
GET /api/v1/admin/reports/abuse
    ?status={pending|reviewing|resolved|dismissed}
    &priority={low|medium|high|critical}
    &page={number}
    &page_size={1-100}
Auth: Required (admin)
Response: AbuseReportListOut
```

#### Get Report Details
```
GET /api/v1/admin/reports/abuse/{report_id}
Auth: Required (admin)
Response: AbuseReportDetailOut
```

#### Assign Report
```
POST /api/v1/admin/reports/abuse/{report_id}/assign
Auth: Required (admin)
Body: AbuseReportAssignIn
Response: AbuseReportDetailOut
```

#### Resolve Report
```
POST /api/v1/admin/reports/abuse/{report_id}/resolve
Auth: Required (admin)
Body: AbuseReportResolveIn
Response: AbuseReportDetailOut
```

## Data Models

### AbuseReportCreateIn
```json
{
  "reported_user_id": "uuid (optional)",
  "content_type": "comment|review|profile|message|other",
  "content_id": "uuid (optional)",
  "reason": "harassment|spam|inappropriate|copyright|other",
  "description": "string (10-2000 chars)",
  "evidence_urls": ["url1", "url2"] // max 10
}
```

### AbuseReportOut
```json
{
  "id": "uuid",
  "reporter_id": "uuid",
  "reported_user_id": "uuid",
  "content_type": "string",
  "content_id": "uuid",
  "reason": "string",
  "description": "string",
  "evidence_urls": ["string"],
  "status": "pending|reviewing|resolved|dismissed",
  "priority": "low|medium|high|critical",
  "assigned_to_id": "uuid",
  "resolution_notes": "string",
  "resolved_at": "datetime",
  "created_at": "datetime"
}
```

## Priority Matrix

| Reason | Profile | Other Content |
|--------|---------|---------------|
| harassment | critical | critical |
| copyright | high | high |
| inappropriate | high | medium |
| spam | medium | medium |
| other | low | low |

## Status Flow

```
pending → (assign) → reviewing → (resolve) → resolved
                              → (dismiss) → dismissed
```

## Content Types
- `comment` - User comments
- `review` - User reviews/ratings
- `profile` - User profile content
- `message` - Direct messages
- `other` - Other UGC

## Reasons
- `harassment` - Harassment, threats, bullying
- `spam` - Spam content
- `inappropriate` - Offensive content
- `copyright` - Copyright violations
- `other` - Other issues

## Database Schema

```sql
CREATE TABLE abuse_reports (
  id UUID PRIMARY KEY,
  reporter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  reported_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  content_type VARCHAR(50) NOT NULL,
  content_id UUID,
  reason VARCHAR(50) NOT NULL,
  description TEXT NOT NULL,
  evidence_urls JSONB,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  priority VARCHAR(20) NOT NULL DEFAULT 'low',
  assigned_to_id UUID REFERENCES users(id) ON DELETE SET NULL,
  resolution_notes TEXT,
  resolved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Service Functions

### create_abuse_report()
```python
from backend.services.abuse_reports import create_abuse_report

report = create_abuse_report(
    db=db,
    reporter_id=user_id,
    reported_user_id=reported_user_id,
    content_type="comment",
    content_id=comment_id,
    reason="harassment",
    description="User is posting threats",
    evidence_urls=["https://..."],
)
# Auto-assigns priority, notifies admins if high/critical
```

### assign_abuse_report()
```python
from backend.services.abuse_reports import assign_abuse_report

report = assign_abuse_report(
    db=db,
    report_id=report_id,
    assigned_to_id=admin_id,
)
# Changes status to 'reviewing', validates admin role
```

### resolve_abuse_report()
```python
from backend.services.abuse_reports import resolve_abuse_report

report = resolve_abuse_report(
    db=db,
    report_id=report_id,
    status="resolved",  # or "dismissed"
    resolution_notes="Content removed, user warned",
)
# Sets resolved_at timestamp
```

## Testing Commands

```bash
# Apply migration
alembic upgrade head

# Test user submission
curl -X POST http://localhost:8000/api/v1/reports/abuse \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "comment",
    "reason": "harassment",
    "description": "This user is threatening me"
  }'

# Test admin list
curl http://localhost:8000/api/v1/admin/reports/abuse?priority=high \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Test assign
curl -X POST http://localhost:8000/api/v1/admin/reports/abuse/$REPORT_ID/assign \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"assigned_to_id": "'$ADMIN_ID'"}'

# Test resolve
curl -X POST http://localhost:8000/api/v1/admin/reports/abuse/$REPORT_ID/resolve \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "resolution_notes": "Issue addressed"
  }'
```

## Files Changed
- ✅ `backend/models.py` - Added AbuseReport model
- ✅ `backend/schemas.py` - Added 6 schemas
- ✅ `backend/main.py` - Added 6 endpoints
- ✅ `backend/services/abuse_reports.py` - Created service
- ✅ `migrations/versions/0019_abuse_reports.py` - Created migration

## Next Steps for Production

1. **Run Migration**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

2. **Configure Notifications**
   - Set up email service (SendGrid, AWS SES, etc.)
   - Configure push notification service
   - Update `_notify_admins_of_report()` in service

3. **Test End-to-End**
   - Submit test reports
   - Assign and resolve as admin
   - Verify email notifications (when configured)

4. **Monitor & Tune**
   - Monitor report volume
   - Adjust priority thresholds if needed
   - Review resolution times

