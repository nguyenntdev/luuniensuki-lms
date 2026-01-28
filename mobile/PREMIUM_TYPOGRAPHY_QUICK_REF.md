# Premium Typography Quick Reference

## New Typography Styles

### Screen Titles
```dart
AppTypography.screenTitle
// fontSize: 28, bold, letterSpacing: -0.5, height: 1.2
```

### Card Titles
```dart
AppTypography.cardTitle
// fontSize: 18, w600, letterSpacing: 0.2
```

### Premium Heading
```dart
AppTypography.premiumHeading
// letterSpacing: 0.5, w700, height: 1.2
```

### Premium Body
```dart
AppTypography.premiumBody
// letterSpacing: 0.2, height: 1.7 (Vietnamese-optimized)
```

### Stat Numbers
```dart
AppTypography.statNumber
// fontSize: 24, bold, letterSpacing: 0.3
```

## GradientText Widget

### Basic Usage
```dart
GradientText.xp('1,250 XP')
```

### Custom Style
```dart
GradientText.xp(
  '+50 XP',
  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
)
```

### Gold Gradient
```dart
GradientText.gold('Achievement!')
```

### Custom Gradient
```dart
GradientText(
  'Custom',
  gradient: LinearGradient(colors: [...]),
)
```

## Files Updated

✅ `lib/core/theme/app_typography.dart` - New styles
✅ `lib/shared/widgets/text/gradient_text.dart` - New widget
✅ `lib/features/explore/presentation/screens/explore_screen.dart`
✅ `lib/features/learning_path/presentation/screens/learning_path_screen.dart`
✅ `lib/features/practice/presentation/screens/practice_session_screen.dart`
✅ `lib/features/explore/presentation/widgets/urn_card.dart`

## Quick Copy-Paste

### Screen Title
```dart
Text(
  'Screen Name',
  style: AppTypography.screenTitle.copyWith(
    color: Colors.white,
  ),
)
```

### Card Title
```dart
Text(
  'Card Title',
  style: AppTypography.cardTitle.copyWith(
    color: Colors.white,
  ),
)
```

### XP Display
```dart
GradientText.xp(
  '${xpAmount} XP',
  style: TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.bold,
  ),
)
```

## What's Next?

Suggested screens to update:
1. Profile screen
2. Settings screen
3. Achievement screens
4. Quiz results
5. Leaderboard

## Status: ✅ COMPLETE

