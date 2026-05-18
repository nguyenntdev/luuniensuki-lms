# Hearts System - Implementation Summary

## ✅ Completed Tasks

### 1. Domain Layer
- ✅ Created `HeartState` entity with freezed
  - Max hearts: 5
  - Current hearts tracking
  - Last refill time
  - Auto-refill calculation methods
  - Time until next refill
  - Heart manipulation methods

### 2. Presentation Layer - Providers
- ✅ Created `HeartsNotifier` provider with Riverpod
  - Loads/saves state from Hive storage (userBox)
  - Auto-refill timer (checks every minute)
  - Methods: loseHeart, refillWithGems, addHeart, setUnlimited
  - Helper providers: hasHearts, currentHearts

### 3. Presentation Layer - Widgets
- ✅ Created `HeartsDisplay` widget
  - Shows 5 heart icons (filled/empty)
  - Countdown timer for next refill
  - Updates every second
  - Tap handler for info dialog

- ✅ Created `CompactHeartsDisplay` widget
  - Compact version for headers
  - Shows heart icon + count
  - Infinity symbol for unlimited

- ✅ Created `HeartLostAnimation` widget
  - Animated overlay when losing heart
  - Scale + fade + slide animation
  - Auto-dismisses after 1.2s
  - Helper function: `showHeartLostAnimation()`

### 4. Presentation Layer - Screens
- ✅ Created `HeartsRefillScreen`
  - 4 refill options: Wait, Gems, Practice, Ad
  - Shows current hearts and timer
  - Option cards with icons and descriptions
  - Can navigate back or to home

### 5. Quiz Integration
- ✅ Modified `QuizScreen`
  - Added hearts display in AppBar
  - Added compact hearts with tap handler
  - Track incorrect answers (avoid duplicate penalties)
  - Deduct heart on wrong answer
  - Show heart lost animation
  - Navigate to refill screen when out of hearts
  - Info dialog explaining hearts system

### 6. Routing
- ✅ Added hearts refill route to `app_router.dart`
  - Path: `/hearts-refill`
  - Query parameter: `returnPath`
  - Imported `HeartsRefillScreen`

### 7. Documentation
- ✅ Created comprehensive README
  - System overview
  - File structure
  - Implementation details
  - Usage examples
  - Testing checklist
  - Future enhancements

- ✅ Created Visual Guide
  - UI mockups
  - Screen flows
  - State transitions
  - User scenarios
  - Design principles

## 🔧 Technical Stack

### State Management
- **Riverpod**: For reactive state management
- **Freezed**: For immutable entities
- **Hive**: For persistent storage

### Animations
- **AnimationController**: For heart lost animation
- **TweenSequence**: For complex animation sequences
- **Timer**: For auto-refill and UI updates

### Architecture
- **Clean Architecture**: Domain entities, presentation layers
- **Provider Pattern**: Centralized state management
- **Feature-First Structure**: All hearts code in one feature folder

## 📦 Generated Files Required

Run this command to generate required files:

```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
```

This will generate:
- `heart_state.freezed.dart`
- `heart_state.g.dart`
- `hearts_provider.g.dart`

## 🎯 Integration Points

### 1. Quiz Screen
```dart
// Import
import '../../../hearts/presentation/providers/hearts_provider.dart';
import '../../../hearts/presentation/widgets/hearts_display.dart';
import '../../../hearts/presentation/widgets/heart_lost_animation.dart';

// In AppBar
CompactHeartsDisplay(onTap: () => _showHeartsInfoDialog(context))

// On wrong answer
await ref.read(heartsNotifierProvider.notifier).loseHeart();
showHeartLostAnimation(context);
```

### 2. Storage (HiveStorage)
```dart
// Hearts state stored in existing userBox
userBox.put('hearts_state', heartState.toJson());
```

### 3. Router
```dart
// Route added
GoRoute(
  path: '/hearts-refill',
  name: 'heartsRefill',
  builder: (context, state) => HeartsRefillScreen(
    returnPath: state.uri.queryParameters['returnPath'],
  ),
)
```

## 🚀 How to Use

### Start a Quiz
```dart
// Hearts are automatically managed
// Display shown in quiz header
// Deduction happens on wrong answers
```

### Check Hearts
```dart
final hasHearts = ref.watch(hasHeartsProvider);
if (!hasHearts) {
  context.push('/hearts-refill');
}
```

### Refill Hearts
```dart
// Spend gems
await ref.read(heartsNotifierProvider.notifier).refillWithGems(
  gemCost: 50,
  currentGems: user.gems,
);

// Free refill (ad reward)
await ref.read(heartsNotifierProvider.notifier).refillForFree();

// Add single heart (practice reward)
await ref.read(heartsNotifierProvider.notifier).addHeart();
```

## ⚠️ Important Notes

1. **One Penalty Per Question**
   - Track incorrect answers with `_incorrectAnswers` map
   - Prevents multiple penalties for same question
   - Only first wrong answer costs a heart

2. **Storage Key**
   - Hearts state: `'hearts_state'` in userBox
   - Persists across app restarts
   - Auto-loads on app start

3. **Timer Behavior**
   - Checks every 1 minute (not every second)
   - Calculates full 30-minute intervals
   - Updates `lastRefillTime` to last full interval

4. **Navigation Flow**
   - When out of hearts in quiz → refill screen
   - After refill → can return to quiz or home
   - Use `returnPath` query param for deep linking

## 🔮 Future TODOs

### High Priority
- [ ] Integrate actual gems system (currently uses XP)
- [ ] Implement practice mode
- [ ] Add ad SDK integration for rewarded ads

### Medium Priority
- [ ] Add analytics for heart usage
- [ ] Premium unlimited hearts feature
- [ ] Local notifications when hearts full
- [ ] A/B test refill costs

### Low Priority
- [ ] Heart purchase options
- [ ] Daily heart bonus
- [ ] Friend hearts (send/receive)
- [ ] Seasonal heart themes

## 🧪 Testing Checklist

### Manual Testing
- [ ] Hearts display in quiz header
- [ ] Wrong answer deducts heart
- [ ] Animation plays smoothly
- [ ] Timer counts down correctly
- [ ] Auto-refill works after 30 min
- [ ] Refill screen options all work
- [ ] State persists across app restarts
- [ ] No duplicate penalties per question
- [ ] Navigation flows correctly

### Edge Cases
- [ ] Multiple wrong answers on same question
- [ ] App backgrounded during refill
- [ ] App killed during refill
- [ ] System time changes
- [ ] 0 hearts at quiz start
- [ ] Exactly at refill time

## 📈 Metrics to Track

1. **Usage Metrics**
   - Hearts lost per quiz session
   - Average hearts at quiz completion
   - % of users who run out of hearts

2. **Refill Metrics**
   - % using each refill method
   - Average wait time before refill
   - Gems spent on hearts per user

3. **Retention Metrics**
   - Users returning after running out
   - Churn rate when blocked by hearts
   - Engagement before/after hearts system

## 🎨 Design System Compliance

All components follow app design system:
- ✅ AppColors for consistent theming
- ✅ AppTypography for text styles
- ✅ AppSpacing for consistent spacing
- ✅ Dark theme support
- ✅ Responsive layouts
- ✅ Accessibility considerations

## 📱 Supported Platforms

- ✅ iOS
- ✅ Android
- ✅ Portrait orientation
- ✅ Landscape orientation (responsive)
- ✅ Tablets (larger screens)

## 🌐 Localization

Current: Vietnamese only
- All UI text in Vietnamese
- Timer formats: "Xm" or "Xh Ym"
- Ready for i18n extraction

To add English:
1. Extract strings to i18n files
2. Add translations
3. Use intl package for formatting

## 🔐 Security Considerations

1. **Client-Side Only**
   - Hearts state stored locally
   - No server validation (currently)
   - Could be manipulated by root users

2. **Future Server Integration**
   - Sync hearts to backend
   - Validate hearts before quiz submission
   - Prevent client-side manipulation

## 📞 Support

For questions or issues:
1. Check HEARTS_SYSTEM_README.md
2. Check HEARTS_VISUAL_GUIDE.md
3. Review code comments
4. Ask development team

---

**Version**: 1.0.0
**Last Updated**: 2024-01-15
**Status**: ✅ Ready for Testing

