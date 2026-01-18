# P1-EXP-01: A/B Testing Framework - Quick Reference

## Quick Start

### Check Features for User
```bash
curl http://localhost:8000/api/v1/features \
  -H "Authorization: Bearer $TOKEN"
```

### Check Specific Feature
```bash
curl http://localhost:8000/api/v1/features/new_onboarding_flow \
  -H "Authorization: Bearer $TOKEN"
```

### Get Experiment Assignments
```bash
curl http://localhost:8000/api/v1/experiments \
  -H "Authorization: Bearer $TOKEN"
```

## Admin Operations

### Create Boolean Feature Flag
```bash
curl -X POST http://localhost:8000/api/v1/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "new_feature",
    "name": "New Feature",
    "flag_type": "boolean",
    "is_enabled": true
  }'
```

### Create Percentage Rollout Flag
```bash
curl -X POST http://localhost:8000/api/v1/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "gradual_rollout",
    "name": "Gradual Rollout Feature",
    "flag_type": "percentage",
    "is_enabled": true,
    "percentage": 25
  }'
```

### Create User List Flag
```bash
curl -X POST http://localhost:8000/api/v1/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "beta_access",
    "name": "Beta Access",
    "flag_type": "user_list",
    "is_enabled": true,
    "allowed_user_ids": ["user-id-1", "user-id-2"]
  }'
```

### Create Experiment
```bash
curl -X POST http://localhost:8000/api/v1/admin/experiments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "ab_test",
    "name": "A/B Test",
    "description": "Testing two variants",
    "variants": [
      {"key": "control", "name": "Control", "weight": 50},
      {"key": "variant_a", "name": "Variant A", "weight": 50}
    ],
    "is_active": true
  }'
```

### Update Feature Flag (Enable/Disable)
```bash
curl -X PUT http://localhost:8000/api/v1/admin/feature-flags/{FLAG_ID} \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_enabled": false}'
```

### Update Rollout Percentage
```bash
curl -X PUT http://localhost:8000/api/v1/admin/feature-flags/{FLAG_ID} \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"percentage": 100}'
```

### Deactivate Experiment
```bash
curl -X PUT http://localhost:8000/api/v1/admin/experiments/{EXPERIMENT_ID} \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

### List All Flags
```bash
curl http://localhost:8000/api/v1/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### List All Experiments
```bash
curl http://localhost:8000/api/v1/admin/experiments \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### View Experiment Assignments
```bash
curl http://localhost:8000/api/v1/admin/experiments/{EXPERIMENT_ID}/assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Python Service Usage

```python
from backend.services import experiments
from backend.models import FlagType

# Check feature
enabled = experiments.is_feature_enabled_for_user(db, "feature_key", user_id)

# Get variant
variant = experiments.get_experiment_variant_for_user(db, "experiment_key", user_id)

# Create flag
flag = experiments.create_feature_flag(
    db=db,
    key="my_feature",
    name="My Feature",
    flag_type=FlagType.boolean,
    is_enabled=True
)
db.commit()

# Create experiment
experiment = experiments.create_experiment(
    db=db,
    key="my_test",
    name="My A/B Test",
    variants=[
        {"key": "control", "name": "Control", "weight": 50},
        {"key": "variant", "name": "Variant", "weight": 50}
    ],
    is_active=True
)
db.commit()
```

## Flag Types

| Type | Use Case | Example |
|------|----------|---------|
| boolean | Simple on/off | New UI toggle |
| percentage | Gradual rollout | 25% of users |
| user_list | Beta testing | Specific user IDs |

## Common Workflows

### 1. New Feature Rollout
```
Create flag (disabled) → Test internally (user_list) → 
Enable for 5% → 25% → 50% → 100% → Remove flag
```

### 2. A/B Test
```
Create experiment → Run for 2 weeks → 
Analyze results → Pick winner → Remove experiment
```

### 3. Beta Program
```
Create user_list flag → Add beta users → 
Collect feedback → Convert to percentage rollout
```

## Best Practices

✅ **DO:**
- Use descriptive keys (snake_case)
- Start small (1-5% rollout)
- Monitor metrics at each phase
- Set metadata for context
- Clean up old flags

❌ **DON'T:**
- Change variant weights mid-experiment
- Enable 100% immediately
- Leave unused flags
- Use spaces in keys
- Skip testing phase

## Troubleshooting

**Feature not showing for user:**
- Check `is_enabled` is true
- Verify flag_type matches usage
- For percentage: user might be in other 75%
- For user_list: check user_id in array

**Variant assignment inconsistent:**
- Should be deterministic
- Check for multiple experiment keys
- Verify experiment is active

**Can't create flag/experiment:**
- Check for duplicate keys
- Verify admin permissions
- Validate JSON structure

## Migration

```bash
# Run migration
alembic upgrade head

# Check migration status
alembic current

# Rollback if needed
alembic downgrade -1
```

