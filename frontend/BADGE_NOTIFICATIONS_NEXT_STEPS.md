# Badge Unlock Notifications - Next Steps

## For Developers

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Test Locally
```bash
npm run dev
```

Navigate to http://localhost:3000 and test badge notifications.

### 3. Backend Integration

Ensure your API endpoints return `badges_awarded` field:

**Quiz Submit Endpoint:**
```python
# backend/routes/motif_routes.py (or similar)

@router.post("/motifs/{motif_id}/quiz/submit")
async def submit_quiz(motif_id: str, ...):
    # ... existing quiz logic ...
    
    # Check for badge unlocks
    badges_awarded = check_badge_unlocks(user, quiz_result)
    
    return {
        "passed": True,
        "score": score,
        "max_score": max_score,
        "xp_awarded": xp_awarded,
        "total_xp": user.total_xp,
        "badges_awarded": badges_awarded  # ← Add this field
    }
```

**Lesson Complete Endpoint:**
```python
# backend/routes/motif_routes.py (or similar)

@router.post("/motifs/{motif_id}/complete-lesson")
async def complete_lesson(motif_id: str, ...):
    # ... existing lesson logic ...
    
    # Check for badge unlocks
    badges_awarded = check_badge_unlocks(user, lesson_result)
    
    return {
        "status": "learned",
        "xp_awarded": xp_awarded,
        "total_xp": user.total_xp,
        "badges_awarded": badges_awarded  # ← Add this field
    }
```

### 4. Badge Data Structure

Each badge in `badges_awarded` array should have:

```python
{
    "id": str,           # Unique badge identifier
    "name": str,         # Display name (Vietnamese)
    "description": str,  # Achievement description
    "icon_url": str      # Optional: URL to badge icon image
}
```

Example:
```python
badges_awarded = [
    {
        "id": "first-quiz",
        "name": "Người Mới Bắt Đầu",
        "description": "Hoàn thành quiz đầu tiên",
        "icon_url": "https://cdn.example.com/badges/first-quiz.png"
    }
]
```

### 5. Code Quality Checks

Before committing, run:

```bash
# Lint check
npm run lint

# Fix linting issues
npm run lint -- --fix

# Build check
npm run build
```

### 6. Git Commit

```bash
git add frontend/src/stores/badgeStore.js
git add frontend/src/components/badges/
git add frontend/src/app/layout.jsx
git add frontend/src/app/motif/[motifId]/quiz/page.jsx
git add frontend/src/components/LessonSidebar.js
git add frontend/BADGE_*.md

git commit -m "feat: Add badge unlock notifications

- Created BadgeUnlockToast component with slide-up animation
- Created BadgeUnlockProvider for global badge notifications
- Created badgeStore (Zustand) for state management
- Integrated with quiz completion handler
- Integrated with lesson completion handler
- Added auto-dismiss (5s) and manual dismiss
- Supports multiple badges with stagger effect
- Responsive design for desktop/tablet/mobile
- Accessible with keyboard navigation

Refs: #XXX"
```

## For Product Managers

### Feature Overview
Users now receive celebratory toast notifications when they unlock badges, similar to the XP celebration overlay.

### User Experience
1. Complete a quiz or lesson
2. If badges are awarded, a gold toast appears at bottom-right
3. Toast shows badge name, description, and optional icon
4. Toast auto-dismisses after 5 seconds
5. User can manually dismiss by clicking X

### Metrics to Track
- Badge unlock rate (how many badges are earned per user session)
- Notification interaction rate (how many users dismiss manually vs auto)
- Badge unlock impact on retention (do badge notifications increase engagement?)

### A/B Testing Opportunities
- **Animation style**: Slide-up vs fade-in vs bounce
- **Display duration**: 3s vs 5s vs 7s
- **Sound effects**: With sound vs without
- **Position**: Bottom-right vs top-center vs full-screen modal

## Backend Todos

### 1. Create Badge Unlock Logic

```python
# backend/services/badge_service.py

def check_badge_unlocks(user_id: str, event_type: str, event_data: dict) -> List[dict]:
    """
    Check if user unlocked any badges based on event.
    
    Args:
        user_id: User identifier
        event_type: 'quiz_complete', 'lesson_complete', etc.
        event_data: Additional context (score, motif_id, etc.)
    
    Returns:
        List of newly unlocked badges
    """
    badges_awarded = []
    
    # Example: First quiz badge
    if event_type == 'quiz_complete':
        quiz_count = get_user_quiz_count(user_id)
        if quiz_count == 1:
            badges_awarded.append({
                "id": "first-quiz",
                "name": "Người Mới Bắt Đầu",
                "description": "Hoàn thành quiz đầu tiên",
                "icon_url": get_badge_icon_url("first-quiz")
            })
    
    # Example: Perfect score badge
    if event_type == 'quiz_complete' and event_data.get('percentage') == 100:
        badges_awarded.append({
            "id": "perfect-score",
            "name": "Điểm Tuyệt Đối",
            "description": "Đạt điểm tuyệt đối trong quiz",
            "icon_url": get_badge_icon_url("perfect-score")
        })
    
    # Save newly awarded badges to database
    for badge in badges_awarded:
        save_user_badge(user_id, badge['id'])
    
    return badges_awarded
```

### 2. Badge Icon Assets

Store badge icons in a CDN or public directory:

```
/public/badges/
  ├── first-quiz.png
  ├── perfect-score.png
  ├── lesson-master.png
  ├── speed-demon.png
  └── ...
```

Return URLs in API response:
```python
icon_url = f"{CDN_BASE_URL}/badges/{badge_id}.png"
```

### 3. Badge Rules Configuration

Define badge unlock conditions in a configuration file:

```python
# backend/config/badges.py

BADGE_RULES = {
    "first-quiz": {
        "name": "Người Mới Bắt Đầu",
        "description": "Hoàn thành quiz đầu tiên",
        "condition": lambda user: user.quiz_count == 1
    },
    "quiz-master": {
        "name": "Bậc Thầy Quiz",
        "description": "Hoàn thành 50 quiz",
        "condition": lambda user: user.quiz_count >= 50
    },
    # ... more badge rules
}
```

## Design Todos

### 1. Create Badge Icons

Design consistent badge icons with these specifications:
- **Size**: 128×128px (will be displayed at 48×48px for retina)
- **Format**: PNG with transparency
- **Style**: Flat design, Vietnamese cultural elements
- **Colors**: Gold/bronze/silver tiers

### 2. Badge Tier System

Consider visual hierarchy:
- **Bronze**: Common achievements (border: #CD7F32)
- **Silver**: Uncommon achievements (border: #C0C0C0)
- **Gold**: Rare achievements (border: #FFD700)
- **Platinum**: Legendary achievements (border: #E5E4E2)

### 3. Icon Naming Convention

```
{achievement-id}-{tier}.png

Examples:
- first-quiz-bronze.png
- perfect-score-silver.png
- quiz-master-gold.png
```

## QA Testing Checklist

- [ ] Badge appears when quiz is passed
- [ ] Badge appears when lesson is completed
- [ ] Multiple badges show sequentially
- [ ] Animation is smooth on all devices
- [ ] Works on Chrome, Firefox, Safari
- [ ] Works on iOS Safari
- [ ] Works on Android Chrome
- [ ] No console errors
- [ ] No network errors
- [ ] Accessible via keyboard
- [ ] Screen reader compatible

## Documentation Updates

After implementation, update:
- [ ] API documentation (add `badges_awarded` field)
- [ ] User guide (how to earn badges)
- [ ] Admin guide (how to configure badges)
- [ ] Developer guide (how to add new badge types)

## Monitoring & Alerts

Set up monitoring for:
- Badge unlock rate (alerts if drops below threshold)
- API errors on badge unlock endpoints
- Client-side errors in BadgeUnlockToast component
- Performance metrics (animation frame rate)

## Future Enhancements

### Phase 2
- [ ] Sound effects on badge unlock
- [ ] Confetti animation for rare badges
- [ ] Badge collection page
- [ ] Badge sharing on social media
- [ ] Badge rarity indicators

### Phase 3
- [ ] Animated badge icons (Lottie/Rive)
- [ ] Badge unlock history timeline
- [ ] Badge recommendations ("You're close to X!")
- [ ] Seasonal/event badges
- [ ] User badge showcase on profile

## Support Resources

- **Documentation**: See `BADGE_UNLOCK_NOTIFICATIONS.md`
- **Quick Reference**: See `BADGE_NOTIFICATIONS_QUICK_REF.md`
- **Visual Guide**: See `BADGE_NOTIFICATIONS_VISUAL_REF.md`
- **Testing**: See `BADGE_NOTIFICATIONS_TESTING.md`

## Questions?

Contact the development team or file an issue in the project repository.

