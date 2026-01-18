# P1-NOTIFY-01: Email Scheduling System - Quick Reference

## API Endpoints (Admin Only)

### Email Templates

```bash
# List all templates
GET /api/v1/admin/email-templates?page=1&page_size=20&active_only=false

# Create template
POST /api/v1/admin/email-templates
{
  "key": "daily_digest",
  "name": "Daily Digest Email",
  "subject_template": "Your Daily Learning Digest - {{user_name}}",
  "body_html": "<h1>Hello {{user_name}}!</h1><p>Streak: {{streak_count}} days</p>",
  "body_text": "Hello {{user_name}}! Streak: {{streak_count}} days",
  "is_active": true
}

# Update template
PUT /api/v1/admin/email-templates/{template_id}
{
  "name": "Updated Template Name",
  "is_active": true
}
```

### Scheduled Emails

```bash
# List scheduled emails
GET /api/v1/admin/scheduled-emails?page=1&page_size=20&status_filter=pending

# Send test email
POST /api/v1/admin/scheduled-emails/send-test
{
  "template_id": "uuid-here",
  "context_data": {
    "user_name": "Test User",
    "streak_count": 5
  }
}
```

## Service Functions

### Template Rendering
```python
from backend.services import email_scheduler

# Render template with context
subject, body_html, body_text = email_scheduler.render_email_template(
    template,
    {"user_name": "John", "streak_count": 10}
)
```

### Context Generation
```python
# Generate daily digest context
context = email_scheduler.generate_daily_digest_context(db, user_id)
# Returns: {user_name, streak_count, has_freeze, missions, recommendations}

# Generate weekly summary context
context = email_scheduler.generate_weekly_summary_context(db, user_id, week_start, week_end)
# Returns: {user_name, quests, motifs_discovered, motifs_learned, motifs_mastered}
```

### Scheduling Operations
```python
# Schedule single email
email = email_scheduler.schedule_email(
    db, user_id, template_id, scheduled_for, context_data
)

# Schedule for all users
count = email_scheduler.schedule_daily_digest_for_all(db, scheduled_for)
count = email_scheduler.schedule_weekly_summary_for_all(db, scheduled_for, week_start, week_end)

# Get pending emails
emails = email_scheduler.get_pending_emails(db, limit=100)

# Update status
email_scheduler.mark_email_sent(db, email_id)
email_scheduler.mark_email_failed(db, email_id, "Error message")
email_scheduler.cancel_scheduled_email(db, email_id)
```

## Database Schema

### email_templates
```sql
id              UUID PRIMARY KEY
key             VARCHAR(100) UNIQUE NOT NULL
name            VARCHAR(200) NOT NULL
subject_template VARCHAR(500) NOT NULL
body_html       TEXT NOT NULL
body_text       TEXT
is_active       BOOLEAN DEFAULT true
created_at      TIMESTAMP WITH TIME ZONE
updated_at      TIMESTAMP WITH TIME ZONE
```

### scheduled_emails
```sql
id              UUID PRIMARY KEY
user_id         UUID REFERENCES users(id) ON DELETE CASCADE
template_id     UUID REFERENCES email_templates(id) ON DELETE CASCADE
scheduled_for   TIMESTAMP WITH TIME ZONE NOT NULL
status          email_status DEFAULT 'pending'
context_data    JSONB
sent_at         TIMESTAMP WITH TIME ZONE
error_message   TEXT
created_at      TIMESTAMP WITH TIME ZONE
```

### email_status enum
`'pending' | 'sent' | 'failed' | 'cancelled'`

## Template Variables

### Daily Digest
- `user_name`: User's display name
- `streak_count`: Current streak days
- `has_freeze`: Boolean if freeze available
- `missions`: List of daily missions with progress
- `recommendations`: List of recommended content

### Weekly Summary
- `user_name`: User's display name
- `quests`: List of weekly quests with completion status
- `motifs_discovered`: Count of motifs discovered this week
- `motifs_learned`: Count of motifs learned this week
- `motifs_mastered`: Count of motifs mastered this week

## Cron Job Setup

```bash
# Daily digest (8 AM daily)
0 8 * * * python -c "from backend.services import email_scheduler; from backend.database import get_db; from datetime import datetime, timezone; db = next(get_db()); email_scheduler.schedule_daily_digest_for_all(db, datetime.now(timezone.utc))"

# Weekly summary (Monday 9 AM)
0 9 * * 1 python -c "from backend.services import email_scheduler; from backend.database import get_db; from datetime import datetime, timedelta, timezone; db = next(get_db()); now = datetime.now(timezone.utc); week_start = now - timedelta(days=7); email_scheduler.schedule_weekly_summary_for_all(db, now, week_start, now)"

# Process pending emails (every 15 minutes)
*/15 * * * * python process_emails.py
```

## Testing Checklist

- [ ] Create email template via API
- [ ] Update email template
- [ ] List templates with pagination
- [ ] Send test email with sample context
- [ ] Verify template rendering
- [ ] Schedule email for specific user
- [ ] Schedule batch emails for all users
- [ ] Check scheduled_emails table
- [ ] Mark email as sent
- [ ] Mark email as failed
- [ ] Cancel pending email
- [ ] Verify foreign key cascade deletes
- [ ] Test with invalid template ID
- [ ] Test with missing context variables
- [ ] Verify admin-only access control

## Migration

```bash
# Run migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

