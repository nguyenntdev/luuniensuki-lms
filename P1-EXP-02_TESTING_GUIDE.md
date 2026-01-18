# P1-EXP-02: Feature Flags System - Testing Guide

## Overview
This implementation adds a comprehensive feature flags system for gradual rollouts with:
- Deterministic percentage-based rollout
- User whitelist/blacklist
- Targeting rules (role, signup date)
- Admin CRUD endpoints
- Helper dependency for easy feature checking

## Migration

The database migration `0037_update_feature_flags_fields.py` adds the following changes:
- Renames `percentage` → `rollout_percentage`
- Renames `allowed_user_ids` → `user_whitelist`
- Adds `user_blacklist` (JSONB)
- Adds `rules` (JSONB for targeting)
- Adds `created_by_id` (FK to users)
- Removes `flag_type` enum (simplified to single approach)
- Removes `metadata` (replaced by `rules`)

To run migration:
```bash
# Using docker-compose
docker-compose exec api alembic upgrade head

# Or directly with python
python -m alembic upgrade head
```

## API Endpoints

### User Endpoints (Public)
- `GET /api/v1/features` - Get all features for current user
- `GET /api/v1/features/{key}` - Check specific feature

### Admin Endpoints (Admin only)
- `GET /api/v1/admin/feature-flags` - List all feature flags
- `POST /api/v1/admin/feature-flags` - Create feature flag
- `PUT /api/v1/admin/feature-flags/{key}` - Update feature flag
- `DELETE /api/v1/admin/feature-flags/{key}` - Delete feature flag

## Usage Examples

### 1. Create a Feature Flag (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "new_quiz_ui",
    "name": "New Quiz UI",
    "description": "Redesigned quiz interface with better UX",
    "is_enabled": true,
    "rollout_percentage": 25,
    "rules": {
      "roles": ["learner", "teacher"]
    }
  }'
```

### 2. Update Feature Flag (Admin)
```bash
curl -X PUT http://localhost:8000/api/v1/admin/feature-flags/new_quiz_ui \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_enabled": true,
    "rollout_percentage": 50
  }'
```

### 3. Check Features for User
```bash
curl -X GET http://localhost:8000/api/v1/features \
  -H "Authorization: Bearer $USER_TOKEN"
```

### 4. Use Feature Flag Dependency in Endpoint
```python
from backend.main import require_feature

@app.get("/api/v1/new-quiz")
def new_quiz_endpoint(
    current_user: User = Depends(require_feature("new_quiz_ui")),
    db: Session = Depends(get_db),
):
    # This endpoint is only accessible if new_quiz_ui is enabled for user
    return {"message": "New quiz UI"}
```

## Feature Flag Logic Priority

The system checks features in this order:

1. **Global Enable Check**: If `is_enabled = false`, feature is disabled for everyone
2. **Blacklist Check**: If user is in `user_blacklist`, feature is disabled
3. **Whitelist Check**: If user is in `user_whitelist`, feature is enabled
4. **Rules Check**: If `rules` exist and user doesn't match, feature is disabled
5. **Rollout Percentage**: Deterministic hash-based assignment (same user always gets same result)

## Targeting Rules

### Role-based Targeting
```json
{
  "rules": {
    "roles": ["teacher", "admin"]
  }
}
```

### Signup Date Targeting
```json
{
  "rules": {
    "min_signup_days": 7,
    "max_signup_days": 30
  }
}
```

### Combined Rules
```json
{
  "rules": {
    "roles": ["learner"],
    "min_signup_days": 14
  }
}
```

## Testing Scenarios

### Scenario 1: Gradual Rollout
1. Create flag with `rollout_percentage: 10`
2. Test with multiple users
3. Verify ~10% get access (deterministic)
4. Increase to 50%, verify same users still have access + new ones

### Scenario 2: Whitelist Testing
1. Create flag with `is_enabled: false` and specific user IDs in whitelist
2. Verify whitelisted users can access
3. Verify non-whitelisted users cannot access

### Scenario 3: Blacklist Testing
1. Create flag with `rollout_percentage: 100` and blacklist
2. Verify blacklisted users cannot access
3. Verify non-blacklisted users can access

### Scenario 4: Role-based Feature
1. Create flag with `rules: {"roles": ["teacher", "admin"]}`
2. Verify only teachers and admins can access
3. Learners should be blocked

## Next Steps

1. **Run migration** to update database schema
2. **Test endpoints** using curl or Postman
3. **Create initial feature flags** for your use cases:
   - `ai_hints` - AI-powered quiz hints
   - `new_quiz_ui` - Redesigned quiz interface
   - `social_features` - Social learning features
4. **Integrate** `require_feature()` dependency in new/experimental endpoints
5. **Monitor** rollout and adjust percentages based on metrics

