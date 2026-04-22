# Next Steps for Testing Web Frontend Sync

## Installation & Setup

Before testing, install dependencies:
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/frontend
npm install
```

## Development Server

Start the development server:
```bash
npm run dev
```

The app will be available at http://localhost:3000

## Testing Checklist

### 1. Badge System Testing
- [ ] Navigate to `/badges`
- [ ] Verify all badges load correctly
- [ ] Check earned badges show ✓ checkmark
- [ ] Check locked badges show 🔒 lock icon  
- [ ] Verify earned date displays for earned badges
- [ ] Check `/achievements` page tabs work
- [ ] Verify badge count in profile widget

### 2. Network Status Testing
- [ ] Open Chrome DevTools (F12)
- [ ] Go to Network tab → Select "Offline"
- [ ] Verify red banner appears: "Không có kết nối mạng"
- [ ] Re-enable network
- [ ] Verify banner auto-hides with smooth transition

### 3. Error Message Testing
- [ ] Trigger a 404 error (invalid page)
- [ ] Verify Vietnamese error message in toast
- [ ] Try submitting quiz while offline
- [ ] Verify error toast shows Vietnamese message

### 4. XP Celebration Testing (Most Important)

#### Small Celebration (25 XP - Discovery)
- [ ] Discover a new motif on URN viewer
- [ ] Verify simple badge animation appears
- [ ] Should show: ⭐ +25 XP
- [ ] Duration: ~1.5 seconds
- [ ] No confetti or particles

#### Medium Celebration (50 XP - Lesson)
- [ ] Complete a lesson via sidebar
- [ ] Verify badge + particle effects appear
- [ ] Should show: ⭐ +50 XP
- [ ] 15 particles radiating outward
- [ ] Duration: ~2 seconds

#### Large Celebration (75 XP - Quiz)
- [ ] Complete and pass a quiz
- [ ] Verify badge + confetti appear
- [ ] Should show: ⭐ +75 XP
- [ ] 30 confetti particles falling
- [ ] Duration: ~2.5 seconds
- [ ] Multiple colors (gold, green, purple, orange)

#### Level-Up Celebration
- [ ] Complete actions to cross 100/200/300 XP threshold
- [ ] Verify special banner appears: "🎉 LEVEL UP! 🎉"
- [ ] Should show new level number: "Cấp 1", "Cấp 2", etc.
- [ ] 50 confetti particles
- [ ] Banner slides in from top
- [ ] Gradient background (success → primary)

### 5. Visual Quality Checks

#### XP Badge Appearance
- [ ] Golden gradient background (from-xp-gold to-xp-gold-dark)
- [ ] Star emoji visible (⭐)
- [ ] XP amount displays clearly
- [ ] Badge bounces and slides up smoothly
- [ ] Shadow effect visible

#### Confetti Animation
- [ ] Confetti particles fall naturally
- [ ] Random colors applied
- [ ] Rotation visible
- [ ] Particles fade out at bottom
- [ ] No performance lag

#### Level-Up Banner
- [ ] Banner slides from above viewport
- [ ] Gradient background visible
- [ ] Text is centered
- [ ] Emoji displays correctly
- [ ] Level number is large and bold

## Regression Testing

Ensure existing features still work:
- [ ] Quiz submission still works
- [ ] Lesson completion still works
- [ ] Toast notifications still appear
- [ ] Navigation works normally
- [ ] Profile page loads correctly
- [ ] Badge gallery works
- [ ] 3D URN viewer works

## Browser Compatibility

Test in multiple browsers:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (macOS)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

## Performance Checks

- [ ] No memory leaks (check DevTools Memory tab)
- [ ] Smooth 60fps animations (check DevTools Performance)
- [ ] No console errors
- [ ] Quick celebration cleanup
- [ ] Multiple celebrations don't overlap

## Known Limitations

1. **Dependencies Required**: Need to run `npm install` before testing
2. **Backend Required**: Backend API must be running for XP data
3. **User Authentication**: Must be logged in to earn XP
4. **Browser Support**: Requires modern browser with CSS animations

## Quick Verification Commands

```bash
# Check if Next.js is installed
npm list next

# Run linter (after npm install)
npm run lint

# Build production bundle (checks for errors)
npm run build

# View file sizes
du -sh src/components/XpCelebrationOverlay.jsx
du -sh src/lib/xpCelebrationContext.jsx
```

## Troubleshooting

### Issue: Celebration doesn't appear
- Check browser console for errors
- Verify `XpCelebrationProvider` is in layout
- Check that `xp_awarded > 0` in API response
- Verify user object has `total_xp` field

### Issue: Animation looks glitchy
- Check CSS animations loaded (view globals.css)
- Verify Tailwind classes compiled
- Check for conflicting z-index values
- Disable browser extensions

### Issue: Colors not showing
- Verify CSS variables in globals.css
- Check Tailwind config has xp-gold colors
- Run `npm run build` to rebuild
- Clear browser cache

### Issue: Level-up not showing
- Check oldTotalXp calculation
- Verify level threshold (100 XP = Level 1)
- Console.log the newLevel variable
- Check if banner CSS classes applied

## What's Next?

After successful testing, you can:

1. **Add Sound Effects**: Integrate celebration sounds
2. **Add Badge Animations**: Show newly earned badges
3. **Customize Durations**: Let users adjust animation speed
4. **Add More Celebrations**: Quest completions, streaks, etc.
5. **Analytics**: Track celebration engagement

## File Locations

For reference, the main files changed:

```
frontend/
├── src/
│   ├── components/
│   │   ├── XpCelebrationOverlay.jsx (NEW)
│   │   └── LessonSidebar.js (MODIFIED)
│   ├── lib/
│   │   └── xpCelebrationContext.jsx (NEW)
│   ├── app/
│   │   ├── layout.jsx (MODIFIED)
│   │   ├── globals.css (MODIFIED)
│   │   └── motif/[motifId]/quiz/page.jsx (MODIFIED)
├── tailwind.config.js (MODIFIED)
└── WEB_MOBILE_SYNC_SUMMARY.md (NEW)
```

---

**Ready to test?** Start with `npm install` then `npm run dev` and follow the checklist above! 🚀

