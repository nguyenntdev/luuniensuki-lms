# Glass Bottom Nav - Animation Flow Guide

## 🎬 Animation Layers

### Layer 1: Floating Pill Indicator (Background)
```
State: Behind navigation items
Position: Dynamically calculated using GlobalKeys
Animation: AnimatedPositioned (350ms, Curves.easeOutCubic)

[Item 1] [Item 2] [Item 3] [Item 4]
         ╭──────╮
         │ PILL │  ← Slides smoothly between items
         ╰──────╯
```

**Properties:**
- Width: 50% of item width
- Gradient: Gold (30% opacity → 15% opacity)
- Shadow: Gold glow (blurRadius: 12px)
- Border radius: 16px

---

### Layer 2: Navigation Items (Foreground)
```
Each item has its own stateful widget with animations:

┌─────────────────────┐
│   Press Animation   │
│   Scale: 1.0→0.95   │  ← On tap down
│   Duration: 150ms   │
└─────────────────────┘
         ↓
┌─────────────────────┐
│   Icon Animation    │
│   Lift: -2px Y      │  ← When selected
│   Scale: 1.05x      │
│   Curve: elasticOut │
└─────────────────────┘
         ↓
┌─────────────────────┐
│  Icon Transition    │
│  Outlined → Filled  │  ← AnimatedSwitcher
│  Duration: 300ms    │
└─────────────────────┘
         ↓
┌─────────────────────┐
│   Text Animation    │
│   Color transition  │  ← AnimatedDefaultTextStyle
│   Weight: normal→bold│
└─────────────────────┘
```

---

## 🎯 Interaction Timeline

### On Tap Down (t=0ms)
```
User touches item
  ↓
1. setState(_isPressed = true)
2. _pressController.forward()
3. Scale: 1.0 → 0.95 (150ms)
```

### On Tap Up (t=150ms)
```
User releases
  ↓
1. setState(_isPressed = false)
2. _pressController.reverse()
3. Scale: 0.95 → 1.0 (150ms)
4. HapticFeedback.lightImpact()
5. widget.onTap() called
```

### On Index Change (t=300ms)
```
Parent updates currentIndex
  ↓
1. didUpdateWidget detects change
2. _updateIndicatorPosition() called
3. Pill slides to new position (350ms)
4. Icon lifts & scales (350ms elasticOut)
5. Icon switches outlined→filled (300ms)
6. Text color & weight change (300ms)
```

---

## 🎨 Visual States

### Unselected Item
```
┌──────────┐
│    🏠    │  ← 24px, gray, outlined
│   Home   │  ← 11px, gray, normal weight
└──────────┘
No background
No lift
Scale: 1.0
```

### Selected Item (Resting)
```
┌──────────┐
│    🏠    │  ← 24px, GOLD, filled, lifted -2px
│   Home   │  ← 11px, GOLD, bold
└──────────┘
Background: Floating pill (behind)
Lift: -2px
Scale: 1.05
```

### Selected Item (Pressed)
```
┌──────────┐
│    🏠    │  ← Scaled down to 0.95
│   Home   │  
└──────────┘
Background: Floating pill + ripple effect
Scale: 0.95 (temporary)
Ripple: Gold 20% opacity spreading
```

---

## 🔄 Component Hierarchy

```
GlassBottomNav (StatefulWidget)
└── _GlassBottomNavState
    └── Container (64px height)
        └── ClipRRect (24px border radius)
            └── BackdropFilter (blur: 10px)
                └── Container (glass background)
                    └── Stack
                        ├── AnimatedPositioned (Pill Indicator)
                        │   └── Container (gradient + glow)
                        │
                        └── Row (Navigation Items)
                            └── _NavItemButton × N
                                └── _NavItemButtonState
                                    └── Material (transparent)
                                        └── InkWell (ripple)
                                            └── AnimatedBuilder (press scale)
                                                └── Container
                                                    └── Column
                                                        ├── Stack (Icon + Badge)
                                                        │   └── AnimatedContainer
                                                        │       └── AnimatedSwitcher
                                                        │           └── Icon
                                                        │
                                                        └── AnimatedDefaultTextStyle
                                                            └── Text
```

---

## ⚡ Performance Optimizations

1. **AnimatedBuilder**: Only rebuilds scale transform, not entire widget tree
2. **GlobalKeys**: Only for position calculation, minimal overhead
3. **const constructors**: Where possible to avoid rebuilds
4. **Single animation controller**: Per item, not global
5. **Post-frame callback**: Initial position calculated after layout

---

## 🎭 Animation Curves Used

| Animation | Duration | Curve | Effect |
|-----------|----------|-------|--------|
| Pill slide | 350ms | easeOutCubic | Smooth deceleration |
| Icon lift & scale | 350ms | elasticOut | Bouncy spring |
| Icon switch | 300ms | linear (ScaleTransition) | Clean swap |
| Text style | 300ms | easeOutCubic | Smooth fade |
| Press down | 150ms | easeInOut | Quick responsive feel |
| Press up | 150ms | easeInOut | Quick bounce back |

---

## 📱 Haptic Feedback

```dart
onTap: () {
  HapticFeedback.lightImpact();  // ← Tactile confirmation
  widget.onTap(index);
}
```

Triggers on tap release (not tap down) for natural feel.

---

## 🎪 Ripple Effect

```dart
InkWell(
  splashColor: Gold @ 20% opacity,
  highlightColor: Gold @ 10% opacity,
  borderRadius: 16px,
  // ... 
)
```

Material Design ripple that emanates from tap point.

