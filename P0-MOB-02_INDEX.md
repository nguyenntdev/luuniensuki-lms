# P0-MOB-02: App Version Check + Forced Update - Documentation Index

## 📚 Overview

This feature adds mobile app version management with forced update capabilities to the Luuniensuki LMS backend. It allows admins to manage app releases and enforce mandatory updates when critical bugs or security issues are discovered.

## 📖 Documentation Files

### 1. **P0-MOB-02_IMPLEMENTATION.md**
**Full Implementation Guide**

Complete technical implementation documentation including:
- Database model details
- Migration instructions
- API endpoint specifications
- Version comparison logic
- Mobile integration examples (iOS & Android)
- Testing guide
- Deployment checklist
- Admin workflow

**When to use**: For understanding the complete implementation or integrating with mobile apps.

---

### 2. **P0-MOB-02_API_REFERENCE.md**
**Complete API Documentation**

Comprehensive API reference with:
- Endpoint specifications
- Request/response schemas
- Query parameters
- Error responses
- Example requests and responses
- Best practices
- Version format requirements

**When to use**: For developers integrating with the API or looking up specific endpoint details.

---

### 3. **P0-MOB-02_QUICK_REFERENCE.md**
**Quick Reference & Cheat Sheet**

Quick access to:
- Common curl commands
- API endpoint summary
- Database schema
- Version check logic diagram
- Mobile code snippets
- Common scenarios
- Troubleshooting tips

**When to use**: For quick lookups during development or testing.

---

### 4. **test_app_version_api.sh**
**Automated Testing Script**

Bash script that tests all endpoints:
- Creates test versions
- Tests version check logic
- Validates force update
- Tests admin endpoints
- Verifies authentication
- Tests error cases

**When to use**: For automated testing after deployment or changes.

Usage:
```bash
ADMIN_TOKEN=your_token ./test_app_version_api.sh
```

---

## 🚀 Quick Start

### 1. Run Migration
```bash
docker-compose exec backend alembic upgrade head
```

### 2. Create Initial Versions
```bash
curl -X POST "http://localhost:8000/api/v1/admin/app/versions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "android",
    "version": "1.0.0",
    "version_code": 1,
    "min_required_version": "1.0.0",
    "is_current": true,
    "force_update": false,
    "download_url": "https://play.google.com/..."
  }'
```

### 3. Test Version Check
```bash
curl "http://localhost:8000/api/v1/app/version/check?platform=android&current_version=1.0.0"
```

---

## 🔑 Key Concepts

### Version Check Logic
1. **Update Available**: Current version < Latest version
2. **Force Update**: Current version < Min required version OR force_update flag is set
3. **No Update**: Current version >= Latest version

### Semantic Versioning
- Format: `MAJOR.MINOR.PATCH` (e.g., "1.2.3")
- Comparison: Version components compared as integers
- Example: `1.0.0 < 1.0.1 < 1.1.0 < 2.0.0`

### Force Update Triggers
1. User's version < `min_required_version` field
2. Version entry has `force_update=true` AND update is available

---

## 📊 API Endpoints Summary

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/v1/app/version/check` | GET | None | Check if update needed |
| `/api/v1/admin/app/versions` | GET | Admin | List versions |
| `/api/v1/admin/app/versions` | POST | Admin | Create version |
| `/api/v1/admin/app/versions/{id}` | PUT | Admin | Update version |

---

## 🗂️ File Structure

### Backend Files
```
backend/
├── models.py                    # AppVersion model (lines 1817-1858)
├── main.py                      # API endpoints (lines 10657-10948)
├── schemas.py                   # Pydantic schemas (lines 1435-1488)
└── routes/                      # (Future: could extract to separate route file)

migrations/
└── versions/
    └── 0019_app_versions.py     # Database migration
```

### Documentation Files
```
P0-MOB-02_IMPLEMENTATION.md      # Full implementation guide
P0-MOB-02_API_REFERENCE.md       # Complete API docs
P0-MOB-02_QUICK_REFERENCE.md     # Quick reference & cheat sheet
P0-MOB-02_INDEX.md               # This file
test_app_version_api.sh          # Automated test script
```

---

## 🎯 Common Use Cases

### Use Case 1: New App Release
1. Release app to store
2. Create version entry with `is_current=true`
3. Mobile apps check on launch and show update prompt

**See**: Implementation Guide → Admin Workflow → Releasing a New Version

---

### Use Case 2: Critical Security Bug
1. Fix bug and release new version
2. Update version entry: `force_update=true`
3. All users on older versions forced to update

**See**: Implementation Guide → Admin Workflow → Forcing an Update

---

### Use Case 3: Deprecate Old Versions
1. Create new version with higher `min_required_version`
2. Users below min version get force update

**See**: Quick Reference → Common Scenarios → Deprecate Old Versions

---

## 🧪 Testing

### Manual Testing
```bash
# 1. Create test version
curl -X POST .../api/v1/admin/app/versions -d {...}

# 2. Check version (public)
curl .../api/v1/app/version/check?platform=android&current_version=1.0.0

# 3. List versions (admin)
curl .../api/v1/admin/app/versions -H "Authorization: Bearer ..."
```

### Automated Testing
```bash
ADMIN_TOKEN=your_token ./test_app_version_api.sh
```

**See**: test_app_version_api.sh for complete test suite

---

## 📱 Mobile Integration

### iOS
```swift
func checkAppVersion() async throws -> VersionCheckResponse {
    let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
    let url = URL(string: "https://api.luuniensuki.com/api/v1/app/version/check?platform=ios&current_version=\(version)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(VersionCheckResponse.self, from: data)
}
```

### Android
```kotlin
suspend fun checkAppVersion(): VersionCheckResponse {
    val version = BuildConfig.VERSION_NAME
    val url = "https://api.luuniensuki.com/api/v1/app/version/check?platform=android&current_version=$version"
    return client.get(url).body()
}
```

**See**: Implementation Guide → Mobile Integration Guide for complete examples

---

## 🔧 Troubleshooting

### Migration Issues
**Problem**: Migration fails
**Solution**: Check if table exists, verify alembic version
```sql
SELECT * FROM alembic_version;
```

### Version Check Returns No Update
**Problem**: Version check always says no update needed
**Solution**: Verify version has `is_current=true`
```sql
SELECT * FROM app_versions WHERE platform='android' AND is_current=true;
```

### Force Update Not Working
**Problem**: Users not forced to update
**Solution**: Check version comparison and flags
```sql
SELECT version, min_required_version, force_update 
FROM app_versions 
WHERE platform='android' AND is_current=true;
```

**See**: Quick Reference → Troubleshooting for more solutions

---

## 📋 Deployment Checklist

- [ ] Run migration: `alembic upgrade head`
- [ ] Verify table created: `SELECT * FROM app_versions;`
- [ ] Create initial version entries for iOS and Android
- [ ] Test version check endpoint
- [ ] Update mobile apps to integrate version check
- [ ] Test force update flow in mobile apps
- [ ] Document release process for team
- [ ] Set up monitoring for version check endpoint

**See**: Implementation Guide → Deployment Checklist for complete list

---

## 🔐 Security Considerations

1. **Public Endpoint**: Version check is public (no auth) - ensure no sensitive data in responses
2. **Admin Only**: Version management requires admin authentication
3. **Rate Limiting**: Consider adding rate limiting if abuse detected
4. **Input Validation**: Version format validated (semantic versioning)
5. **Error Handling**: Invalid versions handled gracefully without blocking app

---

## 📈 Monitoring Recommendations

Track these metrics:
- Version distribution (how many users on each version)
- Update adoption rate (how quickly users update)
- Force update impact (users affected)
- API response times
- Error rates

**Tools**: Use AnalyticsEvent table or external monitoring (Datadog, etc.)

---

## 🤝 Support & Contributing

### Questions?
- Check documentation files in this index
- Review code comments in `backend/main.py`
- Run test script to understand behavior

### Found a Bug?
- Check troubleshooting section
- Review implementation guide
- Check server logs

### Making Changes?
- Update all relevant documentation files
- Run test script to verify changes
- Update migration if schema changes

---

## 📝 Version History

- **2025-01-19**: Initial implementation (P0-MOB-02)
  - Added AppVersion model
  - Created migration 0019_app_versions
  - Implemented 4 API endpoints
  - Added version comparison logic
  - Created comprehensive documentation

---

## 🔗 Related Features

- **P0-MOB-01**: Device fingerprinting and session tracking
- **User Sessions**: Tracks app_version in user sessions
- **Analytics**: Can track version distribution via analytics events

---

## 📞 Quick Links

- [Full Implementation](./P0-MOB-02_IMPLEMENTATION.md)
- [API Reference](./P0-MOB-02_API_REFERENCE.md)
- [Quick Reference](./P0-MOB-02_QUICK_REFERENCE.md)
- [Test Script](./test_app_version_api.sh)
- [Main Application](./backend/main.py#L10657-L10948)
- [Database Model](./backend/models.py#L1817-L1858)
- [Schemas](./backend/schemas.py#L1435-L1488)
- [Migration](./migrations/versions/0019_app_versions.py)

