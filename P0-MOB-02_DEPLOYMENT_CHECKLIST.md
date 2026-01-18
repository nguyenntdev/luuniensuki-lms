# P0-MOB-02: Deployment Checklist

## Pre-Deployment Checklist

### Code Review
- [ ] Review `backend/models.py` changes (AppVersion model)
- [ ] Review `backend/main.py` changes (4 endpoints + helpers)
- [ ] Review `backend/schemas.py` changes (4 schemas)
- [ ] Review `migrations/versions/0019_app_versions.py`
- [ ] Verify all imports are correct
- [ ] Check for typos or syntax errors

### Testing (Local/Staging)
- [ ] Backend server starts without errors
- [ ] Run migration successfully: `alembic upgrade head`
- [ ] Verify table created: `SELECT * FROM app_versions;`
- [ ] Run automated test script: `ADMIN_TOKEN=xxx ./test_app_version_api.sh`
- [ ] Test public version check endpoint (no auth)
- [ ] Test admin endpoints (with auth)
- [ ] Test with invalid version formats
- [ ] Test duplicate version creation (should fail)
- [ ] Test platform filtering
- [ ] Test force update logic

---

## Deployment Steps

### 1. Backup Database
```bash
# Backup production database
pg_dump luuniensuki_db > backup_before_p0_mob_02_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Deploy Code
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms

# Pull latest changes (if using git)
git pull origin main

# Or deploy via your deployment script
./deploy-to-server.sh
```

### 3. Run Migration
```bash
# On production server
docker-compose exec backend alembic upgrade head

# Or if running locally
alembic upgrade head
```

### 4. Verify Migration
```bash
# Check migration status
docker-compose exec backend alembic current
# Should show: 0019_app_versions (head)

# Verify table exists
docker-compose exec backend psql -U postgres -d luuniensuki_db -c "\d app_versions"

# Verify indexes
docker-compose exec backend psql -U postgres -d luuniensuki_db -c "\d app_versions" | grep "index"
```

### 5. Create Initial Version Entries
```bash
# Get admin token
ADMIN_TOKEN="your_admin_jwt_token"
BASE_URL="https://api.luuniensuki.com"  # or your production URL

# Create Android version
curl -X POST "$BASE_URL/api/v1/admin/app/versions" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "android",
    "version": "1.0.0",
    "version_code": 1,
    "min_required_version": "1.0.0",
    "is_current": true,
    "force_update": false,
    "release_notes": "Initial release",
    "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki"
  }'

# Create iOS version
curl -X POST "$BASE_URL/api/v1/admin/app/versions" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "ios",
    "version": "1.0.0",
    "version_code": 1,
    "min_required_version": "1.0.0",
    "is_current": true,
    "force_update": false,
    "release_notes": "Initial iOS release",
    "download_url": "https://apps.apple.com/app/luuniensuki/id123456789"
  }'
```

### 6. Test Production Endpoints
```bash
# Test public version check (no auth)
curl "$BASE_URL/api/v1/app/version/check?platform=android&current_version=1.0.0"

# Expected response:
# {
#   "update_available": false,
#   "force_update": false,
#   "latest_version": "1.0.0",
#   "current_version": "1.0.0",
#   ...
# }

# Test admin list (with auth)
curl "$BASE_URL/api/v1/admin/app/versions" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Should return array with 2 versions (Android + iOS)
```

### 7. Monitor Logs
```bash
# Watch backend logs for any errors
docker-compose logs -f backend

# Or
tail -f /var/log/luuniensuki/backend.log
```

---

## Post-Deployment Verification

### API Health Check
- [ ] Public endpoint responds: `GET /api/v1/app/version/check`
- [ ] Admin list endpoint responds: `GET /api/v1/admin/app/versions`
- [ ] No errors in backend logs
- [ ] Database queries are performant (check query logs)

### Data Verification
- [ ] Initial versions exist in database
- [ ] `is_current` flags set correctly
- [ ] Indexes created properly
- [ ] Unique constraint works (try creating duplicate - should fail)

### Integration Testing
- [ ] Mobile app can call version check endpoint
- [ ] Version check returns expected data
- [ ] Force update logic works as expected
- [ ] Admin panel can manage versions (if applicable)

---

## Mobile App Integration

### iOS
- [ ] Add version check on app launch
- [ ] Handle `update_available=true` (show optional update prompt)
- [ ] Handle `force_update=true` (show non-dismissible update dialog)
- [ ] Test with various version scenarios
- [ ] Submit updated app to App Store

### Android
- [ ] Add version check on app launch
- [ ] Handle `update_available=true` (show optional update notification)
- [ ] Handle `force_update=true` (show blocking update dialog)
- [ ] Test with various version scenarios
- [ ] Submit updated app to Play Store

---

## Monitoring & Alerts

### Set Up Monitoring
- [ ] Monitor version check endpoint response times
- [ ] Track version check call volume
- [ ] Alert on high error rates
- [ ] Monitor database table size
- [ ] Track version distribution (how many users on each version)

### Analytics
- [ ] Log version check events (optional)
- [ ] Track update adoption rates
- [ ] Monitor forced update impact

---

## Rollback Plan

If issues occur:

### 1. Rollback Migration
```bash
# Downgrade to previous migration
docker-compose exec backend alembic downgrade 0018_lesson_cache

# Verify
docker-compose exec backend alembic current
```

### 2. Rollback Code
```bash
# Revert to previous version
git revert <commit_hash>

# Or restore backup
./restore-previous-version.sh
```

### 3. Restore Database (if needed)
```bash
# Only if data corruption occurred
psql luuniensuki_db < backup_before_p0_mob_02_YYYYMMDD_HHMMSS.sql
```

---

## Documentation & Communication

### Update Team Documentation
- [ ] Add API endpoints to internal docs
- [ ] Update admin user guide
- [ ] Document version release process
- [ ] Share with mobile dev team

### Notify Stakeholders
- [ ] Inform mobile developers
- [ ] Notify QA team
- [ ] Update product team
- [ ] Document in release notes

---

## Known Issues / Limitations

### Current Limitations
- Only supports semantic versioning (major.minor.patch)
- No automatic version detection from app stores
- No scheduled release functionality
- No A/B testing for updates

### Future Enhancements
- Add support for beta/alpha channels
- Add scheduled update releases
- Add version distribution analytics
- Add automatic app store version scraping
- Add localized release notes

---

## Support & Troubleshooting

### Common Issues

**Issue**: Version check returns 500 error
**Solution**: Check if AppVersion table exists, verify migration ran

**Issue**: Force update not working
**Solution**: Verify `min_required_version` is set correctly, check version comparison logic

**Issue**: Multiple versions marked as `is_current`
**Solution**: Run manual query to fix:
```sql
-- Keep only the latest version as current per platform
UPDATE app_versions SET is_current = false 
WHERE platform = 'android' AND version != '1.0.0';
```

### Contact

For deployment issues:
- Check logs: `docker-compose logs backend`
- Review documentation: `P0-MOB-02_*.md`
- Run test script: `./test_app_version_api.sh`

---

## Success Criteria

Deployment is successful when:

- [x] Migration ran without errors
- [x] All 4 endpoints respond correctly
- [x] Initial version entries created
- [x] Mobile apps can call version check
- [x] No errors in production logs
- [x] Database queries performant
- [x] Rollback plan tested (in staging)

---

## Timeline

**Estimated deployment time**: 30-60 minutes

1. Backup: 5 min
2. Deploy code: 5 min
3. Run migration: 2 min
4. Verify migration: 3 min
5. Create initial versions: 5 min
6. Test endpoints: 10 min
7. Monitor: 10-30 min

---

## Sign-Off

- [ ] Backend developer reviewed changes
- [ ] Mobile developers notified
- [ ] QA tested in staging
- [ ] Database admin approved migration
- [ ] Product team approved release
- [ ] Deployment scheduled
- [ ] Rollback plan documented

---

**Deployment Date**: _________________
**Deployed By**: _________________
**Verified By**: _________________

---

## Post-Deployment

After 24 hours:
- [ ] Check error logs
- [ ] Verify version check call volume
- [ ] Monitor database performance
- [ ] Gather mobile developer feedback
- [ ] Update documentation if needed

After 1 week:
- [ ] Review version adoption metrics
- [ ] Check for any reported issues
- [ ] Plan next version release
- [ ] Document lessons learned

---

## References

- Implementation: `P0-MOB-02_IMPLEMENTATION.md`
- API Reference: `P0-MOB-02_API_REFERENCE.md`
- Quick Reference: `P0-MOB-02_QUICK_REFERENCE.md`
- Test Script: `test_app_version_api.sh`

