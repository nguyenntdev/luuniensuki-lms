# P1-REC-02: API Reference

## Overview
This document provides detailed API reference for the Lesson Prerequisites and Next Lesson endpoints.

---

## Endpoints

### 1. Get Next Lesson

**Endpoint**: `GET /api/v1/lessons/next`

**Description**: Returns the next recommended lesson for the authenticated user based on their progress, prerequisites, and optionally filtered by urn.

**Authentication**: Required (Bearer token)

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `urn_id` | UUID | No | Filter lessons from a specific urn |

**Response**: `200 OK`

**Response Schema**: `NextLessonOut`
```json
{
  "lesson_id": "uuid | null",
  "motif_id": "uuid | null",
  "motif_name": "string | null",
  "motif_slug": "string | null",
  "urn_id": "uuid | null",
  "urn_name": "string | null",
  "difficulty_level": "integer (1-5) | null",
  "estimated_time_minutes": "integer | null",
  "reason": "string",
  "has_prerequisites": "boolean",
  "progress_status": "string | null"
}
```

**Reason Values**:
- `continue_learning`: User has started but not completed this lesson
- `next_in_sequence`: Next logical lesson in the learning path
- `no_lessons_available`: No suitable lessons found

**Progress Status Values**:
- `hidden`: Not yet discovered
- `discovered`: Found but not started
- `learned`: Lesson completed
- `mastered`: Lesson mastered (quiz passed)

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/lessons/next" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Example Response**:
```json
{
  "lesson_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "motif_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "motif_name": "Rồng",
  "motif_slug": "rong",
  "urn_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "urn_name": "Cao Đình",
  "difficulty_level": 2,
  "estimated_time_minutes": 15,
  "reason": "continue_learning",
  "has_prerequisites": false,
  "progress_status": "discovered"
}
```

---

### 2. Get Lesson Prerequisites

**Endpoint**: `GET /api/v1/lessons/{lesson_id}/prerequisites`

**Description**: Returns all prerequisite lessons for a specific lesson, including completion status for each prerequisite.

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lesson_id` | UUID | Yes | ID of the lesson |

**Response**: `200 OK`

**Response Schema**: `LessonPrerequisitesOut`
```json
{
  "lesson_id": "uuid",
  "prerequisites": [
    {
      "id": "uuid",
      "motif_id": "uuid",
      "motif_name": "string",
      "motif_slug": "string",
      "difficulty_level": "integer | null",
      "estimated_time_minutes": "integer | null",
      "is_strict": "boolean",
      "is_completed": "boolean"
    }
  ],
  "all_prerequisites_met": "boolean"
}
```

**Field Descriptions**:
- `is_strict`: If true, prerequisite must be completed to unlock the lesson. If false, it's only recommended.
- `is_completed`: Whether the user has completed this prerequisite
- `all_prerequisites_met`: Whether all strict prerequisites have been completed

**Error Responses**:
- `404 Not Found`: Lesson not found

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/lessons/a1b2c3d4-e5f6-7890-abcd-ef1234567890/prerequisites" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Example Response**:
```json
{
  "lesson_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "prerequisites": [
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "motif_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "motif_name": "Phượng Hoàng",
      "motif_slug": "phuong-hoang",
      "difficulty_level": 1,
      "estimated_time_minutes": 10,
      "is_strict": true,
      "is_completed": true
    },
    {
      "id": "d4e5f6a7-b8c9-0123-defg-234567890123",
      "motif_id": "e5f6a7b8-c9d0-1234-efgh-345678901234",
      "motif_name": "Kỳ Lân",
      "motif_slug": "ky-lan",
      "difficulty_level": 1,
      "estimated_time_minutes": 12,
      "is_strict": false,
      "is_completed": false
    }
  ],
  "all_prerequisites_met": true
}
```

---

### 3. Check Lesson Unlock Status

**Endpoint**: `GET /api/v1/lessons/{lesson_id}/is-unlocked`

**Description**: Checks whether a lesson is unlocked for the user. Returns unlock status and lists any missing prerequisites.

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lesson_id` | UUID | Yes | ID of the lesson |

**Response**: `200 OK`

**Response Schema**: `LessonUnlockStatusOut`
```json
{
  "lesson_id": "uuid",
  "is_unlocked": "boolean",
  "missing_prerequisites": [
    {
      "id": "uuid",
      "motif_id": "uuid",
      "motif_name": "string",
      "motif_slug": "string",
      "difficulty_level": "integer | null",
      "estimated_time_minutes": "integer | null",
      "is_strict": true,
      "is_completed": false
    }
  ],
  "recommended_prerequisites": [
    {
      "id": "uuid",
      "motif_id": "uuid",
      "motif_name": "string",
      "motif_slug": "string",
      "difficulty_level": "integer | null",
      "estimated_time_minutes": "integer | null",
      "is_strict": false,
      "is_completed": false
    }
  ]
}
```

**Field Descriptions**:
- `is_unlocked`: True if all strict prerequisites are met
- `missing_prerequisites`: List of strict prerequisites not yet completed (blocks access)
- `recommended_prerequisites`: List of recommended prerequisites not yet completed (doesn't block access)

**Error Responses**:
- `404 Not Found`: Lesson not found

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/lessons/a1b2c3d4-e5f6-7890-abcd-ef1234567890/is-unlocked" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Example Response (Unlocked)**:
```json
{
  "lesson_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "is_unlocked": true,
  "missing_prerequisites": [],
  "recommended_prerequisites": []
}
```

**Example Response (Locked)**:
```json
{
  "lesson_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "is_unlocked": false,
  "missing_prerequisites": [
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "motif_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "motif_name": "Phượng Hoàng",
      "motif_slug": "phuong-hoang",
      "difficulty_level": 1,
      "estimated_time_minutes": 10,
      "is_strict": true,
      "is_completed": false
    }
  ],
  "recommended_prerequisites": []
}
```

---

### 4. Get Lesson Sequence

**Endpoint**: `GET /api/v1/lessons/sequence`

**Description**: Returns the full ordered learning sequence for the user, showing all lessons with their unlock status, completion status, and position in the sequence.

**Authentication**: Required (Bearer token)

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `urn_id` | UUID | No | Filter lessons from a specific urn |

**Response**: `200 OK`

**Response Schema**: `LessonSequenceOut`
```json
{
  "urn_id": "uuid | null",
  "urn_name": "string | null",
  "total_lessons": "integer",
  "completed_lessons": "integer",
  "current_position": "integer",
  "sequence": [
    {
      "lesson_id": "uuid",
      "motif_id": "uuid",
      "motif_name": "string",
      "motif_slug": "string",
      "urn_id": "uuid",
      "urn_name": "string",
      "difficulty_level": "integer | null",
      "estimated_time_minutes": "integer | null",
      "is_unlocked": "boolean",
      "is_completed": "boolean",
      "progress_status": "string | null",
      "position": "integer"
    }
  ]
}
```

**Field Descriptions**:
- `total_lessons`: Total number of lessons in the sequence
- `completed_lessons`: Number of lessons the user has mastered
- `current_position`: The furthest position the user has reached (based on completed lessons)
- `sequence`: Ordered list of lessons
- `position`: 1-based position in the sequence
- `is_unlocked`: Whether the user can access this lesson (prerequisites met)
- `is_completed`: Whether the user has mastered this lesson

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/lessons/sequence" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Example Request (with urn filter)**:
```bash
curl -X GET "http://localhost:8000/api/v1/lessons/sequence?urn_id=c3d4e5f6-a7b8-9012-cdef-123456789012" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Example Response**: (See implementation summary for full example)

---

## Error Responses

All endpoints may return the following error responses:

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Lesson not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```
