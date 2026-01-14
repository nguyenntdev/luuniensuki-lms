# Hearts System - Visual Guide

## 🎯 Overview

The Hearts/Energy system adds a Duolingo-like risk-reward mechanic to quizzes. Users must be careful with their answers or they'll run out of hearts and need to wait or refill.

## 📱 UI Components

### 1. Hearts Display in Quiz Header

```
┌─────────────────────────────────────┐
│ ← Trắc nghiệm    ❤❤❤❤♡ 15m   3/10 │
│                   │       │      │  │
│                   │       │      └─ Question counter
│                   │       └──────── Next heart timer
│                   └──────────────── Hearts (4/5)
└─────────────────────────────────────┘
```

**States:**
- Full hearts: `❤❤❤❤❤` (red, no timer)
- Some hearts: `❤❤❤♡♡ 45m` (mixed, shows timer)
- No hearts: `♡♡♡♡♡ 15m` (empty, shows timer)
- Unlimited: `∞` (infinity symbol)

### 2. Compact Hearts Display

```
┌──────────┐
│ ❤ 3      │  - Used in headers
└──────────┘

┌──────────┐
│ ∞        │  - Unlimited/premium
└──────────┘
```

### 3. Heart Lost Animation

```
Animation sequence (1.2s):

Frame 1 (0-0.3s):    ❤ -1     (scale 0 → 1.2, fade in)
Frame 2 (0.3-0.6s):  ❤ -1     (scale 1.2 → 1.0)
Frame 3 (0.6-1.2s):  ❤ -1 ↑   (scale 1.0 → 0.8, slide up, fade out)
```

Visual appearance:
```
┌──────────────────┐
│                  │
│                  │
│   ┌──────────┐   │
│   │ ❤  -1    │   │  Red badge with glow
│   └──────────┘   │
│                  │
│                  │
└──────────────────┘
```

## 📄 Screen Flows

### Quiz Flow with Hearts

```
START QUIZ
    │
    ▼
┌─────────────────┐
│ Has Hearts?     │
└─────────────────┘
    │         │
   Yes        No
    │         │
    ▼         ▼
┌─────┐   ┌──────────────┐
│QUIZ │   │ Refill Screen│
└─────┘   └──────────────┘
    │
    ▼
Answer Question
    │
    ├─ Correct ✓ → Next Question
    │
    └─ Wrong ✗ → Lose 1 Heart ❤
            │
            ▼
        Show Animation
            │
            ▼
        ┌─────────────┐
        │ Has Hearts? │
        └─────────────┘
            │      │
           Yes     No
            │      │
            ▼      ▼
        Continue  Refill
```

### Hearts Refill Screen

```
┌────────────────────────────────────────┐
│ × Hết Tim                              │
├────────────────────────────────────────┤
│                                        │
│            ┌──────┐                    │
│            │  ♡   │  Large empty heart │
│            └──────┘                    │
│                                        │
│      Bạn đã hết tim!                   │
│                                        │
│  ❤❤♡♡♡  Tim tiếp theo trong 25m       │
│                                        │
│  ┌─────────────────────────────────┐  │
│  │ ⏰ Đợi Tim Hồi                  │  │
│  │ Tim tiếp theo trong 25m   [Đợi]│  │
│  └─────────────────────────────────┘  │
│                                        │
│  ┌─────────────────────────────────┐  │
│  │ 💎 Nạp Đầy Tim                  │  │
│  │ Sử dụng 50💎 để nạp đầy [Nạp]  │  │
│  └─────────────────────────────────┘  │
│                                        │
│  ┌─────────────────────────────────┐  │
│  │ 🎓 Chế Độ Luyện Tập             │  │
│  │ Luyện tập để nhận lại [Luyện]  │  │
│  └─────────────────────────────────┘  │
│                                        │
│  ┌─────────────────────────────────┐  │
│  │ ▶ Xem Quảng Cáo                 │  │
│  │ Xem quảng cáo để nhận 1 [Xem]  │  │
│  └─────────────────────────────────┘  │
│                                        │
└────────────────────────────────────────┘
```

## 🎨 Color Scheme

```dart
// Hearts
Filled:  AppColors.error (#C41E3A)
Empty:   AppColors.textSecondary.withOpacity(0.3)

// Timer text
Timer:   AppColors.textSecondary

// Refill options
Wait:    AppColors.info (#3B82F6)
Gems:    AppColors.primary (#E8B44C)
Practice: AppColors.success (#10B981)
Ad:      AppColors.warning (#F59E0B)

// Background
Surface: AppColors.surface (#141921)
Border:  AppColors.border
```

## 🔄 State Transitions

### Heart Count Changes

```
5 ❤❤❤❤❤ → (wrong answer) → 4 ❤❤❤❤♡
4 ❤❤❤❤♡ → (wrong answer) → 3 ❤❤❤♡♡
3 ❤❤❤♡♡ → (wrong answer) → 2 ❤❤♡♡♡
2 ❤❤♡♡♡ → (wrong answer) → 1 ❤♡♡♡♡
1 ❤♡♡♡♡ → (wrong answer) → 0 ♡♡♡♡♡ → BLOCK

0 ♡♡♡♡♡ → (30 min) → 1 ❤♡♡♡♡
1 ❤♡♡♡♡ → (30 min) → 2 ❤❤♡♡♡
...
4 ❤❤❤❤♡ → (30 min) → 5 ❤❤❤❤❤ → STOP TIMER
```

### Timer Display

```
90 minutes → "1h 30m"
60 minutes → "1h 0m"
45 minutes → "45m"
30 minutes → "30m"
15 minutes → "15m"
5 minutes  → "5m"
1 minute   → "1m"
```

## 📊 User Scenarios

### Scenario 1: Careful Student
```
Start:  ❤❤❤❤❤
Q1: ✓  ❤❤❤❤❤
Q2: ✓  ❤❤❤❤❤
Q3: ✓  ❤❤❤❤❤
Q4: ✓  ❤❤❤❤❤
Q5: ✓  ❤❤❤❤❤
Result: Pass with 5 hearts remaining
```

### Scenario 2: Learning Student
```
Start:  ❤❤❤❤❤
Q1: ✗  ❤❤❤❤♡ 🎬 Animation
Q2: ✓  ❤❤❤❤♡
Q3: ✗  ❤❤❤♡♡ 🎬 Animation
Q4: ✓  ❤❤❤♡♡
Q5: ✓  ❤❤❤♡♡
Result: Pass with 3 hearts remaining
```

### Scenario 3: Struggling Student
```
Start:  ❤❤❤❤❤
Q1: ✗  ❤❤❤❤♡ 🎬 Animation
Q2: ✗  ❤❤❤♡♡ 🎬 Animation
Q3: ✗  ❤❤♡♡♡ 🎬 Animation
Q4: ✗  ❤♡♡♡♡ 🎬 Animation
Q5: ✗  ♡♡♡♡♡ 🎬 Animation → 🚫 BLOCKED
       ↓
   Refill Screen
       ↓
   Choose option:
   - Wait 2.5 hours
   - Spend 50 gems
   - Practice mode
   - Watch ad
```

## 💡 Design Principles

1. **Clear Feedback**: Always show current heart count
2. **Forgiving**: Multiple wrong answers on same question = 1 heart
3. **Transparent**: Timer shows exactly when next heart arrives
4. **Multiple Options**: 4 ways to get hearts back
5. **Non-Punishing**: Can always return to home/wait

## 🎯 Gamification Psychology

- **Loss Aversion**: Fear of losing hearts encourages focus
- **Time Pressure**: Auto-refill creates urgency to return
- **Multiple Currencies**: Gems vs Time tradeoff
- **Progress Protection**: Never lose quiz progress
- **Achievement Feel**: Keeping all hearts = mastery

## 📱 Responsive Design

### Phone Portrait
```
Full hearts display in header
Refill screen: Single column cards
```

### Phone Landscape
```
Compact hearts display
Refill screen: Scrollable
```

### Tablet
```
Standard hearts display
Refill screen: Wider cards
```

