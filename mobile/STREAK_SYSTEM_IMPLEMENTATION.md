# Streak System Implementation - Duolingo Style

## 📋 Overview

Enhanced the existing streak system with Duolingo-inspired features including:
- 🔥 Streak tracking and visualization
- ❄️ Streak Freeze purchases with gems
- 📅 7-day calendar widget
- 🏆 Milestone celebrations (7, 30, 100, 365 days)
- 💎 Gem rewards for milestones

## 🗂️ File Structure

```
mobile/lib/features/streak/
├── domain/
│   └── entities/
│       ├── streak_data.dart          # Main streak data model
│       ├── streak_freeze.dart        # Streak freeze entity
│       ├── streak_milestone.dart     # Milestone definitions
│       └── streak_day.dart           # Calendar day model
├── presentation/
│   ├── providers/
│   │   └── streak_provider.dart      # State management
│   └── widgets/
│       ├── streak_calendar.dart      # 7-day calendar widget
│       ├── streak_display.dart       # Main streak card
│       ├── streak_milestone.dart     # Celebration widget
│       └── buy_streak_freeze_button.dart  # Purchase UI
```

## ✨ Features Implemented

### 1. Streak Freeze Feature
- **Cost**: 50 gems per freeze
- **Limit**: Maximum 2 freezes at once
- **Protection**: 1 day protection
- **Auto-apply**: Automatically used when user misses a day
- Purchase UI integrated in profile screen

### 2. Streak Calendar Widget
- Shows last 7 days of activity
- Visual indicators:
  - 🔥 Active days (orange)
  - ❄️ Freeze-protected days (blue)
  - ⚪ Missed/future days (gray)
  - White glow for today
- Day labels: T2, T3, T4, T5, T6, T7, CN

### 3. Milestone System
Automatic gem rewards at streak milestones:

| Milestone | Days | Reward | Name | Icon |
|-----------|------|--------|------|------|
| Week | 7 | 25 💎 | Tuần Hoàn Hảo | ⭐ |
| Month | 30 | 75 💎 | Người Học Chăm Chỉ | 🎯 |
| Century | 100 | 200 💎 | Bậc Thầy Kiên Trì | 🏆 |
| Year | 365 | 500 💎 | Chiến Binh Bất Bại | 👑 |

### 4. Milestone Celebration
- Full-screen celebration modal
- Confetti animation
- Large milestone icon
- Gem reward display
- Auto-dismiss after 5 seconds

### 5. Enhanced Streak Display
- Current streak with fire icon
- Streak calendar (last 7 days)
- Freeze count badge
- Progress to next milestone
- Longest streak record
- Glass morphism design

## 🔌 API Integration

### Endpoints Used
```dart
// Get streak data
GET /api/v1/users/me/streak
Response: {
  current_streak: int,
  longest_streak: int,
  streak_freezes: int,
  last_active_at: datetime,
  days_since_last_active: int
}

// Use streak freeze
POST /api/v1/users/me/streak/freeze
Response: StreakResponse
```

### API Constants Added
```dart
// mobile/lib/core/constants/api_constants.dart
static const String streak = '$apiPath/users/me/streak';
static const String useStreakFreeze = '$apiPath/users/me/streak/freeze';
```

## 🎨 Design

### Colors (Already in AppColors)
- `AppColors.streakOrange` - #FF6B35 (fire icon, active days)
- `AppColors.streakSurface` - #3D2818 (backgrounds)
- `Colors.blue` - Freeze indicators

### Visual Style
- Glass morphism containers
- Gradient backgrounds
- Glow effects on active elements
- Smooth animations
- Emoji icons for visual appeal

## 📱 Profile Screen Integration

### Changes Made
**File**: `mobile/lib/features/profile/presentation/screens/profile_screen.dart`

1. **Added imports**:
```dart
import '../../../streak/presentation/widgets/streak_display.dart';
import '../../../streak/presentation/widgets/buy_streak_freeze_button.dart';
```

2. **Replaced old streak card** with:
```dart
// Enhanced Streak Display
const StreakDisplay(),

AppSpacing.verticalSpaceMD,

// Buy Streak Freeze Button
const BuyStreakFreezeButton(),
```

### Layout in Profile
```
Profile Screen
├── Header (Avatar, Name, Email)
├── XP Card
├── Stats Grid
├── [NEW] Streak Display ← Enhanced with calendar
├── [NEW] Buy Streak Freeze Button ← Gem purchase
├── Settings Cards
└── Logout
```

## 💻 Usage Examples

### Display Streak in Profile
```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../streak/presentation/widgets/streak_display.dart';

class MyWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return StreakDisplay(
      onTap: () {
        // Navigate to streak details
      },
    );
  }
}
```

### Purchase Streak Freeze
```dart
// Already integrated in BuyStreakFreezeButton
final notifier = ref.read(streakNotifierProvider.notifier);
final success = await notifier.purchaseStreakFreeze();

if (success) {
  // Show success message
}
```

### Check Milestone
```dart
final milestone = StreakMilestone.forStreak(currentStreak);
if (milestone != null) {
  print('Achieved: ${milestone.name}');
  print('Reward: ${milestone.gemReward} gems');
}
```

### Get Days Until Next Milestone
```dart
final daysUntil = StreakMilestone.daysUntilNext(currentStreak);
if (daysUntil != null) {
  print('$daysUntil days until next milestone');
}
```

## 🔄 State Management

### StreakProvider
```dart
@Riverpod(keepAlive: true)
class StreakNotifier extends _$StreakNotifier {
  // Methods:
  - loadStreak()              // Load from API
  - refresh()                 // Refresh data
  - purchaseStreakFreeze()    // Buy with gems
  - useStreakFreeze()         // Use a freeze
  - checkMilestone()          // Check and reward
  - clearError()              // Clear error state
}
```

### State Model
```dart
@freezed
class StreakState with _$StreakState {
  const factory StreakState({
    @Default(StreakData.initial()) StreakData data,
    @Default(StreakFreeze.initial()) StreakFreeze freeze,
    @Default(false) bool isLoading,
    String? error,
    StreakMilestone? justReachedMilestone,
  }) = _StreakState;
}
```

## 🎯 Next Steps

### Code Generation
Run these commands to generate Riverpod and Freezed code:
```bash
cd mobile
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

### Backend Enhancement (Optional)
Consider adding these backend features:
1. **Auto-apply freeze**: Automatically use freeze when streak breaks
2. **Streak history**: Track all streak periods
3. **Weekend amulet**: Skip weekends without breaking streak
4. **Streak recovery**: One-time streak recovery purchase

### Testing
- [ ] Test freeze purchase flow
- [ ] Test milestone celebrations
- [ ] Test calendar display accuracy
- [ ] Test API integration
- [ ] Test with different streak values

## 📊 Gem Economy Integration

### Earning Gems
Users earn gems through milestones automatically via `StreakProvider.checkMilestone()`

### Spending Gems
- Streak Freeze: 50 gems
- Integrated with existing `GemsProvider`
- Balance validation before purchase
- Transaction logging

## 🐛 Known Limitations

1. **Freeze Auto-Apply**: Currently manual - backend needs update to auto-apply
2. **Streak History**: Only shows last 7 days
3. **Timezone**: Uses device timezone (should sync with backend UTC+7)

## 📚 Dependencies

No new dependencies required! Uses existing:
- `flutter_riverpod` - State management
- `freezed_annotation` - Code generation  
- `confetti` - Celebration animations (for milestone widget)

## 🎨 Design Reference

Inspired by Duolingo's streak features:
- Fire icon for active streaks
- Freeze icon for protection
- Calendar grid visualization
- Milestone celebrations
- Gamification with rewards

## 📝 Notes

- All Vietnamese text strings for localization
- Glass morphism design matches app theme
- Integrates seamlessly with existing gems system
- Fully responsive and animated
- Error handling included

