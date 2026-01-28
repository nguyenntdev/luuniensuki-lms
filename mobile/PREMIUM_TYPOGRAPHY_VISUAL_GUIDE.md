# Premium Typography Visual Guide

## Before vs After Comparison

### Screen Titles

**Before:**
```dart
Text(
  'Khám phá',
  style: TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
    letterSpacing: 0.3,
  ),
)
```

**After:**
```dart
Text(
  'Khám phá',
  style: AppTypography.screenTitle.copyWith(
    fontSize: 28,  // Larger, more prominent
  ),
)
// letterSpacing: -0.5 (tighter, more modern)
// height: 1.2 (optimal line height)
```

### Card Titles

**Before:**
```dart
Text(
  widget.urn.name,
  style: TextStyle(
    fontSize: 17,
    fontWeight: FontWeight.bold,
    letterSpacing: 0.2,
  ),
)
```

**After:**
```dart
Text(
  widget.urn.name,
  style: AppTypography.cardTitle.copyWith(
    fontSize: nameSize,  // Responsive
  ),
)
// fontSize: 18 (default)
// fontWeight: w600 (semibold, more refined)
// letterSpacing: 0.2 (optimized spacing)
```

### XP Display

**Before:**
```dart
Text(
  '${session.totalScore} XP',
  style: TextStyle(
    color: AppColors.xpGold,
    fontSize: 16,
    fontWeight: FontWeight.bold,
  ),
)
```

**After:**
```dart
GradientText.xp(
  '${session.totalScore} XP',
  style: TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.bold,
  ),
)
// ✨ Beautiful gold gradient effect!
```

## Typography Hierarchy

```
┌─────────────────────────────────────┐
│ Screen Title (28px, -0.5 spacing)  │  ← AppTypography.screenTitle
│ Bold, Commanding presence           │
├─────────────────────────────────────┤
│                                     │
│  Card Title (18px, 0.2 spacing)    │  ← AppTypography.cardTitle
│  Semibold, Clear hierarchy          │
│                                     │
│  Body Text (16px, 1.7 height)      │  ← AppTypography.premiumBody
│  Regular, Optimized for Vietnamese  │
│                                     │
│  Stat Number (24px, 0.3 spacing)   │  ← AppTypography.statNumber
│  Bold, Emphasis on numbers          │
└─────────────────────────────────────┘
```

## Gradient Text Showcase

### Gold Gradient Composition
```
primaryLight (#F5D078)
      ↓
   primary (#E8B44C)     ← Smooth gradient
      ↓
 primaryDark (#D49B38)
```

### Visual Effect
```
Regular Text:  1,250 XP  (flat gold color)

Gradient Text: 1,250 XP  (shimmering gold gradient)
               ✨✨✨
```

## Vietnamese Text Optimization

### Line Height Comparison

**Before (height: 1.5):**
```
Chín Cửu Đỉnh Ký    ← Diacritics feel cramped
Học Tập Theo Đỉnh
```

**After (height: 1.7):**
```
Chín Cửu Đỉnh Ký    ← Better breathing room
                        for diacritics
Học Tập Theo Đỉnh
```

## Responsive Typography

### Screen Title Responsiveness
```
Compact (< 360px):  22px
Normal (≥ 360px):   28px

Auto-adjusts based on screen width
```

### Card Title Responsiveness
```
Compact (< 160px):  15px
Normal (≥ 160px):   17px

Adapts to card width
```

## Usage Examples

### 1. Screen Headers
```dart
Text(
  'Học Tập',
  style: AppTypography.screenTitle.copyWith(
    color: Colors.white,
  ),
)
```

### 2. Section Titles
```dart
Text(
  'Chặng leo hôm nay',
  style: AppTypography.cardTitle.copyWith(
    color: Colors.white.withOpacity(0.9),
  ),
)
```

### 3. XP/Rewards Display
```dart
GradientText.xp(
  '+50 XP',
  style: TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w600,
  ),
)
```

### 4. Statistics
```dart
Text(
  '1,250',
  style: AppTypography.statNumber,
)
```

## Best Practices

✅ **Use screenTitle for**: Main screen headers
✅ **Use cardTitle for**: Card headers, section titles
✅ **Use premiumBody for**: Long Vietnamese text
✅ **Use GradientText.xp for**: XP displays, rewards
✅ **Use statNumber for**: Large numbers, statistics

❌ **Don't**: Create custom TextStyles for common elements
❌ **Don't**: Use hardcoded font sizes
❌ **Don't**: Forget responsive sizing

## Impact Summary

📊 **Consistency**: All titles now use standardized styles
📱 **Responsiveness**: Auto-adjusts to screen sizes
🇻🇳 **Vietnamese-Optimized**: Better diacritics handling
✨ **Premium Feel**: Gradient effects on rewards
🎯 **Hierarchy**: Clear visual distinction

