# P1-EXP-01: A/B Testing Framework - Documentation Index

## Overview

Complete implementation of A/B testing framework with feature flags for the Luuniensuki LMS platform. This enables gradual feature rollouts, A/B experiments, and targeted feature access.

## 📚 Documentation

### Core Documents

1. **[Implementation Guide](P1-EXP-01_IMPLEMENTATION.md)** ⭐
   - Full technical implementation details
   - Architecture overview
   - Database schema
   - Service layer functions
   - Testing guide
   - Best practices

2. **[API Reference](P1-EXP-01_API_REFERENCE.md)** 📖
   - Complete API endpoint documentation
   - Request/response examples
   - Error handling
   - Authentication requirements
   - Data models

3. **[Quick Reference](P1-EXP-01_QUICK_REFERENCE.md)** 🚀
   - Quick start guide
   - Common operations
   - Code snippets
   - Troubleshooting
   - Migration commands

## 🔧 Implementation Files

### Backend

**Models** (`backend/models.py`):
- `FlagType` enum - Feature flag types
- `FeatureFlag` model - Feature flag storage
- `Experiment` model - A/B test experiments
- `UserExperimentAssignment` model - User variant assignments

**Services** (`backend/services/experiments.py`):
- `is_feature_enabled_for_user()` - Check if feature is enabled
- `get_experiment_variant_for_user()` - Get assigned variant
- `get_all_features_for_user()` - Get all features for user
- `get_all_experiments_for_user()` - Get all experiments
- `create_feature_flag()` - Create new flag
- `update_feature_flag()` - Update existing flag
- `create_experiment()` - Create new experiment
- `update_experiment()` - Update existing experiment

**Schemas** (`backend/schemas.py`):
- `FeatureFlagOut`, `FeatureFlagCreateIn`, `FeatureFlagUpdateIn`
- `ExperimentOut`, `ExperimentCreateIn`, `ExperimentUpdateIn`
- `UserFeaturesOut`, `UserExperimentsOut`
- `FeatureCheckOut`, `UserExperimentAssignmentOut`

**API Endpoints** (`backend/main.py`):

User Endpoints:
- `GET /api/v1/features` - Get all features
- `GET /api/v1/features/{key}` - Check specific feature
- `GET /api/v1/experiments` - Get experiment assignments

Admin Endpoints:
- `GET /api/v1/admin/feature-flags` - List flags
- `POST /api/v1/admin/feature-flags` - Create flag
- `PUT /api/v1/admin/feature-flags/{id}` - Update flag
- `DELETE /api/v1/admin/feature-flags/{id}` - Delete flag
- `GET /api/v1/admin/experiments` - List experiments
- `POST /api/v1/admin/experiments` - Create experiment
- `PUT /api/v1/admin/experiments/{id}` - Update experiment
- `DELETE /api/v1/admin/experiments/{id}` - Delete experiment
- `GET /api/v1/admin/experiments/{id}/assignments` - View assignments

**Migration** (`migrations/versions/0033_feature_flags_experiments.py`):
- Creates `feature_flags` table
- Creates `experiments` table
- Creates `user_experiment_assignments` table
- Creates `flag_type` enum

## 🧪 Testing

**Test Script**: `test_experiments_api.sh`
- Automated API testing
- Tests all endpoints
- Verifies feature flag types
- Tests experiment assignment
- Validates persistence
- Cleanup after tests

**Run tests:**
```bash
./test_experiments_api.sh
```

## 🎯 Quick Start

### 1. Run Migration
```bash
alembic upgrade head
```

### 2. Create a Feature Flag
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

### 3. Check Feature as User
```bash
curl http://localhost:8000/api/v1/features/new_feature \
  -H "Authorization: Bearer $USER_TOKEN"
```

### 4. Create an Experiment
```bash
curl -X POST http://localhost:8000/api/v1/admin/experiments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "ab_test",
    "name": "A/B Test",
    "variants": [
      {"key": "control", "name": "Control", "weight": 50},
      {"key": "variant_a", "name": "Variant A", "weight": 50}
    ],
    "is_active": true
  }'
```

## 📊 Feature Types

### Boolean Flags
Simple on/off toggles for all users when enabled.

**Use cases:**
- Feature toggles
- Kill switches
- Configuration switches

### Percentage Rollout
Gradual rollout to a percentage of users (deterministic).

**Use cases:**
- Gradual feature rollouts
- Canary releases
- Risk mitigation

### User List
Specific list of allowed users.

**Use cases:**
- Beta testing
- VIP features
- Team-only features

## 🧬 Experiment Variants

Experiments support multiple variants with weighted distribution.

**Features:**
- Deterministic assignment (same user always gets same variant)
- Persistent assignments
- Flexible weighting
- Start/end dates

## 📈 Use Cases

### 1. Gradual Rollout
```
Internal (user_list) → 1% → 5% → 25% → 50% → 100% → Remove
```

### 2. A/B Testing
```
Create experiment → Run for 2 weeks → Analyze → Pick winner → Remove
```

### 3. Beta Program
```
user_list flag → Add beta users → Collect feedback → Convert to rollout
```

## 🔐 Security

- All CRUD operations require admin role
- Users can only see their own feature status
- Percentage values validated (0-100)
- Keys must be unique
- Proper authentication required

## 📝 Best Practices

### Feature Flag Naming
- Use snake_case: `new_dashboard_ui`
- Be descriptive: `enhanced_quiz_hints`
- Include version: `onboarding_v2`

### Experiment Design
- Always include "control" variant
- Use meaningful variant names
- Set appropriate weights
- Track start/end dates

### Rollout Strategy
- Start small (1-5%)
- Monitor metrics
- Increase gradually
- Clean up after 100%

## 🗑️ Cleanup

Remove feature flags after full rollout:
```bash
curl -X DELETE http://localhost:8000/api/v1/admin/feature-flags/{flag_id} \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Archive experiment results before deletion:
```bash
# Get assignments first
curl http://localhost:8000/api/v1/admin/experiments/{id}/assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Then delete
curl -X DELETE http://localhost:8000/api/v1/admin/experiments/{id} \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## 🐛 Troubleshooting

### Feature not showing for user
1. Check `is_enabled` is true
2. Verify flag_type matches usage
3. For percentage: user might be in other portion
4. For user_list: check user_id in array

### Variant assignment inconsistent
1. Verify experiment is active
2. Check for duplicate experiment keys
3. Assignments should be deterministic

### Can't create flag/experiment
1. Check for duplicate keys
2. Verify admin permissions
3. Validate JSON structure
4. Check variant validation

## 📖 Additional Resources

- [Feature Flag Best Practices](https://martinfowler.com/articles/feature-toggles.html)
- [A/B Testing Guide](https://www.optimizely.com/optimization-glossary/ab-testing/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

## ✅ Implementation Checklist

- [x] Add models to `backend/models.py`
- [x] Create service layer in `backend/services/experiments.py`
- [x] Add schemas to `backend/schemas.py`
- [x] Implement API endpoints in `backend/main.py`
- [x] Create database migration
- [x] Write comprehensive documentation
- [x] Create API reference
- [x] Create quick reference guide
- [x] Create test script
- [x] Add to project documentation index

## 🎉 Status

**IMPLEMENTATION COMPLETE** ✅

All components have been implemented, tested, and documented. The A/B testing framework is ready for use.

## 📞 Support

For questions or issues:
1. Check the [Implementation Guide](P1-EXP-01_IMPLEMENTATION.md)
2. Review the [API Reference](P1-EXP-01_API_REFERENCE.md)
3. Consult the [Quick Reference](P1-EXP-01_QUICK_REFERENCE.md)
4. Run the test script to verify setup
5. Contact the engineering team

---

**Version**: 1.0  
**Last Updated**: 2025-01-20  
**Status**: Complete ✅

