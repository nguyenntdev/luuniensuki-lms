# Component Structure & Hierarchy

## 🏗️ Application Structure

```
Flutter App
│
├── Core Systems
│   ├── Theme
│   │   └── AppSpacing ✨ NEW
│   │       ├── Base spacing constants (xs, sm, md, lg, xl, xxl)
│   │       ├── Vertical/Horizontal spacing widgets
│   │       ├── Border radius constants
│   │       └── Icon size constants
│   │
│   ├── Colors (defined in code)
│   │   ├── Primary: #D4A84B (Gold)
│   │   ├── Background: #1A1A2E (Dark)
│   │   ├── Success: #4CAF50 (Green)
│   │   ├── Info: #64B5F6 (Blue)
│   │   └── Learning: #81C784 (Green)
│   │
│   └── Typography (standardized)
│       ├── Screen titles: 32px bold
│       ├── Card titles: 17px bold
│       ├── Body text: 15px medium
│       └── Small text: 11-12px
│
├── Screens
│   │
│   ├── Login Screen ✨ ENHANCED
│   │   ├── Gradient Background
│   │   ├── Logo Container (100x100)
│   │   │   └── Glow Effect (multi-layer shadows)
│   │   ├── Title & Subtitle
│   │   ├── Error Message (animated)
│   │   ├── Email Input (glassmorphism)
│   │   ├── Password Input (glassmorphism)
│   │   ├── Forgot Password Link ✨ NEW
│   │   ├── Login Button (enhanced)
│   │   │   └── Loading State (spinner + text)
│   │   └── Register Link
│   │
│   └── Explore Screen ✨ ENHANCED
│       ├── Header Section
│       │   ├── Welcome Message ✨ NEW
│       │   ├── Title & Subtitle
│       │   └── Progress Circle (64x64)
│       │       └── Gradient border
│       ├── Search Bar ✨ NEW (placeholder)
│       ├── Stats Card ✨ ENHANCED
│       │   ├── Gradient Background
│       │   ├── Discovery Stat (blue)
│       │   ├── Learning Stat (green)
│       │   └── Mastery Stat (gold)
│       └── Responsive Grid
│           └── Urn Cards (with stagger animation)
│
└── Components
    │
    └── Urn Card ✨ ENHANCED
        ├── Container (gradient + border)
        │   └── Press Animation (scale 0.95)
        ├── Image Section (60%)
        │   ├── Thumbnail
        │   ├── Gradient Overlay ✨ NEW
        │   ├── Progress Badge (top-right)
        │   │   ├── Gradient (if completed)
        │   │   ├── Shadow
        │   │   └── Check icon (if completed)
        │   └── Demo Badge (top-left, if demo)
        │       ├── Gradient
        │       └── Shadow
        └── Info Section (40%)
            ├── Urn Name
            ├── English Name (if available)
            ├── Progress Bar ✨ ENHANCED
            │   ├── Shine effect
            │   └── Gold gradient
            └── Stats Row
                ├── Discovery Stat (colored bg)
                ├── Learning Stat (colored bg)
                └── Mastery Stat (colored bg)
```

## 🎨 Visual Hierarchy

### Login Screen
```
┌─────────────────────────────────────┐
│  Gradient Background                │
│  ┌───────────────────────────────┐  │
│  │  Logo (100x100)               │  │
│  │  with glow effect             │  │
│  └───────────────────────────────┘  │
│                                     │
│  Lưu Niên Sử Kí (32px bold)         │
│  Đăng nhập để tiếp tục              │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  Error Message (animated)     │  │
│  └───────────────────────────────┘  │
│                                     │
│  Email                              │
│  ┌───────────────────────────────┐  │
│  │  [icon] you@example.com       │  │
│  └───────────────────────────────┘  │
│                                     │
│  Mật khẩu         Quên mật khẩu? ✨  │
│  ┌───────────────────────────────┐  │
│  │  [icon] ••••••••  [eye]       │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │      ĐĂNG NHẬP (56px)         │  │
│  └───────────────────────────────┘  │
│                                     │
│  Chưa có tài khoản? Đăng ký         │
└─────────────────────────────────────┘
```

### Explore Screen
```
┌─────────────────────────────────────┐
│  Animated Background                │
│                                     │
│  Xin chào, User! ✨                  │
│  Cửu Đỉnh (32px)           [64px]  │
│  Khám phá 9 chiếc đỉnh     progress│
│                                     │
│  ┌───────────────────────────────┐  │
│  │ [🔍] Tìm kiếm... [filter] ✨  │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  [👁] 0/9  │  [🎓] 0/9  │  [⭐] 0/9 │  │
│  │  Khám phá │  Học xong │  Thành thạo │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌──────────────┐ ┌──────────────┐  │
│  │  Urn Card 1  │ │  Urn Card 2  │  │
│  │  (stagger 1) │ │  (stagger 2) │  │
│  └──────────────┘ └──────────────┘  │
│  ┌──────────────┐ ┌──────────────┐  │
│  │  Urn Card 3  │ │  Urn Card 4  │  │
│  │  (stagger 3) │ │  (stagger 4) │  │
│  └──────────────┘ └──────────────┘  │
└─────────────────────────────────────┘
```

### Urn Card (Enhanced)
```
┌──────────────────────────┐
│ [DEMO] ✨        [95%] ✨ │
│                          │
│    Urn Thumbnail         │
│    with gradient         │
│    overlay               │
│                          │
├──────────────────────────┤
│  Đỉnh Tuyên Đức          │
│  Tuyen Duc Cauldron      │
│                          │
│  [████████░░] ✨         │
│                          │
│  [👁 0/9] [🎓 0/9] [⭐ 0/9] │
│  (colored backgrounds) ✨ │
└──────────────────────────┘
     ↓ Press Animation
┌──────────────────────────┐
│     (scale to 0.95)      │
└──────────────────────────┘
```

## 🎬 Animation Flow

### Login Screen Entry
```
Time: 0ms
│
├─ 0-800ms: Fade in (opacity 0 → 1)
│  └─ Curve: easeOut
│
└─ 0-600ms: Slide up (offset 0.3 → 0)
   └─ Curve: easeOutCubic
```

### Error Message
```
On Error:
│
├─ 0-300ms: Fade in + Slide down
│  └─ From: offset -0.2
│  └─ To: offset 0
│
On Dismiss:
│
└─ 0-300ms: Fade out + Slide down
```

### Explore Screen Cards
```
Card 1: 400ms delay
Card 2: 500ms delay (+100ms)
Card 3: 600ms delay (+100ms)
Card 4: 700ms delay (+100ms)
...and so on

Each card:
├─ Scale: 0 → 1
└─ Opacity: 0 → 1
   └─ Curve: easeOutCubic
```

### Card Press
```
Press Down:
├─ Scale: 1.0 → 0.95
└─ Duration: 150ms

Release:
├─ Scale: 0.95 → 1.0
└─ Duration: 150ms
```

## 📏 Spacing Map

### Screen Padding
```
Login:    24px horizontal
Explore:  24px all sides
Cards:    16px internal
```

### Vertical Spacing
```
Logo → Title:      32px (xl)
Title → Subtitle:  8px (sm)
Subtitle → Form:   48px (xxl)
Field → Field:     24px (lg)
Field → Button:    24px (lg)
Button → Link:     32px (xl)
```

### Component Spacing
```
Stats Card:
├─ Padding: 24px (lg)
├─ Icon → Value: 4px (xs)
├─ Value → Label: 4px (xs)
└─ Between stats: 16px (divider)

Urn Card:
├─ Badge margin: 8px (sm)
├─ Internal padding: 16px (md)
├─ Name → EN name: 4px (xs)
├─ Progress bar height: 7px
└─ Stats spacing: 4px (xs)
```

## 🎨 Color Usage Map

### Backgrounds
```
Screens:     Gradient (#1A1A2E → #16213E → #0F3460)
Cards:       Gradient (white 12% → 6%)
Inputs:      white 12%
Buttons:     #D4A84B
```

### Borders
```
Cards:       white 15-25%
Inputs:      white 15%
Badges:      white 25% or colored
Focus:       #D4A84B
```

### Text
```
Primary:     white 100%
Secondary:   white 70-80%
Tertiary:    white 40-60%
Button:      #1A1A2E (on gold)
```

### Shadows
```
Cards:       black 20%, blur 20px
Badges:      black 30%, blur 8px
Buttons:     #D4A84B 40%, blur varies
Glow:        #D4A84B 15-40%, blur 30-50px
```

## 📱 Responsive Breakpoints

```
Mobile:    < 600px  → 2 columns
Tablet:    600-900px → 3 columns
Desktop:   > 900px   → 4 columns

Touch targets: minimum 48x48 logical pixels
```

---

✨ = New or Enhanced Component

