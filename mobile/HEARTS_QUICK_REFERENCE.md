# Hearts System - Quick Reference

## 📁 Files Created

### Domain Layer
```
mobile/lib/features/hearts/domain/entities/
└── heart_state.dart           # Hearts state entity (freezed)
```

### Presentation Layer
```
mobile/lib/features/hearts/presentation/
├── providers/
│   └── hearts_provider.dart   # Riverpod provider with auto-refill timer
├── screens/
│   └── hearts_refill_screen.dart  # Screen when out of hearts
└── widgets/
    ├── hearts_display.dart    # Full hearts display with timer
    └── heart_lost_animation.dart  # Animation overlay
```

### Integration
```
mobile/lib/features/quiz/presentation/screens/
└── quiz_screen.dart           # MODIFIED: Added hearts integration

mobile/lib/routing/
└── app_router.dart            # MODIFIED: Added hearts refill route
```

### Documentation
```
mobile/lib/features/hearts/
├── HEARTS_SYSTEM_README.md    # Full implementation guide
└── HEARTS_VISUAL_GUIDE.md     # UI mockups and flows

mobile/
├── HEARTS_IMPLEMENTATION_SUMMARY.md  # What was built
└── HEARTS_NEXT_STEPS.md              # Testing checklist
```

## ⚡ Quick Commands

### Generate Code
```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
```

### Run App
```bash
cd mobile
flutter run
```

### Check for Errors
```bash
cd mobile
flutter analyze
```

## 🎯 Key Concepts

### Hearts State
- Max: 5 hearts
- Refill: 1 heart per 30 minutes
- Storage: Hive userBox, key 'hearts_state'
- Auto-refill: Timer checks every minute

### Quiz Integration
- Display: CompactHeartsDisplay in AppBar
- Penalty: 1 heart per wrong answer (first time only)
- Block: Navigate to refill screen when 0 hearts
- Animation: Heart lost overlay on wrong answer

### Refill Options
1. **Wait**: Free, auto-refills over time
2. **Gems**: 50 gems for full refill (TODO: integrate gems)
3. **Practice**: Earn hearts back (TODO: implement)
4. **Ad**: Watch ad for 1 heart (TODO: integrate ads)

## 📱 UI Components

### Hearts Display
```dart
// Full display with timer
HeartsDisplay(showTimer: true)

// Compact for headers
CompactHeartsDisplay(
  onTap: () => _showHeartsInfoDialog(context),
)
```

### Check Hearts
```dart
final hasHearts = ref.watch(hasHeartsProvider);
final count = ref.watch(currentHeartsProvider);
```

### Lose Heart
```dart
await ref.read(heartsNotifierProvider.notifier).loseHeart();
showHeartLostAnimation(context);
```

### Refill Hearts
```dart
// Full refill with gems
await ref.read(heartsNotifierProvider.notifier).refillWithGems(
  gemCost: 50,
  currentGems: userGems,
);

// Add single heart
await ref.read(heartsNotifierProvider.notifier).addHeart();

// Full free refill
await ref.read(heartsNotifierProvider.notifier).refillForFree();
```

## 🔗 Navigation

```dart
// Go to refill screen
context.push('/hearts-refill?returnPath=/quiz/$motifId');

// Check hearts before quiz
if (!ref.watch(hasHeartsProvider)) {
  context.push('/hearts-refill');
  return;
}
```

## 🎨 Visual States

```
Full:    ❤❤❤❤❤        (5/5, no timer)
Some:    ❤❤❤♡♡  25m   (3/5, with timer)
Empty:   ♡♡♡♡♡  15m   (0/5, blocked)
Premium: ∞             (unlimited)
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Build errors | Run `flutter pub run build_runner build --delete-conflicting-outputs` |
| Hearts not showing | Check provider initialization in quiz screen |
| Timer not updating | Check Timer is created in initState |
| Animation not playing | Use root context for overlay |
| State not persisting | Check Hive.init() called in main.dart |
| Duplicate penalties | Check _incorrectAnswers map is tracking |

## 📊 State Flow

```
Initial Load
    ↓
Load from Hive (or create initial)
    ↓
Auto-refill based on time passed
    ↓
Start auto-refill timer (1 min intervals)
    ↓
Display in UI
    ↓
User actions (lose/refill)
    ↓
Save to Hive
    ↓
Update UI
```

## 🧪 Test Scenarios

1. **Fresh Install**: Should have 5 hearts
2. **Wrong Answer**: Lose 1 heart, see animation
3. **Multiple Wrong (Same Q)**: Only lose 1 heart total
4. **Run Out**: Navigate to refill screen
5. **Wait 30 Min**: Gain 1 heart automatically
6. **Wait 3 Hours**: Gain max hearts (cap at 5)
7. **Kill App**: Hearts persist on restart
8. **Timer Display**: Shows correct countdown

## 💡 Best Practices

### Do ✅
- Check hearts before starting quiz
- Show clear visual feedback
- Provide multiple refill options
- Save state on every change
- Handle edge cases (0 hearts, max hearts)

### Don't ❌
- Penalize same question twice
- Block users permanently
- Hide refill options
- Ignore timer edge cases
- Forget to dispose timers

## 🚀 Next Steps

1. **Build**: `flutter pub run build_runner build`
2. **Test**: Run app and test quiz flow
3. **Verify**: Check all scenarios work
4. **Fix**: Address any bugs
5. **Deploy**: Merge to main branch

## 📚 Learn More

- **Full Details**: `HEARTS_SYSTEM_README.md`
- **Visual Guide**: `HEARTS_VISUAL_GUIDE.md`
- **Implementation**: `HEARTS_IMPLEMENTATION_SUMMARY.md`
- **Testing**: `HEARTS_NEXT_STEPS.md`

---

**Version**: 1.0.0  
**Status**: Ready for Testing  
**Last Updated**: 2024-01-15

