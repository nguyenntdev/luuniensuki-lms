# P0-CMS-03: Content Versioning Implementation

## Overview

This document describes the implementation of content versioning metadata for the Luuniensuki LMS platform. This feature allows tracking changes to lesson content, maintaining version history, and enabling content rollback.

## Changes Made

### 1. Database Models (`backend/models.py`)

#### Extended LessonContent Model
Added versioning fields to the `LessonContent` model:
- `version: int` - Current version number (default: 1, auto-increments on update)
- `last_editor_id: UUID` - Foreign key to users table (nullable)
- `published_at: datetime` - Timestamp when content was published (nullable)
- `publish_note: str` - Note describing this published version (nullable)
- Relationship to `User` via `last_editor`

#### New ContentVersion Model
Created a new `ContentVersion` model to track complete version history:
- `id: UUID` - Primary key
- `content_type: str` - Type of content (e.g., "lesson", "quiz")
- `content_id: UUID` - ID of the content being versioned
- `version: int` - Version number for this snapshot
- `data: JSONB` - Complete snapshot of content at this version
- `editor_id: UUID` - Foreign key to user who created this version
- `change_note: str` - Description of changes (nullable)
- `created_at: datetime` - When this version was created

Indexes added:
- `idx_content_versions_type` on `content_type`
- `idx_content_versions_content` on `content_id`
- `idx_content_versions_created` on `created_at`

### 2. Database Migration

Created migration file: `migrations/versions/0012_content_versioning.py`

**Upgrade Operations:**
- Adds versioning columns to `lesson_content` table
- Creates `content_versions` table with appropriate indexes
- Sets up foreign key constraints

**Downgrade Operations:**
- Removes all versioning-related changes
- Safe rollback to previous schema

### 3. API Schemas (`backend/schemas.py`)

Added new Pydantic schemas:
- `ContentVersionOut` - Full version details with data
- `ContentVersionListOut` - Summary for version listing (without full data)
- `RevertContentIn` - Request body for version revert operations

### 4. Admin Schemas Updates (`backend/main.py`)

Updated `AdminLessonOut` to include:
- `version: int`
- `last_editor_id: Optional[UUID]`
- `published_at: Optional[datetime]`
- `publish_note: Optional[str]`

Updated `AdminLessonUpdateRequest` to include:
- `publish_note: Optional[str]` - Note for publishing this version

### 5. API Endpoints

Added three new admin endpoints for content versioning:

#### GET `/api/v1/admin/content/{content_type}/{content_id}/versions`
- Lists all versions of a content item
- Returns: `list[ContentVersionListOut]`
- Requires: Staff user authentication (`get_staff_user`)
- Includes editor names for each version

#### GET `/api/v1/admin/content/{content_type}/{content_id}/versions/{version}`
- Retrieves a specific version with full data
- Returns: `ContentVersionOut`
- Requires: Staff user authentication (`get_staff_user`)

#### POST `/api/v1/admin/content/{content_type}/{content_id}/revert/{version}`
- Reverts content to a specific version
- Request body: `RevertContentIn` (optional change_note)
- Returns: Success message with new version number
- Requires: Staff user authentication (`get_staff_user`)
- Creates snapshots before and after revert

### 6. Content Update Logic

Modified `update_admin_lesson` endpoint to:
1. Create a snapshot before updating (via `_create_content_snapshot`)
2. Apply updates from request payload
3. Increment version number
4. Set `last_editor_id` to current user
5. Set `published_at` timestamp when publishing
6. Save `publish_note` if provided

Modified `create_admin_lesson` endpoint to:
1. Set `last_editor_id` on creation
2. Set `published_at` if created as published
3. Return new versioning fields in response

### 7. Helper Functions

Added `_create_content_snapshot()` helper function:
- Creates a JSONB snapshot of current content state
- Stores in `content_versions` table
- Supports "lesson" content type (extensible for quiz, etc.)
- Includes editor_id and optional change_note

## Usage Examples

### Creating/Updating Lessons
When admins or teachers update lesson content, the system automatically:
- Saves the previous version
- Increments the version number
- Tracks who made the change
- Records when it was published (if applicable)

### Viewing Version History
```http
GET /api/v1/admin/content/lesson/{lesson_id}/versions
Authorization: Bearer {token}
```

Response includes all versions with metadata.

### Viewing Specific Version
```http
GET /api/v1/admin/content/lesson/{lesson_id}/versions/3
Authorization: Bearer {token}
```

Returns complete data snapshot for version 3.

### Reverting to Previous Version
```http
POST /api/v1/admin/content/lesson/{lesson_id}/revert/3
Authorization: Bearer {token}
Content-Type: application/json

{
  "change_note": "Reverting due to incorrect information"
}
```

## Migration Instructions

To apply this migration to your database:

```bash
# If using Docker
docker-compose exec backend alembic upgrade head

# If running locally with virtual environment
cd backend
source venv/bin/activate  # or your venv activation command
alembic upgrade head
```

To rollback:
```bash
alembic downgrade -1
```

## Security & Access Control

- All versioning endpoints require authentication
- Staff roles (teacher, admin, super_admin) can view versions
- Staff roles can revert content
- Teachers can only edit unpublished content
- Only admins/super_admins can publish content

## Future Enhancements

1. **Quiz Versioning**: Extend to support quiz question versioning
2. **Diff Viewer**: API endpoint to compare two versions
3. **Audit Trail**: Enhanced logging of who changed what
4. **Version Labels**: Allow naming important versions (e.g., "v1.0", "major-revision")
5. **Scheduled Publishing**: Set future publish dates

## Testing Recommendations

1. Test creating new lesson content
2. Test updating existing lessons multiple times
3. Test version listing and retrieval
4. Test reverting to previous versions
5. Test permission boundaries (teacher vs admin)
6. Test published_at timestamp behavior
7. Verify version snapshots contain complete data

## Files Modified

1. `backend/models.py` - Added versioning fields and ContentVersion model
2. `backend/schemas.py` - Added versioning response schemas
3. `backend/main.py` - Added endpoints and updated lesson CRUD
4. `migrations/versions/0012_content_versioning.py` - Database migration

## Notes

- Version numbers start at 1 and increment with each change
- Snapshots are stored as JSONB for efficient querying
- The system maintains complete history - versions are never deleted
- Reverting creates two new snapshots: before and after revert

