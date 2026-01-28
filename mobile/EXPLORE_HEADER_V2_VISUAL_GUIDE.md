# Explore Header V2 - Visual Reference

## Full Layout Preview

```
╔═══════════════════════════════════════════════════════════════════╗
║  EXPLORE HEADER V2                                                ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  GREETING ROW                                                     ║
║  ┌────────────────────────────────────────────────┬────────────┐ ║
║  │ Chào buổi sáng                                 │    ╭───╮   │ ║
║  │ Nguyễn Văn An                                  │   ╱     ╲  │ ║
║  │                                                 │  │   N   │ │ ║
║  │                                                 │   ╲     ╱  │ ║
║  │                                                 │    ╰─[12]╯ │ ║
║  └────────────────────────────────────────────────┴────────────┘ ║
║                                                                   ║
║  STATS DASHBOARD (Glass Morphism)                                ║
║  ┌─────────────────────────────────────────────────────────────┐ ║
║  │  ┌──────────┐   │  ┌──────────┐   │  ┌──────────┐           │ ║
║  │  │   👁     │   │  │   📖     │   │  │   ⭐     │           │ ║
║  │  │  15/45   │   │  │    8     │   │  │    3     │           │ ║
║  │  │ Khám phá │   │  │  Đã học  │   │  │Thành thạo│           │ ║
║  │  └──────────┘   │  └──────────┘   │  └──────────┘           │ ║
║  └─────────────────────────────────────────────────────────────┘ ║
║                                                                   ║
║  ACTION BUTTONS                                                  ║
║  ┌──────────────────────┐   ┌──────────────────────┐            ║
║  │  ▶  Tiếp tục học    │   │ 🏋  Luyện tập        │            ║
║  └──────────────────────┘   └──────────────────────┘            ║
║   (Golden Gradient)           (White Outlined)                   ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

## Avatar Detail (70x70px)

```
    Animated Gradient Ring (Rotating)
         ╭─────────╮
        ╱           ╲
       │   ╭─────╮   │  ← Inner avatar (64x64)
       │   │  N  │   │     with glass border
       │   ╰─────╯   │
        ╲           ╱
         ╰────[12]──╯
              ↑
         Level Badge
     (Golden gradient,
      white border,
      glow shadow)
```

## Stats Card Detail

```
Glass Container with Gradient Background
┌─────────────────────────────────────────────────────────┐
│  Background: LinearGradient(                            │
│    white.withOpacity(0.12) → white.withOpacity(0.05)   │
│  )                                                       │
│  Border: white.withOpacity(0.2), 1.5px                 │
│  Shadow: black.withOpacity(0.2), blur 20, offset (0,10)│
│                                                          │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐      │
│  │ [Icon]   │  │   │ [Icon]   │  │   │ [Icon]   │      │
│  │  Value   │  │   │  Value   │  │   │  Value   │      │
│  │  Label   │  │   │  Label   │  │   │  Label   │      │
│  └──────────┘      └──────────┘      └──────────┘      │
│     ↓ 0ms            ↓ 100ms           ↓ 200ms         │
│  (Staggered entrance animations)                        │
└─────────────────────────────────────────────────────────┘
```

## Button Styles

### Primary Button (Continue)
```
Container with:
┌────────────────────────────────┐
│ Gradient:                       │
│   primary (#E8B44C) ──→        │
│   primaryDark (#D49B38)        │
│                                 │
│ Shadow:                         │
│   color: primary.withOpacity    │
│   blur: 12, offset: (0, 6)     │
│                                 │
│ Content:                        │
│   ▶ icon + "Tiếp tục học"      │
└────────────────────────────────┘
```

### Secondary Button (Practice)
```
Container with:
┌────────────────────────────────┐
│ Border:                         │
│   white.withOpacity(0.4), 1.5px│
│                                 │
│ Background: transparent         │
│                                 │
│ Content:                        │
│   🏋 icon + "Luyện tập"         │
└────────────────────────────────┘
```

## Animation Timeline

```
Time (ms)  │  0    100   200   300   400   500   600   1500
───────────┼────────────────────────────────────────────────────
Avatar     │  ████████████████████████████████████████ (Continuous)
Level Badge│  ████████████████████████████████████████ (Elastic)
Stats Card │  ███████████████████
Stat 1     │  ████████
Stat 2     │       ████████
Stat 3     │            ████████
Button 1   │                  ██████████
Button 2   │                       ███████████
```

## Color Palette Reference

```
Avatar Ring Gradient:
  ┌────────────────────────┐
  │ xpGold (#FFD700)       │ ──┐
  │ primary (#E8B44C)      │   │ Sweep Gradient
  │ xpGold.o(0.3)          │   │ (Rotating 360°)
  │ xpGold (#FFD700)       │ ──┘
  └────────────────────────┘

Level Badge Gradient:
  ┌────────────────────────┐
  │ xpGold → primary       │ Linear Gradient
  └────────────────────────┘

Stats Card:
  ┌────────────────────────┐
  │ white.o(0.12)          │ ──┐
  │        ↓               │   │ Linear Gradient
  │ white.o(0.05)          │ ──┘
  └────────────────────────┘

Primary Button:
  ┌────────────────────────┐
  │ primary (#E8B44C)      │ ──┐
  │        ↓               │   │ Linear Gradient
  │ primaryDark (#D49B38)  │ ──┘
  └────────────────────────┘
```

## Responsive Behavior

```
┌─────────────────────────────────────┐
│  Padding: 16px all sides            │
│  ┌───────────────────────────────┐  │
│  │ Greeting Row                  │  │
│  │  - Name: Flexible, ellipsis   │  │
│  │  - Avatar: Fixed 70x70        │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ Stats Card: width: double.∞   │  │
│  │  - 3 columns: spaceAround     │  │
│  └───────────────────────────────┘  │
│  ┌─────────────┐ ┌──────────────┐  │
│  │ Button 1    │ │ Button 2     │  │
│  │ (Expanded)  │ │ (Expanded)   │  │
│  └─────────────┘ └──────────────┘  │
│        ↑ gap: 8px ↑                 │
└─────────────────────────────────────┘
```

