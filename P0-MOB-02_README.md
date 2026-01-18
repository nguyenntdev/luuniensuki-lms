# P0-MOB-02: App Version Check + Forced Update

**Status**: ✅ Implementation Complete  
**Date**: January 19, 2025  
**Feature**: Mobile app version management with forced update capabilities

---

## 🚀 Quick Start

### 1. Deploy (Run Migration)
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
docker-compose exec backend alembic upgrade head
```

### 2. Test
```bash
ADMIN_TOKEN=your_token ./test_app_version_api.sh
```

### 3. Read Documentation
Start with [`P0-MOB-02_INDEX.md`](./P0-MOB-02_INDEX.md) for navigation.

---

## 📚 Documentation Files

All documentation is organized for easy navigation:

### 🗂️ [`P0-MOB-02_INDEX.md`](./P0-MOB-02_INDEX.md)
**Start here!** Navigation hub with:
- Overview of all documentation
- Quick links to specific topics
- Common use cases
- Troubleshooting guide

### 📖 [`P0-MOB-02_IMPLEMENTATION.md`](./P0-MOB-02_IMPLEMENTATION.md)
**For developers** - Complete technical guide:
- Database model details
- API endpoint specifications
- Version comparison logic
- Mobile integration examples (iOS & Android)
- Testing guide

### 📚 [`P0-MOB-02_API_REFERENCE.md`](./P0-MOB-02_API_REFERENCE.md)
**For API consumers** - Full API documentation:
- Endpoint specifications
- Request/response schemas
- Query parameters
- Example requests
- Error responses

### ⚡ [`P0-MOB-02_QUICK_REFERENCE.md`](./P0-MOB-02_QUICK_REFERENCE.md)
**For quick lookups** - Cheat sheet with:
- Common curl commands
- Database queries
- Version check logic
- Mobile code snippets
- Troubleshooting tips

### ✅ [`P0-MOB-02_DEPLOYMENT_CHECKLIST.md`](./P0-MOB-02_DEPLOYMENT_CHECKLIST.md)
**For deployment** - Step-by-step checklist:
- Pre-deployment checks
- Deployment steps
- Verification procedures
- Rollback plan
- Monitoring setup

### 📋 [`P0-MOB-02_COMPLETE.md`](./P0-MOB-02_COMPLETE.md)
**Implementation summary** - High-level overview:
- What was implemented
- Success criteria
- Next steps
- File changes summary

---

## 🧪 Testing

### Automated Testing
```bash
chmod +x test_app_version_api.sh
ADMIN_TOKEN=your_token ./test_app_version_api.sh
```

The test script includes 12 comprehensive test scenarios.

### Manual Testing
See [`P0-MOB-02_QUICK_REFERENCE.md`](./P0-MOB-02_QUICK_REFERENCE.md) for manual test commands.

---

## 🏗️ Implementation Overview

### What Was Built

1. **Database Model**: `AppVersion` model in `backend/models.py`
2. **Migration**: `migrations/versions/0019_app_versions.py`
3. **API Endpoints**: 4 endpoints in `backend/main.py`
   - GET `/api/v1/app/version/check` (public)
   - GET `/api/v1/admin/app/versions` (admin)
   - POST `/api/v1/admin/app/versions` (admin)
   - PUT `/api/v1/admin/app/versions/{id}` (admin)
4. **Schemas**: 4 Pydantic schemas in `backend/schemas.py`
5. **Version Logic**: Semantic version comparison + force update
6. **Documentation**: 6 comprehensive documentation files
7. **Testing**: Automated test script

### Key Features

- ✅ Semantic version comparison (major.minor.patch)
- ✅ Optional vs forced updates
- ✅ Platform-specific (iOS & Android)
- ✅ Release notes & download URLs
- ✅ Admin-only version management
- ✅ Public version check (no auth)
- ✅ Graceful error handling

---

## 📁 File Changes

### Backend Code
```
backend/
├── models.py              [MODIFIED] +41 lines (AppVersion model)
├── main.py                [MODIFIED] +285 lines (endpoints + helpers)
└── schemas.py             [MODIFIED] +69 lines (4 schemas)

migrations/versions/
└── 0019_app_versions.py   [CREATED] Migration file
```

### Documentation
```
P0-MOB-02_INDEX.md                  [CREATED] Documentation index
P0-MOB-02_IMPLEMENTATION.md         [CREATED] Full implementation guide
P0-MOB-02_API_REFERENCE.md          [CREATED] Complete API docs
P0-MOB-02_QUICK_REFERENCE.md        [CREATED] Quick reference
P0-MOB-02_DEPLOYMENT_CHECKLIST.md   [CREATED] Deployment guide
P0-MOB-02_COMPLETE.md               [CREATED] Implementation summary
P0-MOB-02_README.md                 [CREATED] This file
```

### Testing
```
test_app_version_api.sh    [CREATED] Automated test script (executable)
```

---

## 🎯 Use Cases

### 1. Check for Updates (Mobile App)
```bash
curl "http://localhost:8000/api/v1/app/version/check?platform=android&current_version=1.0.0"
```

Response tells app:
- Is update available?
- Is update required (forced)?
- Where to download?
- What's new?

### 2. Release New Version (Admin)
```bash
curl -X POST "http://localhost:8000/api/v1/admin/app/versions" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"platform":"android","version":"1.1.0",...}'
```

### 3. Force Update (Critical Bug Fix)
```bash
curl -X PUT "http://localhost:8000/api/v1/admin/app/versions/{id}" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"force_update":true}'
```

All users on older versions will be required to update.

---

## 🔍 How It Works

### Version Check Flow

```
Mobile App Launch
    ↓
Call /api/v1/app/version/check
    ↓
Backend compares versions:
- current_version vs latest_version → update_available
- current_version vs min_required_version → force_update
    ↓
Return result to app
    ↓
App shows:
- Nothing (up to date)
- Optional update dialog
- Forced update dialog (blocking)
```

### Version Comparison Logic

```python
# Semantic versioning: major.minor.patch
"1.0.0" < "1.0.1" < "1.1.0" < "2.0.0"

# Force update triggers when:
current < min_required_version  OR  force_update flag is set
```

See [`P0-MOB-02_IMPLEMENTATION.md`](./P0-MOB-02_IMPLEMENTATION.md) for detailed logic.

---

## 📱 Mobile Integration

### iOS (Swift)
```swift
func checkAppVersion() async throws -> VersionCheckResponse {
    let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
    let url = URL(string: "https://api.luuniensuki.com/api/v1/app/version/check?platform=ios&current_version=\(version)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(VersionCheckResponse.self, from: data)
}
```

### Android (Kotlin)
```kotlin
suspend fun checkAppVersion(): VersionCheckResponse {
    val version = BuildConfig.VERSION_NAME
    return client.get("https://api.luuniensuki.com/api/v1/app/version/check") {
        parameter("platform", "android")
        parameter("current_version", version)
    }.body()
}
```

Full integration examples in [`P0-MOB-02_IMPLEMENTATION.md`](./P0-MOB-02_IMPLEMENTATION.md).

---

## 🔐 Security

- ✅ Public endpoint returns only necessary data
- ✅ Admin endpoints require authentication
- ✅ Input validation on all fields
- ✅ No sensitive data in responses
- ✅ Version format validated

---

## 📊 Database Schema

```sql
CREATE TABLE app_versions (
    id UUID PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,           -- 'ios' or 'android'
    version VARCHAR(20) NOT NULL,            -- '1.2.3'
    version_code INTEGER NOT NULL,           -- Build number
    min_required_version VARCHAR(20),        -- Minimum supported version
    is_current BOOLEAN DEFAULT FALSE,        -- Latest version flag
    force_update BOOLEAN DEFAULT FALSE,      -- Force update flag
    release_notes TEXT,                      -- What's new
    download_url VARCHAR(500),               -- App store link
    released_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_platform_version UNIQUE(platform, version)
);
```

---

## 🚦 Next Steps

### Immediate (Required for Deployment)
1. ✅ Code implemented → **DONE**
2. ⏳ Run migration → `alembic upgrade head`
3. ⏳ Create initial versions
4. ⏳ Test endpoints
5. ⏳ Integrate in mobile apps

### Near-Term (Recommended)
- Set up monitoring
- Add analytics tracking
- Document release process
- Train team on version management

### Future Enhancements
- Beta/alpha channel support
- Scheduled releases
- A/B testing for updates
- Localized release notes

See [`P0-MOB-02_DEPLOYMENT_CHECKLIST.md`](./P0-MOB-02_DEPLOYMENT_CHECKLIST.md) for full deployment plan.

---

## 🆘 Support

### Need Help?

1. **Start Here**: [`P0-MOB-02_INDEX.md`](./P0-MOB-02_INDEX.md)
2. **API Questions**: [`P0-MOB-02_API_REFERENCE.md`](./P0-MOB-02_API_REFERENCE.md)
3. **Implementation Details**: [`P0-MOB-02_IMPLEMENTATION.md`](./P0-MOB-02_IMPLEMENTATION.md)
4. **Quick Lookup**: [`P0-MOB-02_QUICK_REFERENCE.md`](./P0-MOB-02_QUICK_REFERENCE.md)
5. **Deployment**: [`P0-MOB-02_DEPLOYMENT_CHECKLIST.md`](./P0-MOB-02_DEPLOYMENT_CHECKLIST.md)

### Troubleshooting

Common issues and solutions in [`P0-MOB-02_QUICK_REFERENCE.md`](./P0-MOB-02_QUICK_REFERENCE.md) → Troubleshooting section.

---

## ✅ Implementation Complete

All requirements met:
- ✅ Database model
- ✅ Migration
- ✅ API endpoints (4)
- ✅ Version logic
- ✅ Schemas
- ✅ Documentation
- ✅ Testing script

**Ready for deployment!**

---

## 📝 License & Credits

Part of the Luuniensuki LMS project.  
Implementation: P0-MOB-02  
Date: January 2025

