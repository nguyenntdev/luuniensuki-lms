# AppColors Usage Guide

## Quick Reference for Developers

This guide helps you use AppColors constants correctly in the mobile app.

---

## ✅ DO - Correct Usage

### Primary Actions & Highlights
```dart
// Buttons
ElevatedButton(
  style: ElevatedButton.styleFrom(
    backgroundColor: AppColors.primary,
    foregroundColor: AppColors.onPrimary,
  ),
  child: Text('Submit'),
)

// Progress Indicators
CircularProgressIndicator(
  color: AppColors.primary,
)

// Gold Gradients
Container(
  decoration: BoxDecoration(
    gradient: LinearGradient(
      colors: [AppColors.primaryDark, AppColors.primaryLight],
    ),
  ),
)
```

### Status Colors
```dart
// Success states (completed, earned, positive)
Icon(Icons.check_circle, color: AppColors.success)

// Error states
Text('Error message', style: TextStyle(color: AppColors.error))

// Info/Discovery
Icon(Icons.info, color: AppColors.info)

// Warning
Icon(Icons.warning, color: AppColors.warning)
```

### Backgrounds
```dart
// Main background
Scaffold(backgroundColor: AppColors.background)

// Cards and surfaces
Container(color: AppColors.surface)

// Elevated surfaces
Container(color: AppColors.surfaceElevated)
```

### Text
```dart
// Primary text (headings, important)
Text('Title', style: TextStyle(color: AppColors.textPrimary))

// Secondary text (body, descriptions)
Text('Description', style: TextStyle(color: AppColors.textSecondary))

// Hint text (placeholders)
Text('Hint', style: TextStyle(color: AppColors.textHint))
```

### Gamification
```dart
// XP displays
Icon(Icons.star, color: AppColors.xpGold)

// Streak indicators
Icon(Icons.local_fire_department, color: AppColors.streakOrange)

// Badges
Icon(Icons.military_tech, color: AppColors.badgePurple)
```

---

## ❌ DON'T - Incorrect Usage

### Never Use Hardcoded Colors
```dart
// ❌ BAD
Container(color: Color(0xFFD4A84B))
Container(color: Color(0xFF1A1A2E))
Container(color: Color(0xFF4CAF50))

// ✅ GOOD
Container(color: AppColors.primary)
Container(color: AppColors.onPrimary)
Container(color: AppColors.success)
```

### Don't Use Material Colors Directly
```dart
// ❌ BAD
Icon(Icons.star, color: Colors.amber)
Text('Error', style: TextStyle(color: Colors.red))

// ✅ GOOD
Icon(Icons.star, color: AppColors.primary)
Text('Error', style: TextStyle(color: AppColors.error))
```

---

## 📚 Common Patterns

### Gold Button
```dart
ElevatedButton(
  style: ElevatedButton.styleFrom(
    backgroundColor: AppColors.primary,
    foregroundColor: AppColors.onPrimary,
  ),
  child: Text('Action'),
)
```

### Status Badge
```dart
Container(
  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
  decoration: BoxDecoration(
    color: AppColors.success.withOpacity(0.2),
    borderRadius: BorderRadius.circular(8),
  ),
  child: Text(
    'Completed',
    style: TextStyle(color: AppColors.success),
  ),
)
```

### Loading State
```dart
Center(
  child: CircularProgressIndicator(
    color: AppColors.primary,
  ),
)
```

---

## 🎨 Full Color Palette

### Primary (Gold)
- `AppColors.primary` - Main gold
- `AppColors.primaryDark` - Darker gold
- `AppColors.primaryLight` - Lighter gold
- `AppColors.onPrimary` - Text on gold backgrounds

### Backgrounds
- `AppColors.background` - Main app background
- `AppColors.surface` - Card/container background
- `AppColors.surfaceElevated` - Elevated cards

### Text
- `AppColors.textPrimary` - Main text
- `AppColors.textSecondary` - Secondary text
- `AppColors.textHint` - Placeholder text

### Semantic
- `AppColors.success` - Green for success
- `AppColors.error` - Red for errors
- `AppColors.warning` - Orange for warnings
- `AppColors.info` - Blue for info

### Gamification
- `AppColors.xpGold` - XP displays
- `AppColors.streakOrange` - Streak counters
- `AppColors.badgePurple` - Badges
- `AppColors.questBlue` - Quests

---

## 🔗 Import Statement

Always add this import at the top of your file:

```dart
import 'package:luuniensuki_lms/core/theme/app_colors.dart';
```

Or use relative path based on your file location:
```dart
import '../../../../core/theme/app_colors.dart';
```

---

**Remember:** Using AppColors ensures consistency, maintainability, and makes theme changes easier!

