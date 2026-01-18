# P0-MOB-02: App Version Check + Forced Update Implementation

## Overview

This implementation adds mobile app version management with forced update capabilities to the Luuniensuki LMS backend.

## Implementation Summary

### 1. Database Model (backend/models.py)

Added `AppVersion` model with the following fields:

- **id**: UUID primary key
- **platform**: String ("ios" or "android")
- **version**: Semantic version string (e.g., "1.2.3")
- **version_code**: Integer build number
- **min_required_version**: Minimum supported version
- **is_current**: Boolean flag for latest version
- **force_update**: Boolean to enforce mandatory updates
- **release_notes**: Optional release notes text
- **download_url**: Optional app store/play store link
- **released_at**: Release timestamp
- **created_at**: Creation timestamp

**Indexes:**
- `idx_app_versions_platform` - for platform filtering
- `idx_app_versions_is_current` - for quick current version lookup
- `idx_app_versions_released_at` - for chronological sorting

**Constraints:**
- `uq_app_version_platform_version` - unique constraint on (platform, version)

### 2. Database Migration (migrations/versions/0019_app_versions.py)

- Creates `app_versions` table
- Adds all necessary indexes and constraints
- Includes upgrade and downgrade functions
- Follows existing migration patterns with safety checks

### 3. API Schemas (backend/schemas.py)

Added the following Pydantic schemas:

#### AppVersionCheckOut
Response for version check endpoint:
```python
{
    "update_available": bool,
    "force_update": bool,
    "latest_version": str | null,
    "current_version": str,
    "min_required_version": str | null,
    "download_url": str | null,
    "release_notes": str | null
}
```

#### AppVersionOut
Response for admin version listing:
```python
{
    "id": UUID,
    "platform": str,
    "version": str,
    "version_code": int,
    "min_required_version": str,
    "is_current": bool,
    "force_update": bool,
    "release_notes": str | null,
    "download_url": str | null,
    "released_at": datetime,
    "created_at": datetime
}
```

#### AppVersionCreateIn
Input for creating new version:
```python
{
    "platform": str,  # "ios" or "android"
    "version": str,
    "version_code": int,
    "min_required_version": str,
    "is_current": bool,
    "force_update": bool,
    "release_notes": str | null,
    "download_url": str | null,
    "released_at": datetime | null
}
```

#### AppVersionUpdateIn
Input for updating existing version:
```python
{
    "is_current": bool | null,
    "force_update": bool | null,
    "release_notes": str | null,
    "download_url": str | null
}
```

### 4. API Endpoints (backend/main.py)

#### Public Endpoint

**GET /api/v1/app/version/check**
- **Authentication**: None (public)
- **Query Parameters**:
  - `platform`: "ios" or "android" (required)
  - `current_version`: Current app version, e.g., "1.2.3" (required)
- **Response**: `AppVersionCheckOut`
- **Description**: Checks if app update is available or required

**Logic:**
1. Fetches latest version for platform (where `is_current=true`)
2. Compares current version with latest version (semantic versioning)
3. Checks if current < min_required_version → force_update
4. Returns update status with download URL and release notes

#### Admin Endpoints

**GET /api/v1/admin/app/versions**
- **Authentication**: Admin only
- **Query Parameters**:
  - `platform`: Optional filter ("ios" or "android")
- **Response**: `list[AppVersionOut]`
- **Description**: Lists all app versions, optionally filtered by platform

**POST /api/v1/admin/app/versions**
- **Authentication**: Admin only
- **Request Body**: `AppVersionCreateIn`
- **Response**: `AppVersionOut` (201 Created)
- **Description**: Creates a new app version entry
- **Features**:
  - Validates semantic version format
  - Prevents duplicate platform + version combinations
  - Auto-unsets `is_current` for other versions if new one is marked current

**PUT /api/v1/admin/app/versions/{version_id}**
- **Authentication**: Admin only
- **Request Body**: `AppVersionUpdateIn`
- **Response**: `AppVersionOut`
- **Description**: Updates an existing app version entry
- **Features**:
  - Allows updating flags and metadata
  - Auto-manages `is_current` flag consistency

### 5. Version Comparison Logic

**Helper Functions:**

**_parse_semver(version_str: str) -> tuple[int, int, int]**
- Parses "major.minor.patch" format
- Raises HTTPException on invalid format

**_compare_versions(version1: str, version2: str) -> int**
- Returns -1 if version1 < version2
- Returns 0 if equal
- Returns 1 if version1 > version2
- Uses tuple comparison for semantic versioning

**Force Update Logic:**
1. If `current_version < min_required_version` → force_update = true
2. If `force_update` flag is set on version entry AND update available → force_update = true
3. Otherwise → force_update = false

## Testing Guide

### 1. Create Test Version Entries

```bash
# Create initial version for Android
curl -X POST "http://localhost:8000/api/v1/admin/app/versions" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
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

# Create newer version with forced update
curl -X POST "http://localhost:8000/api/v1/admin/app/versions" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "android",
    "version": "1.2.0",
    "version_code": 3,
    "min_required_version": "1.1.0",
    "is_current": true,
    "force_update": false,
    "release_notes": "Bug fixes and performance improvements",
    "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki"
  }'
```

### 2. Test Version Check (Public Endpoint)

```bash
# Check with current version (no update needed)
curl "http://localhost:8000/api/v1/app/version/check?platform=android&current_version=1.2.0"

# Expected Response:
# {
#   "update_available": false,
#   "force_update": false,
#   "latest_version": "1.2.0",
#   "current_version": "1.2.0",
#   "min_required_version": "1.1.0",
#   "download_url": "...",
#   "release_notes": "..."
# }

# Check with older version (update available)
curl "http://localhost:8000/api/v1/app/version/check?platform=android&current_version=1.1.5"

# Expected Response:
# {
#   "update_available": true,
#   "force_update": false,
#   "latest_version": "1.2.0",
#   ...
# }

# Check with very old version (forced update)
curl "http://localhost:8000/api/v1/app/version/check?platform=android&current_version=1.0.5"

# Expected Response:
# {
#   "update_available": true,
#   "force_update": true,
#   "latest_version": "1.2.0",
#   ...
# }
```

### 3. Test Admin Endpoints

```bash
# List all versions
curl "http://localhost:8000/api/v1/admin/app/versions" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# List versions for specific platform
curl "http://localhost:8000/api/v1/admin/app/versions?platform=ios" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Update version to force update
curl -X PUT "http://localhost:8000/api/v1/admin/app/versions/{VERSION_ID}" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "force_update": true,
    "release_notes": "Critical security update - please update immediately"
  }'
```

### 4. Run Database Migration

```bash
cd /Users/nguyennt/Documents/luuniensuki-lms

# Run migration
docker-compose exec backend alembic upgrade head

# Or if running locally:
# alembic upgrade head

# Verify migration
docker-compose exec backend alembic current
```

## Mobile Integration Guide

### iOS Integration

```swift
struct VersionCheckResponse: Codable {
    let updateAvailable: Bool
    let forceUpdate: Bool
    let latestVersion: String?
    let currentVersion: String
    let downloadUrl: String?
    let releaseNotes: String?
}

func checkAppVersion() async throws -> VersionCheckResponse {
    let currentVersion = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
    let url = URL(string: "https://api.luuniensuki.com/api/v1/app/version/check?platform=ios&current_version=\(currentVersion)")!
    
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(VersionCheckResponse.self, from: data)
}

// Usage in app launch
func handleVersionCheck() async {
    do {
        let versionInfo = try await checkAppVersion()
        
        if versionInfo.forceUpdate {
            // Show non-dismissible update dialog
            showForceUpdateDialog(
                latestVersion: versionInfo.latestVersion,
                releaseNotes: versionInfo.releaseNotes,
                downloadUrl: versionInfo.downloadUrl
            )
        } else if versionInfo.updateAvailable {
            // Show optional update dialog
            showOptionalUpdateDialog(
                latestVersion: versionInfo.latestVersion,
                releaseNotes: versionInfo.releaseNotes,
                downloadUrl: versionInfo.downloadUrl
            )
        }
    } catch {
        // Handle error silently - don't block app usage
        print("Version check failed: \(error)")
    }
}
```

### Android Integration

```kotlin
data class VersionCheckResponse(
    val updateAvailable: Boolean,
    val forceUpdate: Boolean,
    val latestVersion: String?,
    val currentVersion: String,
    val downloadUrl: String?,
    val releaseNotes: String?
)

suspend fun checkAppVersion(): VersionCheckResponse {
    val currentVersion = BuildConfig.VERSION_NAME
    val url = "https://api.luuniensuki.com/api/v1/app/version/check?platform=android&current_version=$currentVersion"
    
    return withContext(Dispatchers.IO) {
        val response = client.get(url)
        response.body()
    }
}

// Usage in MainActivity onCreate or Application class
lifecycleScope.launch {
    try {
        val versionInfo = checkAppVersion()
        
        when {
            versionInfo.forceUpdate -> {
                // Show non-cancellable dialog
                showForceUpdateDialog(
                    latestVersion = versionInfo.latestVersion,
                    releaseNotes = versionInfo.releaseNotes,
                    downloadUrl = versionInfo.downloadUrl
                )
            }
            versionInfo.updateAvailable -> {
                // Show dismissible notification
                showOptionalUpdateNotification(
                    latestVersion = versionInfo.latestVersion,
                    releaseNotes = versionInfo.releaseNotes,
                    downloadUrl = versionInfo.downloadUrl
                )
            }
        }
    } catch (e: Exception) {
        // Log error but don't block app
        Log.e("VersionCheck", "Failed to check version", e)
    }
}
```

## Deployment Checklist

- [ ] Run migration: `alembic upgrade head`
- [ ] Verify `app_versions` table created
- [ ] Create initial version entries for both iOS and Android
- [ ] Test version check endpoint with various version combinations
- [ ] Update mobile apps to call version check on launch
- [ ] Document version management workflow for team
- [ ] Set up monitoring/alerts for version check endpoint
- [ ] Plan release process for forced updates

## Admin Workflow

### Releasing a New Version

1. **Build and release app** to App Store / Play Store
2. **Create version entry**:
   ```bash
   POST /api/v1/admin/app/versions
   {
     "platform": "android",
     "version": "1.3.0",
     "version_code": 5,
     "min_required_version": "1.2.0",  # Users below this MUST update
     "is_current": true,
     "force_update": false,
     "release_notes": "What's new...",
     "download_url": "https://play.google.com/..."
   }
   ```

### Forcing an Update (Critical Bug/Security Issue)

1. **Update existing current version**:
   ```bash
   PUT /api/v1/admin/app/versions/{version_id}
   {
     "force_update": true,
     "release_notes": "Critical security update required"
   }
   ```

2. Or **create new version** with higher `min_required_version`

## Files Modified

1. **backend/models.py** - Added `AppVersion` model
2. **backend/main.py** - Added import and 4 new endpoints
3. **backend/schemas.py** - Added 4 new schema classes
4. **migrations/versions/0019_app_versions.py** - New migration file

## Next Steps

1. Test migration in development
2. Test all endpoints with various scenarios
3. Integrate version check in mobile apps
4. Create initial version entries for production
5. Monitor version check API usage
6. Document internal process for version releases

## Notes

- Version check endpoint is **public** (no auth required) to allow checks before user login
- Semantic versioning (major.minor.patch) is required
- Only one version per platform can have `is_current=true`
- Invalid version formats are handled gracefully (don't block app)
- Force update logic uses both `min_required_version` comparison AND `force_update` flag

