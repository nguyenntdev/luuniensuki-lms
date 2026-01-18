# P0-CMS-04: Review Workflow States - Implementation Summary

## Overview

This document summarizes the implementation of the content review workflow system for the Luuniensuki LMS. This feature allows content (lessons and quiz questions) to go through different states (draft, review, published, archived) with proper workflow controls and role-based permissions.

**Status**: ✅ Implementation Complete  
**Date**: December 2024  
**Related**: P0-CMS-03 (Content Versioning)

---

## Table of Contents

1. [Database Changes](#database-changes)
2. [Backend Models](#backend-models)
3. [API Schemas](#api-schemas)
4. [API Endpoints](#api-endpoints)
5. [Role-Based Permissions](#role-based-permissions)
6. [Migration Instructions](#migration-instructions)
7. [Testing Guide](#testing-guide)
8. [Next Steps](#next-steps)

---

## Database Changes

### New Enum Type

Created `ContentStatus` enum with four states:
- **draft**: Content is being worked on
- **review**: Content is ready for review
- **published**: Content is live and visible to users
- **archived**: Content is hidden/archived

### LessonContent Table Updates

Added 5 new columns:
```sql
- status: content_status (default 'draft')
- submitted_for_review_at: timestamptz (nullable)
- reviewed_by_id: uuid (FK to users, SET NULL on delete, nullable)
- reviewed_at: timestamptz (nullable)
- review_notes: text (nullable)
```

### QuizQuestion Table Updates

Added 6 new columns:
```sql
- status: content_status (default 'draft')
- submitted_for_review_at: timestamptz (nullable)
- reviewed_by_id: uuid (FK to users, SET NULL on delete, nullable)
- reviewed_at: timestamptz (nullable)
- review_notes: text (nullable)
- created_by_id: uuid (FK to users, SET NULL on delete, nullable)
```

### Migration File

**File**: `migrations/versions/0013_review_workflow.py`
- Revises: `0012_daily_missions`
- Creates enum type and adds columns
- Includes complete upgrade() and downgrade() functions

---

## Backend Models

### ContentStatus Enum

**File**: `backend/models.py` (lines 1300-1304)

```python
class ContentStatus(str, Enum):
    draft = "draft"
    review = "review"
    published = "published"
    archived = "archived"
```

### LessonContent Model Extensions

**File**: `backend/models.py` (lines 415-439)

Added workflow fields:
- `status`: ContentStatus enum (default=draft)
- `submitted_for_review_at`: DateTime with timezone
- `reviewed_by_id`: UUID foreign key to users
- `reviewed_at`: DateTime with timezone
- `review_notes`: Text field
- Relationships for `last_editor` and `reviewed_by` users

### QuizQuestion Model Extensions

**File**: `backend/models.py` (lines 587-624)

Added same workflow fields as LessonContent, plus:
- `created_by_id`: UUID foreign key to track question creator
- Relationships for `reviewed_by` and `created_by` users

---

## API Schemas

### Request Schemas

**File**: `backend/schemas.py` (lines 680-697)

```python
class SubmitForReviewIn(BaseModel):
    """Request schema for submitting content for review."""
    pass  # No additional fields needed

class ApproveContentIn(BaseModel):
    """Request schema for approving and publishing content."""
    review_notes: Optional[str] = None

class RejectContentIn(BaseModel):
    """Request schema for rejecting content."""
    review_notes: str = Field(..., min_length=1, description="Required rejection reason")
```

### Response Schemas

**File**: `backend/schemas.py` (lines 699-717)

```python
class PendingReviewItemOut(BaseSchema):
    """Schema for a content item pending review."""
    id: UUID
    content_type: str  # 'lesson' or 'quiz_question'
    title: str
    motif_name: Optional[str] = None
    submitted_by_id: Optional[UUID] = None
    submitted_by_name: Optional[str] = None
    submitted_at: Optional[datetime] = None
    version: Optional[int] = None

class PendingReviewListOut(BaseModel):
    """Response schema for pending review list."""
    lessons: list[PendingReviewItemOut] = Field(default_factory=list)
    quiz_questions: list[PendingReviewItemOut] = Field(default_factory=list)
    total_count: int
```

### Updated Admin Schemas

**AdminLessonOut** - Added workflow fields (lines 3499-3504):
- `status: str = "draft"`
- `submitted_for_review_at: Optional[datetime] = None`
- `reviewed_by_id: Optional[UUID] = None`
- `reviewed_at: Optional[datetime] = None`
- `review_notes: Optional[str] = None`

**AdminQuizQuestionOut** - Added workflow fields (lines 3550-3557):
- Same as AdminLessonOut, plus `created_by_id: Optional[UUID] = None`

---

## API Endpoints

All endpoints are in `backend/main.py` starting at line 7785.

## API Endpoints

All endpoints are in `backend/main.py` starting at line 7785.

### Lesson Workflow Endpoints

#### 1. Submit Lesson for Review
```http
POST /api/v1/admin/lessons/{lesson_id}/submit-review
Authorization: Bearer <token> (Teacher or Admin)
Content-Type: application/json

{}
```

**Permissions**: Teachers and Admins
**Action**: Changes status from `draft` → `review`
**Response**: AdminLessonOut with updated status

#### 2. Approve Lesson
```http
POST /api/v1/admin/lessons/{lesson_id}/approve
Authorization: Bearer <token> (Admin only)
Content-Type: application/json

{
  "review_notes": "Approved - content looks good" // optional
}
```

**Permissions**: Admins only
**Action**: Changes status from `review` or `draft` → `published`, sets `is_published=true`
**Response**: AdminLessonOut with updated status

#### 3. Reject Lesson
```http
POST /api/v1/admin/lessons/{lesson_id}/reject
Authorization: Bearer <token> (Admin only)
Content-Type: application/json

{
  "review_notes": "Needs more details on historical context" // required
}
```

**Permissions**: Admins only
**Action**: Changes status from `review` → `draft`
**Response**: AdminLessonOut with updated status and review notes

### Quiz Question Workflow Endpoints

#### 4. Submit Quiz Question for Review
```http
POST /api/v1/admin/quiz-questions/{question_id}/submit-review
Authorization: Bearer <token> (Teacher or Admin)
Content-Type: application/json

{}
```

**Permissions**: Teachers and Admins
**Action**: Changes status from `draft` → `review`
**Response**: AdminQuizQuestionOut with updated status

#### 5. Approve Quiz Question
```http
POST /api/v1/admin/quiz-questions/{question_id}/approve
Authorization: Bearer <token> (Admin only)
Content-Type: application/json

{
  "review_notes": "Approved" // optional
}
```

**Permissions**: Admins only
**Action**: Changes status from `review` or `draft` → `published`, sets `is_published=true`
**Response**: AdminQuizQuestionOut with updated status

#### 6. Reject Quiz Question
```http
POST /api/v1/admin/quiz-questions/{question_id}/reject
Authorization: Bearer <token> (Admin only)
Content-Type: application/json

{
  "review_notes": "Question is too ambiguous" // required
}
```

**Permissions**: Admins only
**Action**: Changes status from `review` → `draft`
**Response**: AdminQuizQuestionOut with updated status

### Pending Review List

#### 7. Get All Pending Reviews
```http
GET /api/v1/admin/content/pending-review
Authorization: Bearer <token> (Teacher or Admin)
```

**Permissions**: Teachers and Admins
**Returns**: All content items with status=`review`, grouped by type

**Response**:
```json
{
  "lessons": [
    {
      "id": "uuid",
      "content_type": "lesson",
      "title": "Lesson: Rồng",
      "motif_name": "Rồng",
      "submitted_by_id": "uuid",
      "submitted_by_name": "Teacher Name",
      "submitted_at": "2024-12-01T10:00:00Z",
      "version": 2
    }
  ],
  "quiz_questions": [
    {
      "id": "uuid",
      "content_type": "quiz_question",
      "title": "What does the dragon symbolize...",
      "motif_name": "Rồng",
      "submitted_by_id": "uuid",
      "submitted_by_name": "Teacher Name",
      "submitted_at": "2024-12-01T09:30:00Z",
      "version": null
    }
  ],
  "total_count": 2
}
```

---

## Role-Based Permissions

### Teachers (UserRole.teacher)
- ✅ Can create draft lessons and quiz questions
- ✅ Can edit their own draft content
- ✅ Can submit draft content for review
- ✅ Can view pending reviews
- ❌ Cannot approve/reject content
- ❌ Cannot publish content directly
- ❌ Cannot edit published content

### Admins (UserRole.admin, UserRole.super_admin)
- ✅ Can create, edit, and publish content directly
- ✅ Can submit content for review
- ✅ Can approve content (changes status to published)
- ✅ Can reject content (changes status back to draft with notes)
- ✅ Can view all pending reviews
- ✅ Can edit content in any status

### Status Transition Rules

```
draft ──(submit-review)──> review
         [Teacher/Admin]

review ──(approve)──> published
         [Admin only]

review ──(reject)──> draft
         [Admin only]

draft ──(approve)──> published
        [Admin only, direct publish]
```

---

## Migration Instructions

### Step 1: Apply Migration

Run the migration to create the new columns and enum:

```bash
# If using Docker
docker compose exec backend alembic upgrade head

# If running locally
cd /path/to/project
alembic upgrade head
```

### Step 2: Verify Migration

Check that the migration was applied:

```bash
# Check current revision
docker compose exec backend alembic current

# Should show: 0013_review_workflow (head)
```

### Step 3: Initialize Existing Data

All existing lessons and quiz questions will have `status=NULL`. The application defaults this to `draft` in the code.

Optionally, update existing published content:

```sql
-- Set published lessons to published status
UPDATE lesson_content
SET status = 'published'
WHERE is_published = true;

-- Set published questions to published status
UPDATE quiz_questions
SET status = 'published'
WHERE is_published = true;

-- Set unpublished content to draft
UPDATE lesson_content
SET status = 'draft'
WHERE is_published = false OR is_published IS NULL;

UPDATE quiz_questions
SET status = 'draft'
WHERE is_published = false OR is_published IS NULL;
```

---

## Testing Guide

### Manual Testing Checklist

#### Test 1: Teacher Creates and Submits Lesson

1. **Login as Teacher**
   ```bash
   POST /api/v1/auth/login
   {
     "email": "teacher@example.com",
     "password": "password"
   }
   ```

2. **Create Draft Lesson**
   ```bash
   POST /api/v1/admin/lessons
   {
     "motif_id": "<motif-uuid>",
     "description": "Test lesson about dragons",
     "intro_text": "Introduction to dragon motifs"
   }
   # Expected: status = "draft"
   ```

3. **Submit for Review**
   ```bash
   POST /api/v1/admin/lessons/{lesson_id}/submit-review
   {}
   # Expected: status = "review", submitted_for_review_at set
   ```

4. **Try to Approve (Should Fail)**
   ```bash
   POST /api/v1/admin/lessons/{lesson_id}/approve
   {}
   # Expected: 403 Forbidden - Teachers cannot approve
   ```

#### Test 2: Admin Reviews and Approves

1. **Login as Admin**
   ```bash
   POST /api/v1/auth/login
   {
     "email": "admin@example.com",
     "password": "password"
   }
   ```

2. **Get Pending Reviews**
   ```bash
   GET /api/v1/admin/content/pending-review
   # Expected: List of lessons and questions with status="review"
   ```

3. **Approve Lesson**
   ```bash
   POST /api/v1/admin/lessons/{lesson_id}/approve
   {
     "review_notes": "Content approved - looks good!"
   }
   # Expected: status = "published", is_published = true,
   #           reviewed_by_id = admin user id, reviewed_at set
   ```

#### Test 3: Admin Rejects Content

1. **Submit Question for Review** (as Teacher)
   ```bash
   POST /api/v1/admin/quiz-questions
   {
     "motif_id": "<motif-uuid>",
     "question_type": "multiple_choice",
     "question_text": "What does the dragon symbolize?",
     "correct_answer": "Power and prosperity",
     "options": ["Power", "Weakness", "Sadness"]
   }
   # Expected: status = "draft"

   POST /api/v1/admin/quiz-questions/{question_id}/submit-review
   {}
   # Expected: status = "review"
   ```

2. **Reject as Admin**
   ```bash
   POST /api/v1/admin/quiz-questions/{question_id}/reject
   {
     "review_notes": "Question needs more context and better options"
   }
   # Expected: status = "draft", review_notes saved,
   #           reviewed_by_id and reviewed_at set
   ```

#### Test 4: Admin Direct Publish

1. **Create and Publish in One Step**
   ```bash
   POST /api/v1/admin/lessons
   {
     "motif_id": "<motif-uuid>",
     "description": "Admin created lesson",
     "is_published": true
   }
   # Expected: status = "published", is_published = true
   #           (Admins can bypass review workflow)
   ```

### Integration Testing

#### Test Status Transitions

```python
# tests/backend/test_review_workflow.py

def test_lesson_workflow_full_cycle(client, teacher_token, admin_token):
    # Teacher creates draft
    response = client.post("/api/v1/admin/lessons",
        json={"motif_id": str(motif_id), "description": "Test"},
        headers={"Authorization": f"Bearer {teacher_token}"})
    assert response.json()["status"] == "draft"

    lesson_id = response.json()["id"]

    # Teacher submits for review
    response = client.post(f"/api/v1/admin/lessons/{lesson_id}/submit-review",
        json={},
        headers={"Authorization": f"Bearer {teacher_token}"})
    assert response.json()["status"] == "review"

    # Admin approves
    response = client.post(f"/api/v1/admin/lessons/{lesson_id}/approve",
        json={"review_notes": "Approved"},
        headers={"Authorization": f"Bearer {admin_token}"})
    assert response.json()["status"] == "published"
    assert response.json()["is_published"] == True
```

#### Test Permission Boundaries

```python
def test_teacher_cannot_approve(client, teacher_token):
    # Attempt to approve should fail with 403
    response = client.post(f"/api/v1/admin/lessons/{lesson_id}/approve",
        json={},
        headers={"Authorization": f"Bearer {teacher_token}"})
    assert response.status_code == 403

def test_cannot_submit_non_draft(client, teacher_token):
    # Attempt to submit already-reviewed content should fail
    response = client.post(f"/api/v1/admin/lessons/{lesson_id}/submit-review",
        json={},
        headers={"Authorization": f"Bearer {teacher_token}"})
    assert response.status_code == 400
    assert "draft" in response.json()["detail"].lower()
```

### Database Verification

```sql
-- Check workflow fields are populated correctly
SELECT
    id,
    status,
    is_published,
    submitted_for_review_at,
    reviewed_by_id,
    reviewed_at,
    review_notes
FROM lesson_content
WHERE status IS NOT NULL
ORDER BY submitted_for_review_at DESC;

-- Check quiz questions
SELECT
    id,
    status,
    created_by_id,
    submitted_for_review_at,
    reviewed_by_id
FROM quiz_questions
WHERE status = 'review'
ORDER BY submitted_for_review_at DESC;
```

---

## Next Steps

### Phase 1: Backend Testing (Current)
- [ ] Apply migration to development database
- [ ] Test all workflow endpoints manually
- [ ] Write integration tests for workflow
- [ ] Test permission boundaries
- [ ] Verify existing content compatibility

### Phase 2: Frontend Integration
- [ ] Update admin lesson editor to show workflow status
- [ ] Add "Submit for Review" button for teachers
- [ ] Create admin review dashboard showing pending items
- [ ] Add approve/reject buttons for admins
- [ ] Display review notes and reviewer information
- [ ] Add status badges (draft/review/published/archived)

### Phase 3: Notifications (Optional Enhancement)
- [ ] Notify admins when content is submitted for review
- [ ] Notify teachers when their content is approved/rejected
- [ ] Add email notifications for review actions
- [ ] Create in-app notification system

### Phase 4: Enhanced Features
- [ ] Add workflow history tracking
- [ ] Implement content archiving workflow
- [ ] Add bulk approve/reject operations
- [ ] Create analytics dashboard for content review metrics
- [ ] Add scheduled publishing (review → published at specific time)

---

## Files Changed

### Backend Files

1. **backend/models.py**
   - Added `ContentStatus` enum (lines 1300-1304)
   - Extended `LessonContent` model with workflow fields (lines 415-439)
   - Extended `QuizQuestion` model with workflow fields (lines 587-624)

2. **backend/schemas.py**
   - Added review workflow request schemas (lines 680-697)
   - Added review workflow response schemas (lines 699-717)

3. **backend/main.py**
   - Updated `ContentStatus` import (line 58)
   - Updated `AdminLessonOut` schema (lines 3482-3506)
   - Updated `AdminQuizQuestionOut` schema (lines 3537-3557)
   - Updated lesson list endpoint (lines 3606-3633)
   - Updated quiz question list endpoint (lines 3804-3827)
   - Updated create lesson endpoint (lines 3662-3708)
   - Updated create quiz question endpoint (lines 3855-3894)
   - Updated update endpoints with workflow fields
   - Added 7 new review workflow endpoints (lines 7785-8181)

4. **migrations/versions/0013_review_workflow.py**
   - New migration file (181 lines)
   - Creates `content_status` enum type
   - Adds workflow columns to both tables
   - Complete upgrade/downgrade functions

### Documentation Files

1. **P0-CMS-04_IMPLEMENTATION_SUMMARY.md** (this file)
   - Complete implementation documentation
   - API reference
   - Testing guide
   - Migration instructions

---

## Summary

✅ **Database Schema**: ContentStatus enum and workflow columns added
✅ **Backend Models**: Models extended with workflow fields and relationships
✅ **API Schemas**: Request/response schemas for all workflow operations
✅ **API Endpoints**: 7 new endpoints for complete workflow management
✅ **Permissions**: Role-based access control implemented
✅ **Migration**: Complete migration file with upgrade/downgrade
✅ **Documentation**: Comprehensive implementation guide

**Ready for**: Database migration and testing
**Next**: Apply migration, test endpoints, integrate with frontend

---

## Related Documentation

- [P0-CMS-03: Content Versioning](./P0-CMS-03_IMPLEMENTATION_SUMMARY.md)
- [Backend Models Reference](./backend/models.py)
- [API Schemas Reference](./backend/schemas.py)
- [Migration Files](./migrations/versions/)

---

**Implementation Date**: December 2024
**Implemented By**: Development Team
**Status**: ✅ Complete - Ready for Migration and Testing

