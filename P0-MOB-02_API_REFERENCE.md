# P0-MOB-02: App Version Management - API Reference

## Table of Contents

1. [Overview](#overview)
2. [Public Endpoints](#public-endpoints)
3. [Admin Endpoints](#admin-endpoints)
4. [Data Models](#data-models)
5. [Error Responses](#error-responses)
6. [Examples](#examples)

---

## Overview

The App Version Management API provides endpoints for:
- Checking if mobile app updates are available
- Enforcing mandatory updates for critical fixes
- Managing version releases for iOS and Android platforms

**Base URL**: `https://api.luuniensuki.com` or your configured backend URL

---

## Public Endpoints

### Check App Version

Check if an app update is available or required.

**Endpoint**: `GET /api/v1/app/version/check`

**Authentication**: None (public endpoint)

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| platform | string | Yes | Platform identifier: "ios" or "android" |
| current_version | string | Yes | Current app version in semantic format (e.g., "1.2.3") |

**Response**: `200 OK`

```json
{
  "update_available": false,
  "force_update": false,
  "latest_version": "1.2.3",
  "current_version": "1.2.3",
  "min_required_version": "1.1.0",
  "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki",
  "release_notes": "Bug fixes and performance improvements"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| update_available | boolean | True if a newer version exists |
| force_update | boolean | True if user MUST update (current < min_required) |
| latest_version | string \| null | Latest available version number |
| current_version | string | Echo of the version sent in request |
| min_required_version | string \| null | Minimum version required to use the app |
| download_url | string \| null | App Store or Play Store link |
| release_notes | string \| null | What's new in the latest version |

**Behavior**:
- If no version info exists for platform → returns `update_available=false, force_update=false`
- If current version format is invalid → logs warning, returns `update_available=false, force_update=false`
- `force_update=true` when:
  - `current_version < min_required_version`, OR
  - Version entry has `force_update=true` AND update is available

---

## Admin Endpoints

All admin endpoints require authentication with admin role.

**Authentication**: Bearer token in `Authorization` header

```
Authorization: Bearer YOUR_JWT_TOKEN
```

### List App Versions

Get all app versions, optionally filtered by platform.

**Endpoint**: `GET /api/v1/admin/app/versions`

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| platform | string | No | Filter by platform: "ios" or "android" |

**Response**: `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "platform": "android",
    "version": "1.2.0",
    "version_code": 3,
    "min_required_version": "1.0.0",
    "is_current": true,
    "force_update": false,
    "release_notes": "Bug fixes and improvements",
    "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki",
    "released_at": "2025-01-15T10:00:00Z",
    "created_at": "2025-01-15T09:30:00Z"
  }
]
```

**Response Fields**: See [Data Models](#data-models) section.

---

### Create App Version

Create a new app version entry.

**Endpoint**: `POST /api/v1/admin/app/versions`

**Request Body**:

```json
{
  "platform": "android",
  "version": "1.3.0",
  "version_code": 5,
  "min_required_version": "1.1.0",
  "is_current": true,
  "force_update": false,
  "release_notes": "New features:\n- Feature A\n- Feature B\n\nBug fixes:\n- Fixed issue #123",
  "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki",
  "released_at": "2025-01-20T10:00:00Z"
}
```

**Request Fields**:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| platform | string | Yes | "ios" or "android" | Platform identifier |
| version | string | Yes | Semantic version | Version number (e.g., "1.2.3") |
| version_code | integer | Yes | >= 1 | Build number (incremental) |
| min_required_version | string | Yes | Semantic version | Minimum supported version |
| is_current | boolean | No | - | Mark as latest version (default: false) |
| force_update | boolean | No | - | Force users to update (default: false) |
| release_notes | string | No | - | Release notes text (supports markdown) |
| download_url | string | No | - | App store/play store URL |
| released_at | datetime | No | - | Release timestamp (default: now) |

**Response**: `201 Created`

Returns the created version object (see [Data Models](#data-models)).

**Errors**:

- `400 Bad Request`: Invalid version format
- `409 Conflict`: Version already exists for this platform
- `403 Forbidden`: Not an admin user

**Special Behavior**:
- If `is_current=true`, automatically unsets `is_current` for all other versions of the same platform
- Version and min_required_version must be in semantic version format (major.minor.patch)

---

### Update App Version

Update an existing app version entry.

**Endpoint**: `PUT /api/v1/admin/app/versions/{version_id}`

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| version_id | UUID | ID of the version to update |

**Request Body**:

```json
{
  "is_current": true,
  "force_update": true,
  "release_notes": "CRITICAL SECURITY UPDATE\n\nPlease update immediately to fix security vulnerability.",
  "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki"
}
```

**Request Fields** (all optional):

| Field | Type | Description |
|-------|------|-------------|
| is_current | boolean | Update current version flag |
| force_update | boolean | Toggle forced update |
| release_notes | string | Update release notes |
| download_url | string | Update download URL |

**Response**: `200 OK`

Returns the updated version object.

**Errors**:

- `404 Not Found`: Version ID not found
- `403 Forbidden`: Not an admin user

**Special Behavior**:
- If `is_current=true`, automatically unsets `is_current` for all other versions of the same platform

---

## Data Models

### AppVersionOut

Complete app version object returned by admin endpoints.

```typescript
{
  id: UUID;
  platform: "ios" | "android";
  version: string;              // Semantic version, e.g., "1.2.3"
  version_code: number;         // Integer build number
  min_required_version: string; // Minimum version to use app
  is_current: boolean;          // True if this is the latest version
  force_update: boolean;        // True to force users to update
  release_notes: string | null; // Release notes text
  download_url: string | null;  // App store URL
  released_at: string;          // ISO 8601 datetime
  created_at: string;           // ISO 8601 datetime
}
```

### AppVersionCheckOut

Response from version check endpoint.

```typescript
{
  update_available: boolean;
  force_update: boolean;
  latest_version: string | null;
  current_version: string;
  min_required_version: string | null;
  download_url: string | null;
  release_notes: string | null;
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created (for POST requests) |
| 400 | Bad Request (validation error) |
| 403 | Forbidden (not authorized) |
| 404 | Not Found |
| 409 | Conflict (duplicate entry) |
| 422 | Unprocessable Entity (validation error) |
| 500 | Internal Server Error |

---

## Examples

### Example 1: Version Check - No Update Needed

**Request**:
```bash
curl "https://api.luuniensuki.com/api/v1/app/version/check?platform=android&current_version=1.2.0"
```

**Response**:
```json
{
  "update_available": false,
  "force_update": false,
  "latest_version": "1.2.0",
  "current_version": "1.2.0",
  "min_required_version": "1.0.0",
  "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki",
  "release_notes": "Bug fixes and improvements"
}
```

---

### Example 2: Version Check - Optional Update Available

**Request**:
```bash
curl "https://api.luuniensuki.com/api/v1/app/version/check?platform=android&current_version=1.1.0"
```

**Response**:
```json
{
  "update_available": true,
  "force_update": false,
  "latest_version": "1.2.0",
  "current_version": "1.1.0",
  "min_required_version": "1.0.0",
  "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki",
  "release_notes": "New features and improvements"
}
```

---

### Example 3: Version Check - Forced Update Required

**Request**:
```bash
curl "https://api.luuniensuki.com/api/v1/app/version/check?platform=android&current_version=0.9.5"
```

**Response**:
```json
{
  "update_available": true,
  "force_update": true,
  "latest_version": "1.2.0",
  "current_version": "0.9.5",
  "min_required_version": "1.0.0",
  "download_url": "https://play.google.com/store/apps/details?id=com.luuniensuki",
  "release_notes": "Critical update required for security and stability"
}
```

---

### Example 4: Create New Version (Admin)

**Request**:
```bash
curl -X POST "https://api.luuniensuki.com/api/v1/admin/app/versions" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "ios",
    "version": "1.3.0",
    "version_code": 10,
    "min_required_version": "1.1.0",
    "is_current": true,
    "force_update": false,
    "release_notes": "New features and improvements",
    "download_url": "https://apps.apple.com/app/luuniensuki/id123456789"
  }'
```

**Response** (`201 Created`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "ios",
  "version": "1.3.0",
  "version_code": 10,
  "min_required_version": "1.1.0",
  "is_current": true,
  "force_update": false,
  "release_notes": "New features and improvements",
  "download_url": "https://apps.apple.com/app/luuniensuki/id123456789",
  "released_at": "2025-01-20T10:00:00Z",
  "created_at": "2025-01-20T09:30:00Z"
}
```

---

### Example 5: Force Update on Existing Version (Admin)

**Request**:
```bash
curl -X PUT "https://api.luuniensuki.com/api/v1/admin/app/versions/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "force_update": true,
    "release_notes": "CRITICAL SECURITY UPDATE - Please update immediately"
  }'
```

**Response** (`200 OK`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "ios",
  "version": "1.3.0",
  "version_code": 10,
  "min_required_version": "1.1.0",
  "is_current": true,
  "force_update": true,
  "release_notes": "CRITICAL SECURITY UPDATE - Please update immediately",
  "download_url": "https://apps.apple.com/app/luuniensuki/id123456789",
  "released_at": "2025-01-20T10:00:00Z",
  "created_at": "2025-01-20T09:30:00Z"
}
```

---

### Example 6: List All Versions (Admin)

**Request**:
```bash
curl "https://api.luuniensuki.com/api/v1/admin/app/versions" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response** (`200 OK`):
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "platform": "android",
    "version": "1.2.0",
    "version_code": 3,
    "min_required_version": "1.0.0",
    "is_current": true,
    "force_update": false,
    "release_notes": "Android improvements",
    "download_url": "https://play.google.com/...",
    "released_at": "2025-01-15T10:00:00Z",
    "created_at": "2025-01-15T09:30:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "platform": "ios",
    "version": "1.3.0",
    "version_code": 10,
    "min_required_version": "1.1.0",
    "is_current": true,
    "force_update": true,
    "release_notes": "CRITICAL SECURITY UPDATE",
    "download_url": "https://apps.apple.com/...",
    "released_at": "2025-01-20T10:00:00Z",
    "created_at": "2025-01-20T09:30:00Z"
  }
]
```

---

## Version Format

Versions must follow **semantic versioning** format:

```
MAJOR.MINOR.PATCH
```

Examples:
- ✅ Valid: "1.0.0", "1.2.3", "2.0.1"
- ❌ Invalid: "1.0", "1", "v1.2.3", "1.2.3-beta"

Version comparison follows semantic versioning rules:
- "1.0.0" < "1.0.1" < "1.1.0" < "2.0.0"
- Each component is compared as an integer

---

## Best Practices

### For Mobile Developers

1. **Call version check early**: Check on app launch, before main UI loads
2. **Handle gracefully**: Don't block app if version check fails (network issues)
3. **Cache response**: Cache for 1-6 hours to reduce API calls
4. **Force update UI**: Non-dismissible dialog that blocks app usage
5. **Optional update UI**: Dismissible notification or banner

### For Backend Admins

1. **Test before release**: Create version entry in staging first
2. **Gradual rollout**: Set `is_current=true` only after app is live in stores
3. **Clear release notes**: Write user-friendly release notes
4. **Emergency updates**: Use `force_update=true` sparingly for critical issues
5. **Version history**: Keep old version entries for historical tracking

---

## Rate Limiting

Currently no rate limiting on version check endpoint (it's public and lightweight).

Consider adding rate limiting if abuse is detected:
- Recommended: 10 requests per minute per IP
- Or: 100 requests per day per device ID

---

## Monitoring

Recommended metrics to track:

1. **Version distribution**: How many users on each version
2. **Update adoption rate**: How quickly users update
3. **Force update impact**: Users affected by forced updates
4. **API response times**: Performance of version check endpoint
5. **Error rates**: Failed version checks

---

## Support

For API issues or questions:
- Check implementation docs: `P0-MOB-02_IMPLEMENTATION.md`
- Backend logs: Check server logs for errors
- Database: Query `app_versions` table directly if needed

