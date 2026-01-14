# Quiz Auto-Save Visual Flow

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          QuizScreen                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Init (didChangeDependencies)                              │ │
│  │    └─> _checkForSavedProgress()                            │ │
│  │          ├─> Load quizStateProvider                        │ │
│  │          ├─> Validate quiz hash                            │ │
│  │          └─> Show resume dialog if valid                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  User Actions                                              │ │
│  │    ├─> Answer question                                     │ │
│  │    │     └─> setAnswer() → Auto-save                       │ │
│  │    ├─> Navigate next/previous                              │ │
│  │    │     └─> setQuestionIndex() → Auto-save                │ │
│  │    ├─> Answer incorrectly                                  │ │
│  │    │     └─> markIncorrect() → Auto-save                   │ │
│  │    └─> Submit quiz                                         │ │
│  │          └─> clearProgress() → Clear saved data            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│                     QuizState Provider                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  State Management                                          │ │
│  │    • currentQuestionIndex                                  │ │
│  │    • answers (Map<String, String>)                         │ │
│  │    • incorrectAnswers (Map<String, bool>)                  │ │
│  │    • startTime                                             │ │
│  │    • hasSavedProgress flag                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Auto-Save Trigger                                         │ │
│  │    _autoSave()                                             │ │
│  │      ├─> Create QuizProgress object                        │ │
│  │      ├─> Calculate questionsHash                           │ │
│  │      ├─> Calculate timeSpentSeconds                        │ │
│  │      └─> Save to HiveStorage                               │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

                              ↓

┌─────────────────────────────────────────────────────────────────┐
│                       HiveStorage                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Quiz Progress Box                                         │ │
│  │    Key: "quiz_progress_{motifId}"                          │ │
│  │                                                             │ │
│  │    {                                                        │ │
│  │      "motifId": "abc-123",                                 │ │
│  │      "motifName": "Hoa Sen",                               │ │
│  │      "currentQuestionIndex": 2,                            │ │
│  │      "answers": {                                          │ │
│  │        "q1-id": "A",                                        │ │
│  │        "q2-id": "B"                                         │ │
│  │      },                                                     │ │
│  │      "incorrectAnswers": {                                 │ │
│  │        "q1-id": true                                        │ │
│  │      },                                                     │ │
│  │      "timeSpentSeconds": 145,                              │ │
│  │      "savedAt": "2024-01-15T10:30:00Z",                    │ │
│  │      "questionsHash": "12345678"                           │ │
│  │    }                                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## User Flow Diagram

### Scenario 1: First Time Starting Quiz

```
User Opens Quiz Screen
         │
         ↓
    Init State
         │
         ↓
Check for Saved Progress
         │
         ↓
   No Progress Found
         │
         ↓
Start Fresh Quiz
  (question 0, no answers)
```

### Scenario 2: Resuming Saved Progress

```
User Opens Quiz Screen
         │
         ↓
    Init State
         │
         ↓
Check for Saved Progress
         │
         ↓
  Progress Found ✓
         │
         ↓
 Validate Quiz Hash
         │
    ┌────┴────┐
    │         │
Hash Match   Hash Mismatch
    │         │
    ↓         ↓
Show Resume  Clear Old
   Dialog    Progress
    │         │
    └────┬────┘
         │
    ┌────┴─────┐
    │          │
 Resume     Start Fresh
    │          │
    ↓          ↓
Continue    Clear &
from Q3     Start Q1
```

### Scenario 3: During Quiz (Auto-Save)

```
User Answers Question
         │
         ↓
    setState()
         │
         ↓
quizStateProvider.setAnswer()
         │
         ↓
   _autoSave()
         │
         ├─> Get quiz data
         ├─> Create hash
         ├─> Create QuizProgress object
         └─> HiveStorage.saveQuizProgress()
                  │
                  ↓
            Saved to Disk ✓
```

### Scenario 4: Completing Quiz

```
User Completes All Questions
         │
         ↓
  Press "Nộp bài"
         │
         ↓
quizSubmissionProvider.submit()
         │
         ├─> Submit to API
         │
         ├─> Get result ✓
         │
         └─> HiveStorage.clearQuizProgress()
                  │
                  ↓
          Progress Cleared ✓
                  │
                  ↓
          Show Result Screen
```

## Resume Dialog UI

```
┌─────────────────────────────────────────────────┐
│  🔄  Tiếp tục bài quiz?                         │
├─────────────────────────────────────────────────┤
│                                                  │
│  Bạn có bài quiz chưa hoàn thành:               │
│                                                  │
│  ✓ Câu hỏi: 3                                   │
│  ✓ Đã trả lời: 2 câu                            │
│  ✓ Thời gian: 2 phút 25 giây                    │
│                                                  │
│  Bạn muốn tiếp tục hay bắt đầu lại?             │
│                                                  │
├─────────────────────────────────────────────────┤
│              [Bắt đầu lại]  [Tiếp tục]          │
└─────────────────────────────────────────────────┘
```

## State Transitions

```
┌─────────────────┐
│  Fresh Start    │
│  (No Progress)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   In Progress   │◄────────────┐
│  (Auto-saving)  │             │
└────────┬────────┘             │
         │                      │
         ├─> Answer Question ───┤
         ├─> Navigate ──────────┤
         └─> Exit & Return ─────┘
         │
         ↓
┌─────────────────┐
│    Submitted    │
│  (Cleared)      │
└─────────────────┘
```

## Auto-Save Triggers

| User Action | Triggers Auto-Save | Saved Data |
|-------------|-------------------|------------|
| Select answer | ✓ Yes | answers, currentQuestionIndex |
| Navigate next | ✓ Yes | currentQuestionIndex |
| Navigate previous | ✓ Yes | currentQuestionIndex |
| Wrong answer | ✓ Yes | incorrectAnswers |
| Exit quiz | ✗ No (already saved) | - |
| Submit quiz | ✗ No (clears instead) | - |

## Data Validation Flow

```
Load Saved Progress
         │
         ↓
    Parse JSON
         │
         ↓
  Check savedAt
    │         │
Old?───┤      │───Recent?
    │         │
    ↓         ↓
 Ignore    Validate Hash
              │
         ┌────┴────┐
         │         │
    Hash Match  Hash Mismatch
         │         │
         ↓         ↓
      Valid     Invalid
    (Resume)   (Clear)
```

## Error Handling

```
┌─────────────────────────────────────────────────┐
│  Potential Errors                               │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. Corrupt JSON                                │
│     └─> Try-catch → Ignore → Start Fresh       │
│                                                  │
│  2. Missing Quiz Data                           │
│     └─> whenData() no-op → No resume dialog    │
│                                                  │
│  3. Quiz Changed                                │
│     └─> Hash mismatch → Clear → Start Fresh    │
│                                                  │
│  4. Storage Full                                │
│     └─> Hive handles → Auto-compaction         │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Performance Considerations

- **Auto-save is async**: Uses `Future<void>` to avoid blocking UI
- **Hive is fast**: Local disk I/O, no network delay
- **Minimal overhead**: Only saves when state changes
- **Lazy loading**: Progress loaded only when needed
- **Hash calculation**: O(n) where n = number of questions, typically < 20

## Integration with Existing Features

```
┌─────────────────────────────────────────────────┐
│  Feature Integration                            │
├─────────────────────────────────────────────────┤
│                                                  │
│  Hearts System                                  │
│    • Incorrect answers → Lose heart             │
│    • Tracked in incorrectAnswers map            │
│    • Auto-saved for resume                      │
│                                                  │
│  Gems/Hints (Not Auto-Saved)                    │
│    • Hint usage not persisted                   │
│    • Gems deduction happens on backend          │
│    • User can buy hints again after resume      │
│                                                  │
│  Sound Effects                                  │
│    • Plays on answer selection                  │
│    • Works normally with auto-save              │
│                                                  │
│  Time Tracking                                  │
│    • Accumulated time saved                     │
│    • Restored as time offset on resume          │
│                                                  │
└─────────────────────────────────────────────────┘
```

