# UrnCard Animated Border Glow - Quick Reference

## 🎯 Overview
Enhanced UrnCard with animated border glow for completed/in-progress urns.

## ✨ Key Features

### 1. Rotating Gradient Border
- **Duration**: 3 seconds per rotation
- **Colors**: 
  - 🟢 Green (`AppColors.success`) for completed urns
  - 🟡 Gold (`AppColors.primary`) for in-progress urns
- **Gradient**: SweepGradient with 5 stops (0.0 → 0.3 → 0.6 → 0.3 → 0.0)

### 2. Subtle Pulse Animation
- **Duration**: 2 seconds (reverse)
- **Scale**: 1.0 → 1.02 → 1.0
- **Shadow**: Intensity pulses with scale

### 3. Enhanced Progress Badge
- **Type**: Circular arc indicator
- **Size**: 40px (compact) / 48px (normal)
- **Shows**: Percentage or check icon when completed

### 4. Animated Progress Bar
- **Transition**: 600ms smooth animation
- **Shine**: Moving left-to-right (150px sweep)
- **Colors**: Dynamic based on completion status

## 🔧 Animation Logic

```dart
// Animations start when:
widget.urn.hasProgress || widget.urn.isCompleted

// Color determination:
if (isCompleted) → AppColors.success
else if (hasProgress) → AppColors.primary
else → Colors.white.withOpacity(0.2)
```

## 📋 Status Detection

```dart
// From Urn entity:
urn.hasProgress    // discoveredCount > 0
urn.isCompleted    // masteredCount >= motifCount
urn.progressPercent // masteredCount / motifCount
```

## 🎨 Visual States

| Status | Border Glow | Pulse | Badge | Progress Bar |
|--------|------------|-------|-------|--------------|
| **No Progress** | White static | None | Static badge | Gray |
| **In Progress** | Gold rotating | Yes | Circular arc | Gold animated |
| **Completed** | Green rotating | Yes | Check icon | Green animated |

## 🛠️ Code Structure

```dart
_UrnCardState
├── _glowController (3s, repeat)
├── _pulseController (2s, reverse)
└── Methods:
    ├── _buildCardWithGlow() → Stack with rotating border
    ├── _buildCardContent() → Card UI
    ├── _buildEnhancedProgressBadge() → Circular progress
    └── _buildProgressBar() → Animated bar

_CircularProgressPainter
└── Custom painter for arc drawing
```

## 🔍 Testing

```bash
# Navigate to Explore screen
# Check:
✓ No animation on 0% progress urns
✓ Gold glow on 1-99% urns
✓ Green glow on 100% urns
✓ Subtle pulse (1.0 → 1.02)
✓ Circular progress badge
✓ Animated progress bar
✓ Moving shine effect
```

## 💡 Performance Notes

- Uses `TickerProviderStateMixin` for multiple controllers
- Animations only run when needed (hasProgress check)
- Efficient use of `AnimatedBuilder` for selective rebuilds
- Controllers properly disposed in `dispose()`

## 🎯 Design Principles

✅ **Subtle & Premium** - Smooth, elegant animations  
✅ **Smart Activation** - Only animates active urns  
✅ **Visual Feedback** - Clear status indication  
✅ **Performance First** - Minimal rebuilds  

## 📝 Developer Notes

- Animation timing: 3s glow + 2s pulse for visual harmony
- Shadow intensity formula: `0.15 + (pulseValue - 1.0) * 0.5`
- Progress arc starts from top: `-π/2` radians
- Gradient stops create smooth fade effect

---

**File**: `lib/features/explore/presentation/widgets/urn_card.dart`  
**LOC**: ~780 lines  
**Dependencies**: dart:math, AppColors, AppSpacing

