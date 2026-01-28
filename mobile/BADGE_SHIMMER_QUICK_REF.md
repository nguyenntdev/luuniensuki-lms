# Badge Shimmer Effects - Quick Reference

## 📦 New Components

### ShimmerWidget
```dart
ShimmerWidget(
  duration: Duration(milliseconds: 2800),
  gradient: LinearGradient(...),  // Optional
  enabled: true,                   // Toggle on/off
  child: YourWidget(),
)
```

### PulsingGlowWidget
```dart
PulsingGlowWidget(
  glowColor: AppColors.primary,
  maxBlurRadius: 12.0,
  minBlurRadius: 4.0,
  duration: Duration(milliseconds: 2500),
  enabled: true,
  child: YourWidget(),
)
```

---

## 🎨 Badge Visual States

### ✅ EARNED Badge
```
┌═══════════════════┐  ← Golden border (2px, 0.6 opacity)
║ ✨ Pulsing Glow   ║  ← Animated glow layer
║  ┌─────────────┐  ║
║  │ [⭐ GOLDEN] │  ║  ← Golden gradient icon
║  └─────────────┘  ║  ← Dual shadow (primary + light)
║   Badge Name      ║  ← Bold white text
║  [✓ Đã nhận]      ║  ← Green success badge with border
└═══════════════════┘
   Glass: 0.15 opacity
   Gradient background
```

### 🔒 LOCKED Badge
```
┌───────────────────┐  ← Thin border (1.5px, 0.1 opacity)
│ →→→ Shimmer →→→   │  ← Diagonal sweep (2.8s)
│  ┌─────────────┐  │
│  │ [🔒 GRAY]   │  │  ← Gray icon (40% opacity)
│  └─────────────┘  │  ← No shadow
│   Badge Name      │  ← Muted text (40% opacity)
│  [🔒 +50 XP]      │  ← Lock icon + XP bonus
└───────────────────┘
   Glass: 0.06 opacity
   No gradient
```

---

## 🔄 Animations

| Animation | Duration | Trigger | Effect |
|-----------|----------|---------|--------|
| **3D Flip** | 800ms | Screen load | Cards flip from 90° to 0° |
| **Shimmer** | 2800ms | Continuous | Diagonal sweep (locked) |
| **Pulse Glow** | 2500ms | Continuous | Breathing glow (earned) |
| **Stagger** | 100ms | Per badge | Delayed entrance |

---

## 📁 File Structure

```
lib/shared/widgets/effects/
├── shimmer_widget.dart       # ShimmerWidget & PulsingGlowWidget
└── index.dart                # Exports

lib/features/achievements/presentation/screens/
└── achievements_screen.dart  # Enhanced badge rendering
```

---

## 🎯 Key Code Patterns

### 3D Flip Animation
```dart
Transform(
  alignment: Alignment.center,
  transform: Matrix4.identity()
    ..setEntry(3, 2, 0.001)      // Perspective
    ..rotateY(rotationAngle),    // Rotation
  child: child,
)
```

### Conditional Effects
```dart
if (isEarned) {
  return PulsingGlowWidget(child: badge);
} else {
  return ShimmerWidget(child: badge);
}
```

### Helper Methods
```dart
_buildBadgeIcon(badge, isEarned)    // Icon with gradient/shadow
_buildBadgeName(badge, isEarned)    // Styled text
_buildBadgeStatus(badge, isEarned)  // Status badge
```

---

## ✨ Visual Specs

### Colors (Earned)
- Border: `AppColors.primary` @ 0.6 opacity
- Icon gradient: `primaryDark → primaryLight`
- Shadow 1: `primary` @ 0.4 opacity, 16px blur
- Shadow 2: `primaryLight` @ 0.3 opacity, 24px blur
- Status: `AppColors.success` @ 0.2 background

### Colors (Locked)
- Border: `white` @ 0.1 opacity
- Icon: `white` @ 0.08 opacity (container), 0.3 (icon)
- Text: `white` @ 0.4 opacity
- Shimmer: `white` 0.0 → 0.12 → 0.0 opacity

### Sizing
- Icon circle: 64×64px
- Icon: 32px
- Border width: 2px (earned), 1.5px (locked)
- Padding: 16px all sides

---

## 🧪 Quick Test

1. **Navigate**: Trophy icon → "Huy Hiệu" tab
2. **Watch**: 3D flip entrance animation
3. **Find locked**: Look for shimmer sweep
4. **Find earned**: Look for pulsing glow
5. **Scroll**: Check performance
6. **Tab switch**: Verify re-animation

---

## 🚀 What's Next?

### Suggested Enhancements
1. Particle effects on badge unlock
2. Haptic feedback on earned badges
3. Sound effects for unlock
4. Progress bars on locked badges
5. Category-specific colors
6. Rarity-based effects

---

## 📞 Usage in Other Screens

### Generic Shimmer
```dart
import 'package:your_app/shared/widgets/effects/shimmer_widget.dart';

ShimmerWidget(
  child: YourLockedContent(),
)
```

### Generic Glow
```dart
import 'package:your_app/shared/widgets/effects/shimmer_widget.dart';

PulsingGlowWidget(
  glowColor: Colors.blue,
  child: YourHighlightedContent(),
)
```

---

## 💡 Tips

- **Performance**: Effects use `AnimatedBuilder` for efficiency
- **Memory**: Controllers properly disposed in `dispose()`
- **Flexibility**: All parameters customizable
- **Hardware**: Transform uses GPU acceleration
- **Compatibility**: Works on Android/iOS

---

**Ready to use!** 🎉

Import from: `lib/shared/widgets/effects/index.dart`

