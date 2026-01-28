# Explore Header V2 - Testing Checklist

## Visual Testing

### Greeting Row
- [ ] Morning greeting shows "Chào buổi sáng" (before 12:00)
- [ ] Afternoon greeting shows "Chào buổi chiều" (12:00-17:59)
- [ ] Evening greeting shows "Chào buổi tối" (18:00+)
- [ ] User display name shows correctly
- [ ] Email fallback works when display name is empty
- [ ] Long names are truncated with ellipsis
- [ ] Greeting text is readable (white, 14px)
- [ ] User name is prominent (white, 28px, bold)

### Premium Avatar
- [ ] Avatar displays user image when avatarUrl is available
- [ ] Avatar shows initial letter when no avatarUrl
- [ ] Initial letter is capitalized correctly
- [ ] Gradient ring rotates continuously
- [ ] Rotation is smooth (no jank)
- [ ] Golden gradient colors are vibrant
- [ ] Level badge displays correct level number
- [ ] Level badge has golden gradient background
- [ ] Level badge has white border
- [ ] Level badge has glow shadow effect
- [ ] Level badge bounces with elastic animation
- [ ] Avatar ring is 70x70px
- [ ] Inner avatar is 64x64px
- [ ] Level badge positioned correctly (bottom-right)

### Stats Dashboard
- [ ] Glass container has gradient background
- [ ] Border is visible (white, 20% opacity)
- [ ] Shadow creates depth effect
- [ ] Stats card slides in with scale animation
- [ ] Stats card fades in smoothly
- [ ] All 3 stat pods are visible
- [ ] Stat pods have staggered entrance (0ms, 100ms, 200ms)
- [ ] Icons match status types (eye, book, star)
- [ ] Icons have background circles
- [ ] Discovered shows "X/Total" format
- [ ] Learned shows count correctly
- [ ] Mastered shows count correctly
- [ ] Labels are in Vietnamese
- [ ] Dividers between stats are subtle
- [ ] Stats are centered (spaceAround)

### Action Buttons
- [ ] Primary button has golden gradient
- [ ] Primary button has glow shadow
- [ ] Primary button text: "Tiếp tục học"
- [ ] Primary button has play icon
- [ ] Secondary button has white outline
- [ ] Secondary button background is transparent
- [ ] Secondary button text: "Luyện tập"
- [ ] Secondary button has fitness icon
- [ ] Both buttons have equal width
- [ ] Buttons slide up from below
- [ ] Buttons fade in smoothly
- [ ] Primary button animates at 500ms
- [ ] Secondary button animates at 600ms
- [ ] Buttons are pill-shaped (rounded)
- [ ] Touch feedback works (InkWell)

## Functional Testing

### Data Binding
- [ ] Progress data updates correctly
- [ ] User data displays accurately
- [ ] Level number reflects user.rank.level
- [ ] Stats reflect actual progress values
- [ ] Zero values display correctly (0/45, 0, 0)
- [ ] Large numbers format properly

### Navigation
- [ ] Continue button calls onContinue callback
- [ ] Continue button navigates to correct urn
- [ ] Continue button disabled when no urn available
- [ ] Practice button calls onPractice callback
- [ ] Practice button navigates to /practice route
- [ ] Navigation preserves app state

### Authentication States
- [ ] ExploreHeaderV2 shows for authenticated users
- [ ] Legacy header shows for unauthenticated users
- [ ] Switching between auth states works smoothly
- [ ] User data loads correctly after login
- [ ] Header updates after user profile changes

## Animation Testing

### Performance
- [ ] Animations are smooth (60fps)
- [ ] No frame drops during rotation
- [ ] Multiple simultaneous animations work well
- [ ] Animation controller disposes properly
- [ ] No memory leaks from animations
- [ ] Animations respect device performance

### Timing
- [ ] Avatar rotation completes in 1.5 seconds
- [ ] Stats card appears in 600ms
- [ ] Stat pods appear with 100ms stagger
- [ ] Primary button appears in 500ms
- [ ] Secondary button appears in 600ms
- [ ] All animations feel natural

### Curves
- [ ] Avatar rotation is linear (constant speed)
- [ ] Level badge bounces with elastic effect
- [ ] Stats card scales with easeOutCubic
- [ ] Stat pods scale with easeOutBack
- [ ] Buttons translate with easeOutCubic

## Edge Cases

### User Data
- [ ] Works with no display name (uses email)
- [ ] Works with no avatar URL (shows initial)
- [ ] Handles very short names (1 char)
- [ ] Handles very long names (30+ chars)
- [ ] Handles special characters in name
- [ ] Handles emoji in name
- [ ] Level 0 displays correctly
- [ ] Level 999+ displays correctly

### Progress Data
- [ ] All zeros: 0/0, 0, 0
- [ ] All maxed: 45/45, 45, 45
- [ ] Partial progress displays correctly
- [ ] Large numbers (100+) format properly
- [ ] Negative values handled (shouldn't happen)

### Screen Sizes
- [ ] Works on small phones (320px width)
- [ ] Works on regular phones (375px width)
- [ ] Works on large phones (428px width)
- [ ] Works on tablets (768px+ width)
- [ ] Buttons don't overflow
- [ ] Stats card doesn't overflow
- [ ] Avatar doesn't clip
- [ ] Text doesn't overflow

### Theme & Colors
- [ ] Colors match AppColors theme
- [ ] Gradients render correctly
- [ ] Shadows render correctly
- [ ] Text is readable on all backgrounds
- [ ] Icons are visible
- [ ] Borders are visible

## Integration Testing

### With ExploreScreen
- [ ] Header renders in correct position
- [ ] Doesn't overlap with grid
- [ ] Scroll behavior works correctly
- [ ] Pull-to-refresh doesn't affect header
- [ ] Header animates on screen load
- [ ] "Tiếp tục: {urn name}" subtitle shows
- [ ] RecommendationsCard displays below header

### With Providers
- [ ] exploreProgressProvider data flows correctly
- [ ] authNotifierProvider data flows correctly
- [ ] User changes reflect immediately
- [ ] Progress updates reflect immediately
- [ ] Provider rebuilds don't cause issues

## Accessibility

- [ ] Text has sufficient contrast
- [ ] Touch targets are large enough (48x48 minimum)
- [ ] Buttons have clear labels
- [ ] Icons have semantic meaning
- [ ] Animations can be reduced if needed
- [ ] Screen readers work (if supported)

## Testing Commands

### Manual Test Scenarios

1. **Morning Test**: Set device time to 10:00 AM, verify greeting
2. **Evening Test**: Set device time to 8:00 PM, verify greeting
3. **No Avatar Test**: Use account without avatar URL
4. **Max Progress Test**: Use account with 45/45 progress
5. **Zero Progress Test**: Use new account with 0/45 progress
6. **Long Name Test**: Change display name to 30+ characters
7. **Navigation Test**: Tap both buttons, verify routes

### Automated Tests (Future)

```dart
// Example widget test
testWidgets('ExploreHeaderV2 displays greeting', (tester) async {
  await tester.pumpWidget(
    MaterialApp(
      home: ExploreHeaderV2(
        progress: mockProgress,
        user: mockUser,
      ),
    ),
  );
  
  expect(find.textContaining('Chào buổi'), findsOneWidget);
  expect(find.text(mockUser.displayName), findsOneWidget);
});
```

## Performance Benchmarks

- [ ] Initial render < 100ms
- [ ] Animation frame rate > 55fps
- [ ] Memory usage stable
- [ ] No UI jank during animations
- [ ] Smooth on low-end devices

