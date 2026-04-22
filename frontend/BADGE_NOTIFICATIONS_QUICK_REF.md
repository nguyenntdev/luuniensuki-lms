# Badge Unlock Notifications - Quick Reference

## Usage

### Trigger Badge Notification (from any component)

```javascript
import useBadgeStore from '@/stores/badgeStore';

const showUnlockBadge = useBadgeStore((s) => s.showUnlockBadge);

// Show single badge
showUnlockBadge({
  id: 'badge-123',
  name: 'First Steps',
  description: 'Completed your first lesson',
  icon_url: 'https://example.com/badge.png'
});

// Show multiple badges (staggered)
badges.forEach((badge, index) => {
  setTimeout(() => {
    showUnlockBadge(badge);
  }, index * 6000); // 6 seconds apart
});
```

## API Response Format

```json
{
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

## Integration Points

1. **Quiz Submit**: `frontend/src/app/motif/[motifId]/quiz/page.jsx` (line ~266)
2. **Lesson Complete**: `frontend/src/components/LessonSidebar.js` (line ~445)

## Files

```
frontend/src/
├── stores/
│   └── badgeStore.js                    # Zustand store
├── components/
│   └── badges/
│       ├── BadgeUnlockToast.jsx         # Toast component
│       ├── BadgeUnlockProvider.jsx      # Global provider
│       └── index.js                     # Barrel exports
└── app/
    └── layout.jsx                       # Provider integration
```

## Customization

### Change Display Duration
In `BadgeUnlockToast.jsx`, modify the timeout:
```javascript
setTimeout(() => {
  // ...
}, 5000); // Change this value (milliseconds)
```

### Change Position
In `BadgeUnlockToast.jsx`, modify the className:
```javascript
className="fixed bottom-4 right-4 z-50" // Change position here
```

### Change Stagger Delay
When showing multiple badges:
```javascript
setTimeout(() => {
  showUnlockBadge(badge);
}, index * 6000); // Change 6000 to desired delay
```

## Troubleshooting

**Badges not showing?**
- Check if `badges_awarded` field exists in API response
- Verify `BadgeUnlockProvider` is in layout.jsx
- Check browser console for errors

**Animation not smooth?**
- Ensure Tailwind CSS is properly configured
- Check for CSS conflicts with z-index

**Multiple badges overlapping?**
- Increase stagger delay between badges
- Current implementation shows one at a time

## Testing Commands

```bash
# In browser console
useBadgeStore.getState().showUnlockBadge({
  name: 'Test Badge',
  description: 'This is a test',
  icon_url: null
});
```

