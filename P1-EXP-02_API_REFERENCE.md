# P1-EXP-02: Feature Flags API Reference

## Overview
Feature flags system for gradual rollouts, A/B testing, and controlled feature deployment.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
- User endpoints: Requires valid access token
- Admin endpoints: Requires admin or super_admin role

---

## User Endpoints

### Get All Features for Current User
Get all feature flags and their enabled/disabled status for the authenticated user.

**Endpoint:** `GET /features`  
**Auth:** Required  
**Response:** `200 OK`

```json
{
  "features": {
    "new_quiz_ui": true,
    "ai_hints": false,
    "social_features": true
  }
}
```

---

### Check Specific Feature
Check if a specific feature is enabled for the current user.

**Endpoint:** `GET /features/{key}`  
**Auth:** Required  
**Response:** `200 OK`

```json
{
  "key": "new_quiz_ui",
  "enabled": true,
  "metadata": {
    "roles": ["learner", "teacher"]
  }
}
```

**Errors:**
- `404 Not Found` - Feature flag not found

---

## Admin Endpoints

### List All Feature Flags
Get a list of all feature flags in the system.

**Endpoint:** `GET /admin/feature-flags`  
**Auth:** Admin required  
**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "key": "new_quiz_ui",
    "name": "New Quiz UI",
    "description": "Redesigned quiz interface with improved UX",
    "is_enabled": true,
    "rollout_percentage": 25,
    "user_whitelist": ["user-id-1", "user-id-2"],
    "user_blacklist": ["user-id-3"],
    "rules": {
      "roles": ["learner", "teacher"],
      "min_signup_days": 7
    },
    "created_by_id": "admin-user-id",
    "created_at": "2025-01-18T10:00:00Z",
    "updated_at": "2025-01-18T15:30:00Z"
  }
]
```

---

### Create Feature Flag
Create a new feature flag.

**Endpoint:** `POST /admin/feature-flags`  
**Auth:** Admin required  
**Content-Type:** `application/json`  
**Response:** `201 Created`

**Request Body:**
```json
{
  "key": "ai_hints",
  "name": "AI-Powered Quiz Hints",
  "description": "Enable AI-generated hints for quiz questions",
  "is_enabled": true,
  "rollout_percentage": 10,
  "user_whitelist": ["beta-tester-1"],
  "user_blacklist": null,
  "rules": {
    "roles": ["learner"],
    "min_signup_days": 14
  }
}
```

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "key": "ai_hints",
  "name": "AI-Powered Quiz Hints",
  "description": "Enable AI-generated hints for quiz questions",
  "is_enabled": true,
  "rollout_percentage": 10,
  "user_whitelist": ["beta-tester-1"],
  "user_blacklist": null,
  "rules": {
    "roles": ["learner"],
    "min_signup_days": 14
  },
  "created_by_id": "admin-user-id",
  "created_at": "2025-01-18T16:00:00Z",
  "updated_at": "2025-01-18T16:00:00Z"
}
```

**Errors:**
- `400 Bad Request` - Invalid data or duplicate key
- `403 Forbidden` - Not an admin user

---

### Update Feature Flag
Update an existing feature flag by key.

**Endpoint:** `PUT /admin/feature-flags/{key}`  
**Auth:** Admin required  
**Content-Type:** `application/json`  
**Response:** `200 OK`

**Request Body (all fields optional):**
```json
{
  "name": "AI Quiz Hints (Updated)",
  "description": "Updated description",
  "is_enabled": true,
  "rollout_percentage": 50,
  "user_whitelist": ["user-1", "user-2"],
  "user_blacklist": ["banned-user"],
  "rules": {
    "roles": ["learner", "teacher"]
  }
}
```

**Response:** Same as create response with updated values

**Errors:**
- `404 Not Found` - Feature flag not found
- `403 Forbidden` - Not an admin user

---

### Delete Feature Flag
Delete a feature flag by key.

**Endpoint:** `DELETE /admin/feature-flags/{key}`  
**Auth:** Admin required  
**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Feature flag not found
- `403 Forbidden` - Not an admin user

---

## Feature Flag Schema

### FeatureFlagOut
```typescript
{
  id: UUID
  key: string                        // Unique identifier
  name: string                       // Display name
  description?: string               // Optional description
  is_enabled: boolean                // Global on/off switch
  rollout_percentage: number         // 0-100
  user_whitelist?: string[]          // Always enabled for these users
  user_blacklist?: string[]          // Always disabled for these users
  rules?: {                          // Targeting rules
    roles?: string[]                 // Allowed user roles
    min_signup_days?: number         // Minimum days since signup
    max_signup_days?: number         // Maximum days since signup
  }
  created_by_id?: UUID               // Admin who created it
  created_at: datetime
  updated_at: datetime
}
```

---

## Feature Checking Logic

Features are evaluated in this priority order:

1. **Global Enable**: If `is_enabled = false`, return `false`
2. **Blacklist**: If user in `user_blacklist`, return `false`
3. **Whitelist**: If user in `user_whitelist`, return `true`
4. **Rules**: If `rules` exist and user doesn't match, return `false`
5. **Rollout**: Deterministic hash-based check against `rollout_percentage`

### Deterministic Rollout
- Same user always gets same result for same feature
- Uses MD5 hash of `user_id:feature_key`
- Ensures consistent experience across sessions

