# Milestone Tracking API Reference

## Quick Reference

### Endpoints

#### 1. Get All Milestones
```http
GET /api/v1/milestones
Authorization: Bearer {token}
```

**Response:**
```json
{
  "milestones": [
    {
      "id": "uuid",
      "user_id": "uuid", 
      "milestone_type": "first_motif_discovered",
      "achieved_at": "2025-01-16T10:30:00Z",
      "context_data": {"motif_id": "uuid"},
      "celebrated": true,
      "created_at": "2025-01-16T10:30:00Z"
    }
  ]
}
```

#### 2. Get Pending Celebrations
```http
GET /api/v1/milestones/pending-celebration
Authorization: Bearer {token}
```

**Response:**
```json
{
  "pending_milestones": [
    {
      "id": "uuid",
      "milestone_type": "first_quiz_passed",
      "achieved_at": "2025-01-16T11:45:00Z",
      "context_data": {
        "motif_id": "uuid",
        "score": 8,
        "max_score": 10,
        "percentage": 80
      }
    }
  ]
}
```

#### 3. Celebrate Milestone
```http
POST /api/v1/milestones/{milestone_id}/celebrate
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "milestone_id": "uuid",
  "milestone_type": "first_quiz_passed",
  "message": "Amazing! You passed your first quiz!"
}
```

## Milestone Types

1. `first_motif_discovered` - Discovered first motif
2. `first_lesson_completed` - Completed first lesson
3. `first_quiz_passed` - Passed first quiz (≥70%)
4. `first_badge_earned` - Earned first badge
5. `first_streak_7` - Reached 7-day streak
6. `onboarding_completed` - Completed onboarding

## Context Data by Type

```typescript
type ContextData = 
  | { motif_id: string }                                    // first_motif_discovered
  | { motif_id: string }                                    // first_lesson_completed
  | { motif_id: string, score: number, max_score: number, percentage: number } // first_quiz_passed
  | { badge_slug: string }                                  // first_badge_earned
  | { streak_count: number }                                // first_streak_7
  | {}                                                       // onboarding_completed
```

## Frontend Integration Example

```typescript
// Check for pending celebrations after user actions
async function checkMilestones() {
  const response = await fetch('/api/v1/milestones/pending-celebration', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (response.ok) {
    const { pending_milestones } = await response.json();
    
    for (const milestone of pending_milestones) {
      await showCelebration(milestone);
      await celebrateMilestone(milestone.id);
    }
  }
}

async function celebrateMilestone(milestoneId: string) {
  await fetch(`/api/v1/milestones/${milestoneId}/celebrate`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

// Load all milestones for profile page
async function loadAllMilestones() {
  const response = await fetch('/api/v1/milestones', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (response.ok) {
    const { milestones } = await response.json();
    return milestones;
  }
}
```

## Celebration Messages

Default messages returned by celebrate endpoint:

- **first_motif_discovered**: "Congratulations on discovering your first motif!"
- **first_quiz_passed**: "Amazing! You passed your first quiz!"
- **first_lesson_completed**: "Great job on completing your first lesson!"
- **first_badge_earned**: "You earned your first badge!"
- **first_streak_7**: "Incredible! You've maintained a 7-day streak!"
- **onboarding_completed**: "Welcome aboard! You've completed onboarding!"

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized to celebrate this milestone"
}
```

### 404 Not Found
```json
{
  "detail": "Milestone not found"
}
```

## Best Practices

1. **Poll after key events**: Check pending celebrations after quiz submissions, lesson completions
2. **Show celebrations immediately**: Don't batch - show each milestone celebration right away
3. **Mark as celebrated**: Always call celebrate endpoint after showing the modal
4. **Cache all milestones**: Load once for profile page, update cache when new milestones created
5. **Handle errors gracefully**: Don't block user flow if milestone endpoints fail

## Database Schema

```sql
CREATE TABLE user_milestones (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    milestone_type milestone_type NOT NULL,
    achieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    context_data JSONB,
    celebrated BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_milestones_user_type UNIQUE (user_id, milestone_type)
);
```

