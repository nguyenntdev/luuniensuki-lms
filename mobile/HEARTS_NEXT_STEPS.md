# Hearts System - Next Steps Checklist

## 🔨 Required Before Testing

### 1. Generate Code Files
```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
```

This generates:
- [ ] `heart_state.freezed.dart`
- [ ] `heart_state.g.dart`
- [ ] `hearts_provider.g.dart`

### 2. Verify Imports
Check that all imports resolve:
- [ ] `heart_state.dart` imports work
- [ ] `hearts_provider.dart` imports work
- [ ] `quiz_screen.dart` imports work
- [ ] `app_router.dart` imports work

### 3. Fix Any Build Errors
- [ ] Run `flutter analyze`
- [ ] Fix any import errors
- [ ] Fix any type errors
- [ ] Ensure no naming conflicts

## 🧪 Testing Steps

### Initial Setup Test
1. [ ] Run app on device/emulator
2. [ ] Verify app starts without crashes
3. [ ] Check that hearts initialize to 5

### Quiz Flow Test
1. [ ] Navigate to any quiz
2. [ ] Verify hearts display in header (❤❤❤❤❤)
3. [ ] Tap hearts icon → info dialog appears
4. [ ] Answer question correctly → hearts stay same
5. [ ] Answer question incorrectly → heart lost animation plays
6. [ ] Verify heart count decreased (❤❤❤❤♡)
7. [ ] Answer same question wrong again → NO second penalty
8. [ ] Continue until 0 hearts
9. [ ] Verify navigation to refill screen

### Refill Screen Test
1. [ ] Verify all 4 options display
2. [ ] Verify timer shows correct countdown
3. [ ] Tap "Đợi" → navigates back
4. [ ] Tap "Nạp Đầy" → (TODO: needs gems system)
5. [ ] Tap "Luyện Tập" → shows placeholder
6. [ ] Tap "Xem" → adds 1 heart (placeholder)

### Auto-Refill Test
1. [ ] Set device time forward 30 minutes
2. [ ] Open app
3. [ ] Verify 1 heart added
4. [ ] Set device time forward 2 hours
5. [ ] Open app
6. [ ] Verify 4 hearts added (max)

### Persistence Test
1. [ ] Lose some hearts
2. [ ] Kill app completely
3. [ ] Restart app
4. [ ] Verify hearts state preserved

### Edge Cases Test
1. [ ] Start quiz with 0 hearts → redirected
2. [ ] Multiple wrong answers on same question → 1 penalty
3. [ ] Timer at exactly 0 seconds → heart refills
4. [ ] Hearts at max (5) → timer hidden

## 🐛 Common Issues to Watch For

### Build Issues
- [ ] Missing generated files → run build_runner
- [ ] Import errors → check paths
- [ ] Type mismatches → check generated code

### Runtime Issues
- [ ] Hearts not displaying → check provider initialization
- [ ] Timer not updating → check widget lifecycle
- [ ] Animation not playing → check overlay context
- [ ] Storage errors → check Hive box initialization

### Logic Issues
- [ ] Duplicate penalties → check _incorrectAnswers map
- [ ] Wrong refill calculation → check time math
- [ ] Timer showing negative → check boundary conditions
- [ ] Hearts exceeding max → check refill logic

## 🔧 Quick Fixes

### Hearts Not Showing
```dart
// Check provider is initialized
final heartState = ref.watch(heartsNotifierProvider);
print('Hearts: ${heartState.currentHearts}');
```

### Animation Not Playing
```dart
// Check overlay context
showHeartLostAnimation(context);
// Should use root context, not nested
```

### Timer Not Updating
```dart
// Check timer is created in initState
@override
void initState() {
  super.initState();
  _timer = Timer.periodic(Duration(seconds: 1), (_) {
    setState(() {}); // Force rebuild
  });
}
```

### Storage Errors
```dart
// Check Hive box is opened in main.dart
await HiveStorage.init();
// Should be called before runApp()
```

## 📝 Code Review Checklist

### HeartState Entity
- [ ] All fields properly annotated
- [ ] Methods return correct types
- [ ] Edge cases handled (negative hearts, etc.)
- [ ] Time calculations correct

### HeartsNotifier Provider
- [ ] Timer properly disposed
- [ ] Storage errors caught
- [ ] State updates trigger rebuilds
- [ ] Methods are async where needed

### UI Widgets
- [ ] Proper use of Consumer/ConsumerWidget
- [ ] Timer disposed in dispose()
- [ ] Null safety handled
- [ ] Accessibility considered

### Quiz Integration
- [ ] Hearts checked before quiz start
- [ ] Wrong answers detected correctly
- [ ] Animation shown at right time
- [ ] Navigation works properly

## 🚀 Deployment Checklist

Before merging to main:
- [ ] All tests passing
- [ ] No console warnings
- [ ] Performance acceptable (no jank)
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Tested on iOS and Android

## 📊 Analytics to Add (Future)

```dart
// Track heart loss
analytics.logEvent('heart_lost', {
  'quiz_id': motifId,
  'question_index': questionIndex,
  'hearts_remaining': currentHearts,
});

// Track refill method
analytics.logEvent('hearts_refilled', {
  'method': 'gems' | 'wait' | 'practice' | 'ad',
  'cost': gemCost,
});

// Track quiz blocked
analytics.logEvent('quiz_blocked_no_hearts', {
  'quiz_id': motifId,
  'questions_answered': answeredCount,
});
```

## 🎯 Success Criteria

System is ready when:
- [x] All files created
- [ ] Code generates without errors
- [ ] App runs without crashes
- [ ] Hearts display correctly
- [ ] Wrong answers deduct hearts
- [ ] Animation plays smoothly
- [ ] Refill screen works
- [ ] Auto-refill works
- [ ] State persists
- [ ] No duplicate penalties

## 📞 Getting Help

If stuck:
1. Check error message in console
2. Review HEARTS_SYSTEM_README.md
3. Check HEARTS_VISUAL_GUIDE.md
4. Review similar working code (e.g., XP system)
5. Ask team for help

---

**Next Action**: Run `flutter pub run build_runner build --delete-conflicting-outputs` in mobile directory

