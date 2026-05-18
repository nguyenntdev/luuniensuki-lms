# Quiz Progress Auto-Save Implementation Summary

## Overview
Implemented automatic progress saving for quiz sessions in the Flutter app, allowing users to resume incomplete quizzes without losing their progress.

## Implementation Details

### 1. Data Model - QuizProgress
**File**: `mobile/lib/features/quiz/data/models/quiz_progress.dart`

Created a new Freezed model to store quiz progress:

```dart
class QuizProgress {
  final String motifId;
  final String motifName;
  final int currentQuestionIndex;
  final Map<String, String> answers;
  final Map<String, bool> incorrectAnswers;
  final int timeSpentSeconds;
  final DateTime savedAt;
  final String questionsHash; // For validation
}
```

**Features**:
- Auto-generates JSON serialization via json_serializable
- Includes `isValid()` method to check if progress hasn't expired (default: 7 days)
- `createQuestionsHash()` static method to validate quiz content hasn't changed

### 2. Storage Service Extension
**File**: `mobile/lib/core/storage/hive_storage.dart`

**Added Methods**:
- `saveQuizProgress(motifId, progress)` - Save progress for a specific motif
- `getQuizProgress(motifId)` - Retrieve saved progress
- `clearQuizProgress(motifId)` - Clear progress for a specific motif
- `clearAllQuizProgress()` - Clear all saved quiz progress

**Key Format**: `quiz_progress_{motifId}`

**Storage Box**: Added new `_quizProgressBox` to Hive initialization

### 3. Quiz State Provider
**File**: `mobile/lib/features/quiz/presentation/providers/quiz_provider.dart`

**New Classes**:

#### QuizStateData
Simple data class to hold quiz session state:
- `currentQuestionIndex`
- `answers`
- `incorrectAnswers`
- `startTime`
- `hasSavedProgress` (flag)
- `savedProgress` (optional)

#### QuizState Provider
Riverpod NotifierProvider that manages quiz state with auto-save:

**Methods**:
- `build(motifId)` - Initializes state, loads saved progress if exists
- `setQuestionIndex(index)` - Update current question and auto-save
- `setAnswer(questionId, answer)` - Save answer and auto-save
- `markIncorrect(questionId)` - Mark incorrect answer and auto-save
- `startFresh(quiz)` - Clear saved progress and start new session
- `resumeProgress()` - Mark saved progress as resumed
- `_autoSave()` - Internal method that saves current state to Hive
- `clearProgress()` - Clear saved progress

### 4. Quiz Submission Enhancement
**File**: `mobile/lib/features/quiz/presentation/providers/quiz_provider.dart`

Updated `QuizSubmission.submit()` to automatically clear saved progress on successful submission:

```dart
// Clear saved progress on successful submission
final storage = ref.read(hiveStorageProvider);
await storage.clearQuizProgress(motifId);
```

### 5. Quiz Screen Updates
**File**: `mobile/lib/features/quiz/presentation/screens/quiz_screen.dart`

#### New Features:

**A. Progress Check on Init**
- Added `_hasCheckedSavedProgress` flag
- `_checkForSavedProgress()` method runs after first build
- Validates quiz content hasn't changed using question hash
- Shows resume dialog if valid progress exists

**B. Resume Dialog**
`_showResumeDialog(QuizProgress)` displays:
- Current question number
- Number of answered questions
- Time spent so far
- Options: "Bắt đầu lại" or "Tiếp tục"

**C. Auto-Save Integration**
- Answer selection triggers `quizStateProvider.setAnswer()`
- Navigation triggers `quizStateProvider.setQuestionIndex()`
- Incorrect answers trigger `quizStateProvider.markIncorrect()`

**D. Exit Confirmation Update**
Changed message from:
> "Tiến trình làm bài sẽ bị mất. Bạn có chắc chắn muốn thoát?"

To:
> "Tiến trình làm bài đã được tự động lưu. Bạn có thể tiếp tục sau. Bạn có chắc chắn muốn thoát?"

## Edge Cases Handled

### 1. Multiple Devices (Local-Only Storage)
- Progress is stored locally in Hive, not synced to server
- Each device maintains its own progress
- **Implication**: Users may see different progress on different devices

### 2. Quiz Content Changed
- Uses `questionsHash` to validate quiz structure
- Hash is based on question IDs and order
- If hash mismatch detected, old progress is automatically cleared
- User starts fresh without seeing invalid resume dialog

### 3. Expired Progress
- Default expiration: 7 days
- `isValid()` method checks age of saved progress
- Expired progress is ignored (not shown in resume dialog)

### 4. Incomplete State
- Only saves when quiz is partially completed
- Clears automatically on submission
- Safe to interrupt at any time

### 5. Navigation Edge Cases
- Uses `addPostFrameCallback` to avoid build-time state mutations
- Prevents multiple resume dialogs with `_hasCheckedSavedProgress` flag
- Handles async quiz loading gracefully

## User Flow

### Starting a Quiz
1. User navigates to quiz screen
2. System checks for saved progress after build
3. If saved progress exists and is valid:
   - Show resume dialog
   - User chooses to resume or start fresh
4. If resuming:
   - Restore question index, answers, and time
   - Continue from saved state
5. If starting fresh:
   - Clear old progress
   - Start new session

### During Quiz
1. Every answer selection auto-saves
2. Every navigation (next/previous) auto-saves
3. Every incorrect answer auto-saves
4. No user action required for saving

### Completing Quiz
1. User submits answers
2. System clears saved progress automatically
3. Shows results screen

### Exiting Quiz
1. User taps close button
2. Sees updated message about auto-save
3. Progress is already saved
4. Can return anytime to resume

## Testing Checklist

- [ ] Start quiz, answer some questions, exit, return → Should see resume dialog
- [ ] Resume from saved progress → Should continue from correct question
- [ ] Start fresh from resume dialog → Should clear progress
- [ ] Complete and submit quiz → Should clear saved progress
- [ ] Answer questions, wait 8 days, return → Should not see resume dialog
- [ ] Start quiz, backend changes questions, return → Should not see resume dialog
- [ ] Test navigation saves (next/previous)
- [ ] Test incorrect answer tracking
- [ ] Test multiple quizzes (different motifs)
- [ ] Test hint usage with auto-save

## Files Changed

1. **New Files**:
   - `mobile/lib/features/quiz/data/models/quiz_progress.dart`
   - `mobile/lib/features/quiz/data/models/quiz_progress.freezed.dart`
   - `mobile/lib/features/quiz/data/models/quiz_progress.g.dart`

2. **Modified Files**:
   - `mobile/lib/core/storage/hive_storage.dart`
   - `mobile/lib/features/quiz/presentation/providers/quiz_provider.dart`
   - `mobile/lib/features/quiz/presentation/screens/quiz_screen.dart`

## Future Enhancements

1. **Server-Side Sync** (Optional):
   - Store progress on backend
   - Sync across devices
   - Requires API endpoint changes

2. **Progress Analytics**:
   - Track completion rates
   - Identify difficult questions where users pause
   - Measure time spent per question

3. **Better Expiration Policy**:
   - Different expiration for different quiz types
   - Configurable expiration via settings

4. **Progress Notification**:
   - Remind users of incomplete quizzes
   - Show badge count for unfinished quizzes

## Notes

- Auto-save is transparent to users
- No manual save button required
- Progress is persisted across app restarts
- Compatible with existing hearts and gems systems
- Works with hint feature (hints state not saved, but gems deduction persists)

