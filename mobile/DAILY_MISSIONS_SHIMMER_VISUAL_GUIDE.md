# Daily Missions Shimmer - Visual Guide

## 🎬 Animation Flow

```
User Opens Screen
       ↓
State: isLoading = true, summary = null
       ↓
Show _buildShimmerLoading()
       ↓
┌─────────────────────────────────────┐
│  SHIMMER LOADING STATE              │
│                                     │
│  [████████] ← Title shimmer         │
│  [█████] ← Subtitle shimmer         │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Glass Card Shimmer         │   │
│  │  ┌───┐                      │   │
│  │  │[●]│ Progress Badge       │   │
│  │  └───┘                      │   │
│  │                             │   │
│  │  Stats Row:                 │   │
│  │  [███] | [███]              │   │
│  │                             │   │
│  │  [███████████] ← Progress   │   │
│  └─────────────────────────────┘   │
│                                     │
│  [████████] ← Section title         │
│                                     │
│  Mission Card 1                     │
│  ┌─────────────────────────────┐   │
│  │ ┌───┐                       │   │
│  │ │[●]│ [██████████]          │   │
│  │ └───┘ [████]                │   │
│  │                             │   │
│  │ [███████████] ← Progress    │   │
│  │                             │   │
│  │ [██]      [█ XP]            │   │
│  └─────────────────────────────┘   │
│                                     │
│  (3 more identical cards...)        │
└─────────────────────────────────────┘
       ↓
Data Loaded
       ↓
State: isLoading = false, summary = data
       ↓
Show Actual Content
```

## 🎨 Design Specifications

### Header Shimmer
```
┌────────────────┐
│ [████████]     │  Width: 180px, Height: 24px
└────────────────┘
      ↓ 8px gap
┌───────────┐
│ [█████]   │      Width: 120px, Height: 14px
└───────────┘
```

### Summary Card Shimmer
```
┌─────────────────────────────────────────┐
│  Glass Effect Container                 │
│  - Border radius: 20px                  │
│  - Gradient: white 0.12 → 0.06         │
│  - Border: white 0.3, width 1px        │
│  ┌─────────────────────────────────┐   │
│  │ ┌────┐  [████████]              │   │
│  │ │ 56 │  [█████]                 │   │
│  │ │ x  │                          │   │
│  │ │ 56 │  Title & subtitle        │   │
│  │ └────┘                          │   │
│  │                                 │   │
│  │  ┌──────────┐  ┌──────────┐   │   │
│  │  │ [████]   │  │ [████]   │   │   │
│  │  │ [██]     │  │ [██]     │   │   │
│  │  └──────────┘  └──────────┘   │   │
│  │                                 │   │
│  │  [████████████████████]         │   │
│  │  Progress bar: full width x 12  │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Mission Card Shimmer (×4)
```
┌─────────────────────────────────────────┐
│  Glass Effect Container                 │
│  - Border radius: 16px                  │
│  - Gradient: white 0.12 → 0.06         │
│  - Border: white 0.2, width 1px        │
│  ┌─────────────────────────────────┐   │
│  │ ┌────┐                          │   │
│  │ │ 48 │  [████████████████]      │   │
│  │ │ x  │  Title (full width x 16) │   │
│  │ │ 48 │                          │   │
│  │ └────┘  [█████]                 │   │
│  │         Desc (150px x 12)       │   │
│  │                                 │   │
│  │  [████████████████████]         │   │
│  │  Progress (full width x 8)      │   │
│  │                                 │   │
│  │  [████]            [████ XP]    │   │
│  │  Count              Reward      │   │
│  │  60x14              80x24       │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## 📐 Measurements

| Element | Width | Height | Border Radius |
|---------|-------|--------|---------------|
| Header title | 180px | 24px | default (AppSpacing.radiusMD) |
| Header subtitle | 120px | 14px | default |
| Summary card | full | auto | 20px |
| Progress badge | 56px | 56px | 28px (circular) |
| Summary title | 150px | 20px | default |
| Summary subtitle | 100px | 14px | default |
| Stat label | 80px | 12px | default |
| Stat value | 50px | 16px | default |
| Progress bar | full | 12px | 8px |
| Section title | 150px | 20px | default |
| Mission card | full | auto | 16px |
| Mission icon | 48px | 48px | 24px (circular) |
| Mission title | full | 16px | default |
| Mission desc | 150px | 12px | default |
| Mission progress | full | 8px | 8px |
| Progress count | 60px | 14px | default |
| XP reward | 80px | 24px | 12px |

## 🎭 Color Scheme

### Glass Effect (Dark Theme)
```dart
// Container gradient
colors: [
  Colors.white.withOpacity(0.12),  // Top-left
  Colors.white.withOpacity(0.06),  // Bottom-right
]

// Border
color: Colors.white.withOpacity(0.3)  // Summary card
color: Colors.white.withOpacity(0.2)  // Mission cards
```

### Shimmer Animation
```dart
// From ShimmerSkeleton widget
baseColor: AppColors.surface
highlightColor: AppColors.surfaceElevated
```

## 🔄 Component Hierarchy

```
Column (crossAxisAlignment: start)
├── ShimmerSkeleton (header title)
├── SizedBox (8px)
├── ShimmerSkeleton (header subtitle)
├── SizedBox (AppSpacing.lg)
├── Container (summary card)
│   └── Column
│       ├── Row (badge + title)
│       ├── SizedBox (AppSpacing.lg)
│       ├── Row (stats)
│       ├── SizedBox (AppSpacing.md)
│       └── ShimmerSkeleton (progress)
├── SizedBox (AppSpacing.lg)
├── ShimmerSkeleton (section title)
├── SizedBox (AppSpacing.md)
└── List.generate (4 mission cards)
    └── Padding
        └── Container (mission card)
            └── Column
                ├── Row (icon + content)
                ├── SizedBox (AppSpacing.md)
                ├── ShimmerSkeleton (progress)
                ├── SizedBox (AppSpacing.sm)
                └── Row (count + reward)
```

## ✨ Animation Details

The shimmer effect is handled by the `ShimmerSkeleton` widget which uses the `shimmer` package:
- **Base Color:** Dark surface color
- **Highlight Color:** Lighter surface color
- **Duration:** Default shimmer animation speed
- **Direction:** Left to right sweep

## 🎯 Layout Matching

The shimmer layout precisely matches:
1. **Header Card** structure (line 97-180)
2. **Mission Card** structure (line 344-482)
3. **Spacing** using AppSpacing constants
4. **Border radius** matching actual cards
5. **Glass effect** matching app theme

This ensures a seamless transition from loading to loaded state.

