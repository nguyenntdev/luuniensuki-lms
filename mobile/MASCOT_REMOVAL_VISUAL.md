# Mascot Removal - Visual Reference

## 🎨 Before & After Comparison

### Login Screen

#### BEFORE:
```
┌─────────────────────────────┐
│                             │
│                             │
│        ┌─────────┐          │
│        │         │          │
│        │   🦉    │  ← Duolingo-like owl
│        │         │          │
│        └─────────┘          │
│                             │
│    Lưu Niên Sử Kí         │
│   Đăng nhập để tiếp tục   │
│                             │
│     [Login Form]            │
│                             │
└─────────────────────────────┘
```

#### AFTER:
```
┌─────────────────────────────┐
│                             │
│                             │
│    ╔═══════════════╗        │
│    ║ ╭───────────╮ ║        │
│    ║ │    📚     │ ║  ← Education icon
│    ║ │           │ ║     with golden gradient
│    ║ ╰───────────╯ ║        │
│    ╚═══════════════╝        │
│         (glow)              │
│                             │
│    Lưu Niên Sử Kí         │
│   Đăng nhập để tiếp tục   │
│                             │
│     [Login Form]            │
│                             │
└─────────────────────────────┘
```

### Register Screen

#### BEFORE:
```
┌─────────────────────────────┐
│                             │
│        ┌─────────┐          │
│        │         │          │
│        │   🦉    │  ← Excited owl
│        │         │     expression
│        └─────────┘          │
│                             │
│      Tạo tài khoản         │
│                             │
│   [Registration Form]       │
│                             │
└─────────────────────────────┘
```

#### AFTER:
```
┌─────────────────────────────┐
│                             │
│    ╔═══════════════╗        │
│    ║ ╭───────────╮ ║        │
│    ║ │    📚     │ ║  ← Education icon
│    ║ │           │ ║     with golden gradient
│    ║ ╰───────────╯ ║        │
│    ╚═══════════════╝        │
│         (glow)              │
│                             │
│      Tạo tài khoản         │
│                             │
│   [Registration Form]       │
│                             │
└─────────────────────────────┘
```

## 🎯 Design Elements

### New Logo Container

```
┌────────────────────────────────┐
│  Dimensions: 100×100           │
│  Border Radius: 20px           │
│                                │
│  Background:                   │
│  ┌──────────────────────────┐ │
│  │ Gold Gradient (Top→Bottom)│ │
│  │ • primaryLight  #F5D078   │ │
│  │ • primary       #E8B44C   │ │
│  │ • primaryDark   #D49B38   │ │
│  └──────────────────────────┘ │
│                                │
│  Icon: history_edu             │
│  • Size: 50                    │
│  • Color: White (#FFFFFF)      │
│                                │
│  Shadow:                       │
│  • Color: Gold 30% opacity     │
│  • Blur: 20                    │
│  • Spread: 5                   │
│                                │
└────────────────────────────────┘
```

## 🎨 Color Palette Used

```
┌─────────────────────────────────────────────┐
│ Imperial Gold Gradient                      │
├─────────────────────────────────────────────┤
│ Top     ██████  #F5D078  Champagne Gold     │
│ Middle  ██████  #E8B44C  Primary Gold       │
│ Bottom  ██████  #D49B38  Deep Gold          │
└─────────────────────────────────────────────┘

Icon Color:  ██████  #FFFFFF  White
Shadow:      ██████  #E8B44C30  Gold @ 30%
```

## 📐 Layout Specifications

```
Container
├── Size: 100×100 px
├── Border Radius: 20 px
├── Decoration
│   ├── Gradient: Linear (TopLeft → BottomRight)
│   │   ├── Color 1: #F5D078
│   │   ├── Color 2: #E8B44C
│   │   └── Color 3: #D49B38
│   └── Shadow
│       ├── Color: #E8B44C @ 30% opacity
│       ├── Blur Radius: 20
│       └── Spread: 5
└── Child: Icon
    ├── Type: Icons.history_edu
    ├── Size: 50
    └── Color: #FFFFFF
```

## ✨ Visual Effects

### Shadow & Glow
```
   Outer Glow Effect
  ╔═══════════════════╗
  ║   ╔═══════════╗   ║  ← 20px blur
  ║   ║ Container ║   ║  ← 5px spread
  ║   ╚═══════════╝   ║  ← Gold @ 30%
  ╚═══════════════════╝
```

### Gradient Flow
```
  ╔════════════════╗
  ║ #F5D078 ████   ║  ← Light Gold
  ║ #E8B44C ████   ║  ← Primary Gold
  ║ #D49B38 ████   ║  ← Dark Gold
  ╚════════════════╝
     Top → Bottom
```

## 🎭 Theme Alignment

The new design aligns with the Vietnamese Imperial Heritage theme:

- **Gold Gradient**: Represents imperial prosperity and cultural richness
- **Education Icon**: Symbolizes learning and historical knowledge
- **Rounded Corners**: Softer, more welcoming appearance
- **Premium Shadows**: Adds depth and sophistication

## 📱 Responsive Design

Both screens maintain consistent design across different screen sizes:
- Logo size remains fixed at 100×100
- Spacing adjusts based on AppSpacing constants
- Icon scales appropriately within container

