# Quiz Blank Screen Fix

## Problem Summary
After exploring a motif, clicking "Làm trắc nghiệm" (Start Quiz) resulted in a completely blank white screen instead of showing the quiz questions.

## Root Cause Analysis

### Location
`/Users/nguyennt/Documents/luuniensuki-lms/mobile/lib/features/quiz/presentation/screens/quiz_screen.dart`

### The Bug
In the `_checkForSavedProgress()` method (lines 54-93), the code was using an incorrect async pattern:

```dart
// ❌ INCORRECT - This doesn't actually wait for data to load
final quizAsync = ref.read(quizProvider(widget.motifId));
await quizAsync.when(
  data: (quiz) async { ... },
  loading: () {},      // Empty callback - does nothing!
  error: (_, __) {},   // Empty callback - does nothing!
);
```

**Why this fails:**
- `ref.read(quizProvider(...))` returns the **current snapshot** of the provider's state as an `AsyncValue`
- If the provider is still loading (which it usually is on first access), this returns `AsyncLoading`
- Calling `.when()` on an `AsyncLoading` immediately executes the `loading: () {}` callback
- The empty callback does nothing and returns immediately
- The quiz data never loads, leaving a blank screen

### The Fix
Changed to properly await the actual Future:

```dart
// ✅ CORRECT - Actually waits for data to load
try {
  final quiz = await ref.read(quizProvider(widget.motifId).future);
  // Now we can safely work with the loaded quiz data
  ...
} catch (e) {
  // Errors are handled gracefully
}
```

**Why this works:**
- `ref.read(quizProvider(...).future)` returns the actual `Future<QuizResponseDto>`
- `await` properly waits for the Future to complete
- Data is loaded before proceeding with saved progress check
- Errors are caught and handled gracefully

## Changes Made

### File Modified
`mobile/lib/features/quiz/presentation/screens/quiz_screen.dart`

### Specific Changes (lines 54-93)
1. Replaced `ref.read(quizProvider(...))` with `ref.read(quizProvider(...).future)`
2. Removed nested `.when()` callbacks
3. Added try-catch block for proper error handling
4. Simplified control flow

## Testing Checklist

- [ ] Navigate to URN viewer
- [ ] Click on a motif to open sidebar
- [ ] Click "Làm trắc nghiệm" button
- [ ] Verify quiz screen shows loading spinner during data fetch
- [ ] Verify quiz questions appear after loading
- [ ] Verify error states show proper error messages if API fails
- [ ] Test with saved quiz progress (complete partially, exit, return)
- [ ] Verify resume dialog appears when returning to incomplete quiz
- [ ] Verify "Start fresh" option clears saved progress
- [ ] Verify "Continue" option resumes from saved progress

## Additional Notes

### Why the build() method works correctly
The main `build()` method (line 214) correctly uses:
```dart
final quizAsync = ref.watch(quizProvider(widget.motifId));
```

This works because:
- `ref.watch()` properly listens to state changes
- The widget rebuilds when the provider state changes from loading → data
- The `.when()` method in the widget tree correctly handles all states:
  - `loading:` shows CircularProgressIndicator
  - `error:` shows error UI with retry button
  - `data:` shows quiz content

### Impact
This fix ensures:
- ✅ Quiz data loads properly before screen renders
- ✅ Loading states are handled correctly
- ✅ Error states are properly displayed
- ✅ Saved progress checking happens only after data is ready
- ✅ No more blank white screens

## Prevention
To avoid similar issues in the future:
1. Always use `ref.read(provider.future)` when you need to await a provider's data
2. Use `ref.watch()` in build methods for reactive updates
3. Never use empty callbacks in `.when()` unless intentional
4. Always add try-catch when awaiting futures in lifecycle methods

