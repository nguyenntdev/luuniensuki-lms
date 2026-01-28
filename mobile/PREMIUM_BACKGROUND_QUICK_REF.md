# Quick Reference: Premium Animated Background

## 📦 Import
```dart
import 'package:mobile/shared/widgets/backgrounds/modern_gradient_background_animated.dart';
```

## ✨ Basic Usage
```dart
ModernGradientBackgroundAnimated(
  child: YourContent(),
)
```

## 🎨 Custom Configuration
```dart
ModernGradientBackgroundAnimated(
  particleCount: 10,  // Default: 8
  showNoise: true,    // Default: true
  animationDuration: const Duration(seconds: 20),  // Default: 15s
  gradientColors: [
    Color(0xFF1A0A2E),  // Imperial purple
    Color(0xFF16213E),  // Deep blue
    Color(0xFFE8B44C),  // Gold accent
  ],
  child: YourContent(),
)
```

## 🔍 Features
- Aurora-like animated gradient
- 8-12 floating glowing particles
- Subtle noise texture overlay
- Smooth color transitions (15s cycle)
- Performance optimized

## 📍 Used In
- Explore Screen
- Learning Path Screen
- Practice Home Screen
- Achievements Screen
- Profile Screen

## 🎯 Color Palette
- Imperial Purple: `#1A0A2E`
- Deep Blue: `#16213E`
- Gold Accent: `#E8B44C`

## 🚀 What's Next
Test it by running: `flutter run`

