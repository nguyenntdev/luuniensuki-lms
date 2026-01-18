# P0-ACT-02: Guest Preview - README

> **First-time user "value demo" - Let guests experience a lesson before signup**

---

## 🎯 What Is This?

Guest Preview is a feature that allows visitors to try a demo lesson **without creating an account**. This reduces friction, increases engagement, and boosts conversion rates.

## ⚡ Quick Start

### For Developers

```bash
# 1. Apply database migration
alembic upgrade head

# 2. Mark a lesson as preview-eligible
psql -U postgres -d luuniensuki_lms -c \
  "UPDATE lesson_content SET preview_eligible = true 
   WHERE is_published = true LIMIT 1;"

# 3. Test the API
./test_guest_preview.sh

# 4. Check it works
curl http://localhost:8000/api/v1/preview/lesson
```

### For Frontend/Mobile

```javascript
// Get the preview lesson
const lesson = await fetch('/api/v1/preview/lesson').then(r => r.json());

// Start tracking
const sessionId = generateSessionId(); // See API Reference for details
await fetch('/api/v1/preview/start', {
  method: 'POST',
  body: JSON.stringify({ session_id: sessionId })
});

// After user views lesson
await fetch('/api/v1/preview/complete', {
  method: 'POST',
  body: JSON.stringify({ session_id: sessionId })
});

// After user signs up (authenticated)
await fetch('/api/v1/preview/convert', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({ session_id: sessionId })
});
```

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **[📍 Start Here: Index](P0-ACT-02_INDEX.md)** | Navigation hub for all documentation |
| [Implementation Guide](P0-ACT-02_GUEST_PREVIEW_IMPLEMENTATION.md) | Complete technical details |
| [API Reference](P0-ACT-02_API_REFERENCE.md) | Endpoint documentation with examples |
| [Quick Reference](P0-ACT-02_QUICK_REFERENCE.md) | Cheat sheet for common tasks |
| [Deployment Checklist](P0-ACT-02_DEPLOYMENT_CHECKLIST.md) | Step-by-step deployment guide |
| [Visual Architecture](P0-ACT-02_VISUAL_ARCHITECTURE.md) | Diagrams and flow charts |
| [Complete Summary](P0-ACT-02_COMPLETE.md) | Implementation summary |

## 🔌 API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/preview/lesson` | GET | ❌ No | Get demo lesson for guests |
| `/api/v1/preview/start` | POST | ❌ No | Start preview session |
| `/api/v1/preview/complete` | POST | ❌ No | Mark preview complete |
| `/api/v1/preview/convert` | POST | ✅ Yes | Link preview to user account |

## 📊 What Gets Tracked?

- **Session Start**: When guest begins preview
- **Session Completion**: When guest finishes lesson  
- **Device Info**: Platform, browser (no PII)
- **Conversion**: Link to user account after signup

## 💾 Database

### New Table: `guest_previews`
Tracks all guest preview sessions with conversion attribution.

### Modified: `lesson_content`  
Added `preview_eligible` boolean field (default: false).

### Migration
`migrations/versions/0022_guest_preview.py`

## 🧪 Testing

```bash
# Automated test
./test_guest_preview.sh

# Manual test
curl http://localhost:8000/api/v1/preview/lesson
```

## 📈 Success Metrics

Track these KPIs:
- **Preview Start Rate**: % of visitors who try preview
- **Completion Rate**: % who finish the lesson
- **Conversion Rate**: % who sign up after preview
- **Time to Complete**: Average lesson duration

## 🎨 User Flow

```
Visitor → View Landing → Click "Try Demo" → View Lesson → 
Sign Up → Account Created → Preview Linked to Account
```

## 🔐 Security

- All endpoints except `/convert` are public (no auth required)
- Session IDs are client-generated (not sensitive)
- Device info is optional and should contain no PII
- Rate limiting recommended for production

## 🚀 Deployment

See **[Deployment Checklist](P0-ACT-02_DEPLOYMENT_CHECKLIST.md)** for complete guide.

### Quick Deploy
1. ✅ Run migration: `alembic upgrade head`
2. ✅ Mark preview lesson: `UPDATE lesson_content SET preview_eligible = true WHERE ...`
3. ✅ Restart backend
4. ✅ Test endpoints

## 🆘 Troubleshooting

**"No preview lesson available"**  
→ Mark at least one lesson as `preview_eligible = true`

**"Preview session not found"**  
→ Check that session_id is being persisted correctly

**Migration fails**  
→ Check database connection and existing schema

Full troubleshooting in [Deployment Checklist](P0-ACT-02_DEPLOYMENT_CHECKLIST.md).

## 📝 Files Changed

### Backend
- `backend/models.py` - Added GuestPreview model, preview_eligible field
- `backend/schemas.py` - Added 7 new Pydantic schemas  
- `backend/main.py` - Added 4 new API endpoints

### Database
- `migrations/versions/0022_guest_preview.py` - New migration

### Documentation
- 7 comprehensive documentation files
- 1 automated testing script

## 🎓 Best Practices

1. **Session ID**: Generate once, persist in localStorage
2. **Preview Content**: Choose engaging, representative lessons
3. **Analytics**: Track all events for optimization
4. **Error Handling**: Handle "no preview available" gracefully
5. **Testing**: Test complete flow before deployment

## 🔗 Related Features

- [P0-ACT-01: Onboarding](P0-ACT-01_ONBOARDING_IMPLEMENTATION.md)
- [Analytics Taxonomy](ANALYTICS_TAXONOMY_ARCHITECTURE.md)
- [API Quick Reference](API_QUICK_REFERENCE.md)

## 📞 Support

- **Technical Questions**: See [API Reference](P0-ACT-02_API_REFERENCE.md)
- **Integration Help**: See [Implementation Guide](P0-ACT-02_GUEST_PREVIEW_IMPLEMENTATION.md)
- **Quick Lookup**: See [Quick Reference](P0-ACT-02_QUICK_REFERENCE.md)

---

**Feature:** P0-ACT-02 Guest Preview  
**Version:** 1.0.0  
**Status:** ✅ Complete and Ready for Deployment  
**Last Updated:** 2025-01-16

**👉 [Start Here: Documentation Index](P0-ACT-02_INDEX.md)**

