# 👥 Social Features - Visual Guide

## 🎨 Screen Layouts

### Friends Screen

```
┌─────────────────────────────────────────┐
│  ← Bạn Bè                    👤  🔄     │  ← AppBar
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Bạn Bè (3)  │  Lời Mời (1)    │  │  ← Tabs
│  └──────────────────────────────────┘  │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  👤  Lê Văn C         ⋮         │   │
│  │      🌟1500  🔥12  🛡️Cấp 6      │   │  ← Friend Card
│  │      ⬆️ Hơn bạn 500 XP         │   │     (Highest XP)
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  👤  Nguyễn Văn A     ⋮         │   │
│  │      🌟1250  🔥7   🛡️Cấp 5      │   │  ← Friend Card
│  │      ⬆️ Hơn bạn 250 XP         │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  👤  Trần Thị B       ⋮         │   │
│  │      🌟980   🔥3   🛡️Cấp 4      │   │  ← Friend Card
│  │      ⬇️ Kém bạn 20 XP          │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### Friend Requests Tab

```
┌─────────────────────────────────────────┐
│  ← Bạn Bè                    👤  🔄     │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Bạn Bè (3)  │  Lời Mời (1) 🔴 │  │  ← Badge
│  └──────────────────────────────────┘  │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  👤  Phạm Thị D                 │   │
│  │      2 giờ trước        ✓   ✗   │   │  ← Request Card
│  └─────────────────────────────────┘   │     with Accept/Reject
│                                         │
└─────────────────────────────────────────┘
```

### Empty State - No Friends

```
┌─────────────────────────────────────────┐
│  ← Bạn Bè                    👤  🔄     │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Bạn Bè (0)  │  Lời Mời (0)    │  │
│  └──────────────────────────────────┘  │
│                                         │
│           ┌─────────────┐              │
│           │      👥      │              │
│           └─────────────┘              │
│                                         │
│         Chưa có bạn bè                 │
│                                         │
│   Thêm bạn bè để cùng học tập          │
│         và thi đua!                     │
│                                         │
└─────────────────────────────────────────┘
```

### Profile Menu Integration

```
┌─────────────────────────────────────────┐
│  Hồ Sơ                         ⚙️  🔔  │
├─────────────────────────────────────────┤
│  ┌──────────────────┐                  │
│  │   👤 User Name    │                  │
│  │   ⭐ 1000 XP      │                  │
│  └──────────────────┘                  │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  👤  Thông tin cá nhân    ›     │   │
│  │      Chỉnh sửa hồ sơ            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  👥  Bạn bè              ›      │   │  ← NEW!
│  │      Kết nối và thi đua         │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  💎  Cửa Hàng Gems       ›      │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

## 🎨 Component Details

### Friend Card Component

```
┌─────────────────────────────────────────┐
│  ┌──┐                                   │
│  │👤│  Nguyễn Văn A              ⋮      │
│  └──┘                                   │
│       ┌──────┐ ┌──────┐ ┌─────────┐    │
│       │🌟1250│ │🔥 7  │ │🛡️Cấp 5  │    │
│       └──────┘ └──────┘ └─────────┘    │
│       ⬆️ Hơn bạn 250 XP                │
└─────────────────────────────────────────┘

Components:
- Avatar (circular, 56x56)
- Display name (bold, 16px)
- Stat chips (color-coded)
- XP comparison (green=ahead, orange=behind)
- Options menu (⋮)
```

### Friend Request Card

```
┌─────────────────────────────────────────┐
│  ┌──┐                                   │
│  │👤│  Phạm Thị D                       │
│  └──┘  2 giờ trước          ✓     ✗    │
│                                         │
└─────────────────────────────────────────┘

Components:
- Avatar (circular, 48x48)
- Display name (bold, 16px)
- Time ago (gray, 12px)
- Accept button (green circle)
- Reject button (red circle)
```

### Stat Chip Design

```
XP Chip:
┌──────────┐
│ 🌟 1250  │  ← Gold background
└──────────┘

Streak Chip:
┌──────────┐
│ 🔥  7    │  ← Orange background
└──────────┘

Level Chip:
┌──────────┐
│ 🛡️ Cấp 5 │  ← Blue background
└──────────┘
```

## 🎨 Color Palette

### Stat Colors
```
XP:     #FFD700 (AppColors.xpGold)
Streak: #FF6B35 (AppColors.streakOrange)
Level:  #4A90E2 (AppColors.info)
```

### Action Colors
```
Accept:  #10B981 (AppColors.success)
Reject:  #EF4444 (AppColors.error)
Primary: #6366F1 (AppColors.primary)
```

### Status Colors
```
Ahead:   #10B981 (Green)
Behind:  #F59E0B (Orange/Warning)
```

## 📐 Spacing & Sizing

### Card Spacing
```dart
Padding:        16px all around
Card Gap:       12px (AppSpacing.verticalSpaceMD)
Border Radius:  16px
```

### Avatar Sizes
```dart
Friend Card:    56x56 pixels
Request Card:   48x48 pixels
Border Width:   2px
```

### Text Sizes
```dart
Display Name:   16px (bold)
Stats:          12px (bold)
Time Ago:       12px (regular)
XP Comparison:  11px (regular)
```

## 🎭 Interaction States

### Friend Card Options Menu
```
Tap card → (Future: Navigate to friend profile)
Tap ⋮    → Show bottom sheet
  ├─ 🚫 Hủy kết bạn (Red)
  └─ ✕  Hủy (Gray)
```

### Request Actions
```
Tap ✓ → Accept Request
  ├─ Add to friends list
  ├─ Remove from requests
  └─ Show success snackbar

Tap ✗ → Reject Request
  ├─ Remove from requests
  └─ Show info snackbar
```

### Add Friend Flow
```
Tap 👤 → Show Dialog
  ├─ Text input field
  ├─ Search user (TODO)
  └─ Send request button
```

