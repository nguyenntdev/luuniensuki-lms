# P1-SOC-01: Friend List and Follow System - Implementation Complete

## Status: ✅ IMPLEMENTED

Implementation Date: 2024-01-16

---

## Overview

Added comprehensive friend list and follow system to enable social features in the LMS. Users can:
- Follow other users to see their activity
- Send and accept friend requests for mutual following
- View lists of followers, following, and friends
- Manage friend requests (accept/reject)

---

## Database Schema

### 1. Models (`backend/models.py`)

#### FriendRequestStatus Enum
```python
class FriendRequestStatus(str, Enum):
    """Status of friend requests."""
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
```

#### UserFollow Model
- **Table**: `user_follows`
- **Fields**:
  - `id`: UUID primary key
  - `follower_id`: FK to users (who is following)
  - `following_id`: FK to users (who is being followed)
  - `created_at`: DateTime with timezone
- **Constraints**:
  - Unique constraint on (follower_id, following_id)
  - Check constraint: follower_id != following_id (no self-following)
- **Indexes**:
  - idx_user_follows_follower
  - idx_user_follows_following
  - idx_user_follows_created

#### FriendRequest Model
- **Table**: `friend_requests`
- **Fields**:
  - `id`: UUID primary key
  - `from_user_id`: FK to users (who sent the request)
  - `to_user_id`: FK to users (who received the request)
  - `status`: FriendRequestStatus enum (default: 'pending')
  - `created_at`: DateTime with timezone
  - `responded_at`: DateTime with timezone (nullable)
- **Constraints**:
  - Unique constraint on (from_user_id, to_user_id)
- **Indexes**:
  - idx_friend_requests_from_user
  - idx_friend_requests_to_user
  - idx_friend_requests_status
  - idx_friend_requests_created

#### User Model Updates
Added relationships:
- `following`: List of UserFollow (users this user is following)
- `followers`: List of UserFollow (users following this user)
- `sent_friend_requests`: List of FriendRequest
- `received_friend_requests`: List of FriendRequest

---

## 2. Schemas (`backend/schemas.py`)

### Input Schemas

#### FriendRequestCreateIn
```python
{
    "to_user_id": "uuid",
    "message": "Optional message (max 500 chars)"
}
```

### Output Schemas

#### FollowUserOut
```python
{
    "id": "uuid",
    "user_id": "uuid",
    "display_name": "string",
    "username": "string | null",
    "avatar_url": "string | null",
    "bio": "string | null",
    "total_xp": "int",
    "followed_at": "datetime"
}
```

#### FollowListOut
```python
{
    "users": [FollowUserOut],
    "total": "int",
    "page": "int",
    "page_size": "int"
}
```

#### FriendOut
```python
{
    "id": "uuid",
    "user_id": "uuid",
    "display_name": "string",
    "username": "string | null",
    "avatar_url": "string | null",
    "bio": "string | null",
    "total_xp": "int",
    "is_online": "bool"
}
```

#### FriendListOut
```python
{
    "friends": [FriendOut],
    "total": "int"
}
```

#### FriendRequestOut
```python
{
    "id": "uuid",
    "from_user_id": "uuid",
    "from_user_display_name": "string",
    "from_user_avatar_url": "string | null",
    "to_user_id": "uuid",
    "to_user_display_name": "string",
    "to_user_avatar_url": "string | null",
    "status": "pending | accepted | rejected",
    "created_at": "datetime",
    "responded_at": "datetime | null"
}
```

#### FriendRequestListOut
```python
{
    "requests": [FriendRequestOut],
    "total": "int",
    "pending_count": "int"
}
```

---

## 3. Service Layer (`backend/services/social.py`)

### Functions

- `follow_user(db, follower_id, following_id)` - Follow a user
- `unfollow_user(db, follower_id, following_id)` - Unfollow a user
- `get_following(db, user_id, skip, limit)` - Get users this user is following
- `get_followers(db, user_id, skip, limit)` - Get users following this user
- `get_friends(db, user_id)` - Get mutual follows (friends)
- `create_friend_request(db, from_user_id, to_user_id)` - Send friend request
- `get_friend_requests(db, user_id, status)` - Get received friend requests
- `get_sent_friend_requests(db, user_id, status)` - Get sent friend requests
- `accept_friend_request(db, request_id, user_id)` - Accept a friend request
- `reject_friend_request(db, request_id, user_id)` - Reject a friend request

---

## 4. API Endpoints (`backend/main.py`)

### GET /api/v1/social/following
List users the current user is following.

**Query Parameters**:
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20, max: 100): Items per page

**Response**: `FollowListOut`

---

### GET /api/v1/social/followers
List users following the current user.

**Query Parameters**:
- `page` (int, default: 1): Page number  
- `page_size` (int, default: 20, max: 100): Items per page

**Response**: `FollowListOut`

---

### POST /api/v1/social/follow/{user_id}
Follow a user.

**Path Parameters**:
- `user_id` (UUID): User to follow

**Response** (201):
```json
{
    "message": "User followed successfully",
    "follow_id": "uuid"
}
```

---

### DELETE /api/v1/social/follow/{user_id}
Unfollow a user.

**Path Parameters**:
- `user_id` (UUID): User to unfollow

**Response**: 204 No Content

---

### GET /api/v1/social/friends
Get list of friends (mutual follows).

**Response**: `FriendListOut`

---

### POST /api/v1/social/friend-requests
Send a friend request.

**Request Body**: `FriendRequestCreateIn`

**Response** (201): `FriendRequestOut`

---

### GET /api/v1/social/friend-requests
Get friend requests received by the current user.

**Query Parameters**:
- `status` (string, optional): Filter by status (pending|accepted|rejected)

**Response**: `FriendRequestListOut`

---

### POST /api/v1/social/friend-requests/{id}/accept
Accept a friend request.

**Path Parameters**:
- `id` (UUID): Friend request ID

**Response**: `FriendRequestOut`

**Side Effects**:
- Creates mutual follows between both users
- Updates request status to 'accepted'
- Sets responded_at timestamp

---

### POST /api/v1/social/friend-requests/{id}/reject
Reject a friend request.

**Path Parameters**:
- `id` (UUID): Friend request ID

**Response**: `FriendRequestOut`

**Side Effects**:
- Updates request status to 'rejected'
- Sets responded_at timestamp

---

## 5. Migration (`migrations/versions/0031_social_features.py`)

- Creates `friend_request_status` enum type
- Creates `user_follows` table with all indexes and constraints
- Creates `friend_requests` table with all indexes and constraints
- Includes upgrade() and downgrade() functions

---

## Testing

### Manual Testing Steps

1. **Follow System**:
   ```bash
   # Get following list
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/social/following
   
   # Get followers list
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/social/followers
   
   # Follow a user
   curl -X POST -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/social/follow/{user_id}
   
   # Unfollow a user
   curl -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/social/follow/{user_id}
   
   # Get friends
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/social/friends
   ```

2. **Friend Requests**:
   ```bash
   # Send friend request
   curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"to_user_id":"uuid"}' \
     http://localhost:8000/api/v1/social/friend-requests
   
   # Get received requests
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/social/friend-requests
   
   # Accept request
   curl -X POST -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/social/friend-requests/{id}/accept
   
   # Reject request
   curl -X POST -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/social/friend-requests/{id}/reject
   ```

---

## Security Considerations

- ✅ All endpoints require authentication
- ✅ Users can only follow/unfollow through their own account
- ✅ Users can only accept/reject friend requests sent to them
- ✅ No self-following allowed (database constraint)
- ✅ Duplicate follow relationships prevented (unique constraint)
- ✅ Duplicate friend requests prevented (unique constraint)
- ✅ Proper CASCADE delete on user deletion

---

## Future Enhancements

1. **Notifications**: Send push notifications for new friend requests
2. **Activity Feed**: Show friend activity in user's feed
3. **Online Status**: Real-time online/offline status for friends
4. **Follow Date**: Store actual follow date in relationships
5. **Block Users**: Add ability to block users
6. **Privacy Settings**: Allow users to make profile private
7. **Mutual Friends**: Show mutual friends count
8. **Friend Suggestions**: AI-powered friend suggestions

---

## Files Modified

- ✅ `backend/models.py` - Added UserFollow and FriendRequest models
- ✅ `backend/schemas.py` - Added social feature schemas
- ✅ `backend/services/social.py` - New service file
- ✅ `backend/main.py` - Added 9 API endpoints
- ✅ `migrations/versions/0031_social_features.py` - Database migration

---

## Deployment Checklist

- [ ] Run database migration: `alembic upgrade head`
- [ ] Test all endpoints with Postman/curl
- [ ] Verify constraint behavior (no self-follow, unique constraints)
- [ ] Test pagination on following/followers lists
- [ ] Verify friend request workflow (send → accept → mutual follows)
- [ ] Test error cases (user not found, duplicate requests, etc.)
- [ ] Update API documentation
- [ ] Notify frontend team of new endpoints

---

## Notes

- Friend requests automatically create mutual follows when accepted
- Accepting a friend request is idempotent - already accepted requests return success
- Rejected friend requests can be resent (status is reset to pending)
- All timestamps use UTC timezone
- Database uses native PostgreSQL enum for friend request status

