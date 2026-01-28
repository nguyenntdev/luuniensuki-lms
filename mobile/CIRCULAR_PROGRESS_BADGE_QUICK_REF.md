# Circular Progress Badge - Quick Reference

## Import
```dart
import 'package:cuudinhky/shared/widgets/progress/circular_progress_badge.dart';
```

## Basic Usage
```dart
CircularProgressBadge(
  progress: 0.75,           // 75% complete (0.0 to 1.0)
  icon: Icons.terrain,       // Icon to display
)
```

## Full Configuration
```dart
CircularProgressBadge(
  progress: 0.65,                      // Required: Progress value
  icon: Icons.flag,                     // Required: Icon to display
  progressColor: AppColors.success,     // Optional: Progress arc color
  backgroundColor: Colors.white.withOpacity(0.12),  // Optional: Background ring
  size: 48,                             // Optional: Badge diameter
  strokeWidth: 4,                       // Optional: Arc thickness
  animated: true,                       // Optional: Enable animation
  animationDuration: Duration(milliseconds: 800),  // Optional: Animation duration
)
```

## Icon Recommendations
- **Completed**: `Icons.flag`, `Icons.check_circle`, `Icons.stars`
- **In Progress**: `Icons.terrain`, `Icons.landscape`, `Icons.hiking`
- **Locked**: `Icons.lock_outline`, `Icons.lock`, `Icons.lock_clock`

## Color Schemes
```dart
// Success (Completed)
progressColor: AppColors.success

// Primary (In Progress)
progressColor: AppColors.primary

// Muted (Locked)
progressColor: Colors.white54
```

## Progress States
```dart
// Locked (0%)
CircularProgressBadge(progress: 0.0, icon: Icons.lock_outline)

// Partial (any %)
CircularProgressBadge(progress: 0.42, icon: Icons.terrain)

// Complete (100% with glow)
CircularProgressBadge(progress: 1.0, icon: Icons.flag)
```

## Animation Control
```dart
// Animated (default)
CircularProgressBadge(progress: 0.5, icon: Icons.terrain, animated: true)

// Instant (no animation)
CircularProgressBadge(progress: 0.5, icon: Icons.terrain, animated: false)

// Custom duration
CircularProgressBadge(
  progress: 0.5,
  icon: Icons.terrain,
  animationDuration: Duration(milliseconds: 1200),
)
```

## Size Variants
```dart
// Small
CircularProgressBadge(progress: 0.5, icon: Icons.terrain, size: 36, strokeWidth: 3)

// Default
CircularProgressBadge(progress: 0.5, icon: Icons.terrain, size: 48, strokeWidth: 4)

// Large
CircularProgressBadge(progress: 0.5, icon: Icons.terrain, size: 64, strokeWidth: 5)
```

## Features
✅ Animated progress arc (800ms, easeOutCubic)  
✅ Gradient stroke (primary → primaryLight)  
✅ Glow effect at 100%  
✅ Icon in center  
✅ Fully configurable  
✅ Optimized rendering (CustomPainter)

## Integration Example (UrnPathCard)
```dart
Widget _buildSummitBadge(_UrnData urnData) {
  final totalMotifs = urnData.tracks.fold<int>(0, (sum, track) => sum + track.motifsTotal);
  final completedMotifs = urnData.tracks.fold<int>(0, (sum, track) => sum + track.motifsCompleted);
  final progress = totalMotifs > 0 ? completedMotifs / totalMotifs : 0.0;
  
  return CircularProgressBadge(
    progress: urnData.status == _UrnStatus.completed ? 1.0 : progress,
    icon: urnData.status == _UrnStatus.completed ? Icons.flag : Icons.terrain,
    progressColor: _getStatusColor(urnData.status),
  );
}
```

## Performance Tips
- Use `animated: false` for list items (avoid many simultaneous animations)
- CustomPainter ensures hardware-accelerated drawing
- `shouldRepaint` logic prevents unnecessary redraws

## Common Patterns
```dart
// Loading state
CircularProgressBadge(progress: 0.0, icon: Icons.refresh, animated: false)

// Indeterminate progress (use explicit value)
CircularProgressBadge(progress: 0.5, icon: Icons.hourglass_empty)

// Dynamic updates
setState(() {
  _progress += 0.1;  // Widget will re-animate
});
```

## Visual Effects
- **0-99%**: Colored arc with icon
- **100%**: Full circle + radiant glow + white icon

## File Location
`lib/shared/widgets/progress/circular_progress_badge.dart`

