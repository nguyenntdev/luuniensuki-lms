# Abuse Reporting System - README

## Overview

The Abuse Reporting System provides comprehensive tools for users to report inappropriate user-generated content (UGC) and for administrators to manage and resolve these reports efficiently.

## Features

### For Users
- ✅ Submit reports for inappropriate content
- ✅ Track status of submitted reports
- ✅ Provide evidence (screenshots, URLs)
- ✅ Filter personal reports by status
- ✅ Privacy-protected reporting

### For Administrators
- ✅ View all reports with pagination
- ✅ Filter by status and priority
- ✅ Automatic priority assignment
- ✅ Assign reports to team members
- ✅ Resolve or dismiss reports
- ✅ Add resolution notes
- ✅ Track reporter and reported user info

## Priority System

Reports are automatically prioritized based on the reason:

- **Critical** (🔴): Harassment, threats - Immediate attention required
- **High** (🟠): Copyright violations, inappropriate profiles
- **Medium** (🟡): Spam, general inappropriate content
- **Low** (⚪): Other issues

High and Critical priority reports automatically notify all administrators.

## Quick Start

### 1. Apply Database Migration

```bash
# Using Docker
docker-compose exec backend alembic upgrade head

# Local development
alembic upgrade head
```

### 2. User: Submit a Report

```bash
curl -X POST http://localhost:8000/api/v1/reports/abuse \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "comment",
    "content_id": "comment-uuid",
    "reason": "harassment",
    "description": "Detailed description of the issue",
    "evidence_urls": ["https://example.com/screenshot.png"]
  }'
```

### 3. Admin: Review Reports

```bash
# List all reports
curl http://localhost:8000/api/v1/admin/reports/abuse \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Filter by priority
curl "http://localhost:8000/api/v1/admin/reports/abuse?priority=critical" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 4. Admin: Handle Report

```bash
# Assign to yourself or another admin
curl -X POST http://localhost:8000/api/v1/admin/reports/abuse/$REPORT_ID/assign \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"assigned_to_id": "admin-uuid"}'

# Resolve the report
curl -X POST http://localhost:8000/api/v1/admin/reports/abuse/$REPORT_ID/resolve \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "resolution_notes": "User warned and content removed"
  }'
```

## API Documentation

### User Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/reports/abuse` | Submit new report |
| GET | `/api/v1/reports/abuse/mine` | Get my reports |

### Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/reports/abuse` | List all reports |
| GET | `/api/v1/admin/reports/abuse/{id}` | Get report details |
| POST | `/api/v1/admin/reports/abuse/{id}/assign` | Assign to admin |
| POST | `/api/v1/admin/reports/abuse/{id}/resolve` | Resolve report |

See [P0-SEC-02_QUICK_REFERENCE.md](./P0-SEC-02_QUICK_REFERENCE.md) for detailed API specs.

## Testing

Run the automated test suite:

```bash
./test_abuse_reports.sh
```

This will test:
- User report submission
- Priority assignment
- Admin listing and filtering
- Report assignment
- Report resolution/dismissal
- Status tracking

## Content Types

| Type | Description | Examples |
|------|-------------|----------|
| `comment` | User comments | Lesson comments, forum posts |
| `review` | User reviews | Content ratings, feedback |
| `profile` | User profiles | Bio, display name, avatar |
| `message` | Direct messages | User-to-user communication |
| `other` | Other UGC | Any other user content |

## Report Reasons

| Reason | Description | Priority |
|--------|-------------|----------|
| `harassment` | Threats, bullying | Critical |
| `copyright` | Copyright violation | High |
| `inappropriate` | Offensive content | Medium/High |
| `spam` | Spam, advertising | Medium |
| `other` | Other issues | Low |

## Status Workflow

```
┌─────────┐
│ pending │ (Initial state)
└────┬────┘
     │
     ↓ (admin assigns)
┌───────────┐
│ reviewing │ (Assigned to admin)
└─────┬─────┘
      │
      ├──→ (resolve) ──→ ┌──────────┐
      │                  │ resolved │ (Action taken)
      │                  └──────────┘
      │
      └──→ (dismiss) ──→ ┌───────────┐
                         │ dismissed │ (No action needed)
                         └───────────┘
```

## Database Schema

The `abuse_reports` table includes:
- Reporter and reported user references
- Content type and ID for linking
- Reason and detailed description
- Evidence URLs (JSONB array)
- Status and priority tracking
- Assignment to admin
- Resolution notes and timestamp

See [P0-SEC-02_IMPLEMENTATION.md](./P0-SEC-02_IMPLEMENTATION.md) for complete schema.

## Notifications

The system includes placeholders for notifications:

- **Admin Notifications**: Triggered for high/critical reports
- **User Notifications**: When reports are resolved (future)

Current implementation logs notifications to console. To enable email/push:

1. Configure email service (SendGrid, AWS SES, etc.)
2. Update `_notify_admins_of_report()` in `backend/services/abuse_reports.py`
3. Add user notification on resolution

## Security & Privacy

- ✅ Users can only view their own submitted reports
- ✅ Admin endpoints require admin role
- ✅ Reporter identity protected
- ✅ Evidence URLs stored securely
- ✅ Audit trail with timestamps
- ✅ GDPR-compliant (cascading deletes)

## Performance

- ✅ Indexed fields for fast queries
- ✅ Pagination prevents large transfers
- ✅ Eager loading prevents N+1 queries
- ✅ Priority-based sorting for admin efficiency

## Future Enhancements

Planned features for future releases:

- [ ] Email notifications to admins
- [ ] Email notifications to reporters on resolution
- [ ] Push notifications for mobile
- [ ] In-app notification center
- [ ] Auto-moderation using AI
- [ ] Pattern detection for repeat offenders
- [ ] Analytics dashboard for report trends
- [ ] Bulk actions for admins
- [ ] Report templates
- [ ] User reputation scoring

## Troubleshooting

### Reports not showing up?
- Check user authentication token
- Verify user has submitted reports
- Check database connection

### Can't assign report?
- Verify assignee has admin role
- Check report exists and isn't already resolved
- Verify admin authentication

### Priority not auto-assigning?
- Check reason field is valid
- Review priority logic in `services/abuse_reports.py`
- Verify database default value

## Support

For issues or questions:
1. Check [P0-SEC-02_IMPLEMENTATION.md](./P0-SEC-02_IMPLEMENTATION.md) for details
2. Review [P0-SEC-02_QUICK_REFERENCE.md](./P0-SEC-02_QUICK_REFERENCE.md) for API specs
3. Run test suite: `./test_abuse_reports.sh`
4. Check application logs for errors

## License

Part of the Luuniensuki LMS project.

