# Profile Menu - Visual Verification Guide

## 🎨 Profile Screen Layout

```
┌─────────────────────────────────────────────────────────────┐
│                     Profile Screen                          │
│                                                             │
│         ╔═════════════════════════════════════╗            │
│         ║          User Avatar (120x120)      ║            │
│         ║        with gradient border         ║            │
│         ╚═════════════════════════════════════╝            │
│                                                             │
│                    John Doe                                 │
│              john.doe@example.com                           │
│                 【 Intermediate 】                          │
│                                                             │
│         ┌─────────────────────────────────┐                │
│         │    ⭐ Experience: 450 XP         │                │
│         │    Progress: ████████░░  75%    │                │
│         └─────────────────────────────────┘                │
│                                                             │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│     │  👁 15   │  │  📚 6    │  │  🏆 0    │             │
│     │ Khám phá │  │  Đã học  │  │ Huy hiệu │             │
│     └──────────┘  └──────────┘  └──────────┘             │
│                                                             │
│         ┌─────────────────────────────────┐                │
│         │  🔥 Current Streak: 3 days      │                │
│         └─────────────────────────────────┘                │
│                                                             │
│              Cài đặt & Tài khoản                           │
│                                                             │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓              │
│  ┃ 👤  Thông tin cá nhân              ▶ ┃ ← 💙 Blue     │
│  ┃     Chỉnh sửa hồ sơ và ảnh đại diện  ┃              │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛              │
│                                                             │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓              │
│  ┃ 🔔  Thông báo                      ▶ ┃ ← 🟡 Amber    │
│  ┃     Quản lý nhắc nhở và thông báo    ┃              │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛              │
│                                                             │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓              │
│  ┃ ⚙️  Cài đặt                        ▶ ┃ ← ⚪ Gray     │
│  ┃     Tùy chỉnh ứng dụng                ┃              │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛              │
│                                                             │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓              │
│  ┃ ❓  Trợ giúp & Hỗ trợ              ▶ ┃ ← 💚 Green    │
│  ┃     Câu hỏi thường gặp và liên hệ    ┃              │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛              │
│                                                             │
│  ┌─────────────────────────────────────┐                  │
│  │  🚪  Đăng xuất                      │ ← 🔴 Red       │
│  └─────────────────────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Menu Card Components

### Card Structure
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                              ┃
┃  ┌────────┐   Title Text (16px bold)    ▶  ┃
┃  │  ICON  │   Subtitle (12px gray)          ┃
┃  └────────┘                                  ┃
┃   48x48px                                    ┃
┃                                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Icon Box Design
```
┌─────────┐
│ Gradient│  ← Color.withOpacity(0.3) to 0.1
│  Border │  ← Color.withOpacity(0.3)
│  Icon   │  ← Themed color
└─────────┘
   48x48
```

---

## 🎯 Color Scheme Visual

```
Personal Info:    ┌─────┐
                  │ 💙  │  AppColors.info (Blue)
                  └─────┘

Notifications:    ┌─────┐
                  │ 🟡  │  AppColors.warning (Amber)
                  └─────┘

Settings:         ┌─────┐
                  │ ⚪  │  AppColors.textSecondary (Gray)
                  └─────┘

Help & Support:   ┌─────┐
                  │ 💚  │  AppColors.success (Green)
                  └─────┘

Logout:           ┌─────┐
                  │ 🔴  │  AppColors.error (Red)
                  └─────┘
```

---

## 📱 Screen Transitions

### Personal Info
```
Profile Screen          Personal Info Screen
┌────────────┐         ┌────────────────────┐
│            │         │  ← Back            │
│  [Tap]     │  ════>  │                    │
│  💙 Info   │         │  Display Name: __  │
│            │         │  Username: ______  │
└────────────┘         │  [Save] [Cancel]   │
                       └────────────────────┘
```

### Notifications
```
Profile Screen          Notifications Screen
┌────────────┐         ┌────────────────────┐
│            │         │  ← Back            │
│  [Tap]     │  ════>  │                    │
│  🟡 Notif  │         │  All | Lessons | 🏆│
│            │         │  ┌──────────────┐  │
└────────────┘         │  │ Notification │  │
                       │  └──────────────┘  │
                       └────────────────────┘
```

### Settings
```
Profile Screen          Settings Screen
┌────────────┐         ┌────────────────────┐
│            │         │  ← Back            │
│  [Tap]     │  ════>  │                    │
│  ⚪ Config │         │  🔔 Notifications  │
│            │         │  🔊 Sound: ON      │
└────────────┘         │  🌐 Language: VI   │
                       └────────────────────┘
```

### Help & Support
```
Profile Screen          Help & Support Screen
┌────────────┐         ┌────────────────────┐
│            │         │  ← Back            │
│  [Tap]     │  ════>  │                    │
│  💚 Help   │         │  FAQ               │
│            │         │  ▼ Question 1      │
└────────────┘         │  ▶ Question 2      │
                       └────────────────────┘
```

---

## ✨ Visual Effects

### Glassmorphism
```
┌─────────────────┐
│ Semi-transparent│  ← opacity: 0.08
│ White overlay   │  ← Colors.white
│ Blurred edges   │  ← borderRadius: 16
│ Border glow     │  ← opacity: 0.2
└─────────────────┘
```

### Animations
```
Card Entrance:
  Opacity: 0.0 → 1.0 (600ms)
  Slide:   Offset(0, 0.3) → Offset.zero

Screen Transition:
  Slide in from right
  Duration: 300ms
  Curve: easeOutCubic
```

---

## 🎬 Interaction States

### Normal State
```
┏━━━━━━━━━━━━━━┓
┃  💙 Menu Item  ┃  ← Normal opacity
┗━━━━━━━━━━━━━━┛
```

### Tap/Hover State
```
┏━━━━━━━━━━━━━━┓
┃  💙 Menu Item  ┃  ← Slight scale down
┗━━━━━━━━━━━━━━┛    ← Increased shadow
```

### Pressed State
```
┏━━━━━━━━━━━━━━┓
┃  💙 Menu Item  ┃  ← Ripple effect
┗━━━━━━━━━━━━━━┛    ← Color overlay
```

---

## 📐 Spacing & Sizing

```
Section Header:      18px, bold, white(0.9)
Card Height:         ~80px
Card Padding:        16px all sides
Icon Size:           24px
Icon Container:      48x48px
Title Font:          16px, w600
Subtitle Font:       12px
Card Gap:            8px (AppSpacing.sm)
Section Gap:         24px (AppSpacing.lg)
```


