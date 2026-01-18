# P1-SOC-02: Social Sharing API Reference

## Base URL
```
https://api.lms.luuniensuki.com/api/v1
```

## Authentication
Most endpoints require Bearer token authentication:
```
Authorization: Bearer {access_token}
```

## Endpoints

---

### 1. Get Activity Feed

Get activity feed from followed users (currently shows public shares from all users).

**Endpoint:** `GET /social/feed`

**Authentication:** Required

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1, min: 1)
- `page_size` (integer, optional): Items per page (default: 20, min: 1, max: 100)

**Response:** `200 OK`
```json
{
  "activities": [
    {
      "id": "uuid",
      "activity_type": "share",
      "user_id": "uuid",
      "user_display_name": "Nguyen Van A",
      "user_avatar_url": "https://...",
      "content": {
        "share_type": "badge",
        "caption": "First achievement!",
        "content_data": {
          "badge_name": "First Discovery",
          "badge_slug": "first-discovery",
          "badge_icon_url": "https://...",
          "badge_description": "Discovered your first motif",
          "earned_at": "2025-01-20T10:00:00Z"
        },
        "share_url": "https://lms.luuniensuki.com/share/uuid",
        "view_count": 42
      },
      "created_at": "2025-01-20T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid authentication

---

### 2. Create Share

Create a new share of an achievement, badge, streak, level-up, or certificate.

**Endpoint:** `POST /social/share`

**Authentication:** Required

**Request Body:**
```json
{
  "share_type": "badge",
  "content_id": "uuid",
  "caption": "Just earned my first badge!",
  "visibility": "public"
}
```

**Fields:**
- `share_type` (string, required): Type of share
  - Allowed values: `achievement`, `badge`, `streak`, `level_up`, `certificate`
- `content_id` (uuid, optional): ID of the shared item (required for badge/certificate)
- `caption` (string, optional): User's custom message (max 500 characters)
- `visibility` (string, optional): Who can view this share (default: "public")
  - Allowed values: `public`, `followers`, `private`

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "share_type": "badge",
  "content_id": "uuid",
  "caption": "Just earned my first badge!",
  "visibility": "public",
  "share_url": "https://lms.luuniensuki.com/share/uuid",
  "view_count": 0,
  "created_at": "2025-01-20T10:00:00Z"
}
```

**Errors:**
- `400 Bad Request`: Invalid share type or missing required fields
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Badge or certificate not found

---

### 3. Get My Shares

Get the current user's shares with full details and metadata.

**Endpoint:** `GET /social/shares/mine`

**Authentication:** Required

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1, min: 1)
- `page_size` (integer, optional): Items per page (default: 20, min: 1, max: 100)

**Response:** `200 OK`
```json
{
  "shares": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "user_display_name": "Nguyen Van A",
      "user_avatar_url": "https://...",
      "user_xp": 1250,
      "share_type": "badge",
      "content_id": "uuid",
      "content_data": {
        "badge_name": "First Discovery",
        "badge_slug": "first-discovery",
        "badge_icon_url": "https://...",
        "badge_description": "Discovered your first motif",
        "earned_at": "2025-01-20T10:00:00Z"
      },
      "caption": "My first achievement!",
      "visibility": "public",
      "share_url": "https://lms.luuniensuki.com/share/uuid",
      "view_count": 42,
      "created_at": "2025-01-20T10:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

**Errors:**
- `401 Unauthorized`: Missing or invalid authentication

---

### 4. Get Share by ID

Get a specific share by ID. Public endpoint with visibility checks.

**Endpoint:** `GET /social/shares/{share_id}`

**Authentication:** Optional

**Path Parameters:**
- `share_id` (uuid, required): ID of the share

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "user_display_name": "Nguyen Van A",
  "user_avatar_url": "https://...",
  "user_xp": 1250,
  "share_type": "certificate",
  "content_id": "uuid",
  "content_data": {
    "certificate_code": "LNS-2025-001",
    "issuer_name": "Lưu Niên Sử Kí",
    "issued_at": "2025-01-20T10:00:00Z",
    "reason_type": "urn_exam_passed"
  },
  "caption": "Passed my first exam!",
  "visibility": "public",
  "share_url": "https://lms.luuniensuki.com/share/uuid",
  "view_count": 100,
  "created_at": "2025-01-20T10:00:00Z"
}
```

**Errors:**
- `404 Not Found`: Share not found or not accessible

**Notes:**
- View count is automatically incremented when viewing
- Owner's views are not counted
- Visibility rules:
  - `public`: Anyone can view
  - `followers`: Only followers can view (TODO: requires friend system)
  - `private`: Only the owner can view

---

### 5. Delete Share

Delete a share. Users can only delete their own shares.

**Endpoint:** `DELETE /social/shares/{share_id}`

**Authentication:** Required

**Path Parameters:**
- `share_id` (uuid, required): ID of the share to delete

**Response:** `204 No Content`

**Errors:**
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Share not found or not authorized to delete

---

### 6. Get User Activity

Get public activity (shares) for a specific user.

**Endpoint:** `GET /users/{user_id}/activity`

**Authentication:** Optional

**Path Parameters:**
- `user_id` (uuid, required): ID of the user

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1, min: 1)
- `page_size` (integer, optional): Items per page (default: 20, min: 1, max: 100)

**Response:** `200 OK`
```json
{
  "shares": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "user_display_name": "Nguyen Van A",
      "user_avatar_url": "https://...",
      "user_xp": 1250,
      "share_type": "streak",
      "content_id": null,
      "content_data": {
        "current_streak": 30,
        "longest_streak": 45
      },
      "caption": "30 days and counting!",
      "visibility": "public",
      "share_url": "https://lms.luuniensuki.com/share/uuid",
      "view_count": 75,
      "created_at": "2025-01-20T10:00:00Z"
    }
  ],
  "total": 20,
  "page": 1,
  "page_size": 20
}
```

**Errors:**
- `404 Not Found`: User not found

**Notes:**
- Shows only public shares
- Does not require authentication

---

## Content Data by Share Type

### Badge Share
```json
{
  "badge_name": "First Discovery",
  "badge_slug": "first-discovery",
  "badge_icon_url": "https://...",
  "badge_description": "Discovered your first motif",
  "earned_at": "2025-01-20T10:00:00Z"
}
```

### Certificate Share
```json
{
  "certificate_code": "LNS-2025-001",
  "issuer_name": "Lưu Niên Sử Kí",
  "issued_at": "2025-01-20T10:00:00Z",
  "reason_type": "urn_exam_passed"
}
```

### Streak Share
```json
{
  "current_streak": 30,
  "longest_streak": 45
}
```

### Level Up Share
```json
{
  "total_xp": 1250,
  "rank_title": "Học giả",
  "rank_min_xp": 1000
}
```

---

## Common Error Responses

### 400 Bad Request
```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid share type",
    "details": {
      "field": "share_type",
      "allowed_values": ["achievement", "badge", "streak", "level_up", "certificate"]
    }
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Share not found or not accessible"
}
```

