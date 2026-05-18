# Streak System - Visual Comparison Guide

## 📊 Before vs After

### BEFORE: Basic Streak Card
```
┌─────────────────────────────────────────┐
│  🔥                                     │
│  7                  Kỷ lục: 14          │
│  ngày                                   │
│  Chuỗi học tập hiện tại                 │
│                                         │
│                    ❄️ 2                 │
│                    Freezes              │
└─────────────────────────────────────────┘
```

### AFTER: Enhanced Duolingo-Style Streak
```
┌─────────────────────────────────────────┐
│  🔥  7 ngày                        ❄️ 2 │
│      Chuỗi hiện tại                     │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Lịch Chuỗi            🔥 7 ngày  │   │
│  │ T2  T3  T4  T5  T6  T7  CN      │   │
│  │ 🔥  🔥  🔥  🔥  🔥  🔥  ⚪      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ⭐ Tuần Hoàn Hảo              +25 💎  │
│     Còn 0 ngày nữa                      │
│                                         │
│  Kỷ lục: 14 ngày 🏆                     │
└─────────────────────────────────────────┘

+
┌─────────────────────────────────────────┐
│  ❄️  Đóng Băng Chuỗi                   │
│      Bảo vệ chuỗi của bạn 1 ngày       │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ✓ Tự động kích hoạt khi bạn     │   │
│  │   bỏ lỡ 1 ngày                  │   │
│  │ ✓ Tối đa 2 đóng băng cùng lúc   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │       💎 Mua (50 Gems)          │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## 🎯 New Features Added

### 1. Calendar Visualization
**Shows Last 7 Days**
```
T2  T3  T4  T5  T6  T7  CN
🔥  🔥  🔥  🔥  🔥  🔥  ⚪

Legend:
🔥 = Active day (completed learning)
❄️ = Freeze-protected day
⚪ = Missed day or future day
```

**Visual Indicators**:
- Orange glow for active days
- Blue glow for frozen days
- White ring for today
- Gray for inactive/future

### 2. Milestone Progress
**Shows Next Achievement**
```
⭐ Tuần Hoàn Hảo              +25 💎
   Còn 0 ngày nữa

🎯 Người Học Chăm Chỉ         +75 💎
   Còn 23 ngày nữa

🏆 Bậc Thầy Kiên Trì          +200 💎
   Còn 93 ngày nữa

👑 Chiến Binh Bất Bại         +500 💎
   Còn 358 ngày nữa
```

### 3. Streak Freeze Purchase
**Easy Gem Purchase**
```
┌──────────────────────────────┐
│ 💎 Current Balance: 150      │
│                              │
│ ❄️ Streak Freeze (50 gems)  │
│    Max 2 at a time           │
│                              │
│ [ Buy Now ]                  │
└──────────────────────────────┘

After Purchase:
┌──────────────────────────────┐
│ ✅ Success!                  │
│ 💎 Balance: 100              │
│ ❄️ Freezes: 1                │
└──────────────────────────────┘
```

### 4. Milestone Celebration
**When Reaching Milestone**
```
                ✨ ✨ ✨
           ✨           ✨
        ✨                 ✨
       ┌─────────────────────┐
       │                     │
       │        👑           │
       │                     │
       │   Chiến Binh Bất    │
       │        Bại          │
       │                     │
       │  Hoàn thành 365     │
       │   ngày liên tiếp!   │
       │                     │
       │  ┌───────────────┐  │
       │  │   💎 +500     │  │
       │  └───────────────┘  │
       │                     │
       │    [ Tiếp tục ]     │
       │                     │
       └─────────────────────┘
        ✨                 ✨
           ✨           ✨
                ✨ ✨ ✨
```

## 🎨 Design Enhancements

### Color Scheme
```
Active Streak:
- Background: Orange gradient (0.2 opacity)
- Border: Orange (0.3 opacity)
- Glow: Orange shadow
- Icon: 🔥 with orange background

Freeze:
- Background: Blue gradient (0.2 opacity)
- Border: Blue (0.3 opacity)
- Icon: ❄️ with blue background

Milestones:
- 7 days: ⭐ Yellow/Gold
- 30 days: 🎯 Purple
- 100 days: 🏆 Gold
- 365 days: 👑 Royal Gold
```

### Layout Structure
```
Profile Screen Layout:
┌─────────────────────────────┐
│  Header                     │
│  ├─ Avatar                  │
│  ├─ Name                    │
│  └─ Email                   │
├─────────────────────────────┤
│  XP Progress Card           │
├─────────────────────────────┤
│  Stats Grid                 │
│  ├─ Total XP                │
│  ├─ Motifs Discovered       │
│  ├─ Lessons Completed       │
│  └─ Quizzes Mastered        │
├─────────────────────────────┤
│  🆕 Streak Display          │ ← NEW!
│  ├─ Current streak          │
│  ├─ 7-day calendar          │
│  ├─ Freeze count            │
│  ├─ Next milestone          │
│  └─ Longest streak          │
├─────────────────────────────┤
│  🆕 Buy Streak Freeze       │ ← NEW!
│  ├─ Feature description     │
│  ├─ Benefits list           │
│  └─ Purchase button         │
├─────────────────────────────┤
│  Settings & Account         │
│  ├─ Personal Info           │
│  ├─ Gems Shop               │
│  ├─ Help Center             │
│  ├─ Notifications           │
│  └─ Logout                  │
└─────────────────────────────┘
```

## 📱 Interaction Flow

### Viewing Streak
```
1. Open App
   └─> Main Screen
       └─> Tap "Profile" tab
           └─> See Streak Display
               └─> Calendar shows activity
                   ├─ Current streak highlighted
                   ├─ Freeze count visible
                   └─> Next milestone shown
```

### Purchasing Freeze
```
1. Profile Screen
   └─> Scroll to "Đóng Băng Chuỗi"
       └─> Check gem balance
           ├─ Enough gems?
           │  └─> Tap "Mua (50 Gems)"
           │      └─> Confirm purchase
           │          └─> Success! Freezes +1
           │              └─> Gems -50
           └─ Not enough?
              └─> See warning message
                  └─> Tap to go Gems Shop
```

### Reaching Milestone
```
1. Complete Daily Activity
   └─> Streak increases
       └─> Milestone reached?
           └─> 🎉 Celebration Modal!
               ├─ Confetti animation
               ├─ Milestone icon
               ├─ Name and description
               ├─ Gem reward
               └─> Auto-dismiss (5s)
                   └─> Gems added to balance
```

## 🔥 Calendar States

### Active Streak Week
```
T2  T3  T4  T5  T6  T7  CN
🔥  🔥  🔥  🔥  🔥  🔥  🔥
Perfect week! 7-day streak maintained
```

### Missed Day (No Freeze)
```
T2  T3  T4  T5  T6  T7  CN
🔥  🔥  ⚪  🔥  🔥  🔥  🔥
Streak broken on T4
```

### Freeze Protected
```
T2  T3  T4  T5  T6  T7  CN
🔥  🔥  ❄️  🔥  🔥  🔥  🔥
T4 missed but protected by freeze
```

### Current Week Progress
```
T2  T3  T4  T5  T6  T7  CN
🔥  🔥  🔥  ⚪  ⚪  ⚪  ⚪
       ↑ Today
3-day streak so far this week
```

## 💎 Gem Economy

### Earning Through Streaks
```
Milestone Rewards:
┌──────┬──────┬──────────┐
│ Days │ Gems │ Name     │
├──────┼──────┼──────────┤
│   7  │  25  │ ⭐       │
│  30  │  75  │ 🎯       │
│ 100  │ 200  │ 🏆       │
│ 365  │ 500  │ 👑       │
└──────┴──────┴──────────┘

Total possible: 800 gems/year
```

### Spending on Protection
```
Streak Freeze Cost:
- 1 Freeze = 50 gems
- Max 2 freezes = 100 gems total
- Auto-applies when missed

ROI Calculation:
- 7-day milestone = 25 gems
- Cost to protect = 50 gems
- Net cost = 25 gems to protect 7+ streaks
```

## 🎯 User Benefits

### Motivation
- Visual progress tracking
- Clear goals (milestones)
- Instant feedback (calendar)
- Protection option (freeze)
- Celebration rewards

### Flexibility
- Buy protection in advance
- Auto-apply when needed
- Multiple freezes available
- Weekend protection possible

### Rewards
- Gems for milestones
- Achievement recognition
- Progress visualization
- Gamification elements

## 📊 Statistics

### What's Tracked
```
Current Streak: Active consecutive days
Longest Streak: Personal best record
Freeze Count: Protection available
Last Active: Most recent activity
Calendar: Last 7 days history
```

### What's Displayed
```
Profile Card:
✓ Current streak with fire icon
✓ 7-day calendar grid
✓ Freeze count badge
✓ Next milestone progress
✓ Longest streak record

Buy Freeze Card:
✓ Feature description
✓ Benefits list
✓ Current gem balance
✓ Purchase button
✓ Warning if insufficient
```

This visual guide shows exactly how the streak system looks and works!

