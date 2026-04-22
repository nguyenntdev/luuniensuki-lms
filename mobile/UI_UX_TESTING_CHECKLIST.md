# UI/UX Testing Checklist

## 🧪 Pre-Flight Checks

### Build & Compile
- [ ] App compiles without errors
- [ ] No analyzer warnings
- [ ] All imports resolve correctly
- [ ] No missing dependencies

### Visual Inspection
- [ ] All screens render correctly
- [ ] No layout overflow errors
- [ ] Images load properly
- [ ] Fonts display correctly

---

## 📱 Login Screen Testing

### Layout & Spacing
- [ ] Logo displays at 100x100 pixels
- [ ] Logo has visible glow effect
- [ ] Title is 32px and bold
- [ ] Subtitle has proper opacity
- [ ] Form fields have consistent spacing (24px vertical)
- [ ] Button is 56px tall
- [ ] Screen padding is 24px horizontal
- [ ] Background gradient displays correctly

### Animations
- [ ] Screen fades in on load (800ms)
- [ ] Content slides up smoothly (600ms)
- [ ] Error messages animate in/out (300ms)
- [ ] Error messages slide from top
- [ ] All animations are smooth (60fps)

### Interactions
- [ ] Email field focuses correctly
- [ ] Password field toggles visibility
- [ ] Tab key moves between fields correctly
- [ ] Enter key submits form from password field
- [ ] Login button shows loading state
- [ ] Loading state shows spinner + text
- [ ] Disabled button has reduced opacity
- [ ] Forgot password shows snackbar
- [ ] Register link navigates correctly
- [ ] Error messages display properly

### Visual States
- [ ] Input fields highlight on focus (gold border)
- [ ] Button changes appearance when disabled
- [ ] Loading spinner is visible on dark background
- [ ] Error container has proper styling
- [ ] Error icon and text align correctly

---

## 🏛️ Explore Screen Testing

### Layout & Spacing
- [ ] Welcome message displays when logged in
- [ ] Title is 32px and bold
- [ ] Progress circle is 64x64 pixels
- [ ] Progress circle has gradient border
- [ ] Search bar displays correctly
- [ ] Stats card has gradient background
- [ ] Icon containers have colored backgrounds
- [ ] Grid spacing is consistent (16px)
- [ ] Header padding is 24px

### Grid Responsiveness
- [ ] Phone screens show 2 columns
- [ ] Tablet screens (>600px) show 3 columns
- [ ] Desktop screens (>900px) show 4 columns
- [ ] Cards maintain 0.75 aspect ratio
- [ ] Grid scrolls smoothly
- [ ] Bottom padding prevents nav bar overlap

### Animations
- [ ] Screen fades in on load
- [ ] Cards animate in with stagger effect
- [ ] First card appears at 400ms
- [ ] Each subsequent card delays by 100ms
- [ ] Cards scale from 0 to 1
- [ ] Cards fade in simultaneously
- [ ] All animations are smooth

### Stats Display
- [ ] Overall progress percentage is accurate
- [ ] Circular progress indicator animates
- [ ] Discovered stat shows correct color (blue)
- [ ] Learned stat shows correct color (green)
- [ ] Mastered stat shows correct color (gold)
- [ ] Stats update when data changes
- [ ] Dividers have gradient effect

### Interactions
- [ ] Pull-to-refresh works correctly
- [ ] Refresh indicator shows gold color
- [ ] Cards navigate on tap
- [ ] Search bar shows "coming soon" message
- [ ] Filter icon displays correctly

---

## 🏺 UrnCard Testing

### Layout & Spacing
- [ ] Card has gradient background
- [ ] Border is 1.5px and visible
- [ ] Border radius is 16px
- [ ] Image takes 60% of card height
- [ ] Info section takes 40% of card height
- [ ] Internal padding is 16px
- [ ] Progress badge positioned correctly (top-right)
- [ ] Demo badge positioned correctly (top-left)

### Visual Effects
- [ ] Card has multi-layer shadow
- [ ] Completed cards have gold glow
- [ ] Image has gradient overlay
- [ ] Progress bar has shine effect
- [ ] Progress badge has gradient (when completed)
- [ ] Progress badge has shadow
- [ ] Demo badge has gradient
- [ ] Demo badge has shadow

### Animations
- [ ] Card scales to 0.95 on press
- [ ] Scale animation is smooth (150ms)
- [ ] Card returns to normal on release
- [ ] Animation cancels on tap cancel
- [ ] No animation glitches or jumps

### Content Display
- [ ] Urn name displays correctly
- [ ] English name displays (if available)
- [ ] Progress percentage is accurate
- [ ] Check icon shows for completed urns
- [ ] Progress bar fills correctly
- [ ] Discovery stat (blue) displays correctly
- [ ] Learning stat (green) displays correctly
- [ ] Mastery stat (gold) displays correctly
- [ ] All stats have colored backgrounds
- [ ] Placeholder shows when no image

### States
- [ ] Demo badge shows only for demo urns
- [ ] Completed badge shows green gradient
- [ ] In-progress badge shows dark background
- [ ] Progress bar color is gold gradient
- [ ] Stats update based on progress

---

## 📐 Spacing System Testing

### AppSpacing Constants
- [ ] AppSpacing.xs = 4.0
- [ ] AppSpacing.sm = 8.0
- [ ] AppSpacing.md = 16.0
- [ ] AppSpacing.lg = 24.0
- [ ] AppSpacing.xl = 32.0
- [ ] AppSpacing.xxl = 48.0

### Spacing Widgets
- [ ] verticalSpaceMD creates 16px space
- [ ] horizontalSpaceLG creates 24px space
- [ ] Spacing is consistent across screens

### Border Radius
- [ ] radiusSM = 8.0 (badges)
- [ ] radiusMD = 12.0 (buttons, inputs)
- [ ] radiusLG = 16.0 (cards)
- [ ] radiusXL = 24.0 (logo)

---

## 🎨 Design Consistency

### Colors
- [ ] Gold accent is #D4A84B throughout
- [ ] Dark background is #1A1A2E
- [ ] Success green is #4CAF50
- [ ] Info blue is #64B5F6
- [ ] Learning green is #81C784
- [ ] All opacity values are consistent

### Typography
- [ ] Screen titles are 32px bold
- [ ] Card titles are 17px bold
- [ ] Body text is 15px medium
- [ ] Small text is 11-12px
- [ ] Letter spacing is consistent
- [ ] Font weights match design

### Shadows
- [ ] All cards have consistent shadows
- [ ] Shadow blur and offset are appropriate
- [ ] Glow effects are visible but subtle
- [ ] No excessive shadow stacking

---

## ♿ Accessibility Testing

### Touch Targets
- [ ] All buttons are at least 48x48 logical pixels
- [ ] Card tap areas are adequate
- [ ] Input fields are easy to tap
- [ ] Links have sufficient tap area

### Visual Accessibility
- [ ] Text has sufficient contrast (4.5:1+)
- [ ] Large text has sufficient contrast (3:1+)
- [ ] Gold on dark has good contrast
- [ ] White on dark has good contrast
- [ ] Error messages are clearly visible

### Feedback
- [ ] Loading states provide feedback
- [ ] Error messages are descriptive
- [ ] Success states are clear
- [ ] All actions have visual feedback

---

## 🚀 Performance Testing

### Animation Performance
- [ ] Animations run at 60fps on device
- [ ] No frame drops during transitions
- [ ] Staggered animations don't lag
- [ ] Press animations respond immediately

### Memory Management
- [ ] No memory leaks from controllers
- [ ] Animation controllers are disposed
- [ ] Images are cached properly
- [ ] No excessive rebuilds

### Loading
- [ ] Initial load is fast
- [ ] Images load progressively
- [ ] No blocking operations on UI thread
- [ ] Smooth scrolling in grid view

---

## 🐛 Edge Cases

### Data States
- [ ] Empty state displays correctly
- [ ] Loading state displays correctly
- [ ] Error state displays correctly
- [ ] No data crashes the app

### Content Overflow
- [ ] Long urn names truncate properly
- [ ] Long English names truncate properly
- [ ] Text doesn't overflow containers
- [ ] Stats display correctly at all values

### Navigation
- [ ] Back button works correctly
- [ ] Deep links work (if applicable)
- [ ] Navigation state persists correctly
- [ ] No navigation loops or crashes

---

## ✅ Final Checks

- [ ] All screens tested on multiple devices
- [ ] Tested in portrait and landscape
- [ ] No console warnings or errors
- [ ] Code is clean and commented
- [ ] Documentation is up to date
- [ ] Git commit messages are clear

---

## 📝 Notes

**Testing Date:** _______________
**Tested By:** _______________
**Device(s):** _______________
**Issues Found:** _______________

