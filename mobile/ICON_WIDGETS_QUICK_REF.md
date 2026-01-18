# Icon Widgets - Quick Reference

## Import
```dart
import 'package:your_app/shared/widgets/icons/index.dart';
// Or individually:
import 'package:your_app/shared/widgets/icons/status_icon.dart';
import 'package:your_app/shared/widgets/icons/streak_icon.dart';
import 'package:your_app/shared/widgets/icons/milestone_icon.dart';
```

## StatusIcon

### Basic Usage
```dart
StatusIcon(
  status: MotifStatus.discovered,
  size: 16,
)
```

### With Background
```dart
StatusIcon(
  status: MotifStatus.mastered,
  size: 16,
  showBackground: true, // Adds colored background
)
```

### Available Statuses
- `MotifStatus.discovered` - 👁 Blue visibility icon
- `MotifStatus.learned` - 📖 Green book icon
- `MotifStatus.mastered` - ⭐ Gold star icon

## StreakIcon

### Basic Usage
```dart
StreakIcon(
  type: StreakIconType.fire,
  size: 18,
)
```

### With Glow Effect
```dart
StreakIcon(
  type: StreakIconType.warning,
  size: 18,
  showGlow: true, // Adds glow shadow
)
```

### Available Types
- `StreakIconType.fire` - 🔥 Orange fire icon
- `StreakIconType.freeze` - ❄ Light blue freeze icon
- `StreakIconType.warning` - ⚠ Red warning icon

## MilestoneIcon

### Standard Usage
```dart
MilestoneIcon(
  days: 30,
  size: 56,
  showGlow: true,
)
```

### Inline/Compact Usage
```dart
SimpleMilestoneIcon(
  days: 7,
  size: 12,
)
```

### Milestone Mappings
- **7 days** → ⭐ Star (Gold)
- **30 days** → 🎯 Target (Purple)
- **100 days** → 🏆 Trophy (Amber)
- **365 days** → 👑 Crown (XP Gold)

## Color Reference

From `AppColors`:
- `AppColors.info` - #60A5FA (Blue)
- `AppColors.success` - #34D399 (Green)
- `AppColors.primary` - #E8B44C (Gold)
- `AppColors.streakOrange` - #FF6B35 (Orange)
- `AppColors.xpGold` - #FFD700 (Bright Gold)

## Common Patterns

### Stats Row
```dart
Row(
  children: [
    StatusIcon(status: MotifStatus.discovered, size: 16),
    SizedBox(width: 6),
    Text('${count}/${total}'),
  ],
)
```

### Streak Display
```dart
Container(
  child: StreakIcon(
    type: hasStreak ? StreakIconType.fire : StreakIconType.freeze,
    size: 18,
  ),
)
```

### Milestone Progress
```dart
Row(
  children: [
    Text('Còn $days ngày đến '),
    SimpleMilestoneIcon(days: nextMilestone, size: 12),
  ],
)
```

