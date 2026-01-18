# P1-EXP-01: A/B Testing Framework with Feature Flags

## Overview

This document describes the implementation of the A/B testing framework with feature flags for the Luuniensuki LMS platform. This feature enables gradual rollouts, A/B experiments, and user-specific feature toggles.

## Architecture

### Components

1. **FeatureFlag Model** - Manages feature toggles with various rollout strategies
2. **Experiment Model** - Manages A/B test experiments with multiple variants
3. **UserExperimentAssignment Model** - Tracks user assignments to experiment variants
4. **Experiments Service** - Business logic for feature checks and variant assignments
5. **API Endpoints** - RESTful API for managing and checking features/experiments

### Database Schema

#### feature_flags Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| key | String(100) | Unique feature identifier (e.g., "new_onboarding_flow") |
| name | String(255) | Display name |
| description | Text | Optional description |
| flag_type | Enum | Type: boolean, percentage, user_list |
| is_enabled | Boolean | Master toggle (default: false) |
| percentage | Integer | Rollout percentage 0-100 (for percentage type) |
| allowed_user_ids | JSONB | List of user IDs (for user_list type) |
| metadata | JSONB | Additional configuration |
| created_at | Timestamp | Creation timestamp |
| updated_at | Timestamp | Last update timestamp |

#### experiments Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| key | String(100) | Unique experiment identifier |
| name | String(255) | Display name |
| description | Text | Optional description |
| variants | JSONB | List of variant objects with key, name, weight |
| is_active | Boolean | Whether experiment is running (default: false) |
| start_date | Timestamp | Optional start date |
| end_date | Timestamp | Optional end date |
| created_at | Timestamp | Creation timestamp |

#### user_experiment_assignments Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| experiment_id | UUID | Foreign key to experiments |
| variant_key | String(100) | Assigned variant (e.g., "control", "variant_a") |
| assigned_at | Timestamp | Assignment timestamp |

**Unique Constraint**: (user_id, experiment_id)

## Feature Flag Types

### 1. Boolean Flags

Simple on/off toggles. When enabled, all users have access.

```json
{
  "key": "new_dashboard",
  "name": "New Dashboard UI",
  "flag_type": "boolean",
  "is_enabled": true
}
```

### 2. Percentage Rollout

Gradual rollout to a percentage of users using deterministic hashing.

```json
{
  "key": "enhanced_analytics",
  "name": "Enhanced Analytics",
  "flag_type": "percentage",
  "is_enabled": true,
  "percentage": 25
}
```

### 3. User List

Specific list of allowed users (beta testing, VIP access).

```json
{
  "key": "beta_feature",
  "name": "Beta Feature Access",
  "flag_type": "user_list",
  "is_enabled": true,
  "allowed_user_ids": [
    "user-uuid-1",
    "user-uuid-2"
  ]
}
```

## Experiments

### Variant Structure

Each experiment has multiple variants with weights for distribution:

```json
{
  "key": "quiz_difficulty_test",
  "name": "Quiz Difficulty A/B Test",
  "variants": [
    {
      "key": "control",
      "name": "Original Difficulty",
      "weight": 50
    },
    {
      "key": "easier",
      "name": "Easier Questions",
      "weight": 25
    },
    {
      "key": "harder",
      "name": "Harder Questions",
      "weight": 25
    }
  ],
  "is_active": true
}
```

### Deterministic Assignment

- Users are assigned to variants deterministically based on MD5 hash of `user_id:experiment_key`
- Assignment is permanent for the duration of the experiment
- Ensures consistent user experience across sessions

## API Reference

### User Endpoints

#### Get All Features for Current User
```http
GET /api/v1/features
Authorization: Bearer <token>
```

**Response:**
```json
{
  "features": {
    "new_onboarding_flow": true,
    "enhanced_analytics": false,
    "beta_feature": false
  }
}
```

#### Check Specific Feature
```http
GET /api/v1/features/{key}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "key": "new_onboarding_flow",
  "enabled": true,
  "metadata": {
    "description": "New user onboarding experience",
    "version": "2.0"
  }
}
```

#### Get Experiment Assignments
```http
GET /api/v1/experiments
Authorization: Bearer <token>
```

**Response:**
```json
{
  "experiments": {
    "quiz_difficulty_test": "variant_a",
    "lesson_layout_test": "control"
  }
}
```

### Admin Endpoints

#### List All Feature Flags
```http
GET /api/v1/admin/feature-flags
Authorization: Bearer <admin_token>
```

**Response:**
```json
[
  {
    "id": "uuid",
    "key": "new_onboarding_flow",
    "name": "New Onboarding Flow",
    "description": "Redesigned user onboarding experience",
    "flag_type": "percentage",
    "is_enabled": true,
    "percentage": 50,
    "allowed_user_ids": null,
    "metadata": {},
    "created_at": "2025-01-20T10:00:00Z",
    "updated_at": "2025-01-20T10:00:00Z"
  }
]
```

#### Create Feature Flag
```http
POST /api/v1/admin/feature-flags
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "key": "new_feature",
  "name": "New Feature",
  "description": "A new experimental feature",
  "flag_type": "boolean",
  "is_enabled": false,
  "percentage": 0,
  "metadata": {
    "owner": "product-team"
  }
}
```

#### Update Feature Flag
```http
PUT /api/v1/admin/feature-flags/{flag_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "is_enabled": true,
  "percentage": 100
}
```

#### Delete Feature Flag
```http
DELETE /api/v1/admin/feature-flags/{flag_id}
Authorization: Bearer <admin_token>
```

#### List All Experiments
```http
GET /api/v1/admin/experiments
Authorization: Bearer <admin_token>
```

#### Create Experiment
```http
POST /api/v1/admin/experiments
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "key": "quiz_difficulty_test",
  "name": "Quiz Difficulty A/B Test",
  "description": "Test different quiz difficulty levels",
  "variants": [
    {"key": "control", "name": "Original", "weight": 50},
    {"key": "variant_a", "name": "Easier", "weight": 50}
  ],
  "is_active": true,
  "start_date": "2025-01-20T00:00:00Z",
  "end_date": "2025-02-20T00:00:00Z"
}
```

#### Update Experiment
```http
PUT /api/v1/admin/experiments/{experiment_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "is_active": false
}
```

#### Delete Experiment
```http
DELETE /api/v1/admin/experiments/{experiment_id}
Authorization: Bearer <admin_token>
```

#### Get Experiment Assignments
```http
GET /api/v1/admin/experiments/{experiment_id}/assignments?page=1&page_size=50
Authorization: Bearer <admin_token>
```

**Response:**
```json
[
  {
    "id": "uuid",
    "user_id": "user-uuid",
    "experiment_id": "experiment-uuid",
    "variant_key": "variant_a",
    "assigned_at": "2025-01-20T10:30:00Z"
  }
]
```

## Service Layer Functions

### Feature Flag Functions

```python
from backend.services import experiments

# Check if feature is enabled for user
is_enabled = experiments.is_feature_enabled_for_user(db, "new_feature", user_id)

# Get all features for user
features = experiments.get_all_features_for_user(db, user_id)

# Create feature flag
flag = experiments.create_feature_flag(
    db=db,
    key="new_feature",
    name="New Feature",
    flag_type=FlagType.boolean,
    is_enabled=True
)

# Update feature flag
flag = experiments.update_feature_flag(
    db=db,
    flag_id=flag_id,
    is_enabled=False
)
```

### Experiment Functions

```python
# Get variant for user (creates assignment if needed)
variant = experiments.get_experiment_variant_for_user(db, "quiz_test", user_id)

# Get all experiments for user
user_experiments = experiments.get_all_experiments_for_user(db, user_id)

# Create experiment
experiment = experiments.create_experiment(
    db=db,
    key="quiz_test",
    name="Quiz Test",
    variants=[
        {"key": "control", "name": "Control", "weight": 50},
        {"key": "variant_a", "name": "Variant A", "weight": 50}
    ],
    is_active=True
)
```

## Testing Guide

### Testing Feature Flags

1. **Create a boolean flag:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "test_feature",
    "name": "Test Feature",
    "flag_type": "boolean",
    "is_enabled": true
  }'
```

2. **Check flag as user:**
```bash
curl http://localhost:8000/api/v1/features/test_feature \
  -H "Authorization: Bearer $USER_TOKEN"
```

3. **Test percentage rollout:**
```bash
# Create 25% rollout flag
curl -X POST http://localhost:8000/api/v1/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "gradual_feature",
    "name": "Gradual Feature",
    "flag_type": "percentage",
    "is_enabled": true,
    "percentage": 25
  }'

# Check with multiple users - ~25% should see it enabled
for i in {1..10}; do
  curl http://localhost:8000/api/v1/features/gradual_feature \
    -H "Authorization: Bearer $USER_TOKEN_$i"
done
```

### Testing Experiments

1. **Create an experiment:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/experiments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "ab_test",
    "name": "A/B Test",
    "variants": [
      {"key": "control", "name": "Control", "weight": 50},
      {"key": "variant", "name": "Variant", "weight": 50}
    ],
    "is_active": true
  }'
```

2. **Check variant assignments:**
```bash
curl http://localhost:8000/api/v1/experiments \
  -H "Authorization: Bearer $USER_TOKEN"
```

3. **Verify assignment persistence:**
```bash
# Call multiple times - should always return same variant
for i in {1..5}; do
  curl http://localhost:8000/api/v1/experiments \
    -H "Authorization: Bearer $USER_TOKEN"
done
```

## Migration

Run the migration to create the tables:

```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
alembic upgrade head
```

## Implementation Summary

### Files Created/Modified

1. **backend/models.py** - Added:
   - FlagType enum
   - FeatureFlag model
   - Experiment model
   - UserExperimentAssignment model
   - Updated User model relationships

2. **backend/services/experiments.py** - New service with functions for:
   - Feature flag evaluation
   - Experiment variant assignment
   - CRUD operations for flags and experiments

3. **backend/schemas.py** - Added schemas:
   - FeatureFlagOut, FeatureFlagCreateIn, FeatureFlagUpdateIn
   - ExperimentOut, ExperimentCreateIn, ExperimentUpdateIn
   - UserFeaturesOut, UserExperimentsOut
   - FeatureCheckOut, UserExperimentAssignmentOut

4. **backend/main.py** - Added endpoints:
   - GET /api/v1/features
   - GET /api/v1/features/{key}
   - GET /api/v1/experiments
   - GET /api/v1/admin/feature-flags
   - POST /api/v1/admin/feature-flags
   - PUT /api/v1/admin/feature-flags/{flag_id}
   - DELETE /api/v1/admin/feature-flags/{flag_id}
   - GET /api/v1/admin/experiments
   - POST /api/v1/admin/experiments
   - PUT /api/v1/admin/experiments/{experiment_id}
   - DELETE /api/v1/admin/experiments/{experiment_id}
   - GET /api/v1/admin/experiments/{experiment_id}/assignments

5. **migrations/versions/0033_feature_flags_experiments.py** - Database migration

## Best Practices

1. **Feature Flag Naming:**
   - Use snake_case: `new_dashboard_ui`
   - Be descriptive: `enhanced_quiz_hints`
   - Include version if applicable: `onboarding_v2`

2. **Experiment Design:**
   - Always include a "control" variant
   - Use meaningful variant names
   - Set appropriate weights (must sum to total weight for distribution)
   - Set start_date and end_date for tracking

3. **Rollout Strategy:**
   - Start with percentage=0 or user_list for testing
   - Gradually increase percentage: 1% → 5% → 25% → 50% → 100%
   - Monitor metrics at each step
   - Use metadata for additional context

4. **Cleanup:**
   - Remove feature flags after 100% rollout
   - Archive experiment results before deletion
   - Clean up unused flags regularly

## Use Cases

### Gradual Rollout
```python
# Phase 1: Internal testing
flag = create_feature_flag(
    key="new_ui",
    flag_type=FlagType.user_list,
    is_enabled=True,
    allowed_user_ids=["team_member_1", "team_member_2"]
)

# Phase 2: Small rollout
update_feature_flag(
    flag_id=flag.id,
    flag_type=FlagType.percentage,
    percentage=5
)

# Phase 3: Full rollout
update_feature_flag(flag_id=flag.id, percentage=100)
```

### A/B Testing
```python
# Create experiment
experiment = create_experiment(
    key="quiz_hints_test",
    variants=[
        {"key": "control", "name": "Free Hints", "weight": 50},
        {"key": "paid", "name": "Paid Hints", "weight": 50}
    ],
    is_active=True
)

# In application code
variant = get_experiment_variant_for_user(db, "quiz_hints_test", user_id)
if variant == "paid":
    # Show paid hints UI
else:
    # Show free hints UI
```

### Beta Features
```python
# VIP/Beta access
flag = create_feature_flag(
    key="ai_tutor_beta",
    flag_type=FlagType.user_list,
    is_enabled=True,
    allowed_user_ids=beta_user_ids
)
```

## Monitoring and Analytics

Track feature flag and experiment usage in your analytics:

```python
from backend.services import analytics

# Track feature flag check
analytics.track_event(
    db=db,
    user_id=user_id,
    event_type="feature_flag_check",
    event_category="experiments",
    metadata={
        "flag_key": "new_feature",
        "enabled": is_enabled
    }
)

# Track experiment variant assignment
analytics.track_event(
    db=db,
    user_id=user_id,
    event_type="experiment_variant_assigned",
    event_category="experiments",
    metadata={
        "experiment_key": "quiz_test",
        "variant": variant_key
    }
)
```

## Security Considerations

1. **Admin-only access:**
   - All CRUD operations require admin role
   - Use `require_admin` dependency

2. **User isolation:**
   - Users can only see their own feature status
   - No cross-user information leakage

3. **Validation:**
   - Percentage values clamped to 0-100
   - Variant weights must be non-negative
   - Keys must be unique

## Support

For questions or issues, contact the engineering team or refer to the main project documentation.

