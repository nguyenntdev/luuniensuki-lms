# Gems Shop Testing Guide

## 🧪 Quick Test Scenarios

### 1. **Animation Testing**
**What to test:** Entrance animations when screen loads

**Steps:**
1. Navigate to Gems Shop screen
2. Observe the staggered entrance animations
3. Items should fade and slide in from bottom (Y+30%)
4. Delay between items: 150ms
5. Total animation: 800ms

**Expected:**
- Item 0 (Streak Freeze): 0-400ms
- Item 1 (Double XP): 150-550ms
- Item 2 (Hint): 300-700ms
- How to Earn section: 450-850ms

**Pass criteria:** Smooth, no jank, pleasant stagger effect

---

### 2. **Icon Display Testing**
**What to test:** Material Icons instead of emojis

**Check these icons:**
- ❄️ `Icons.ac_unit` for Streak Freeze (ice/freeze icon)
- ⚡ `Icons.bolt` for Double XP (lightning bolt)
- 💡 `Icons.lightbulb_outline` for Hint (light bulb outline)
- 💎 `Icons.diamond` for gems (everywhere)
- 🎓 `Icons.school` for "How to Earn" header

**Pass criteria:** All icons are Material Icons, no emojis visible

---

### 3. **Affordability States**
**What to test:** Visual feedback for affordable vs not affordable items

#### Test Case 3A: User has 100 gems
**Expected for each item:**
- Streak Freeze (50 gems): ✅ Affordable
  - Bright colors, glow effect
  - No error message
  - Scale: 1.0
  - Button clickable
  
- Double XP (100 gems): ✅ Affordable
  - Same as above
  
- Hint (25 gems): ✅ Affordable
  - Same as above

#### Test Case 3B: User has 30 gems
**Expected for each item:**
- Streak Freeze (50 gems): ❌ Not Affordable
  - Dimmed colors (opacity 0.3 → 0.2)
  - Shows "Cần thêm 20 gems" in red
  - Scale: 0.98 (slightly smaller)
  - Button not clickable
  - No glow effect
  
- Double XP (100 gems): ❌ Not Affordable
  - Shows "Cần thêm 70 gems"
  
- Hint (25 gems): ✅ Affordable
  - Bright and clickable

**Pass criteria:** Clear visual distinction between states

---

### 4. **Purchase Flow Testing**
**What to test:** Buying an item updates balance and shows feedback

**Steps:**
1. Note current gem balance
2. Click on affordable item (e.g., Hint - 25 gems)
3. Observe feedback

**Expected:**
- SnackBar appears: "Đã mua Gợi Ý!" (green)
- Gem balance updates immediately
- CompactGemsDisplay in AppBar reflects new balance
- If balance now too low for item, it becomes dimmed

**Negative test:**
1. Try clicking disabled/dimmed item
2. Nothing should happen (onTap is null)

**Pass criteria:** Purchase works, balance updates, feedback shown

---

### 5. **How to Earn Section**
**What to test:** Icon-based earn method cards

**Check:**
- Header has gradient icon container with `Icons.school`
- Each method has:
  - Colored icon container (36x36)
  - Proper icon:
    - ✓ `Icons.check_circle_outline` - Complete lesson
    - 🏁 `Icons.flag_outlined` - Daily goal
    - 🔥 `Icons.local_fire_department_outlined` - 7-day streak
    - ⭐ `Icons.stars_outlined` - Perfect lesson
  - Reward badge with gradient background
  - `Icons.diamond` in badge

**Pass criteria:** All icons present, badges styled correctly

---

### 6. **Transaction History Modal**
**What to test:** Diamond icon instead of emoji in transactions

**Steps:**
1. Tap on CompactGemsDisplay in AppBar
2. Modal appears from bottom
3. Check transaction items

**Expected:**
- Each transaction shows `Icons.diamond` icon (size 14)
- Color matches transaction type (green/red)
- No emoji "💎" anywhere

**Pass criteria:** Icons used instead of emojis

---

### 7. **Background Animation**
**What to test:** AnimatedGradientBackground smooth transitions

**Observation:**
- Background should have subtle color transitions
- Duration: 10 seconds (default)
- Colors should lerp smoothly

**Pass criteria:** No visual glitches, smooth gradient animation

---

### 8. **Visual Consistency**
**What to test:** Matches AchievementsScreen and ProfileScreen

**Compare:**
- Background style (AnimatedGradientBackground)
- Animation patterns (staggered fade + slide)
- GlassContainer usage
- Icon usage (Material Icons)
- Color scheme

**Pass criteria:** Feels like part of the same app

---

## 📱 Device-Specific Tests

### iOS
- [ ] Animations 60fps
- [ ] Icons render correctly
- [ ] Glass effect works
- [ ] Safe areas respected

### Android
- [ ] Animations 60fps
- [ ] Material ripple on buttons
- [ ] Icons render correctly
- [ ] Status bar handling

---

## 🐛 Known Edge Cases

### Edge Case 1: User has exactly enough gems
- Example: 50 gems, item costs 50
- Should be affordable, clickable
- After purchase, balance = 0

### Edge Case 2: Empty transaction history
- Shows "Chưa có giao dịch"
- Centered text, dimmed

### Edge Case 3: Very large gem amounts
- Test with 9999+ gems
- Numbers should display correctly
- All items affordable

---

## ✅ Acceptance Criteria

All tests pass if:
- ✅ Animations smooth (no jank)
- ✅ All Material Icons display correctly
- ✅ Affordability states clear and accurate
- ✅ Purchase flow works end-to-end
- ✅ "How to Earn" section uses icons
- ✅ Transaction history uses icons
- ✅ Background animates smoothly
- ✅ Consistent with other screens
- ✅ No console errors
- ✅ Works on both iOS and Android

