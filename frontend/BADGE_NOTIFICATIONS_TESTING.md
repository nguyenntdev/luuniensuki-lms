# Badge Unlock Notifications - Testing Guide

## Prerequisites

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Login to the application with a test account

## Manual Testing

### Test 1: Quiz Completion Badge

1. Navigate to any lesson page
2. Complete the lesson
3. Navigate to the quiz page
4. Submit the quiz with passing score
5. **Expected**: 
   - XP celebration appears (if configured)
   - Badge unlock toast appears at bottom-right
   - Toast shows badge name and description
   - Toast auto-dismisses after 5 seconds

### Test 2: Lesson Completion Badge

1. Navigate to any lesson page
2. Click "Complete Lesson" button
3. **Expected**:
   - Success toast shows
   - XP celebration appears (if XP awarded)
   - Badge unlock toast appears at bottom-right
   - Toast auto-dismisses after 5 seconds

### Test 3: Manual Dismiss

1. Trigger any badge unlock (quiz or lesson)
2. Click the X button on the badge toast
3. **Expected**:
   - Toast immediately starts exit animation
   - Toast disappears after 300ms

### Test 4: Multiple Badges

1. Complete an action that awards multiple badges
2. **Expected**:
   - First badge appears immediately
   - Second badge appears 6 seconds later
   - Third badge appears 12 seconds later
   - Each badge displays for 5 seconds

### Test 5: Icon Display

**With icon_url:**
1. Complete action that returns badge with `icon_url`
2. **Expected**: Badge icon image displays in circular container

**Without icon_url:**
1. Complete action that returns badge without `icon_url`
2. **Expected**: Award icon (lucide-react) displays as fallback

### Test 6: Responsive Design

**Desktop (>1024px):**
1. Trigger badge unlock
2. **Expected**: Toast appears at bottom-right, max-width 384px

**Tablet (768px-1024px):**
1. Resize browser to tablet width
2. Trigger badge unlock
3. **Expected**: Toast adapts to screen width

**Mobile (<768px):**
1. Resize browser to mobile width
2. Trigger badge unlock
3. **Expected**: Toast fits screen with proper margins

### Test 7: Z-Index Stacking

1. Open a modal or overlay
2. Trigger badge unlock
3. **Expected**: Badge toast appears above other elements

### Test 8: Animation Smoothness

1. Trigger badge unlock
2. Observe entrance animation (slide-up, fade-in)
3. Wait for auto-dismiss
4. Observe exit animation (slide-down, fade-out)
5. **Expected**: Smooth 60fps animations, no jank

## Browser Console Testing

### Quick Test Command

Open browser console and run:

```javascript
// Import the store (if using dev tools)
const { showUnlockBadge } = require('@/stores/badgeStore').default.getState();

// Show a test badge
useBadgeStore.getState().showUnlockBadge({
  id: 'test-badge-1',
  name: 'Test Badge',
  description: 'This is a test badge notification',
  icon_url: null
});
```

### Test with Custom Icon

```javascript
useBadgeStore.getState().showUnlockBadge({
  id: 'test-badge-2',
  name: 'Custom Icon Badge',
  description: 'Badge with custom icon',
  icon_url: 'https://via.placeholder.com/64'
});
```

### Test Multiple Badges

```javascript
const badges = [
  { id: '1', name: 'Badge 1', description: 'First badge' },
  { id: '2', name: 'Badge 2', description: 'Second badge' },
  { id: '3', name: 'Badge 3', description: 'Third badge' }
];

badges.forEach((badge, index) => {
  setTimeout(() => {
    useBadgeStore.getState().showUnlockBadge(badge);
  }, index * 6000);
});
```

## API Testing

### Mock API Response

Create a mock API response with `badges_awarded`:

```javascript
// In quiz submission handler
const mockResponse = {
  passed: true,
  score: 10,
  max_score: 10,
  xp_awarded: 50,
  total_xp: 1250,
  badges_awarded: [
    {
      id: 'first-quiz',
      name: 'Người Mới Bắt Đầu',
      description: 'Hoàn thành quiz đầu tiên',
      icon_url: null
    },
    {
      id: 'perfect-score',
      name: 'Điểm Tuyệt Đối',
      description: 'Đạt điểm tuyệt đối trong quiz',
      icon_url: null
    }
  ]
};
```

### Backend API Endpoints to Verify

1. **Quiz Submit**: `POST /api/v1/motifs/{motif_id}/quiz/submit`
   - Should return `badges_awarded` array when applicable

2. **Lesson Complete**: `POST /api/v1/motifs/{motif_id}/complete-lesson`
   - Should return `badges_awarded` array when applicable

## Visual Regression Testing

### Desktop (1920×1080)
- [ ] Badge toast positioned correctly at bottom-right
- [ ] Gold gradient renders properly
- [ ] Text is readable and properly aligned
- [ ] Icon displays at correct size
- [ ] Close button is visible and accessible

### Tablet (768×1024)
- [ ] Badge toast adapts to screen width
- [ ] All content remains visible
- [ ] No horizontal scrolling

### Mobile (375×667)
- [ ] Badge toast fits within viewport
- [ ] Text truncates appropriately
- [ ] Icon remains visible
- [ ] Close button is tappable

## Performance Testing

### Animation Performance
1. Open Chrome DevTools → Performance tab
2. Start recording
3. Trigger badge unlock
4. Stop recording after auto-dismiss
5. **Expected**: Consistent 60fps, no layout thrashing

### Memory Leaks
1. Open Chrome DevTools → Memory tab
2. Take heap snapshot
3. Trigger multiple badge unlocks (10+)
4. Wait for all to dismiss
5. Take another heap snapshot
6. **Expected**: No significant memory growth

## Accessibility Testing

### Keyboard Navigation
- [ ] Close button is focusable with Tab
- [ ] Enter/Space key dismisses toast

### Screen Reader
1. Enable screen reader (VoiceOver on Mac, NVDA on Windows)
2. Trigger badge unlock
3. **Expected**: Badge name and description are announced
4. Close button announces "Đóng thông báo"

### Color Contrast
1. Use browser extension (e.g., axe DevTools)
2. Verify text contrast ratios
3. **Expected**: All text meets WCAG AA standards

## Edge Cases

### Rapid Badge Unlocks
1. Trigger multiple badges in quick succession
2. **Expected**: Badges queue and show sequentially

### Network Delay
1. Throttle network in DevTools
2. Complete quiz/lesson
3. **Expected**: Badge shows after API response completes

### Badge with Long Text
1. Test with badge description >100 characters
2. **Expected**: Description truncates with ellipsis after 2 lines

### Badge with No Description
1. Test with badge object missing `description` field
2. **Expected**: Component handles gracefully (empty or placeholder)

### Missing Icon URL
1. Test with `icon_url: null` or undefined
2. **Expected**: Award icon displays as fallback

## Integration Testing

### With XP Celebration
1. Complete quiz that awards both XP and badge
2. **Expected**: 
   - XP celebration plays first (centered)
   - Badge toast appears (bottom-right)
   - No visual conflicts

### With Toast Notifications
1. Trigger badge unlock
2. Trigger regular toast (e.g., error message)
3. **Expected**: Both visible simultaneously, no overlap

### With Modals
1. Open a modal
2. Trigger badge unlock
3. **Expected**: Badge toast appears above modal

## Checklist Summary

- [ ] Badge appears on quiz completion
- [ ] Badge appears on lesson completion
- [ ] Auto-dismiss works (5 seconds)
- [ ] Manual dismiss works (X button)
- [ ] Multiple badges stagger correctly
- [ ] Icon displays (with and without icon_url)
- [ ] Responsive on all screen sizes
- [ ] Animations are smooth
- [ ] No z-index conflicts
- [ ] Accessible via keyboard
- [ ] Screen reader compatible
- [ ] No performance issues
- [ ] No memory leaks
- [ ] Works with XP celebrations
- [ ] Works with other toasts

## Reporting Issues

If you find any issues, please report:

1. **Description**: What went wrong?
2. **Steps to Reproduce**: How to trigger the bug?
3. **Expected Behavior**: What should happen?
4. **Actual Behavior**: What actually happened?
5. **Browser**: Chrome/Firefox/Safari version?
6. **Screen Size**: Desktop/Tablet/Mobile?
7. **Screenshots**: Visual evidence if applicable

