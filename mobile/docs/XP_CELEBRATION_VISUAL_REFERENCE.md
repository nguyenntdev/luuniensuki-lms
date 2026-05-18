# XP Celebration System - Visual Reference

## Celebration Animations

### 🌟 Small Celebration (25 XP)
**Duration:** 1.5 seconds
**Use Case:** Discovery, small achievements

```
Animation Timeline:
0.0s ─────────────────────────────────────── 1.5s
     ↓                                        ↓
     
     Scale: 0 → 1.3 → 1.0 (bounce)
     Y-Pos: center → center - 200px
     Opacity: 0 → 1 → 0

Visual:
     
                    ┌──────────────┐
                    │  ⭐ +25 XP   │  ← Golden badge
                    └──────────────┘
                          ↑
                     (slides up)
```

### 🎯 Medium Celebration (50-75 XP)
**Duration:** 2.0 seconds
**Use Case:** Lesson completion, quiz pass

```
Animation Timeline:
0.0s ─────────────────────────────────────── 2.0s
     ↓                                        ↓
     
     Badge: 0 → 1.3 → 1.0 (bounce)
     Particles: radiate outward from center
     Opacity: 1 → 0 (particles fade)

Visual:

           •        •        •
        •              •  •      •
           •  ┌──────────────┐  •
        •     │  ⭐ +50 XP   │     •
           •  └──────────────┘  •
        •          •         •      •
           •        •        •
           
     (15 particles radiating outward)
```

### 🎊 Large Celebration (300+ XP)
**Duration:** 2.5 seconds
**Use Case:** URN exam completion

```
Animation Timeline:
0.0s ─────────────────────────────────────── 2.5s
     ↓                                        ↓
     
     Badge: 0 → 1.3 → 1.0 (bounce)
     Confetti: explosive blast (30 particles)
     Colors: Multi-colored (gold, green, purple, orange)

Visual:

    🎊  *  🎊     *  🎊  *     🎊
  *   🎊     *  🎊    *    🎊   *
      *  🎊  ┌──────────────┐  🎊  *
   🎊    *   │  ⭐ +300 XP  │   *   🎊
      *  🎊  └──────────────┘  🎊  *
  *   🎊     *  🎊    *    🎊   *
    🎊  *  🎊     *  🎊  *     🎊
    
  (Full confetti explosion with gravity)
```

### 🏆 Level Up Celebration
**Duration:** 2.5 seconds + banner
**Trigger:** When rank changes

```
Animation Timeline:
0.0s ─────────────────────────────────────── 2.5s
     ↓                                        ↓
     
     Banner: slides down from top
     Badge: 0 → 1.3 → 1.0 (bounce)
     Confetti: explosive blast (50 particles!)
     Colors: Gold + Green gradient

Visual:

    ╔═══════════════════════════════════╗
    ║     🎖️  THĂNG CẤP!  🎖️            ║  ← Golden banner
    ║                                    ║     (slides down)
    ║        Thư Sinh                    ║
    ║        Cấp độ 3                    ║
    ╚═══════════════════════════════════╝
    
         🎊  *  🎊     *  🎊  *     🎊
       *   🎊     *  🎊    *    🎊   *
           *  🎊  ┌──────────────┐  🎊  *
        🎊    *   │  ⭐ +50 XP   │   *   🎊
           *  🎊  └──────────────┘  🎊  *
       *   🎊     *  🎊    *    🎊   *
         🎊  *  🎊     *  🎊  *     🎊
```

## Color Palette

### Badge Colors
```
Background: Linear Gradient
  - Top:    #FFD700 (xpGold)
  - Bottom: #D4A200 (xpGoldDark)

Shadow: #FFD700 with 60% opacity, 30px blur

Text: White (#FFFFFF)
Icon: ⭐ White
```

### Particle Colors
```
Small:   N/A
Medium:  [#FFD700, #E8B44C, #34D399, #F59E0B]
Large:   [#FFD700, #E8B44C, #34D399, #9C27B0, #00C853, #FF9800]
```

### Level-Up Banner
```
Background: Linear Gradient
  - Top:    #00C853 (levelUpGreen)
  - Bottom: #00A844

Border: White with 30% opacity, 2px
Shadow: #00C853 with 50% opacity, 25px blur

Text: White (#FFFFFF)
Icon: 🎖️ (military_tech)
```

## Animation Curves

### Scale Animation
```
0% ──────► 30%: ease-out (0.0 → 1.3)
30% ─────► 50%: ease-in-out (1.3 → 0.9)
50% ─────► 60%: ease-out (0.9 → 1.0)
60% ─────► 85%: constant (1.0)
85% ────► 100%: ease-in (1.0 → 0.0)
```

### Slide Animation
```
Tween: 100px → -200px (moves up 300px total)
Curve: ease-out-cubic
```

### Fade Animation
```
0% ──────► 70%: opacity 1.0
70% ────► 100%: opacity 1.0 → 0.0 (ease-in)
```

### Banner Slide (Level-Up)
```
20% ─────► 50%: -100px → 0px (ease-out-back)
Provides a "bouncy" entrance effect
```

## Particle Physics

### Medium Particles
```
Count: 15
Speed: 100-150 px/s (random)
Angle: Distributed evenly in circle (2π radians)
Size: 4-8px (random)
Lifetime: 1.5s
Fade: Linear (1.0 → 0.0)
```

### Large Confetti
```
Count: 30 (normal) / 50 (level-up)
Directionality: Explosive (all directions)
Gravity: 0.3
Blast Force: 8-20 (random)
Emission: 0.05 frequency
Colors: 5-6 colors from palette
```

## Responsive Behavior

### Portrait Mode
```
Banner: Full width - 32px margin
Badge: Centered horizontally
Vertical: Top 1/2 of screen
```

### Landscape Mode
```
Banner: Max width 600px, centered
Badge: Centered both axes
Adjusted for wider screens
```

## Performance Notes

- **Hardware Acceleration:** All animations use GPU compositing
- **Frame Rate:** Target 60fps
- **Memory:** <5MB overhead per celebration
- **CPU:** <10% utilization during animation

## Integration Checklist

- [ ] Import celebration service
- [ ] Track old user XP before action
- [ ] Call celebration after XP-earning action
- [ ] Pass old and new XP for level-up detection
- [ ] Test all celebration levels
- [ ] Verify level-up triggers correctly
- [ ] Check performance on low-end devices

