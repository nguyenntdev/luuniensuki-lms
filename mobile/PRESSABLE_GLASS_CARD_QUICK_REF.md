# PressableGlassCard - Quick Reference

## Import
```dart
import 'package:cuudinhky/shared/widgets/glass/index.dart';
```

## Basic Usage
```dart
PressableGlassCard(
  onTap: () {
    print('Card pressed!');
  },
  child: Text('Hello World'),
)
```

## Complete Example
```dart
PressableGlassCard(
  // Callbacks
  onTap: () => print('Tapped'),
  onLongPress: () => print('Long pressed'),
  
  // 3D Effect Control
  enable3DEffect: true,  // Set to false for disabled/locked states
  pressScale: 0.97,      // Scale factor on press (default: 0.97)
  pressDepth: 4.0,       // Translate Y pixels (default: 4.0)
  
  // Styling
  padding: const EdgeInsets.all(16),
  borderRadius: BorderRadius.circular(20),
  backgroundColor: Colors.white,
  opacity: 0.1,
  
  // Gradient (optional)
  gradient: LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Colors.blue.withOpacity(0.15),
      Colors.blue.withOpacity(0.05),
    ],
  ),
  
  // Border (optional)
  border: Border.all(
    color: Colors.white.withOpacity(0.3),
    width: 1.5,
  ),
  
  // Shadows (optional)
  shadows: [
    BoxShadow(
      color: Colors.blue.withOpacity(0.2),
      blurRadius: 16,
      offset: const Offset(0, 6),
    ),
  ],
  
  // Content
  child: YourWidget(),
)
```

## Animation Details

### On Press (TapDown)
- **Scale**: 1.0 → 0.97 (shrinks slightly)
- **Depth**: 0 → +4px Y-axis (moves down)
- **Shadow**: Blur 15 → 5 (reduces shadow)
- **Haptic**: Light impact feedback
- **Duration**: 150ms
- **Curve**: Curves.easeInOut

### On Release (TapUp/TapCancel)
- All animations reverse back to original state
- Same duration and curve

## Common Patterns

### Card with Gradient Background
```dart
PressableGlassCard(
  onTap: onTap,
  gradient: LinearGradient(
    colors: [color.withOpacity(0.15), color.withOpacity(0.05)],
  ),
  child: content,
)
```

### Locked/Disabled Card (No 3D Effect)
```dart
PressableGlassCard(
  onTap: isLocked ? null : onTap,
  enable3DEffect: !isLocked,  // Disable animation for locked state
  child: content,
)
```

### Simple Glass Card
```dart
PressableGlassCard(
  onTap: onTap,
  backgroundColor: Colors.white,
  opacity: 0.08,
  borderRadius: BorderRadius.circular(12),
  padding: const EdgeInsets.all(16),
  child: content,
)
```

## Key Features
✅ Smooth 3D press animation  
✅ Haptic feedback on tap  
✅ Customizable scale and depth  
✅ Optional gradient, border, shadows  
✅ Can be disabled for locked states  
✅ Supports onTap and onLongPress  
✅ Auto-formats and auto-animates  

## When to Use
- Interactive cards that need tactile feedback
- Practice mode cards
- Achievement cards
- Navigation cards
- Any glass-style UI element that responds to touch

## When NOT to Use
- Static informational cards (use GlassContainer instead)
- Buttons (use ElevatedButton or custom button widgets)
- List items with complex gestures (use custom GestureDetector)

## Performance Notes
- Uses SingleTickerProviderStateMixin for efficient animation
- Animations are hardware-accelerated
- Haptic feedback is async and non-blocking
- Minimal rebuild scope (only animates transform and shadow)

