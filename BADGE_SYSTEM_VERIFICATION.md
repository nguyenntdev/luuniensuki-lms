# Badge System - Verification Checklist

## Pre-Testing Setup

### 1. Code Generation
Run build_runner to generate freezed and JSON serialization code:
```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
```

### 2. Dependencies Check
Verify these packages are in `pubspec.yaml`:
- ✅ flutter_riverpod
- ✅ freezed_annotation
- ✅ json_annotation
- ✅ hive_flutter
- ✅ dio
- ✅ intl

### 3. File Verification
Verify all files exist:
```bash
# Check badge DTO
ls -l lib/features/achievements/data/models/badge_dto.dart
ls -l lib/features/achievements/data/models/badge_dto.freezed.dart
ls -l lib/features/achievements/data/models/badge_dto.g.dart

# Check provider
ls -l lib/features/achievements/presentation/providers/badge_provider.dart

# Check widget
ls -l lib/features/achievements/presentation/widgets/badge_detail_sheet.dart

# Check screen update
git diff lib/features/achievements/presentation/screens/achievements_screen.dart
```

## Compilation Check

### Build the app
```bash
flutter clean
flutter pub get
flutter build apk --debug
# or
flutter run
```

Expected: ✅ No compilation errors

## Runtime Testing

### Test Case 1: Screen Load
1. Navigate to Achievements screen
2. Select "Huy Hiệu" tab

**Expected**:
- Loading indicator appears briefly
- Badges load and display in grid
- Visual distinction between earned/unearned badges

### Test Case 2: Badge Card Display
**For Earned Badges**:
- ✅ Bright gradient background
- ✅ White icon
- ✅ Badge name in white
- ✅ Green "Đã nhận" status badge

**For Unearned Badges**:
- ✅ Muted gray background
- ✅ Faded icon
- ✅ Badge name in muted color
- ✅ Lock icon with "+X XP" text

### Test Case 3: Badge Detail Sheet
1. Tap any badge card

**Expected**:
- ✅ Bottom sheet slides up
- ✅ Badge icon displays with correct styling
- ✅ Badge name shows correctly
- ✅ Category badge displays
- ✅ Description text visible
- ✅ XP bonus and status show correctly
- ✅ For earned: "Đạt được vào [date]" appears
- ✅ For unearned: No date shown

### Test Case 4: Error Handling
1. Turn off internet
2. Clear app cache
3. Navigate to Achievements screen

**Expected**:
- ✅ Error state displays
- ✅ Error message shows
- ✅ "Thử lại" button appears
- ✅ Tap retry loads data when internet back

### Test Case 5: Empty State
*Only if backend has no badges*

**Expected**:
- ✅ Empty state icon displays
- ✅ "Chưa có huy hiệu" message shows

### Test Case 6: Cache
1. Load badges (with internet)
2. Turn off internet
3. Close and reopen app
4. Navigate to Achievements

**Expected**:
- ✅ Badges load from cache
- ✅ No loading delay
- ✅ All data displays correctly

### Test Case 7: Category Icons
Verify these categories display correct icons:
- ✅ discovery → visibility (eye icon)
- ✅ learning → school (graduation cap)
- ✅ mastery → star
- ✅ streak → local_fire_department (flame)
- ✅ collection → collections (folder)
- ✅ achievement → workspace_premium (medal)

## API Verification

### Test Badge Endpoints
```bash
# Get all badges
curl https://lms.histolab.icu/api/v1/badges | jq

# Get user badges (replace TOKEN)
curl -H "Authorization: Bearer TOKEN" \
  https://lms.histolab.icu/api/v1/users/me/badges | jq
```

**Expected Response Format**:
```json
// All badges
[
  {
    "id": "...",
    "slug": "...",
    "name": "...",
    "name_en": "...",
    "description": "...",
    "icon_url": null,
    "category": "discovery",
    "xp_bonus": 50
  }
]

// User badges
[
  {
    "badge_id": "...",
    "earned_at": "2024-01-17T10:00:00Z"
  }
]
```

## Performance Check

### Metrics to Verify
- ✅ Initial load < 2 seconds (with good connection)
- ✅ Cache load < 100ms
- ✅ Animations smooth (60fps)
- ✅ No janky scrolling in badge grid
- ✅ Sheet opens/closes smoothly

### Memory Check
- ✅ No memory leaks
- ✅ Images/icons load efficiently
- ✅ Cache size reasonable

## Edge Cases

### Test Scenarios
1. ✅ User with 0 badges earned
2. ✅ User with all badges earned
3. ✅ Badge with null description
4. ✅ Badge with null icon_url
5. ✅ Badge with very long name
6. ✅ Badge with unknown category
7. ✅ Network timeout during load
8. ✅ Rapid tab switching

## Code Quality Check

### Run Static Analysis
```bash
flutter analyze
```
Expected: ✅ No errors, minimal warnings

### Check Formatting
```bash
flutter format lib/features/achievements/
```

## Integration Points

### Verify These Still Work
- ✅ Leaderboard tab loads
- ✅ Tab switching smooth
- ✅ Navigation to/from screen
- ✅ App bar displays correctly
- ✅ Bottom navigation works

## Final Sign-Off

- [ ] All files created and committed
- [ ] Code compiles without errors
- [ ] Runtime testing passes
- [ ] API integration works
- [ ] Cache functionality verified
- [ ] UI/UX matches design
- [ ] Performance acceptable
- [ ] No crashes or errors
- [ ] Documentation complete

## Known Limitations

1. Icons are mapped by category string (no custom icons per badge yet)
2. No badge filtering/sorting yet
3. No pull-to-refresh implemented yet
4. No badge sharing feature yet

## Next Developer Tasks

After verification passes:
1. Consider adding pull-to-refresh
2. Implement badge category filter
3. Add badge search functionality
4. Create badge sharing feature
5. Add badge progress tracking for multi-step badges

---
**Status**: Ready for Testing
**Date**: 2024-01-17

