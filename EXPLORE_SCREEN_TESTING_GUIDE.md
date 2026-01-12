# Explore Screen Fix - Testing Guide

## How to Test the Fix

### Prerequisites
1. Ensure you have the latest code changes
2. The backend API should be running and accessible
3. You should have valid test credentials

### Build and Run

#### Option 1: If build_runner works on your system
```bash
cd mobile
flutter pub run build_runner build --delete-conflicting-outputs
flutter run
```

#### Option 2: If build_runner fails (shell issues)
The generated code has already been manually updated, so you can just:
```bash
cd mobile
flutter run
```

### Test Scenarios

#### 1. Normal Flow - Happy Path ✅
**Steps:**
1. Launch the app
2. Login with valid credentials
3. Navigate to Explore screen (Cửu Đỉnh tab)

**Expected:**
- Loading indicator appears briefly
- 9 urns load and display in a grid
- Progress summary shows correct counts
- Animations play smoothly

#### 2. Navigation Persistence ✅
**Steps:**
1. From explore screen, navigate to another tab (e.g., Profile)
2. Navigate back to Explore screen

**Expected:**
- Data should still be there (no re-loading)
- Screen appears instantly with cached data
- Pull-to-refresh should still work

#### 3. Error Handling 🔴
**Steps:**
1. Turn off WiFi/mobile data
2. Launch app or navigate to Explore
3. (Or alternatively, modify API URL to be invalid)

**Expected:**
- Error icon appears
- Error message in Vietnamese: "Không có kết nối mạng. Vui lòng kiểm tra lại."
- "Thử lại" (Retry) button appears
- Clicking retry attempts to reload

#### 4. Empty State 📭
**Note:** This is harder to test without modifying backend, but you can:

**Steps:**
1. Temporarily modify `explore_provider.dart` line ~76 to return empty list:
   ```dart
   // FOR TESTING ONLY - REMOVE AFTER
   final urns = <Urn>[];  // Empty list
   // final urns = response.map(...).toList();
   ```
2. Rebuild and run

**Expected:**
- Empty state icon (inbox) appears
- Message: "Không có dữ liệu" / "Vui lòng thử lại sau."
- "Thử lại" button appears

#### 5. Pull to Refresh 🔄
**Steps:**
1. When on explore screen with data loaded
2. Pull down from top of screen
3. Release

**Expected:**
- Refresh indicator appears
- Data reloads from API
- Any changes in backend data appear

#### 6. Urn Navigation ➡️
**Steps:**
1. Tap on any urn card in the grid

**Expected:**
- Navigate to urn detail screen
- Show motifs for that urn
- Back button returns to explore screen with data intact

### Success Criteria

✅ No blank white screen on first load
✅ Loading state shows while data is being fetched
✅ 9 urns display correctly after loading
✅ Progress summary shows correct numbers
✅ Error states have clear messages and retry options
✅ Empty states have clear messages and retry options
✅ Data persists when navigating away and back
✅ Pull-to-refresh works correctly
✅ Navigation to urn detail works

### Common Issues and Solutions

#### Issue: Still seeing blank screen
**Solution:**
1. Check if auth is working (try login screen)
2. Check backend logs for API errors
3. Check Flutter console for any errors
4. Verify the generated file was updated correctly

#### Issue: Data doesn't persist
**Solution:**
1. Verify `@Riverpod(keepAlive: true)` is in explore_provider.dart
2. Verify generated file uses `NotifierProvider` not `AutoDisposeNotifierProvider`
3. Rebuild with build_runner

#### Issue: Infinite loading
**Solution:**
1. Check backend is running and accessible
2. Check auth token is valid
3. Check network connectivity
4. Look for errors in Flutter console

#### Issue: Build errors after changes
**Solution:**
```bash
cd mobile
flutter clean
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
flutter run
```

### Verification Checklist

Before marking as complete, verify:

- [ ] App launches without crashes
- [ ] Explore screen loads and shows data
- [ ] All 9 urns are visible
- [ ] Progress card shows correct totals
- [ ] Can tap on urns to view details
- [ ] Can navigate away and back without re-loading
- [ ] Pull-to-refresh works
- [ ] Error handling works (test by disabling network)
- [ ] No console errors during normal operation

### Screenshots to Capture

1. Loading state (brief moment after launch)
2. Loaded state with 9 urns
3. Error state (network disabled)
4. Empty state (if testable)
5. Pull-to-refresh in action

### Debug Logging

Look for these log messages in console:
```
[EXPLORE] Loading urns from API...
[EXPLORE] Got 9 urns
[EXPLORE] Urns loaded successfully
```

Or error messages:
```
[EXPLORE] Error loading urns: <error details>
[EXPLORE] StackTrace: <stack trace>
```

## Rollback Plan

If the fix causes issues, revert these files:
```bash
git checkout mobile/lib/features/explore/presentation/providers/explore_provider.dart
git checkout mobile/lib/features/explore/presentation/screens/explore_screen.dart
git checkout mobile/lib/features/explore/presentation/providers/explore_provider.g.dart
```

Then rebuild:
```bash
cd mobile
flutter clean
flutter pub get
flutter run
```

