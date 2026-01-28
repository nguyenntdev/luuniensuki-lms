# Badge Shimmer Effects - Visual Reference

## 🎨 Badge States Comparison

### EARNED Badge (With Pulsing Glow)
```
Time 0ms:                    Time 1250ms:                Time 2500ms:
┌═══════════════┐           ┌═══════════════┐           ┌═══════════════┐
║ ✨✨✨✨✨✨✨ ║           ║ ✨  Glow  ✨  ║           ║ ✨✨✨✨✨✨✨ ║
║ ✨ [⭐ Golden] ✨          ║ ✨ [⭐ Golden] ✨          ║ ✨ [⭐ Golden] ✨
║ ✨  Badge     ✨          ║ ✨  Badge     ✨          ║ ✨  Badge     ✨
║ ✨ [✓ Đã nhận] ✨         ║ ✨ [✓ Đã nhận] ✨         ║ ✨ [✓ Đã nhận] ✨
║ ✨✨✨✨✨✨✨ ║           ║ ✨  Glow  ✨  ║           ║ ✨✨✨✨✨✨✨ ║
└═══════════════┘           └═══════════════┘           └═══════════════┘
  Max glow (12px)             Min glow (4px)              Max glow (12px)
  └─────────────────────────> Breathing effect <────────────────────────┘
```

**Characteristics**:
- 🎯 Golden border: 2px width, 60% opacity
- 🌟 Icon gradient: primaryDark → primaryLight
- 💫 Dual shadow layers (primary + primaryLight)
- ✨ Pulsing glow: 4px ↔ 12px blur radius
- 🎨 Background gradient: subtle primaryDark/Light
- ✅ Green success badge with border
- 📊 Glass opacity: 0.15

---

### LOCKED Badge (With Shimmer Sweep)
```
Time 0ms:                    Time 1400ms:                Time 2800ms:
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│               │           │  →→→         │           │               →
│  [🔒 Gray]    │           │  [🔒→→Gray]  │           │  [🔒 Gray]   →
│  Badge        │           │  Bad→→ge     │           │  Badge       →
│  [🔒 +50 XP]  │           │  [🔒→→+50 XP]│           │  [🔒 +50 XP] →
│               │           │  →→→         │           │               →
└───────────────┘           └───────────────┘           └───────────────┘
  No shimmer                  Shimmer at center           Shimmer exiting
  └─────────────────────────> Diagonal sweep ────────────────────────────┘
```

**Characteristics**:
- 🔘 Thin border: 1.5px, 10% opacity
- 🌫️ Icon: 40% opacity (dimmed)
- 💨 Text: 40% opacity (muted)
- ✨ Shimmer: 0-12% opacity sweep
- 🔒 Lock icon indicator
- 💎 XP bonus display (+X XP)
- 📊 Glass opacity: 0.06

---

## 🎬 3D Flip Entrance Animation

### Timeline View (Per Badge)
```
Frame 0ms:        Frame 200ms:      Frame 400ms:      Frame 600ms:      Frame 800ms:
    |                 |                 |                 |                 |
    ▌                 ▌                 ▌                ▐▌               ▐█▌
    ▌                ▌▌               ▐▌               ▐██▌             ▐███▌
    ▌               ▌▌▌              ▐█▌              ▐███▌            ▐████▌
    ▌              ▌▌▌▌             ▐██▌             ▐████▌           ▐█████▌
    ▌                 ▌                 ▌                 ▌                 ▌
  90° (side)      67.5°              45°              22.5°             0° (front)
  Invisible      Appearing        Half-rotated      Almost full       Fully visible
```

### Staggered Effect (Multiple Badges)
```
Time:    0ms    100ms   200ms   300ms   400ms   500ms   600ms   700ms   800ms
Badge 1: [Start]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[End]
Badge 2:         [Start]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[End]
Badge 3:                 [Start]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[End]
Badge 4:                         [Start]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[End]
Badge 5:                                 [Start]━━━━━━━━━━━━━━━━━━━━━━━━━━━━[End]
Badge 6:                                         [Start]━━━━━━━━━━━━━━━━━━━━━[End]
         └──────────────> Wave effect (100ms delay per badge) <─────────────────┘
```

---

## 🌈 Color Palette

### Earned Badge Colors
```
Golden Border:     #E8B44C @ 60% ═══════════
Icon Gradient:     #D49B38 → #F5D078 ═══════
Shadow Primary:    #E8B44C @ 40% (16px blur)
Shadow Light:      #F5D078 @ 30% (24px blur)
Background:        #D49B38 @ 8% → #F5D078 @ 4%
Success Badge:     #34D399 @ 20% + border @ 30%
```

### Locked Badge Colors
```
Border:            #FFFFFF @ 10% ───────────
Icon Container:    #FFFFFF @ 8%  ───────────
Icon:              #FFFFFF @ 30% ───────────
Text:              #FFFFFF @ 40% ───────────
Shimmer Peak:      #FFFFFF @ 12% ⟶⟶⟶⟶⟶⟶⟶⟶
```

---

## 📐 Layout Specifications

### Badge Card Dimensions
```
┌─────────────────────────────┐
│  Padding: 16px              │
│  ┌─────────────────────┐   │
│  │  Icon Circle        │   │ ← 64×64px circle
│  │  • Size: 64×64px    │   │   Icon: 32×32px
│  │  • Icon: 32×32px    │   │
│  └─────────────────────┘   │
│         ↕ 12px              │
│  ┌─────────────────────┐   │
│  │  Badge Name         │   │ ← 14px, max 2 lines
│  │  (2 lines max)      │   │
│  └─────────────────────┘   │
│         ↕ 8px               │
│  ┌─────────────────────┐   │
│  │ [Status Badge]      │   │ ← 11px, auto width
│  └─────────────────────┘   │
│  Padding: 16px              │
└─────────────────────────────┘
  Border: 1.5-2px
  Border Radius: from GlassContainer
```

---

## ⚡ Performance Profile

### Animation Performance
```
Component           | CPU Usage | GPU Usage | Memory   | FPS Target
--------------------|-----------|-----------|----------|------------
3D Flip (entrance)  | Low       | High      | ~2MB     | 60fps
Shimmer (continuous)| Low       | Medium    | ~1MB     | 60fps
Glow Pulse         | Very Low  | Medium    | <1MB     | 60fps
Combined (20 cards)| Medium    | High      | ~10MB    | 60fps
```

### Optimization Techniques
- ✅ AnimatedBuilder (efficient rebuilds)
- ✅ Hardware-accelerated transforms (GPU)
- ✅ Conditional rendering (only when visible)
- ✅ Proper controller disposal (no memory leaks)
- ✅ Single ticker per component

---

## 🎯 User Flow Diagram

```
User opens app
     │
     ├─> Taps Trophy Icon (Bottom Nav)
     │        │
     │        ├─> Achievements Screen loads
     │        │        │
     │        │        ├─> AnimationController starts
     │        │        │        │
     │        │        │        ├─> Badges appear with 3D flip
     │        │        │        │        │
     │        │        │        │        ├─> EARNED badges: Start glow pulse
     │        │        │        │        ├─> LOCKED badges: Start shimmer
     │        │        │        │        │
     │        │        │        │        ├─> User scrolls grid
     │        │        │        │        │    (Animations continue)
     │        │        │        │        │
     │        │        │        │        └─> User taps badge
     │        │        │        │                 │
     │        │        │        │                 └─> Badge Detail Sheet opens
     │        │        │        │
     │        │        │        └─> User switches to Leaderboard tab
     │        │        │                 │
     │        │        │                 └─> Returns to Badges tab
     │        │        │                      (Animations restart)
     │        │        │
     │        │        └─> User exits screen
     │        │                 │
     │        │                 └─> AnimationControllers disposed
     │        │
     └─> (Animation lifecycle complete)
```

---

## 🎨 Effect Hierarchy

```
AchievementsScreen
    │
    ├─> _buildBadgeGrid()
    │       │
    │       └─> _buildAnimatedBadgeCard()  [3D Flip Animation]
    │               │
    │               └─> _buildBadgeCard()
    │                       │
    │                       ├─> if (isEarned)
    │                       │       │
    │                       │       └─> PulsingGlowWidget  [Glow Effect]
    │                       │               │
    │                       │               └─> GlassContainer
    │                       │                       │
    │                       │                       ├─> _buildBadgeIcon()
    │                       │                       ├─> _buildBadgeName()
    │                       │                       └─> _buildBadgeStatus()
    │                       │
    │                       └─> else (locked)
    │                               │
    │                               └─> ShimmerWidget  [Shimmer Effect]
    │                                       │
    │                                       └─> GlassContainer
    │                                               │
    │                                               ├─> _buildBadgeIcon()
    │                                               ├─> _buildBadgeName()
    │                                               └─> _buildBadgeStatus()
```

---

**Visual Reference Complete!** 🎨

Use this guide to understand the visual design and animation behavior.

