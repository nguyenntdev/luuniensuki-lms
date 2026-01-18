# P0-HAB-02: Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide gets you up and running with Weekly Quests quickly.

---

## Step 1: Review Documentation

**Start here:** Open [P0_HAB_02_DOCS_INDEX.md](./P0_HAB_02_DOCS_INDEX.md) to see all documentation.

**For quick reference:** Check [P0_HAB_02_QUICK_REFERENCE.md](./P0_HAB_02_QUICK_REFERENCE.md)

---

## Step 2: Deploy to Your Environment

```bash
# Navigate to project directory
cd /Users/nguyennt/Documents/luuniensuki-lms

# 1. Backup database (IMPORTANT!)
docker-compose exec postgres pg_dump -U postgres luuniensuki > backup_$(date +%Y%m%d).sql

# 2. Apply database migration
docker-compose exec backend alembic upgrade head

# 3. Seed default quests
docker-compose exec backend python -m backend.seed_weekly_quests

# 4. Restart backend
docker-compose restart backend
```

---

## Step 3: Verify Deployment

```bash
# Get your auth token (replace with actual user credentials)
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# Test the weekly quests endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/weekly-quests | jq

# You should see 7 quests with 0 progress
```

---

## Step 4: Test Quest Progress

```bash
# Get a quest ID from the previous response
QUEST_ID="<paste-quest-id-here>"

# Update progress
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"increment": 1}' \
  "http://localhost:8000/api/v1/weekly-quests/$QUEST_ID/progress" | jq

# Check quest completion
# When current_count reaches target_count, XP is awarded automatically
```

---

## Step 5: View Quest History

```bash
# Get past 4 weeks of quest history
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/weekly-quests/history?weeks=4" | jq
```

---

## What's Included?

### ✅ 7 Default Quests

**Exploration** (2 quests)
- Discover 10 motifs → 150 XP
- Explore 3 urns → 200 XP

**Mastery** (2 quests)
- Master 5 motifs → 250 XP
- Complete 20 lessons → 300 XP

**Quiz Champion** (2 quests)
- Pass 10 quizzes → 200 XP
- Get 100% on 3 quizzes → 350 XP + badge

**Streak Master** (1 quest)
- Maintain 7-day streak → 400 XP + badge

### ✅ 3 API Endpoints

1. **GET /api/v1/weekly-quests** - Get current week's quests
2. **POST /api/v1/weekly-quests/{id}/progress** - Update progress
3. **GET /api/v1/weekly-quests/history** - View past weeks

### ✅ Auto-Assignment

Quests are automatically assigned to users when they:
- Access any weekly quest endpoint for the first time
- Start a new week (Monday 00:00)

---

## Integration with Existing Features

### When User Discovers a Motif

```python
from backend.services.weekly_quests import get_week_start_date
from backend.models import UserWeeklyQuest, WeeklyQuest, QuestCategory

# Get exploration quests for this week
week_start = get_week_start_date()
exploration_quests = db.query(UserWeeklyQuest).join(WeeklyQuest).filter(
    UserWeeklyQuest.user_id == user.id,
    UserWeeklyQuest.week_start_date == week_start,
    WeeklyQuest.category == QuestCategory.exploration,
    UserWeeklyQuest.is_completed == False
).all()

# Update progress
for quest in exploration_quests:
    quest.current_count += 1
    if quest.current_count >= quest.quest.target_count:
        # Mark as complete
        quest.is_completed = True
        quest.completed_at = datetime.now(timezone.utc)
        quest.xp_awarded = quest.quest.xp_reward
        
        # Award XP to user
        user.total_xp += quest.quest.xp_reward
        
        # Award badge if specified
        if quest.quest.badge_slug:
            # Your badge award logic here
            pass

db.commit()
```

---

## Troubleshooting

### Migration Fails
```bash
# Check current migration version
docker-compose exec backend alembic current

# If stuck, check migration logs
docker-compose logs backend | grep alembic
```

### Seed Script Fails
```bash
# Check if quests already exist
docker-compose exec postgres psql -U postgres luuniensuki \
  -c "SELECT COUNT(*) FROM weekly_quests;"

# The seed script is idempotent - safe to run multiple times
```

### No Quests Returned
```bash
# Verify quests are in database
docker-compose exec postgres psql -U postgres luuniensuki \
  -c "SELECT id, name, is_active FROM weekly_quests;"

# Check user authentication
echo $TOKEN  # Should not be empty
```

---

## Next Steps

1. ✅ **Complete Testing** - Follow [P0_HAB_02_TESTING_GUIDE.md](./P0_HAB_02_TESTING_GUIDE.md)
2. ✅ **Integrate Features** - Link quest progress to user actions
3. ✅ **Monitor Performance** - Check database query performance
4. ✅ **Collect Feedback** - Get user feedback on quest difficulty

---

## Documentation Quick Links

- 📖 [User Guide](./WEEKLY_QUESTS_README.md)
- 📋 [Documentation Index](./P0_HAB_02_DOCS_INDEX.md)
- 📄 [API Reference](./P0_HAB_02_QUICK_REFERENCE.md)
- 🧪 [Testing Guide](./P0_HAB_02_TESTING_GUIDE.md)
- ✅ [Deployment Checklist](./P0_HAB_02_DEPLOYMENT_CHECKLIST.md)

---

## Support

If you encounter issues:
1. Check the [Testing Guide](./P0_HAB_02_TESTING_GUIDE.md)
2. Review the [Implementation Summary](./P0_HAB_02_IMPLEMENTATION_SUMMARY.md)
3. Check database logs and backend logs

---

**You're all set! Weekly Quests are now active in your LMS.** 🎉

