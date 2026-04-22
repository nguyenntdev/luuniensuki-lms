# Quiz Hint System Implementation

## Overview
Implemented a comprehensive hint system for the Quiz feature in the Flutter mobile app. Users can spend 5 gems to eliminate 2 incorrect answers in multiple-choice questions.

## Files Created

### 1. HintUsedDialog Widget
**File:** `mobile/lib/features/quiz/presentation/widgets/hint_used_dialog.dart`
- Animated dialog showing gems deducted
- Lightbulb icon with glow effect
- Auto-dismisses after 2 seconds

## Files Modified

### 2. QuestionCard Widget
**File:** `mobile/lib/features/quiz/presentation/widgets/question_card.dart`
- Added `hiddenOptions` parameter for hint system
- Fade-out animation for hidden options

### 3. QuizScreen
**File:** `mobile/lib/features/quiz/presentation/screens/quiz_screen.dart`
- Added gems display in AppBar
- Added hint button for multiple-choice questions
- Integrated with GemsProvider for gem deduction
- Track hints used per question

## Features

### Hint Button
- **Cost:** 5 gems per hint
- **Effect:** Removes 2 random incorrect answers
- **Limit:** Max 1 hint per question
- **Availability:** Only for multiple-choice with 4+ options

### Visual Design
- Glass container style
- Lightbulb icon (yellow=available, gray=used)
- Shows gems cost and status
- Smooth fade-out animations

### Integration
- Uses GemsProvider for transactions
- Records in gems history
- Real-time balance updates
- Error handling for insufficient gems

## UI Layout

### AppBar (Right to Left)
```
[💎 123] [❤️ 5] [3/10]
```

### Hint Button States

**Available:**
```
┌─────────────────────────────────┐
│  💡 Gợi ý              [💎 5]   │
│     Loại bỏ 2 đáp án sai        │
└─────────────────────────────────┘
```

**Used:**
```
┌─────────────────────────────────┐
│  ⚫ Đã sử dụng gợi ý             │
│     2 đáp án sai đã bị loại     │
└─────────────────────────────────┘
```

## Testing Checklist
- [x] Hint button only for multiple-choice
- [x] Deducts 5 gems correctly
- [x] 2 wrong answers hidden
- [x] Correct answer never hidden
- [x] Dialog animation works
- [x] Gems display updates
- [x] One-time use per question
- [x] Error handling


