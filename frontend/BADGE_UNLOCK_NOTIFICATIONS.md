# Badge Unlock Notifications - Implementation Summary

## Overview
Added toast notification system to celebrate when users unlock new badges after completing quizzes or lessons.

## Files Created

### 1. `frontend/src/stores/badgeStore.js`
Zustand store for managing badge notification state.

**State:**
- `unlockedBadge`: Currently displayed badge (null when no badge is showing)

**Actions:**
- `showUnlockBadge(badge)`: Display a badge unlock notification
- `clearUnlockBadge()`: Clear the current notification

### 2. `frontend/src/components/badges/BadgeUnlockToast.jsx`
Toast component that displays badge unlock animations.

**Features:**
- Slide-up entrance animation
- Auto-dismisses after 5 seconds
- Click-to-dismiss functionality
- Shows badge icon, name, and description
- Gold gradient background for celebration feel
- Responsive design with proper text truncation

**Props:**
- `badge`: Badge object with `name`, `description`, and optional `icon_url`
- `onClose`: Callback when toast is dismissed

### 3. `frontend/src/components/badges/BadgeUnlockProvider.jsx`
Provider component that renders badge toasts globally.

**Usage:**
Wrap the app with this provider to enable badge notifications anywhere.

### 4. `frontend/src/components/badges/index.js`
Barrel export for cleaner imports.

## Files Modified

### 1. `frontend/src/app/layout.jsx`
- Imported `BadgeUnlockProvider`
- Wrapped app content with `<BadgeUnlockProvider>` inside `XpCelebrationProvider`

### 2. `frontend/src/app/motif/[motifId]/quiz/page.jsx`
- Imported `useBadgeStore`
- Added badge notification logic in quiz submission handler
- Shows notifications for `res.badges_awarded` array
- Staggers multiple badge notifications by 6 seconds each

### 3. `frontend/src/components/LessonSidebar.js`
- Imported `useBadgeStore`
- Added badge notification logic in lesson completion handler
- Shows notifications for `res.badges_awarded` array
- Staggers multiple badge notifications by 6 seconds each

## API Integration Points

The system listens for `badges_awarded` field in API responses:

### Quiz Submit Response
```javascript
{
  "passed": true,
  "score": 10,
  "max_score": 10,
  "xp_awarded": 50,
  "total_xp": 1250,
  "badges_awarded": [
    {
      "id": "badge-123",
      "name": "Người Mới Bắt Đầu",
      "description": "Hoàn thành quiz đầu tiên",
      "icon_url": "https://example.com/badge-icon.png"
    }
  ]
}
```

### Lesson Complete Response
```javascript
{
  "status": "learned",
  "xp_awarded": 25,
  "total_xp": 1200,
  "badges_awarded": [
    {
      "id": "badge-456",
      "name": "Học Giả",
      "description": "Hoàn thành 10 bài học",
      "icon_url": "https://example.com/scholar-badge.png"
    }
  ]
}
```

## Animation Behavior

1. **Entrance**: Slides up from bottom-right with opacity fade-in (500ms)
2. **Display**: Shows for 5 seconds
3. **Exit**: Slides down with opacity fade-out (300ms)
4. **Multiple Badges**: Staggered by 6 seconds (5s display + 1s gap)

## User Experience

- **Position**: Fixed at bottom-right corner (z-index: 50)
- **Appearance**: Gold gradient background (yellow-500 to amber-600)
- **Icon**: Badge icon if provided, fallback to Award icon from lucide-react
- **Text**: Vietnamese header "Huy hiệu mới!" with badge name and description
- **Interaction**: Click X button or wait for auto-dismiss

## Visual Design

```
┌─────────────────────────────────────┐
│  [Icon]  Huy hiệu mới!         [X]  │
│          Badge Name                 │
│          Badge description here     │
└─────────────────────────────────────┘
```

- Gold gradient background (#f59e0b to #d97706)
- White/yellow text for contrast
- Rounded corners (8px)
- Drop shadow for depth
- Responsive width (max-width: 24rem)

## Testing Checklist

- [ ] Badge appears when quiz is passed with badges_awarded
- [ ] Badge appears when lesson is completed with badges_awarded
- [ ] Animation plays smoothly (slide-up entrance)
- [ ] Auto-dismisses after 5 seconds
- [ ] Can manually dismiss by clicking X
- [ ] Multiple badges show in sequence (6s stagger)
- [ ] No z-index conflicts with other UI elements
- [ ] Works on mobile (responsive positioning)
- [ ] Icon displays correctly when icon_url is provided
- [ ] Fallback icon shows when icon_url is missing

## Future Enhancements

1. **Sound Effect**: Add celebratory sound when badge unlocks
2. **Confetti**: Add particle effects for rare/special badges
3. **Badge Detail Link**: Click toast to view badge details page
4. **Queue Management**: Better handling of badge notification queue
5. **Persistence**: Remember which badges user has seen
6. **Animation Variants**: Different animations for different badge tiers

## Notes

- Uses existing CSS animations from `globals.css`
- No additional CSS keyframes needed (uses Tailwind transitions)
- Compatible with existing XP celebration overlay
- Does not interfere with toast notifications
- Zustand store is lightweight and performant
- No persistence needed (badges only show once per award event)

## Integration with Backend

The backend should return `badges_awarded` array in these endpoints:

1. `POST /api/v1/motifs/{motif_id}/quiz/submit`
2. `POST /api/v1/motifs/{motif_id}/complete-lesson`

Each badge object should have:
- `id` (string): Unique badge identifier
- `name` (string): Display name
- `description` (string): Achievement description
- `icon_url` (string, optional): URL to badge icon image

## Code Quality

- ✅ Uses existing patterns (similar to XpCelebrationProvider)
- ✅ Proper React hooks (useEffect, useState)
- ✅ Accessible (aria-label on close button)
- ✅ Type-safe prop usage
- ✅ Clean separation of concerns
- ✅ Follows project naming conventions
- ✅ Uses lucide-react icons (already in project)
- ✅ Zustand store pattern matches existing stores

