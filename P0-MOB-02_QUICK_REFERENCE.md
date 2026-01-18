# P0-MOB-02: App Version Management - Quick Reference

## Quick Commands

### Test Version Check (No Auth)
```bash
# Android - current version
curl "http://localhost:8000/api/v1/app/version/check?platform=android&current_version=1.2.0"

# iOS - older version
curl "http://localhost:8000/api/v1/app/version/check?platform=ios&current_version=1.0.0"
```

### Admin - Create Version
```bash
curl -X POST "http://localhost:8000/api/v1/admin/app/versions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "android",
    "version": "1.2.0",
    "version_code": 3,
    "min_required_version": "1.0.0",
    "is_current": true,
    "force_update": false,
    "release_notes": "Bug fixes",
    "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki"
  }'
```

### Admin - List Versions
```bash
curl "http://localhost:8000/api/v1/admin/app/versions" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by platform
curl "http://localhost:8000/api/v1/admin/app/versions?platform=ios" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Admin - Force Update
```bash
curl -X PUT "http://localhost:8000/api/v1/admin/app/versions/{VERSION_ID}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "force_update": true,
    "release_notes": "CRITICAL UPDATE - Please update immediately"
  }'
```

### Run Migration
```bash
# Docker
docker-compose exec backend alembic upgrade head

# Local
alembic upgrade head

# Check current revision
docker-compose exec backend alembic current
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/app/version/check` | None | Check if update available |
| GET | `/api/v1/admin/app/versions` | Admin | List all versions |
| POST | `/api/v1/admin/app/versions` | Admin | Create version |
| PUT | `/api/v1/admin/app/versions/{id}` | Admin | Update version |

---

## Database Schema

```sql
CREATE TABLE app_versions (
    id UUID PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,  -- 'ios' or 'android'
    version VARCHAR(20) NOT NULL,   -- '1.2.3'
    version_code INTEGER NOT NULL,  -- Build number
    min_required_version VARCHAR(20) NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    force_update BOOLEAN DEFAULT FALSE,
    release_notes TEXT,
    download_url VARCHAR(500),
    released_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE(platform, version)
);
```

---

## Version Check Logic

```
if (no version data):
    return update_available=false, force_update=false

if (current_version < latest_version):
    update_available = true
else:
    update_available = false

if (current_version < min_required_version):
    force_update = true
elif (version.force_update == true AND update_available):
    force_update = true
else:
    force_update = false
```

---

## Mobile Integration Snippets

### iOS (Swift)
```swift
func checkVersion() async throws -> VersionCheckResponse {
    let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
    let url = URL(string: "https://api.luuniensuki.com/api/v1/app/version/check?platform=ios&current_version=\(version)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(VersionCheckResponse.self, from: data)
}
```

### Android (Kotlin)
```kotlin
suspend fun checkVersion(): VersionCheckResponse {
    val version = BuildConfig.VERSION_NAME
    val url = "https://api.luuniensuki.com/api/v1/app/version/check?platform=android&current_version=$version"
    return client.get(url).body()
}
```

---

## Common Scenarios

### Scenario 1: New App Release
1. Release app to App Store / Play Store
2. Wait for app to be approved and live
3. Create version entry with `is_current=true`:
   ```json
   {
     "platform": "android",
     "version": "1.3.0",
     "version_code": 5,
     "min_required_version": "1.2.0",
     "is_current": true,
     "force_update": false
   }
   ```

### Scenario 2: Critical Security Bug
1. Release fixed app version to stores
2. Update version entry to force update:
   ```json
   {
     "force_update": true,
     "release_notes": "CRITICAL SECURITY UPDATE"
   }
   ```
3. All users on older versions will be forced to update

### Scenario 3: Deprecate Old Versions
1. Create new version with higher `min_required_version`:
   ```json
   {
     "platform": "android",
     "version": "2.0.0",
     "version_code": 10,
     "min_required_version": "1.8.0",  // Users below 1.8.0 must update
     "is_current": true
   }
   ```

---

## Response Examples

### No Update Needed
```json
{
  "update_available": false,
  "force_update": false,
  "latest_version": "1.2.0",
  "current_version": "1.2.0"
}
```

### Optional Update
```json
{
  "update_available": true,
  "force_update": false,
  "latest_version": "1.3.0",
  "current_version": "1.2.0",
  "download_url": "https://play.google.com/...",
  "release_notes": "New features and improvements"
}
```

### Forced Update
```json
{
  "update_available": true,
  "force_update": true,
  "latest_version": "1.3.0",
  "current_version": "1.0.0",
  "min_required_version": "1.2.0",
  "download_url": "https://play.google.com/...",
  "release_notes": "Critical security update required"
}
```

---

## Files Changed

- `backend/models.py` - Added AppVersion model
- `backend/main.py` - Added 4 endpoints + helper functions
- `backend/schemas.py` - Added 4 schemas
- `migrations/versions/0019_app_versions.py` - Migration

---

## Testing Checklist

- [ ] Migration runs successfully
- [ ] Can create version for Android
- [ ] Can create version for iOS
- [ ] Version check returns correct data for current version
- [ ] Version check detects update available
- [ ] Version check enforces force_update
- [ ] Only one version per platform can be is_current=true
- [ ] Invalid version format handled gracefully
- [ ] Admin endpoints require authentication
- [ ] Public endpoint works without auth

---

## Troubleshooting

**Migration fails**: Check if table already exists
```sql
SELECT * FROM alembic_version;
DROP TABLE IF EXISTS app_versions;  -- If needed
```

**Version check always returns no update**: Verify version entry has `is_current=true`
```sql
SELECT * FROM app_versions WHERE platform='android' AND is_current=true;
```

**Force update not working**: Check version comparison
```sql
SELECT version, min_required_version, force_update 
FROM app_versions 
WHERE platform='android' AND is_current=true;
```

---

## Related Files

- `P0-MOB-02_IMPLEMENTATION.md` - Full implementation guide
- `P0-MOB-02_API_REFERENCE.md` - Complete API documentation
- `backend/models.py` - Database model
- `backend/main.py` - API endpoints
- `backend/schemas.py` - Request/response schemas

