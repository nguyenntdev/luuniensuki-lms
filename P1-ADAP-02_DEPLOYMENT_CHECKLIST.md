# P1-ADAP-02 Deployment Checklist

## Pre-Deployment

### Code Review
- [x] Models reviewed and validated
- [x] Service logic reviewed
- [x] API endpoints implemented
- [x] Schemas defined
- [x] Error handling in place
- [x] Database migration created
- [x] Documentation complete

### Local Testing
- [ ] Migration runs successfully
- [ ] All endpoints return expected responses
- [ ] Skill levels initialize correctly at 0.5
- [ ] Skill updates work on quiz submission
- [ ] Question selection respects difficulty range
- [ ] Recalculation processes history correctly
- [ ] Error cases handled gracefully

### Performance Testing
- [ ] Load test adaptive quiz endpoint
- [ ] Verify database query performance
- [ ] Check index usage
- [ ] Monitor memory usage during recalculation

---

## Deployment Steps

### 1. Database Migration

```bash
# Backup database first!
pg_dump luuniensuki_lms > backup_before_adaptive_quiz.sql

# Run migration
cd /Users/nguyennt/Documents/luuniensuki-lms
source venv/bin/activate  # or your virtual environment
alembic upgrade head

# Verify migration
psql -d luuniensuki_lms -c "\d user_skill_levels"
psql -d luuniensuki_lms -c "\d quiz_questions" | grep skill_type
```

**Rollback if needed:**
```bash
alembic downgrade -1
```

### 2. Deploy Backend Code

```bash
# Pull latest code
git pull origin main

# Restart backend service
sudo systemctl restart luuniensuki-backend
# OR
docker-compose restart backend

# Check logs
tail -f /var/log/luuniensuki/backend.log
# OR
docker-compose logs -f backend
```

### 3. Verify Deployment

```bash
# Run test script
export API_TOKEN="admin-jwt-token"
./test_adaptive_quiz.sh

# Check specific endpoints
curl -H "Authorization: Bearer $API_TOKEN" \
  "http://your-domain.com/api/v1/skills"
```

---

## Post-Deployment

### 1. Data Population

**Option A: Manual Assignment (Recommended)**
```sql
-- Categorize questions by type
UPDATE quiz_questions 
SET skill_type = 'motif_recognition' 
WHERE question_type = 'mesh_location' 
   OR question_type = 'image_select';

UPDATE quiz_questions 
SET skill_type = 'history_knowledge' 
WHERE question_text ILIKE '%dynasty%' 
   OR question_text ILIKE '%century%'
   OR question_text ILIKE '%period%';

UPDATE quiz_questions 
SET skill_type = 'cultural_understanding' 
WHERE question_text ILIKE '%symbol%'
   OR question_text ILIKE '%meaning%'
   OR question_text ILIKE '%tradition%';

-- Verify assignment
SELECT skill_type, COUNT(*) 
FROM quiz_questions 
WHERE skill_type IS NOT NULL 
GROUP BY skill_type;
```

**Option B: Bulk Update Script**
Create and run a Python script to analyze and categorize questions automatically.

### 2. User Skill Initialization

Users will get skills initialized automatically on first access (default 0.5).

**Optional: Pre-initialize for existing users**
```sql
-- Check how many users exist
SELECT COUNT(*) FROM users;

-- Skills will be created on-demand, no pre-population needed
```

### 3. Historical Data Backfill

**For users with quiz history:**
```bash
# Call recalculate endpoint for each user
# This can be done via admin script or manually for power users

curl -X POST -H "Authorization: Bearer $USER_TOKEN" \
  "http://your-domain.com/api/v1/skills/recalculate"
```

**Bulk recalculation script:**
```python
# recalculate_all_skills.py
import requests
from sqlalchemy import create_engine, select
from backend.models import User
from backend.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    users = conn.execute(select(User.id)).scalars().all()
    
for user_id in users:
    # Generate admin token or use service account
    # Call recalculate endpoint
    print(f"Recalculated skills for user {user_id}")
```

---

## Monitoring

### Metrics to Track

**1. Skill Distribution**
```sql
-- Average skill levels by type
SELECT 
    skill_type,
    AVG(skill_level) as avg_level,
    COUNT(DISTINCT user_id) as user_count
FROM user_skill_levels
GROUP BY skill_type;
```

**2. Question Coverage**
```sql
-- How many questions have skill types assigned?
SELECT 
    COUNT(*) FILTER (WHERE skill_type IS NOT NULL) as categorized,
    COUNT(*) FILTER (WHERE skill_type IS NULL) as uncategorized,
    COUNT(*) as total
FROM quiz_questions
WHERE is_active = true AND is_published = true;
```

**3. Usage Statistics**
```sql
-- Skill level updates over time
SELECT 
    DATE(last_updated_at) as date,
    COUNT(*) as updates
FROM user_skill_levels
WHERE last_updated_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(last_updated_at)
ORDER BY date;
```

### Health Checks

**Endpoint Availability:**
```bash
# Check all endpoints respond
curl -I "http://your-domain.com/api/v1/quiz/adaptive"
curl -I "http://your-domain.com/api/v1/skills"
```

**Database Indexes:**
```sql
-- Verify indexes exist
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'user_skill_levels';
```

**Performance:**
```sql
-- Check slow queries
SELECT * FROM pg_stat_statements 
WHERE query LIKE '%user_skill_levels%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Rollback Plan

### If Issues Occur

**1. Quick Fix - Disable Feature**
```python
# In main.py, comment out the adaptive endpoints temporarily
# @app.get("/api/v1/quiz/adaptive")
# def get_adaptive_quiz(...):
#     ...
```

**2. Database Rollback**
```bash
# Revert migration
alembic downgrade -1

# Restore from backup if needed
psql luuniensuki_lms < backup_before_adaptive_quiz.sql
```

**3. Code Rollback**
```bash
git revert <commit-hash>
sudo systemctl restart luuniensuki-backend
```

---

## Troubleshooting

### Common Issues

**Issue: Migration fails**
```
Solution: 
1. Check if tables already exist
2. Verify database connectivity
3. Check for conflicting constraints
```

**Issue: No questions returned from adaptive endpoint**
```
Solution:
1. Verify questions have skill_type assigned
2. Check if user skill level is in valid range
3. Ensure questions exist in the difficulty range
```

**Issue: Skills not updating**
```
Solution:
1. Check logs for update errors
2. Verify questions have skill_type populated
3. Ensure quiz submission completes successfully
```

**Issue: High database load**
```
Solution:
1. Verify indexes are created
2. Add caching for skill levels
3. Batch skill updates if needed
```

---

## Success Criteria

- [ ] Migration completes without errors
- [ ] All API endpoints return 200 for valid requests
- [ ] User skills initialize at 0.5 for new users
- [ ] Skills update correctly after quiz submission
- [ ] Adaptive questions match user skill level
- [ ] No performance degradation
- [ ] Error rates remain below 1%
- [ ] Documentation is accessible
- [ ] Frontend team can integrate successfully

---

## Support Contacts

- **Backend Lead:** [Name]
- **Database Admin:** [Name]  
- **DevOps:** [Name]
- **Documentation:** See P1-ADAP-02_INDEX.md

---

## Notes

- This is a non-breaking change (additive only)
- Existing quiz functionality remains unchanged
- Skills are optional - questions without skill_type still work
- Frontend integration can be gradual

