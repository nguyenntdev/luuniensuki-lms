# Daily Goals Feature - Visual Reference Guide

## 📱 Screen Layouts

### 1. Daily Goal Selection Screen
```
┌─────────────────────────────────────┐
│ ← Mục tiêu hàng ngày               │
├─────────────────────────────────────┤
│                                     │
│  Bạn muốn học bao nhiêu mỗi ngày?  │
│  Đặt mục tiêu giúp bạn duy trì     │
│  động lực học tập                   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🧘 Thoải mái          ✓     │   │ <- Selected
│  │ 5 phút/ngày                 │   │
│  │ [Green border & background] │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🚶 Thường xuyên       ○     │   │
│  │ 10 phút/ngày                │   │
│  │ [Blue tint]                 │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🏃 Nghiêm túc         ○     │   │
│  │ 20 phút/ngày                │   │
│  │ [Orange tint]               │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ⚡ Cao thủ            ○     │   │
│  │ 30 phút/ngày                │   │
│  │ [Red tint]                  │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ℹ️ Bạn có thể thay đổi mục  │   │
│  │   tiêu bất cứ lúc nào       │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 2. Compact Daily Goal Widget (Explore Header)
```
┌─────────────────────────────────────┐
│ Xin chào, Nguyễn!                  │
│                                     │
│ Cửu Đỉnh              [85%]        │
│ Khám phá 9 chiếc đỉnh...           │
│                                     │
│ [Search bar]                        │
│                                     │
│ ┌─────────────────────────────┐    │
│ │ 🚩 15/20 XP                 ▶│    │ <- Daily Goal Widget
│ │ ████████░░░░░░░░░░ (75%)    │    │
│ └─────────────────────────────┘    │
│                                     │
│ [Progress summary card]             │
└─────────────────────────────────────┘
```

**States:**
- **In Progress**: 🚩 flag icon, blue progress bar
- **Completed**: ✅ check icon, green progress bar, "Mục tiêu hoàn thành!"

### 3. Daily Goal Celebration Overlay
```
┌─────────────────────────────────────┐
│         [Semi-transparent]          │
│                                     │
│     ┌───────────────────────┐      │
│     │  [Gradient Background] │      │
│     │                        │      │
│     │        🏆              │      │
│     │   [Trophy Icon]        │      │
│     │                        │      │
│     │   Chúc mừng!          │      │
│     │                        │      │
│     │   Bạn đã hoàn thành   │      │
│     │   mục tiêu hôm nay    │      │
│     │                        │      │
│     │         ✓              │      │
│     │                        │      │
│     └───────────────────────┘      │
│                                     │
│      [Auto-dismiss in 2.5s]        │
└─────────────────────────────────────┘
```

**Animation:**
- Scale: Elastic bounce in (0 → 1)
- Opacity: Fade in (0 → 1)
- Reverse on dismiss

## 🎨 Color Scheme by Goal Level

### Casual (5 XP)
```
Icon: 🧘 Self Improvement
Color: AppColors.success (#4CAF50 - Green)
Mood: Relaxed, easy-going
```

### Regular (10 XP)
```
Icon: 🚶 Walk
Color: AppColors.primary (#2196F3 - Blue)
Mood: Standard, balanced
```

### Serious (20 XP)
```
Icon: 🏃 Run
Color: AppColors.warning (#FF9800 - Orange)
Mood: Committed, focused
```

### Intense (30 XP)
```
Icon: ⚡ Flash
Color: AppColors.error (#F44336 - Red)
Mood: Intense, challenging
```

## 📊 Progress Indicators

### Progress Bar States
```
0% Complete:
░░░░░░░░░░░░░░░░░░░░

25% Complete:
████░░░░░░░░░░░░░░░░

50% Complete:
██████████░░░░░░░░░░

75% Complete:
██████████████░░░░░░

100% Complete:
████████████████████ ✓
```

### XP Display Formats
```
Not Started:  0/20 XP     (20 XP nữa)
In Progress:  15/20 XP    (5 XP nữa)
Completed:    20/20 XP    ✓ Hoàn thành
Exceeded:     25/20 XP    ✓ Hoàn thành
```

## 🔄 State Transitions

### Daily Cycle
```
Day 1 - 09:00
┌────────────────┐
│ 0/20 XP        │
│ ░░░░░░░░ 0%   │
└────────────────┘
    ⬇️ User earns 10 XP

Day 1 - 14:00
┌────────────────┐
│ 10/20 XP       │
│ ████░░░░ 50%   │
└────────────────┘
    ⬇️ User earns 15 XP

Day 1 - 18:00
┌────────────────┐
│ 25/20 XP ✓     │
│ ████████ 100%  │
└────────────────┘
    ⬇️ Midnight reset

Day 2 - 00:00
┌────────────────┐
│ 0/20 XP        │
│ ░░░░░░░░ 0%   │
└────────────────┘
```

## 📱 Navigation Flow

### From Explore Screen
```
Explore Screen
    │
    │ [Tap compact widget]
    ⬇️
Daily Goal Screen
    │
    │ [Select new level]
    ⬇️
Goal Updated
    │
    │ [Back button]
    ⬇️
Explore Screen (Updated)
```

### From Settings Screen
```
Settings Screen
    │
    │ [Tap "Mục tiêu hàng ngày"]
    ⬇️
Daily Goal Screen
    │
    │ [Select new level]
    ⬇️
Goal Updated
    │
    │ [Back button]
    ⬇️
Settings Screen
```

## ⚙️ Settings Integration

### Learning Goals Section
```
┌─────────────────────────────────────┐
│ Mục tiêu học tập                    │
├─────────────────────────────────────┤
│ ┌─────────────────────────────┐    │
│ │ 🚩 Mục tiêu hàng ngày       ▶│    │
│ │ Đặt mục tiêu XP cho mỗi ngày │    │
│ └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

## 🎯 XP Award Integration

### When User Completes Lesson (+50 XP)
```
Before:  10/20 XP (50%)
Award:   +50 XP
After:   60/20 XP (100%) ✓

Triggers:
1. Update daily goal: currentXp = 60
2. Mark as completed: isCompleted = true
3. Show celebration overlay
```

### When User Discovers Motif (+25 XP)
```
Before:  0/5 XP (0%)
Award:   +25 XP
After:   25/5 XP (100%) ✓

Triggers:
1. Update daily goal: currentXp = 25
2. Mark as completed: isCompleted = true
3. Show celebration overlay
```

## 💾 Storage Format

### HiveStorage Key: 'daily_goal'
```json
{
  "level": "serious",
  "currentXp": 15,
  "lastUpdated": "2024-01-15T14:30:00.000Z",
  "isCompleted": false
}
```

### After Completion
```json
{
  "level": "serious",
  "currentXp": 25,
  "lastUpdated": "2024-01-15T18:45:00.000Z",
  "isCompleted": true
}
```

### After Midnight Reset
```json
{
  "level": "serious",
  "currentXp": 0,
  "lastUpdated": "2024-01-16T00:00:00.000Z",
  "isCompleted": false
}
```

## 🌐 Responsive Behavior

### Compact Widget (Width Constraints)
```
Small Screen (< 360px):
┌───────────────────┐
│ 🚩 15/20 XP      ▶│
│ ████░░░░ (75%)    │
└───────────────────┘

Medium Screen (360-600px):
┌─────────────────────────��
│ 🚩 15/20 XP            ▶│
│ ████████░░░░ (75%)      │
└─────────────────────────┘

Large Screen (> 600px):
┌───────────────────────────────┐
│ 🚩 15/20 XP ✓ (5 XP nữa)    ▶│
│ ████████████░░░░ (75%)        │
└───────────────────────────────┘
```

## 🔔 Future: Notification Integration

### Daily Reminder (Planned)
```
📱 Notification (19:00)
─────────────────────
🚩 Mục tiêu hàng ngày
─────────────────────
Bạn đã hoàn thành 75% 
mục tiêu! (15/20 XP)

Học thêm 5 phút nữa để 
hoàn thành nhé! 💪
─────────────────────
[Học ngay]  [Để sau]
```

