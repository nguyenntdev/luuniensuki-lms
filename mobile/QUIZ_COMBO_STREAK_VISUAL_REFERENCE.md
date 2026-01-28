# Quiz Combo Streak - Visual Reference

## Feature Overview
Visual indicator that appears when user achieves 3+ consecutive correct answers in a quiz.

## UI States

### State 1: No Combo (Streak < 3)
```
┌─────────────────────────────────────┐
│ [←] Trắc nghiệm    💎 125  ❤️ 5  1/10│
├─────────────────────────────────────┤
│ ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░       │ ← Progress bar
│                                     │
│  💡 Gợi ý                           │
│  Loại bỏ 2 đáp án sai    [💎 5]    │
│                                     │
│  Câu hỏi 1:                         │
│  Hoa văn này thuộc thời kỳ nào?    │
│                                     │
│  ○ Thời Lý                          │
│  ○ Thời Trần                        │
│  ○ Thời Lê                          │
│  ○ Thời Nguyễn                      │
│                                     │
└─────────────────────────────────────┘
```

### State 2: Combo Active (Streak >= 3)
```
┌─────────────────────────────────────┐
│ [←] Trắc nghiệm    💎 125  ❤️ 5  4/10│
├─────────────────────────────────────┤
│ ▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░         │
│                    ┏━━━━━━━━━┓      │
│                    ┃🔥 5 combo┃  ←── Combo indicator
│                    ┗━━━━━━━━━┛      │
│                                     │
│  💡 Gợi ý                           │
│  Loại bỏ 2 đáp án sai    [💎 5]    │
│                                     │
│  Câu hỏi 4:                         │
│  Họa tiết rồng bay có ý nghĩa gì?  │
│                                     │
│  ○ Quyền lực                        │
│  ● Thần thánh                       │ ← Correct answer
│  ○ Tài lộc                          │
│  ○ May mắn                          │
│                                     │
└─────────────────────────────────────┘
```

## Combo Indicator Details

### Visual Design
```
┌──────────────────┐
│ 🔥 5 combo      │
└──────────────────┘
```

**Components:**
- **Icon**: 🔥 (fire icon - `Icons.local_fire_department`)
- **Count**: Bold white number showing current streak
- **Label**: "combo" text for clarity

**Styling:**
- Background: Orange → Red gradient
- Border radius: 20px (rounded pill shape)
- Padding: 12px horizontal, 6px vertical
- Shadow: Orange glow (blur: 8, spread: 2)
- Text: White, bold

**Position:**
- Top: 20px from top of quiz content
- Right: 16px from right edge
- Z-index: Above quiz content (uses Stack/Positioned)

## Animation

### Appearance (Streak 2 → 3)
```
Before (streak = 2):
┌─────────────────┐
│                 │  ← No indicator
│                 │
│  Question...    │
└─────────────────┘

After (streak = 3):
┌─────────────────┐
│      ┏━━━━━━━┓ │  ← Indicator fades in
│      ┃🔥3 combo┃ │     (300ms animation)
│      ┗━━━━━━━┘ │
│  Question...    │
└─────────────────┘
```

### Update (Streak 3 → 4)
```
┏━━━━━━━┓          ┏━━━━━━━┓
┃🔥3 combo┃   →     ┃🔥4 combo┃  (Smooth transition)
┗━━━━━━━┛          ┗━━━━━━━┛
```

### Disappearance (Wrong Answer)
```
Before (streak = 5, wrong answer):
┌─────────────────┐
│      ┏━━━━━━━┓ │
│      ┃🔥5 combo┃ │
│      ┗━━━━━━━┘ │
└─────────────────┘

After (streak = 0):
┌─────────────────┐
│                 │  ← Indicator disappears
│                 │     (instant)
└─────────────────┘
```

## User Flow Diagram

```
Start Quiz
    │
    ├─→ Answer Correct → Streak = 1 (no indicator)
    │       │
    │       ├─→ Answer Correct → Streak = 2 (no indicator)
    │       │       │
    │       │       ├─→ Answer Correct → Streak = 3 ✨ COMBO SHOWS! ✨
    │       │       │       │
    │       │       │       ├─→ Answer Correct → Streak = 4 (update: 🔥4 combo)
    │       │       │       │       │
    │       │       │       │       ├─→ Answer Wrong → Streak = 0 (indicator disappears)
    │       │       │       │       │       │
    │       │       │       │       │       └─→ Back to start...
    │       │       │       │       │
    │       │       │       │       └─→ Answer Correct → Streak = 5 (update: 🔥5 combo)
    │       │       │       │
    │       │       │       └─→ Answer Wrong → Streak = 0 (indicator disappears)
    │       │       │
    │       │       └─→ Answer Wrong → Streak = 0 (no indicator shown)
    │       │
    │       └─→ Answer Wrong → Streak = 0 (no indicator)
    │
    └─→ Answer Wrong → Streak = 0 (no indicator)
```

## Color Palette

**Combo Indicator:**
- Gradient Start: `Colors.orange` (#FF9800)
- Gradient End: `Colors.red` (#F44336)
- Shadow: `Colors.orange.withOpacity(0.5)`
- Text: `Colors.white` (#FFFFFF)
- Icon: `Colors.white` (#FFFFFF)

## Responsive Behavior

**Position Adjustments:**
- Small screens: Indicator stays in top-right, may overlap slightly (acceptable)
- Large screens: Indicator has ample space
- Landscape: Indicator position maintained

**Z-Index/Layering:**
1. Quiz background (bottom)
2. Quiz content (middle)
3. Combo indicator (top) ← Always visible

## Accessibility

**Visual:**
- High contrast (white on orange/red gradient)
- Bold text for readability
- Clear icon (fire emoji/icon)

**Semantic:**
- Purely decorative/motivational
- No critical information (can be hidden for accessibility if needed)

## File Location
`/mobile/lib/features/quiz/presentation/screens/quiz_screen.dart`

**Key Sections:**
- State variable: Line 42
- Logic: Lines 587-601
- UI: Lines 740-792

