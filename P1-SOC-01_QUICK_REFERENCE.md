# P1-SOC-01: Quick Reference Guide

## 🚀 Quick Start

### API Endpoints Overview

```
Follow System:
  GET    /api/v1/social/following           # Who I follow
  GET    /api/v1/social/followers           # Who follows me
  POST   /api/v1/social/follow/{user_id}    # Follow someone
  DELETE /api/v1/social/follow/{user_id}    # Unfollow someone
  GET    /api/v1/social/friends             # Mutual follows

Friend Requests:
  POST   /api/v1/social/friend-requests                 # Send request
  GET    /api/v1/social/friend-requests                 # Get requests
  POST   /api/v1/social/friend-requests/{id}/accept    # Accept request
  POST   /api/v1/social/friend-requests/{id}/reject    # Reject request
```

---

## 📊 Database Tables

### user_follows
```
Columns: id, follower_id, following_id, created_at
Constraint: No self-follow, unique pairs
Indexes: On follower_id, following_id, created_at
```

### friend_requests
```
Columns: id, from_user_id, to_user_id, status, created_at, responded_at
Constraint: Unique pairs
Status: pending | accepted | rejected
Indexes: On from_user_id, to_user_id, status, created_at
```

---

## 🔧 Common Operations

### Follow a User
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/social/follow/{user_id}
```

### Get Friends List
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/social/friends
```

### Send Friend Request
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_user_id":"uuid"}' \
  http://localhost:8000/api/v1/social/friend-requests
```

### Accept Friend Request
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/social/friend-requests/{request_id}/accept
```

---

## 📝 Code Examples

### Service Layer Usage
```python
from backend.services import social

# Follow a user
follow = social.follow_user(db, follower_id, following_id)

# Get friends (mutual follows)
friends = social.get_friends(db, user_id)

# Send friend request
request = social.create_friend_request(db, from_user_id, to_user_id)

# Accept friend request (creates mutual follows)
accepted = social.accept_friend_request(db, request_id, user_id)
```

### Schema Usage
```python
from backend.schemas import (
    FriendRequestCreateIn,
    FriendRequestOut,
    FriendListOut,
    FollowListOut,
)

# Create friend request
request_data = FriendRequestCreateIn(
    to_user_id="uuid",
    message="Let's be friends!"
)

# Response will be FriendRequestOut with status
```

---

## ⚡ Key Features

- ✅ No self-following (enforced by DB constraint)
- ✅ Unique follow relationships
- ✅ Mutual follow detection (friends)
- ✅ Friend request workflow
- ✅ Pagination on followers/following
- ✅ Automatic mutual follows when request accepted
- ✅ Cascade delete on user deletion

---

## 🐛 Troubleshooting

### "Cannot follow yourself"
- DB constraint prevents self-follow
- Check that follower_id != following_id

### "Already following this user"
- Unique constraint on (follower_id, following_id)
- Use unfollow then follow again if needed

### "Friend request already exists"
- Only one pending request allowed per pair
- Rejected requests can be resent

### "Not authorized to accept this request"
- Only the recipient (to_user_id) can accept
- Verify current_user.id == request.to_user_id

---

## 📁 File Locations

```
Backend:
  backend/models.py          # UserFollow, FriendRequest models
  backend/schemas.py         # Pydantic schemas
  backend/services/social.py # Business logic
  backend/main.py            # API endpoints (lines 14514-14792)

Migration:
  migrations/versions/0031_social_features.py

Documentation:
  P1-SOC-01_IMPLEMENTATION_SUMMARY.md
  P1-SOC-01_DEPLOYMENT_CHECKLIST.md
  P1-SOC-01_QUICK_REFERENCE.md (this file)

Testing:
  test_social_features.sh
```

---

## 🎯 Testing Checklist

- [ ] Follow user
- [ ] Unfollow user
- [ ] Get following list (paginated)
- [ ] Get followers list (paginated)
- [ ] Get friends list
- [ ] Send friend request
- [ ] Get friend requests
- [ ] Accept friend request
- [ ] Reject friend request
- [ ] Verify mutual follows created on accept
- [ ] Test error: self-follow
- [ ] Test error: duplicate follow
- [ ] Test error: user not found
- [ ] Test error: unauthorized accept

---

## 📚 Related Documentation

- Full Implementation: `P1-SOC-01_IMPLEMENTATION_SUMMARY.md`
- Deployment Guide: `P1-SOC-01_DEPLOYMENT_CHECKLIST.md`
- API Reference: See implementation summary
- Testing Script: `test_social_features.sh`

---

## 🔐 Security

All endpoints require authentication:
- Use JWT token in `Authorization: Bearer <token>` header
- Users can only act on their own behalf
- No impersonation allowed
- Database constraints prevent invalid data

---

## 💡 Tips

1. **Pagination**: Use `page` and `page_size` params for large lists
2. **Friend Requests**: Accepting auto-creates mutual follows
3. **Mutual Follows**: Friends = users who follow each other
4. **Status Filter**: Filter friend requests by status (pending/accepted/rejected)
5. **Idempotent**: Accepting already-accepted request returns success

---

**Quick Deploy**: `alembic upgrade head && systemctl restart backend`

**Quick Test**: `export TOKEN=xxx && ./test_social_features.sh`

