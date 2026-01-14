# Quiz Auto-Save Quick Reference

## 🎯 Quick Overview

Auto-save quiz progress locally so users can resume incomplete quizzes.

## 📁 Key Files

| File | Purpose |
|------|---------|
| `quiz_progress.dart` | Data model for saved progress |
| `hive_storage.dart` | Storage methods for progress |
| `quiz_provider.dart` | State management with auto-save |
| `quiz_screen.dart` | UI integration & resume dialog |

## 🔧 Key Components

### 1. QuizProgress Model
```dart
QuizProgress(
  motifId: String,
  motifName: String,
  currentQuestionIndex: int,
  answers: Map<String, String>,
  incorrectAnswers: Map<String, bool>,
  timeSpentSeconds: int,
  savedAt: DateTime,
  questionsHash: String, // Validation
)
```

### 2. Storage Methods (HiveStorage)
```dart
// Save progress
await storage.saveQuizProgress(motifId, progressData);

// Load progress
final progress = storage.getQuizProgress(motifId);

// Clear progress
await storage.clearQuizProgress(motifId);
```

### 3. State Provider (QuizState)
```dart
// Read state
final state = ref.watch(quizStateProvider(motifId));

// Update state (auto-saves)
ref.read(quizStateProvider(motifId).notifier).setAnswer(questionId, answer);
ref.read(quizStateProvider(motifId).notifier).setQuestionIndex(index);
ref.read(quizStateProvider(motifId).notifier).markIncorrect(questionId);

// Manual control
ref.read(quizStateProvider(motifId).notifier).startFresh(quiz);
ref.read(quizStateProvider(motifId).notifier).resumeProgress();
```

## 🚀 How It Works

### Saving (Automatic)
1. User answers question → `setAnswer()` → Auto-save
2. User navigates → `setQuestionIndex()` → Auto-save
3. Wrong answer → `markIncorrect()` → Auto-save

### Loading (On Quiz Start)
1. Init quiz screen
2. Check for saved progress
3. Validate quiz hasn't changed (hash check)
4. Show resume dialog if valid
5. User chooses: Resume or Start Fresh

### Clearing (On Submit)
1. User submits quiz
2. QuizSubmission.submit() clears progress
3. No saved data remains

## 📋 Resume Dialog Flow

```
User opens quiz
    ↓
Has saved progress? ──No──> Start fresh
    │
   Yes
    ↓
Quiz changed? ──Yes──> Clear & start fresh
    │
    No
    ↓
Show dialog:
  • Question: X
  • Answered: Y câu
  • Time: Z seconds
    ↓
User chooses:
  ├─ Tiếp tục → Resume from saved state
  └─ Bắt đầu lại → Clear & start fresh
```

## 🛡️ Edge Cases

| Case | Handling |
|------|----------|
| Quiz content changed | Hash mismatch → Clear old progress |
| Progress expired (>7 days) | isValid() returns false → Ignored |
| Multiple devices | Local-only, no sync |
| Corrupt data | Try-catch → Ignore → Start fresh |
| App crash | Progress saved → Resume on reopen |

## ✅ Testing Checklist

- [ ] Answer questions, exit, return → See resume dialog
- [ ] Choose "Tiếp tục" → Resume from correct question
- [ ] Choose "Bắt đầu lại" → Clear progress & start Q1
- [ ] Complete quiz → Progress cleared automatically
- [ ] Navigate next/previous → Progress saved
- [ ] Wrong answer → incorrectAnswers saved
- [ ] Wait >7 days → No resume dialog (expired)
- [ ] Backend changes quiz → No resume dialog (hash mismatch)

## 🔑 Storage Key Format

```
quiz_progress_{motifId}
```

Example:
```
quiz_progress_abc-123-def-456
```

## 📊 Saved Data Structure

```json
{
  "motifId": "abc-123",
  "motifName": "Hoa Sen",
  "currentQuestionIndex": 2,
  "answers": {
    "question-1-id": "A",
    "question-2-id": "B"
  },
  "incorrectAnswers": {
    "question-1-id": true
  },
  "timeSpentSeconds": 145,
  "savedAt": "2024-01-15T10:30:00.000Z",
  "questionsHash": "123456789"
}
```

## ⚙️ Configuration

### Expiration Time
Change in `quiz_progress.dart`:
```dart
bool isValid({Duration maxAge = const Duration(days: 7)})
```

### Storage Box Name
Defined in `hive_storage.dart`:
```dart
static const String _quizProgressBox = 'quiz_progress';
```

## 🎨 UI Messages

### Exit Confirmation
```
"Tiến trình làm bài đã được tự động lưu. 
Bạn có thể tiếp tục sau. 
Bạn có chắc chắn muốn thoát?"
```

### Resume Dialog Title
```
"Tiếp tục bài quiz?"
```

### Resume Dialog Content
```
Bạn có bài quiz chưa hoàn thành:
✓ Câu hỏi: 3
✓ Đã trả lời: 2 câu
✓ Thời gian: 2 phút 25 giây

Bạn muốn tiếp tục hay bắt đầu lại?
```

## 🐛 Common Issues

### Issue: Resume dialog not showing
**Check**:
- Progress saved? (`storage.getQuizProgress(motifId)`)
- Progress valid? (`isValid()` check)
- Hash matches? (quiz content unchanged)

### Issue: Progress not saving
**Check**:
- `setAnswer()` called on answer selection?
- `setQuestionIndex()` called on navigation?
- Hive box initialized? (in app startup)

### Issue: Old progress persists after submit
**Check**:
- `clearQuizProgress()` called in submit()?
- Check QuizSubmission provider code

## 📝 Code Snippets

### Check if progress exists
```dart
final storage = ref.read(hiveStorageProvider);
final progress = storage.getQuizProgress(motifId);
if (progress != null) {
  // Has saved progress
}
```

### Manual save (if needed)
```dart
final progress = QuizProgress(
  motifId: motifId,
  motifName: 'Quiz Name',
  currentQuestionIndex: 2,
  answers: {'q1': 'A'},
  incorrectAnswers: {},
  timeSpentSeconds: 60,
  savedAt: DateTime.now(),
  questionsHash: '12345',
);

await storage.saveQuizProgress(motifId, progress.toStorage());
```

### Manual clear
```dart
final storage = ref.read(hiveStorageProvider);
await storage.clearQuizProgress(motifId);
```

## 🔗 Related Features

- **Hearts System**: Incorrect answers tracked & saved
- **Time Tracking**: Accumulated time restored on resume
- **Quiz Submission**: Auto-clears progress
- **Navigation**: Auto-saves on every move

## 📖 Documentation Links

- Full Implementation: `QUIZ_AUTO_SAVE_IMPLEMENTATION.md`
- Visual Guide: `QUIZ_AUTO_SAVE_VISUAL_GUIDE.md`

