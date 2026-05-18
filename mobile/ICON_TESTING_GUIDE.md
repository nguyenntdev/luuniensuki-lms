# 🧪 Icon Migration - Testing Guide

## Pre-Testing Setup

1. **Clean and Rebuild**
```bash
cd /Users/nguyennt/Documents/luuniensuki-lms/mobile
flutter clean
flutter pub get
flutter run
```

## 📱 Manual Testing Checklist

### 1. Explore Screen Header

#### Stats Bar Test
Navigate to Explore screen and verify:

**Discovered Icon**
- [ ] Blue eye icon (`👁`) displays correctly
- [ ] Icon is 16px size
- [ ] Color matches `AppColors.info` (#60A5FA)
- [ ] Shows count format: `5/10`
- [ ] 6px spacing between icon and text

**Learned Icon**
- [ ] Green book icon (`📖`) displays correctly
- [ ] Icon is 16px size
- [ ] Color matches `AppColors.success` (#34D399)
- [ ] Shows count format: `3`
- [ ] 6px spacing between icon and text

**Mastered Icon**
- [ ] Gold star icon (`⭐`) displays correctly
- [ ] Icon is 16px size
- [ ] Color matches `AppColors.primary` (#E8B44C)
- [ ] Shows count format: `1`
- [ ] 6px spacing between icon and text

**Visual Inspection**
- [ ] All three icons align horizontally
- [ ] Dividers appear between stats
- [ ] Stats container has proper glass effect
- [ ] Vietnamese labels remain intact

### 2. Streak Widget

#### Active Streak (> 0 days)
Test when user has active streak:

**Fire Icon**
- [ ] Orange fire icon displays
- [ ] Icon is 18px size
- [ ] Color is `AppColors.streakOrange` (#FF6B35)
- [ ] Glow effect visible around icon
- [ ] Icon centered in 32px circle container
- [ ] Container has orange tint background

**Streak Display**
- [ ] Shows format: `15 ngày`
- [ ] Text is orange/white
- [ ] "ngày" text is visible

**Next Milestone**
- [ ] Shows format: `Còn 2 ngày đến [icon]`
- [ ] Milestone icon displays (12px)
- [ ] Correct icon for next milestone:
  - 7 days → Star ⭐
  - 30 days → Target 🎯
  - 100 days → Trophy 🏆
  - 365 days → Crown/Trophy 🏆

#### No Streak (0 days)
Test when user has no streak:

**Freeze Icon**
- [ ] Light blue snowflake icon displays
- [ ] Icon is 18px size
- [ ] Color is light blue
- [ ] No glow effect
- [ ] Shows `0 ngày`

#### At Risk Streak
Test when streak is about to be lost:

**Warning Icon**
- [ ] Red warning icon displays
- [ ] Icon is 18px size
- [ ] Color is red
- [ ] Glow effect visible
- [ ] Shows `Sắp mất chuỗi!` text
- [ ] Text and container are red-tinted

#### Freeze Count
Test when user has streak freezes:

**Freeze Badge**
- [ ] Snowflake icon displays (14px)
- [ ] Light blue color
- [ ] Shows count next to icon
- [ ] Badge has blue background
- [ ] 4px spacing between icon and count

### 3. Milestone Celebrations

#### 7-Day Milestone
Trigger 7-day milestone:

**Celebration Screen**
- [ ] Large star icon (56px) displays
- [ ] Icon is gold colored
- [ ] Radial gradient background
- [ ] Shows "Tuần Hoàn Hảo"
- [ ] Shows "Hoàn thành 7 ngày liên tiếp!"
- [ ] Confetti animation plays
- [ ] No emoji artifacts

#### 30-Day Milestone
Trigger 30-day milestone:

**Celebration Screen**
- [ ] Large target icon (56px) displays
- [ ] Icon is purple colored
- [ ] Radial gradient background
- [ ] Shows "Người Học Chăm Chỉ"
- [ ] Shows "Hoàn thành 30 ngày liên tiếp!"

#### 100-Day Milestone
Trigger 100-day milestone:

**Celebration Screen**
- [ ] Large trophy icon (56px) displays
- [ ] Icon is amber colored
- [ ] Radial gradient background
- [ ] Shows "Bậc Thầy Kiên Trì"
- [ ] Shows "Hoàn thành 100 ngày liên tiếp!"

#### 365-Day Milestone
Trigger 365-day milestone:

**Celebration Screen**
- [ ] Large trophy/crown icon (56px) displays
- [ ] Icon is bright gold colored (`AppColors.xpGold`)
- [ ] Radial gradient background
- [ ] Shows "Chiến Binh Bất Bại"
- [ ] Shows "Hoàn thành 365 ngày liên tiếp!"

### 4. Responsive Testing

#### Different Screen Sizes
- [ ] Icons scale properly on small phones (iPhone SE)
- [ ] Icons scale properly on large phones (iPhone Pro Max)
- [ ] Icons scale properly on tablets
- [ ] Grid layout adjusts correctly
- [ ] Icons maintain aspect ratio

#### Orientation
- [ ] Portrait mode displays correctly
- [ ] Landscape mode displays correctly
- [ ] Icons don't distort on rotation

### 5. Accessibility Testing

#### Screen Reader
- [ ] Icons have proper semantic meaning
- [ ] Text labels are announced
- [ ] Navigation is accessible

#### Dark Mode
- [ ] Icons visible in dark mode
- [ ] Colors have sufficient contrast
- [ ] Glow effects work correctly

### 6. Performance Testing

#### Rendering
- [ ] Icons render smoothly
- [ ] No lag when scrolling
- [ ] Animations are smooth (60fps)
- [ ] No memory leaks

#### Loading
- [ ] Icons load immediately (no delay)
- [ ] No flashing or artifacts
- [ ] Proper fallbacks if icon fails

## 🔍 Edge Cases

Test these scenarios:

1. **Very High Counts**
   - [ ] Test with 999/999 discovered
   - [ ] Verify text doesn't overflow
   
2. **Zero Values**
   - [ ] Test with 0/0 learned
   - [ ] Icons still display

3. **Network Issues**
   - [ ] Icons work offline
   - [ ] No network dependencies

4. **State Changes**
   - [ ] Icons update when data changes
   - [ ] Transitions are smooth

## 🐛 Bug Reporting Template

If you find issues, report using:

```
**Issue**: [Description]
**Icon**: [Which icon]
**Expected**: [What should happen]
**Actual**: [What actually happens]
**Steps**: 
1. [Step 1]
2. [Step 2]
**Screenshot**: [Attach if possible]
```

## ✅ Sign-Off

Once all tests pass:

- [ ] All icons display correctly
- [ ] No emojis remaining
- [ ] Colors match design system
- [ ] Vietnamese text intact
- [ ] Animations smooth
- [ ] No performance issues
- [ ] Accessible
- [ ] Works on all screen sizes

**Tester**: _______________
**Date**: _______________
**Build**: _______________

