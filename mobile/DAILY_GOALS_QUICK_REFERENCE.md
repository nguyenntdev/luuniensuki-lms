# Daily Goals Feature - Quick Reference

## 🚀 Setup Commands

### Generate Provider Files
```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
```

### Run App
```bash
flutter run
```

### Clean Build (if issues)
```bash
flutter clean
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
flutter run
```

## 📂 File Locations

### Core Files
```
mobile/lib/features/daily_goals/
  domain/entities/daily_goal.dart           # Entity & enum
  presentation/
    providers/daily_goal_provider.dart      # State management
    screens/daily_goal_screen.dart          # Full screen
    widgets/
      compact_daily_goal_widget.dart        # Explore header
      daily_goal_widget.dart                # Full widget
      daily_goal_celebration.dart           # Celebration
    services/
      daily_goal_celebration_service.dart   # Service
```

### Modified Files
```
mobile/lib/
  main.dart                                 # Initialize sync
  routing/app_router.dart                   # Add route
  features/
    explore/presentation/screens/
      explore_screen.dart                   # Add widget
    settings/presentation/screens/
      settings_screen.dart                  # Add menu item
```

## 🔧 Key Provider Usage

### Read Current Goal
```dart
final goal = ref.watch(dailyGoalNotifierProvider);
print('Level: ${goal.level.name}');
print('Progress: ${goal.currentXp}/${goal.level.xpRequired}');
print('Completed: ${goal.isCompleted}');
```

### Update Goal Level
```dart
await ref.read(dailyGoalNotifierProvider.notifier)
  .updateGoalLevel(GoalLevel.serious);
```

### Manually Add XP
```dart
final wasCompleted = await ref.read(dailyGoalNotifierProvider.notifier)
  .addXp(50);
if (wasCompleted) {
  // Show celebration
  context.showDailyGoalCelebration();
}
```

### Check Progress
```dart
final goal = ref.read(dailyGoalNotifierProvider);
final percentage = goal.progressPercentage; // 0.0 to 1.0
final remaining = goal.remainingXp;          // XP left
final shouldReset = goal.shouldReset(DateTime.now());
```

## 🎨 Goal Level Reference

| Level     | Vietnamese     | XP  | Icon | Color  |
|-----------|---------------|-----|------|--------|
| Casual    | Thoải mái     | 5   | 🧘   | Green  |
| Regular   | Thường xuyên  | 10  | 🚶   | Blue   |
| Serious   | Nghiêm túc    | 20  | 🏃   | Orange |
| Intense   | Cao thủ       | 30  | ⚡   | Red    |

## 🌐 Navigation Paths

### Routes
```dart
// From code
context.push('/daily-goal');

// From Settings
Settings → Learning Goals → Daily Goal

// From Explore
Tap compact widget → Daily Goal Screen
```

## 💾 Storage Keys

### HiveStorage
```dart
Key: 'daily_goal'
Box: settingsBox
Data: {
  level: String,
  currentXp: int,
  lastUpdated: String (ISO 8601),
  isCompleted: bool
}
```

## 🐛 Common Issues & Fixes

### Issue: Provider not found
```bash
# Solution: Generate providers
flutter pub run build_runner build --delete-conflicting-outputs
```

### Issue: Widget not updating
```dart
// Check if XP sync is initialized in main.dart
ref.read(dailyGoalXpSyncProvider);

// Verify auth provider has user
final user = ref.watch(currentUserProvider);
print('User: $user');
```

### Issue: Storage not persisting
```dart
// Check HiveStorage is initialized in main.dart
await HiveStorage.init();

// Verify setting is saved
final storage = ref.read(hiveStorageProvider);
print(storage.getSetting('daily_goal'));
```

### Issue: Route not found
```dart
// Verify route is added in app_router.dart
GoRoute(
  path: _Paths.dailyGoal, // '/daily-goal'
  name: 'dailyGoal',
  builder: (context, state) => const DailyGoalScreen(),
)
```

### Issue: Midnight reset not working
```dart
// Check shouldReset logic
final goal = ref.read(dailyGoalNotifierProvider);
final now = DateTime.now();
print('Should reset: ${goal.shouldReset(now)}');

// Verify lastUpdated is stored correctly
print('Last updated: ${goal.lastUpdated}');
```

## 🧪 Testing Snippets

### Test Goal Creation
```dart
test('Daily goal initializes correctly', () {
  final goal = DailyGoal.initial();
  expect(goal.level, GoalLevel.regular);
  expect(goal.currentXp, 0);
  expect(goal.isCompleted, false);
});
```

### Test Progress Calculation
```dart
test('Progress percentage is correct', () {
  final goal = DailyGoal(
    level: GoalLevel.regular,
    currentXp: 5,
    lastUpdated: DateTime.now(),
  );
  expect(goal.progressPercentage, 0.5); // 5/10 = 50%
});
```

### Test Reset Logic
```dart
test('Should reset on new day', () {
  final yesterday = DateTime.now().subtract(Duration(days: 1));
  final goal = DailyGoal(
    level: GoalLevel.regular,
    currentXp: 5,
    lastUpdated: yesterday,
  );
  expect(goal.shouldReset(DateTime.now()), true);
});
```

## 📊 Debugging Tips

### Enable Provider Logging
```dart
// In main.dart
ProviderScope(
  observers: [ProviderLogger()],
  child: LuuniensukiApp(),
)

class ProviderLogger extends ProviderObserver {
  @override
  void didUpdateProvider(
    ProviderBase provider,
    Object? previousValue,
    Object? newValue,
    ProviderContainer container,
  ) {
    print('${provider.name ?? provider.runtimeType}: $newValue');
  }
}
```

### Check XP Changes
```dart
ref.listen(currentUserProvider, (previous, next) {
  if (previous?.totalXp != next?.totalXp) {
    print('XP changed: ${previous?.totalXp} → ${next?.totalXp}');
  }
});
```

### Monitor Goal Changes
```dart
ref.listen(dailyGoalNotifierProvider, (previous, next) {
  print('Goal updated:');
  print('  XP: ${previous?.currentXp} → ${next.currentXp}');
  print('  Completed: ${previous?.isCompleted} → ${next.isCompleted}');
});
```

## 🎯 Quick Actions

### Reset Daily Goal (Debug)
```dart
await ref.read(dailyGoalNotifierProvider.notifier).reset();
```

### Simulate XP Gain
```dart
// Add 50 XP manually
await ref.read(dailyGoalNotifierProvider.notifier).addXp(50);
```

### Change Goal Level Programmatically
```dart
await ref.read(dailyGoalNotifierProvider.notifier)
  .updateGoalLevel(GoalLevel.intense);
```

### Force Celebration (Debug)
```dart
if (context.mounted) {
  context.showDailyGoalCelebration();
}
```

## 📱 Hot Reload Tips

After changing:
- **Widgets**: Hot reload (r) works
- **State logic**: Hot restart (R) required
- **Providers**: Rebuild providers, then hot restart
- **Routes**: Hot restart required

## 🔗 Related Features

### XP Award System
```dart
// In lesson completion
final xpGained = 50;
// XP sync will automatically update daily goal
```

### Auth Integration
```dart
// Daily goal syncs with user's totalXp
final user = ref.watch(currentUserProvider);
// When user.totalXp increases, daily goal updates
```

### Notification System (Future)
```dart
// Will integrate with daily goals to send reminders
// E.g., "You're 5 XP away from your daily goal!"
```

## 📝 Code Snippets

### Show Daily Goal in Any Screen
```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../daily_goals/presentation/widgets/compact_daily_goal_widget.dart';

// In your widget
@override
Widget build(BuildContext context, WidgetRef ref) {
  return Column(
    children: [
      // ... other widgets
      CompactDailyGoalWidget(),
      // ... more widgets
    ],
  );
}
```

### Navigate to Goal Screen
```dart
import 'package:go_router/go_router.dart';

// Anywhere in your app
onTap: () => context.push('/daily-goal'),
```

### Check if Goal is Met
```dart
final goal = ref.watch(dailyGoalNotifierProvider);
if (goal.isCompleted) {
  // Show success message or badge
  print('🎉 Daily goal completed!');
}
```

## 🔄 Update Workflow

1. Make code changes
2. Save files
3. Hot reload (if widget changes)
4. Hot restart (if logic changes)
5. Test in app
6. Commit changes

## 📚 Documentation

- [Implementation Summary](DAILY_GOALS_IMPLEMENTATION.md)
- [Visual Guide](DAILY_GOALS_VISUAL_GUIDE.md)
- [Testing Guide](DAILY_GOALS_TESTING_GUIDE.md)
- This Quick Reference

## 🆘 Get Help

If stuck:
1. Check console for errors
2. Verify providers are generated
3. Check HiveStorage is initialized
4. Ensure route is registered
5. Review documentation above
6. Check related features (auth, XP system)

