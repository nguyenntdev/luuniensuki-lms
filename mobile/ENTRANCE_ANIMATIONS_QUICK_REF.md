# Entrance Animations - Quick Reference

## 📦 Implementation Overview

**Screens Updated**: Collection + Achievements  
**Animation Type**: Staggered Fade + Slide  
**Duration**: 800ms total, 400ms per item  
**Stagger**: 100ms delay between items  

## 🎨 Visual Effect

```
Before: [invisible, offset down 30%]
   ↓
During: [fading in, sliding up]
   ↓
After:  [fully visible, in position]
```

## 🔧 Key Components

### Collection Screen
```dart
// State class
class _CollectionScreenState extends ConsumerState<CollectionScreen>
    with SingleTickerProviderStateMixin {
  
  late AnimationController _controller;
  
  // Initialize
  _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 800),
  );
  _controller.forward();
  
  // Dispose
  _controller.dispose();
}
```

### Achievements Screen
```dart
// State class
class _AchievementsScreenState extends ConsumerState<AchievementsScreen>
    with SingleTickerProviderStateMixin {
  
  late AnimationController _animationController;
  
  // Initialize
  _animationController = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 800),
  );
  _animationController.forward();
  
  // Dispose
  _animationController.dispose();
}
```

## 🎯 Animation Logic

```dart
Widget _buildAnimatedCard(item, int index) {
  return AnimatedBuilder(
    animation: _controller,
    builder: (context, child) {
      // Calculate stagger delay
      final delay = index * 0.1;
      
      // Create interval animation
      final animation = CurvedAnimation(
        parent: _controller,
        curve: Interval(
          delay.clamp(0.0, 1.0),
          (delay + 0.4).clamp(0.0, 1.0),
          curve: Curves.easeOutCubic,
        ),
      );
      
      // Apply fade and slide
      return FadeTransition(
        opacity: animation,
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0, 0.3),
            end: Offset.zero,
          ).animate(animation),
          child: child,
        ),
      );
    },
    child: _buildCard(item),
  );
}
```

## 📊 Animation Timeline

| Item | Start (ms) | End (ms) | Duration (ms) |
|------|-----------|---------|---------------|
| 0    | 0         | 400     | 400          |
| 1    | 100       | 500     | 400          |
| 2    | 200       | 600     | 400          |
| 3    | 300       | 700     | 400          |
| 4    | 400       | 800     | 400          |
| 5+   | 500+      | 900+    | 400          |

## ✅ Testing Quick Check

1. **Collection**: Navigate → See grid fade+slide in sequence
2. **Achievements**: Navigate → See badges fade+slide in sequence
3. **Performance**: Smooth 60 FPS, no lag
4. **Memory**: No leaks (controllers disposed)

## 📁 Files Modified

```
mobile/lib/features/
├── collection/presentation/screens/
│   └── collection_screen.dart ✏️
└── achievements/presentation/screens/
    └── achievements_screen.dart ✏️
```

## 🚀 Key Features

✨ **Smooth entrance**: Professional, polished feel  
⚡ **Performant**: GPU-accelerated animations  
🎯 **Staggered**: Natural cascading effect  
🔄 **Reusable**: Pattern can be applied to other screens  
♻️ **Clean**: Properly disposed, no memory leaks  

## 🎛️ Customization Options

Change these values to adjust the effect:

```dart
// Duration
duration: const Duration(milliseconds: 800)  // Total time

// Stagger delay
final delay = index * 0.1;  // 100ms between items

// Slide distance
begin: const Offset(0, 0.3),  // 30% down start

// Curve
curve: Curves.easeOutCubic  // Easing function
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Animation not playing | Check controller.forward() is called |
| Memory leak warning | Ensure dispose() calls controller.dispose() |
| Choppy animation | Check device performance, reduce item count test |
| Items appear before animation | Verify AnimatedBuilder wrapping is correct |

## 📚 Related Documentation

- `ENTRANCE_ANIMATIONS_SUMMARY.md` - Detailed implementation notes
- `ENTRANCE_ANIMATIONS_VISUAL_GUIDE.md` - Visual diagrams and flow
- `ENTRANCE_ANIMATIONS_TESTING.md` - Complete testing guide

