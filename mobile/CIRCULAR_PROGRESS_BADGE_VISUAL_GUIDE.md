# CircularProgressBadge - Visual Reference Guide

## 🎨 Component Overview

```
┌─────────────────────────────────────────┐
│     CircularProgressBadge Widget        │
│                                         │
│         ╭───────────╮                   │
│        ╱  ●●●●●●●●●  ╲                 │
│       │   ●       ●   │                 │
│       │  ●    🏔️    ●  │  ← Icon (center)│
│       │   ●       ●   │                 │
│        ╲  ●●●●●●●●●  ╱                 │
│         ╰───────────╯                   │
│          └─ Progress arc (animated)     │
│                                         │
└─────────────────────────────────────────┘
```

## 📊 Progress States

### 0% - Locked State
```
┌──────────┐
│ ┌──────┐ │
│ │      │ │
│ │  🔒  │ │  Lock icon
│ │      │ │  No progress arc
│ └──────┘ │  Muted colors
└──────────┘
```

### 42% - In Progress
```
┌──────────┐
│ ╭──●●──╮ │
│ │● ⛰️  ●│ │  Mountain icon
│ │●     ●│ │  42% arc (gold gradient)
│ │ ●●●●● │ │  
│ ╰──────╯ │
└──────────┘
```

### 100% - Completed
```
┌──────────┐
│ ┌●●●●●●┐ │
│ │●    ●│ │  Flag icon (white)
│ │● 🚩 ●│ │  Full circle
│ │●    ●│ │  Radiant glow effect
│ └●●●●●●┘ │
└──────────┘
    ↑ Glow halo
```

## 🌈 Color Variations

### Success (Completed Urn)
```dart
progressColor: AppColors.success  // #34D399
```
```
┌──────────┐
│ ╭──●●──╮ │  Green gradient
│ │●  🚩 ●│ │  Emerald glow
│ │●     ●│ │  
│ ╰──●●──╯ │
└──────────┘
```

### Primary (Active Urn)
```dart
progressColor: AppColors.primary  // #E8B44C
```
```
┌──────────┐
│ ╭──●●──╮ │  Gold gradient
│ │●  ⛰️ ●│ │  Warm glow
│ │●     ●│ │  
│ ╰──●●──╯ │
└──────────┘
```

### Muted (Locked Urn)
```dart
progressColor: Colors.white54
```
```
┌──────────┐
│ ┌──────┐ │  Gray/white
│ │  🔒  │ │  No glow
│ └──────┘ │  
└──────────┘
```

## 📏 Size Variants

### Small (36px)
```
┌─────┐
│ ●●● │  Size: 36
│ ● ⛰️ │  Stroke: 3
│ ●●● │  Icon: 16.2px
└─────┘
```

### Default (48px)
```
┌───────┐
│ ●●●●● │  Size: 48
│ ●   ● │  Stroke: 4
│ ●  ⛰️ │  Icon: 21.6px
│ ●   ● │  
│ ●●●●● │
└───────┘
```

### Large (64px)
```
┌──────────┐
│ ●●●●●●●● │  Size: 64
│ ●      ● │  Stroke: 5
│ ●      ● │  Icon: 28.8px
│ ●   ⛰️  ● │
│ ●      ● │
│ ●●●●●●●● │
└──────────┘
```

## 🎬 Animation Sequence

### Initial Mount (800ms)
```
Frame 1 (0ms):      Frame 2 (200ms):    Frame 3 (400ms):
┌──────┐           ┌──────┐           ┌──●───┐
│      │           │ ●    │           │ ● ⛰️  │
│  ⛰️   │  →        │  ⛰️   │  →        │ ●    │
│      │           │      │           │      │
└──────┘           └──────┘           └──────┘

Frame 4 (600ms):    Frame 5 (800ms):
┌──●●──┐           ┌──●●──┐
│●  ⛰️  │           │● ⛰️  ●│
│●     │  →        │●     ●│
│ ●    │           │ ●●●●● │
╰──●───╯           ╰──────╯
```

Easing: `Curves.easeOutCubic` (smooth deceleration)

## 🎨 Gradient Details

### Sweep Gradient (0° to progress angle)
```
Start (top):      Middle:         End (progress):
   Primary          Light            Primary
   #E8B44C         #F5D078          #E8B44C
      ●              ●                 ●
      │              │                 │
      └──────────────┴─────────────────┘
```

Direction: Clockwise from top (-π/2 radians)

## ✨ Glow Effect (100% only)

### Layering
```
Layer 1: Glow halo (background)
   └─ BoxShadow (blur: 16, spread: 2, opacity: 40%)
   
Layer 2: Progress circle (middle)
   └─ Full circular arc with gradient
   
Layer 3: Icon (foreground)
   └─ White color (#FFFFFF)
```

### Visual Effect
```
    ┌─── Spread: 2px
    │  ┌─ Blur: 16px
    │  │
    ╱╱ │ ╲╲
   ╱╱  │  ╲╲
  │    ●●●● │  ← Solid progress ring
  │   ●    ●│
  │   ● 🚩 ●│
  │   ●    ●│
  │    ●●●● │
   ╲╲      ╱╱
    ╲╲    ╱╱
      └─┘
```

## 🔧 Technical Specs

### Canvas Drawing
```
Circle properties:
- Center: (size/2, size/2)
- Radius: (size - strokeWidth) / 2
- Start angle: -π/2 (top)
- Sweep angle: 2π × progress

Paint properties:
- Stroke cap: round
- Style: stroke (not fill)
- Shader: SweepGradient
```

### Widget Tree
```
SizedBox (size × size)
└─ Stack (centered)
   ├─ Container (glow - conditional)
   ├─ AnimatedBuilder
   │  └─ CustomPaint
   │     └─ _CircularProgressPainter
   └─ Icon (center)
```

## 📱 In Context (UrnPathCard)

```
┌─────────────────────────────────┐
│ ┌──●●──┐  Cao Đỉnh           ●│ │
│ │● 🚩 ●│  Cao Dinh     100% │ │
│ │●    ●│                    ▼│ │
│ └──●●──┘  ▓▓▓▓▓▓▓▓▓▓▓▓▓      │ │
│           Progress bar         │ │
└─────────────────────────────────┘
    └─ CircularProgressBadge
```

## 🎯 Use Cases

1. ✅ Urn progress in learning path
2. ✅ Track completion indicator
3. ✅ Motif mastery level
4. ✅ Lesson completion status
5. ✅ Daily goal progress
6. ✅ Achievement milestones
7. ✅ Practice session progress
8. ✅ Course completion badges

---

**File**: `lib/shared/widgets/progress/circular_progress_badge.dart`  
**Lines**: 204  
**Dependencies**: `app_colors.dart`  
**Painter**: Custom (`_CircularProgressPainter`)  
**Animation**: Single ticker provider  

