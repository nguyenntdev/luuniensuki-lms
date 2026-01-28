# UrnCard Animated Glow - Visual Testing Guide

## 🎬 Animation Showcase

### Scenario 1: Urn with 0% Progress
```
┌─────────────────────────┐
│  📦 Urn Name           │
│  (English Name)         │
│                         │
│  ▓░░░░░░░░░░░░ 0%      │  ← Gray bar, no animation
│  👁 0/10  📚 0/10  ⭐ 0/10 │
└─────────────────────────┘
       ▲
       └─ Static white border
       No pulse, no glow
```

### Scenario 2: Urn with 30% Progress (In Progress)
```
┌━━━━━━━━━━━━━━━━━━━━━━━━┐  ← 🟡 Rotating gold gradient
│  📦 Urn Name         ⭕30%│  ← Circular progress badge
│  (English Name)         │
│                         │
│  ▓▓▓▓▓▓░░░░░░░ 30%     │  ← Gold bar + shine ✨
│  👁 5/10  📚 3/10  ⭐ 3/10 │
└━━━━━━━━━━━━━━━━━━━━━━━━┘
    ▲                    ▲
    └─ Subtle pulse      └─ Animated arc
       (1.0 → 1.02)
```

### Scenario 3: Urn with 100% Completion
```
┌━━━━━━━━━━━━━━━━━━━━━━━━┐  ← 🟢 Rotating green gradient
│  📦 Urn Name         ⭕✓│  ← Check icon in badge
│  (English Name)         │
│                         │
│  ▓▓▓▓▓▓▓▓▓▓▓▓ 100%     │  ← Green bar + shine ✨
│  👁10/10  📚10/10  ⭐10/10│
└━━━━━━━━━━━━━━━━━━━━━━━━┘
    ▲                    ▲
    └─ Subtle pulse      └─ Complete arc
       (1.0 → 1.02)
```

## 🎨 Animation Timeline

### Rotating Border (3 seconds)
```
0s    0.75s  1.5s   2.25s  3s
│      │      │      │      │
┌─     ─┐     ─      ─     ─┐
│       │  →  │   →  │  →  │
└─     ─┘     ─      ─     ─┘
Glow starts at top, rotates clockwise 360°
```

### Pulse Animation (2 seconds)
```
0s         0.5s       1s         1.5s       2s
│           │          │           │          │
1.00    →  1.01   →   1.02    →   1.01   →  1.00
Scale up                          Scale down
```

### Progress Bar Shine (3 seconds)
```
0s                    1.5s                  3s
│──────────────────────│──────────────────────│
[░░░░░░░░░░░░░░░░░░░░]
 ✨→                    →                    →✨
Shine sweeps from left to right
```

## 🔍 Visual Inspection Checklist

### Border Glow
- [ ] No glow on urns with 0% progress
- [ ] Gold glow visible on in-progress urns
- [ ] Green glow visible on completed urns
- [ ] Rotation is smooth (3 seconds per cycle)
- [ ] Gradient fades smoothly (0.0 → 0.3 → 0.6 → 0.3 → 0.0)

### Pulse Effect
- [ ] Scale pulses from 1.0 to 1.02
- [ ] Pulse is subtle and smooth
- [ ] Shadow intensity pulses with scale
- [ ] No pulse on urns with 0% progress

### Progress Badge
- [ ] Static badge for 0% progress
- [ ] Circular arc for 1-99% progress
- [ ] Check icon for 100% completion
- [ ] Arc starts from top (12 o'clock)
- [ ] Arc fills clockwise

### Progress Bar
- [ ] Gray background for empty progress
- [ ] Gold fill for in-progress urns
- [ ] Green fill for completed urns
- [ ] Shine effect moves left to right
- [ ] Smooth 600ms transition on progress change

## 🎯 Color Verification

### Primary Colors
- **AppColors.primary**: `#E8B44C` (Warmer gold)
- **AppColors.success**: `#34D399` (Teal-green)

### Opacity Levels
- Border glow: 0.0 → 0.3 → 0.6 → 0.3 → 0.0
- Shadow intensity: 0.15 (base) + pulse variation
- Shine effect: 0.4 (white overlay)

## 📱 Test on Different Screen Sizes

### Compact Mode (< 160px width)
- Badge size: 40px
- Font size: 11px (badge), 15px (title)

### Normal Mode (≥ 160px width)
- Badge size: 48px
- Font size: 13px (badge), 17px (title)

## 🚀 Performance Check

- [ ] Smooth 60fps animation
- [ ] No jank or stuttering
- [ ] Multiple urns animate independently
- [ ] Memory usage stable
- [ ] Battery impact minimal

## 🐛 Edge Cases

- [ ] Progress exactly 0%
- [ ] Progress exactly 100%
- [ ] Progress 0.1% (very small)
- [ ] Progress 99.9% (almost complete)
- [ ] Rapid progress changes
- [ ] Multiple urns on screen (grid view)

---

**Test Environment**: Physical device preferred  
**Frame Rate**: Monitor with DevTools  
**Duration**: Test for 30+ seconds per scenario

