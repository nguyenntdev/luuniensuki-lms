# Explore Screen - New Design Visual Guide

## Header Layout (Clean & Modern)

```
╔═══════════════════════════════════════════════════════════════╗
║  HEADER AREA (~120px)                                         ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  Khám Phá                              🔥 7      ┌──────┐     ║
║                                                  │ [C] 3│     ║
║                                                  └──────┘     ║
║                                                   Avatar       ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │  👁️ 45/270     │     📚 32     │     ⭐ 18             │ ║
║  │  Discovered    │    Learned    │    Mastered            │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
╠═══════════════════════════════════════════════════════════════╣
║  CONTENT AREA (Urn Cards Grid)                                ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║    ┌─────────┐  ┌─────────┐  ┌─────────┐                     ║
║    │  URN 1  │  │  URN 2  │  │  URN 3  │                     ║
║    │         │  │         │  │         │                     ║
║    │  [IMG]  │  │  [IMG]  │  │  [IMG]  │                     ║
║    │         │  │         │  │         │                     ║
║    │  Title  │  │  Title  │  │  Title  │                     ║
║    └─────────┘  └─────────┘  └─────────┘                     ║
║                                                                ║
║    ┌─────────┐  ┌─────────┐  ┌─────────┐                     ║
║    │  URN 4  │  │  URN 5  │  │  URN 6  │                     ║
║    │  [IMG]  │  │  [IMG]  │  │  [IMG]  │                     ║
║    │  Title  │  │  Title  │  │  Title  │                     ║
║    └─────────┘  └─────────┘  └─────────┘                     ║
║                                                                ║
║    ┌─────────┐  ┌─────────┐  ┌─────────┐                     ║
║    │  URN 7  │  │  URN 8  │  │  URN 9  │                     ║
║    │  [IMG]  │  │  [IMG]  │  │  [IMG]  │                     ║
║    │  Title  │  │  Title  │  │  Title  │                     ║
║    └─────────┘  └─────────┘  └─────────┘                     ║
║                                                                ║
║                                                                ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

## Component Breakdown

### 1. Title Section (Top Left)
```
Khám Phá
└─ Font: 28px, Bold
└─ Color: White
└─ Letter Spacing: 0.5
└─ Simple, no decorations
```

### 2. Streak Widget (Top Right - 1st)
```
🔥 7
└─ Fire emoji + day count
└─ Existing CompactStreakWidget
└─ Responsive design
└─ Changes color based on streak length
```

### 3. User Avatar (Top Right - 2nd)
```
┌──────────────┐
│  ┌────────┐  │
│  │   [C]  │  │  ← Avatar (44x44)
│  │        │  │
│  └────────┘  │
│      [3] ←───┼─ Level Badge (golden, bottom-right)
└──────────────┘

Avatar Details:
- Size: 44x44px
- Border: 2px white with opacity
- Background: Primary gradient
- Content: Avatar image or initial letter
- Shadow: Subtle glow

Level Badge:
- Position: Bottom-right (-4, -4 offset)
- Background: Gold gradient
- Border: 1.5px white
- Content: Rank level number
- Size: Auto-sized padding
- Font: 10px, bold, white
```

### 4. Compact Stats Bar
```
┌─────────────────────────────────────────────────────┐
│  👁️ 45/270     │     📚 32     │     ⭐ 18        │
│  Discovered    │    Learned    │    Mastered       │
└─────────────────────────────────────────────────────┘

Stats Bar Details:
- Background: Glass morphism (white 10% opacity)
- Border: White 15% opacity, 1px
- Border Radius: Medium (12px)
- Padding: Horizontal medium, Vertical small
- Layout: Row with space evenly

Each Stat:
- Icon: Emoji (16px)
- Value: 15px, bold, white
- Spacing: 6px between icon and value

Dividers:
- Width: 1px
- Height: 20px
- Color: White 20% opacity
```

## Color Palette

```
Primary Colors:
├─ Primary Gold: #D4A84B
├─ Primary Dark: #8B6914
└─ XP Gold: #FFD700

Background:
├─ Glass: rgba(255, 255, 255, 0.1)
└─ Border: rgba(255, 255, 255, 0.15)

Text:
├─ Main: #FFFFFF
└─ Subtle: rgba(255, 255, 255, 0.7)
```

## Spacing System

```
Header Padding:
├─ Top: 16px (AppSpacing.md)
├─ Sides: 20px (AppSpacing.lg)
└─ Bottom: 16px (AppSpacing.md)

Internal Spacing:
├─ Between top row and stats: 16px (AppSpacing.md)
└─ Between streak and avatar: 16px (AppSpacing.md)
```

## Responsive Behavior

```
Mobile (< 600px):
└─ 2 columns of urns
└─ Header stacks nicely
└─ Stats scale down

Tablet (600-900px):
└─ 3 columns of urns
└─ Header has more breathing room

Desktop (> 900px):
└─ 4 columns of urns
└─ Maximum width container
```

