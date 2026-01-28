# Daily Missions Screen - Visual Reference Guide

## 🎨 Color Coding by Mission Type

### Lesson Missions
```
Background Gradient: Blue (Info)
├─ Top-left: #60A5FA @ 15% opacity
└─ Bottom-right: #60A5FA @ 5% opacity

Icon Color: #60A5FA (AppColors.info)
```

### Quiz Missions  
```
Background Gradient: Purple (Badge)
├─ Top-left: #9C27B0 @ 15% opacity
└─ Bottom-right: #9C27B0 @ 5% opacity

Icon Color: #9C27B0 (AppColors.badgePurple)
```

### Discovery Missions
```
Background Gradient: Green (Success)
├─ Top-left: #34D399 @ 15% opacity
└─ Bottom-right: #34D399 @ 5% opacity

Icon Color: #34D399 (AppColors.success)
```

### Streak Missions
```
Background Gradient: Orange (Streak)
├─ Top-left: #FF6B35 @ 15% opacity
└─ Bottom-right: #FF6B35 @ 5% opacity

Icon Color: #FF6B35 (AppColors.streakOrange)
```

## 🎬 Animation Specifications

### Checkmark Animation
```
Type: TweenAnimationBuilder
Duration: 600ms
Curve: Curves.elasticOut

Properties Animated:
- Scale: 0.0 → 1.0
- Opacity: 0.0 → 1.0

Visual Effect: Bouncy pop-in
```

### Pulsing Overlay (90%+ Progress)
```
Type: AnimationController (repeating)
Duration: 1500ms per cycle
Curve: Curves.easeInOut

Opacity Range: 0.0 → 0.1 → 0.0
Direction: Reverse on complete (continuous)

Visual Effect: Subtle breathing glow
```

### Circular Progress Badge
```
Type: CustomPaint with AnimationController
Duration: 800ms
Curve: Curves.easeOutCubic

Arc Animation: 0° → (progress * 360°)
Gradient: SweepGradient (primary colors)
```

## 📐 Layout Measurements

### Header Card
```
┌─────────────────────────────────────┐
│ Padding: 16px all sides             │
│                                     │
│ ┌──────┐                            │
│ │ 56x56│  Tiến độ hôm nay           │
│ │Badge │  (Gradient Text)           │
│ └──────┘                            │
│                                     │
│ Stats Row (2 items, 16px gap)      │
│ ┌──────────┐  ┌──────────┐        │
│ │Completed │  │ XP Today │        │
│ └──────────┘  └──────────┘        │
│                                     │
│ Progress Bar (12px height)         │
│ ▓▓▓▓▓▓▓▓▓░░░░░░░                  │
└─────────────────────────────────────┘
Border Radius: 20px
```

### Mission Card
```
┌─────────────────────────────────────┐
│ [Type-specific gradient overlay]    │
│ Padding: 12px all sides             │
│                                     │
│ ┌────┐                              │
│ │48x │  Mission Name (Gradient)     │
│ │48  │  Description text            │
│ │Badge                          ✓   │ ← Animated if complete
│ └────┘                              │
│                                     │
│ Progress Bar (8px height)          │
│ ▓▓▓▓▓▓▓▓░░░░                       │
│                                     │
│ 5/10        ⭐ 50 XP (Gradient)    │
└─────────────────────────────────────┘
Border Radius: 16px
```

## 🎯 State Indicators

### Mission Progress States
```
0-49%:   Type-specific color
50-89%:  Warning color (#F59E0B)
90-99%:  Warning + Pulsing effect
100%:    Success color + Checkmark
```

### Visual Hierarchy
```
Priority 1: Completed missions
├─ Gold gradient title
├─ Success green border (2px)
└─ Animated checkmark

Priority 2: Near-completion (90%+)
├─ Pulsing overlay
├─ Warning color
└─ Full progress badge

Priority 3: In-progress
├─ Type-specific gradient
├─ Partial progress badge
└─ Standard border (1px)
```

## 🌈 Gradient Definitions

### XP Gradient (Completed Missions)
```dart
LinearGradient(
  colors: [#FFD700, #D4A200],  // xpGold → xpGoldDark
  begin: Alignment.topCenter,
  end: Alignment.bottomCenter,
)
```

### Primary Gradient (Headers)
```dart
LinearGradient(
  colors: [#F5D078, #E8B44C, #D49B38],  // light → primary → dark
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
)
```

## 💡 Usage Examples

### Standard Mission (In Progress)
- Blue gradient overlay (Lesson type)
- Progress badge at 40%
- Blue icon and accent
- White text title
- 4/10 progress counter

### Near-Complete Mission (92%)
- Orange gradient overlay (Streak type)  
- **Pulsing effect active**
- Warning color indicators
- 23/25 progress counter
- No checkmark yet

### Completed Mission
- Green border highlight
- **Animated checkmark visible**
- Gold gradient on title
- Full progress badge
- Gold XP badge

## 🔧 Technical Notes

- All animations use built-in Flutter curves
- No external animation libraries required
- Animations auto-start on widget build
- Pulsing overlay uses SingleTickerProviderStateMixin
- Checkmark uses TweenAnimationBuilder (no mixin needed)

