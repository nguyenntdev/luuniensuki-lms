# P1-EXP-01: A/B Testing Framework - API Reference

## Table of Contents

1. [User Endpoints](#user-endpoints)
2. [Admin Feature Flag Endpoints](#admin-feature-flag-endpoints)
3. [Admin Experiment Endpoints](#admin-experiment-endpoints)
4. [Data Models](#data-models)

## User Endpoints

### Get All Features for Current User

Get all feature flags and their enabled/disabled status for the authenticated user.

**Endpoint:** `GET /api/v1/features`

**Authentication:** Required (Bearer token)

**Response:** `200 OK`

```json
{
  "features": {
    "new_onboarding_flow": true,
    "enhanced_analytics": false,
    "beta_feature": true
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/features \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### Check Specific Feature

Check if a specific feature is enabled for the authenticated user.

**Endpoint:** `GET /api/v1/features/{key}`

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `key` (string): Feature flag key

**Response:** `200 OK`

```json
{
  "key": "new_onboarding_flow",
  "enabled": true,
  "metadata": {
    "version": "2.0",
    "owner": "product-team"
  }
}
```

**Errors:**
- `404 Not Found`: Feature flag does not exist

**Example:**
```bash
curl http://localhost:8000/api/v1/features/new_onboarding_flow \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### Get Experiment Assignments

Get all active experiments and the assigned variants for the authenticated user.

**Endpoint:** `GET /api/v1/experiments`

**Authentication:** Required (Bearer token)

**Response:** `200 OK`

```json
{
  "experiments": {
    "quiz_difficulty_test": "variant_a",
    "lesson_layout_test": "control"
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/experiments \
  -H "Authorization: Bearer eyJhbGc..."
```

---

## Admin Feature Flag Endpoints

### List All Feature Flags

Get a list of all feature flags in the system.

**Endpoint:** `GET /api/v1/admin/feature-flags`

**Authentication:** Required (Admin role)

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "key": "new_onboarding_flow",
    "name": "New Onboarding Flow",
    "description": "Redesigned user onboarding experience",
    "flag_type": "percentage",
    "is_enabled": true,
    "percentage": 50,
    "allowed_user_ids": null,
    "metadata": {
      "owner": "product-team"
    },
    "created_at": "2025-01-20T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  }
]
```

**Example:**
```bash
curl http://localhost:8000/api/v1/admin/feature-flags \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

### Create Feature Flag

Create a new feature flag.

**Endpoint:** `POST /api/v1/admin/feature-flags`

**Authentication:** Required (Admin role)

**Request Body:**

```json
{
  "key": "new_feature",
  "name": "New Feature",
  "description": "Description of the feature",
  "flag_type": "boolean",
  "is_enabled": false,
  "percentage": 0,
  "allowed_user_ids": null,
  "metadata": {
    "owner": "team-name"
  }
}
```

**Fields:**
- `key` (string, required): Unique identifier (1-100 chars)
- `name` (string, required): Display name (1-255 chars)
- `description` (string, optional): Detailed description
- `flag_type` (string, required): One of: "boolean", "percentage", "user_list"
- `is_enabled` (boolean, optional): Default: false
- `percentage` (integer, optional): 0-100, default: 0
- `allowed_user_ids` (array, optional): List of user ID strings
- `metadata` (object, optional): Additional data

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "key": "new_feature",
  "name": "New Feature",
  ...
}
```

**Errors:**
- `400 Bad Request`: Invalid flag_type or duplicate key
- `403 Forbidden`: Not admin

**Example:**
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

---

### Update Feature Flag

Update an existing feature flag.

**Endpoint:** `PUT /api/v1/admin/feature-flags/{flag_id}`

**Authentication:** Required (Admin role)

**Path Parameters:**
- `flag_id` (UUID): Feature flag ID

**Request Body:**

All fields are optional. Only provided fields will be updated.

```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "flag_type": "percentage",
  "is_enabled": true,
  "percentage": 75,
  "allowed_user_ids": ["user-1", "user-2"],
  "metadata": {
    "updated": true
  }
}
```

**Response:** `200 OK`

**Errors:**
- `404 Not Found`: Feature flag does not exist
- `400 Bad Request`: Invalid flag_type

**Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/admin/feature-flags/$FLAG_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_enabled": false}'
```

---

### Delete Feature Flag

Delete a feature flag.

**Endpoint:** `DELETE /api/v1/admin/feature-flags/{flag_id}`

**Authentication:** Required (Admin role)

**Path Parameters:**
- `flag_id` (UUID): Feature flag ID

**Response:** `204 No Content`

**Errors:**
- `404 Not Found`: Feature flag does not exist

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/admin/feature-flags/$FLAG_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Admin Experiment Endpoints

### List All Experiments

Get a list of all experiments in the system.

**Endpoint:** `GET /api/v1/admin/experiments`

**Authentication:** Required (Admin role)

**Response:** `200 OK`

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "key": "quiz_difficulty_test",
    "name": "Quiz Difficulty A/B Test",
    "description": "Testing different quiz difficulty levels",
    "variants": [
      {
        "key": "control",
        "name": "Original Difficulty",
        "weight": 50
      },
      {
        "key": "variant_a",
        "name": "Easier Questions",
        "weight": 50
      }
    ],
    "is_active": true,
    "start_date": "2025-01-20T00:00:00Z",
    "end_date": "2025-02-20T00:00:00Z",
    "created_at": "2025-01-20T10:00:00Z"
  }
]
```

**Example:**
```bash
curl http://localhost:8000/api/v1/admin/experiments \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

### Create Experiment

Create a new A/B test experiment.

**Endpoint:** `POST /api/v1/admin/experiments`

**Authentication:** Required (Admin role)

**Request Body:**

```json
{
  "key": "quiz_difficulty_test",
  "name": "Quiz Difficulty A/B Test",
  "description": "Testing different quiz difficulty levels",
  "variants": [
    {
      "key": "control",
      "name": "Original Difficulty",
      "weight": 50
    },
    {
      "key": "variant_a",
      "name": "Easier Questions",
      "weight": 25
    },
    {
      "key": "variant_b",
      "name": "Harder Questions",
      "weight": 25
    }
  ],
  "is_active": true,
  "start_date": "2025-01-20T00:00:00Z",
  "end_date": "2025-02-20T00:00:00Z"
}
```

**Fields:**
- `key` (string, required): Unique identifier (1-100 chars)
- `name` (string, required): Display name (1-255 chars)
- `description` (string, optional): Detailed description
- `variants` (array, required): Array of variant objects
  - Each variant must have: `key`, `name`, `weight`
  - Weights must be non-negative integers
- `is_active` (boolean, optional): Default: false
- `start_date` (datetime, optional): Experiment start time
- `end_date` (datetime, optional): Experiment end time

**Response:** `201 Created`

**Errors:**
- `400 Bad Request`: Invalid variants, duplicate key, or validation error
- `403 Forbidden`: Not admin

**Example:**
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

---

### Update Experiment

Update an existing experiment.

**Endpoint:** `PUT /api/v1/admin/experiments/{experiment_id}`

**Authentication:** Required (Admin role)

**Path Parameters:**
- `experiment_id` (UUID): Experiment ID

**Request Body:**

All fields are optional. Only provided fields will be updated.

```json
{
  "name": "Updated Test Name",
  "description": "Updated description",
  "variants": [
    {"key": "control", "name": "Control", "weight": 60},
    {"key": "variant_a", "name": "Variant A", "weight": 40}
  ],
  "is_active": false,
  "start_date": "2025-01-21T00:00:00Z",
  "end_date": "2025-02-21T00:00:00Z"
}
```

**Response:** `200 OK`

**Errors:**
- `404 Not Found`: Experiment does not exist
- `400 Bad Request`: Invalid variants

**Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/admin/experiments/$EXPERIMENT_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

---

### Delete Experiment

Delete an experiment and all its user assignments.

**Endpoint:** `DELETE /api/v1/admin/experiments/{experiment_id}`

**Authentication:** Required (Admin role)

**Path Parameters:**
- `experiment_id` (UUID): Experiment ID

**Response:** `204 No Content`

**Errors:**
- `404 Not Found`: Experiment does not exist

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/admin/experiments/$EXPERIMENT_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

### Get Experiment Assignments

Get all user assignments for a specific experiment (paginated).

**Endpoint:** `GET /api/v1/admin/experiments/{experiment_id}/assignments`

**Authentication:** Required (Admin role)

**Path Parameters:**
- `experiment_id` (UUID): Experiment ID

**Query Parameters:**
- `page` (integer, optional): Page number, default: 1
- `page_size` (integer, optional): Items per page (1-100), default: 50

**Response:** `200 OK`

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "user_id": "880e8400-e29b-41d4-a716-446655440000",
    "experiment_id": "660e8400-e29b-41d4-a716-446655440000",
    "variant_key": "variant_a",
    "assigned_at": "2025-01-20T10:30:00Z"
  }
]
```

**Errors:**
- `404 Not Found`: Experiment does not exist

**Example:**
```bash
curl "http://localhost:8000/api/v1/admin/experiments/$EXPERIMENT_ID/assignments?page=1&page_size=50" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Data Models

### FeatureFlag

```typescript
{
  id: UUID
  key: string (unique, 1-100 chars)
  name: string (1-255 chars)
  description: string | null
  flag_type: "boolean" | "percentage" | "user_list"
  is_enabled: boolean
  percentage: number (0-100)
  allowed_user_ids: string[] | null
  metadata: object | null
  created_at: datetime
  updated_at: datetime
}
```

### Experiment

```typescript
{
  id: UUID
  key: string (unique, 1-100 chars)
  name: string (1-255 chars)
  description: string | null
  variants: Array<{
    key: string
    name: string
    weight: number (non-negative integer)
  }>
  is_active: boolean
  start_date: datetime | null
  end_date: datetime | null
  created_at: datetime
}
```

### UserExperimentAssignment

```typescript
{
  id: UUID
  user_id: UUID
  experiment_id: UUID
  variant_key: string
  assigned_at: datetime
}
```

---

## Error Responses

All endpoints may return these common errors:

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found

```json
{
  "detail": "Feature flag not found"
}
```

### 400 Bad Request

```json
{
  "detail": "Invalid flag_type. Must be one of: boolean, percentage, user_list"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "key"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

- User endpoints: No rate limiting
- Admin endpoints: Standard admin rate limits apply

## Pagination

Endpoints that support pagination:
- `GET /api/v1/admin/experiments/{experiment_id}/assignments`

Default page size: 50
Maximum page size: 100

---

## Authentication

All endpoints require JWT authentication via Bearer token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Admin endpoints additionally require the user to have an admin role (`admin` or `super_admin`).

