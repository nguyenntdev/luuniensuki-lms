# UI/UX Quick Reference Guide

## Color Palette

### Primary Colors
- **Gold Accent:** `#D4A84B` - Primary actions, highlights, progress
- **Gold Light:** `#E8C87E` - Gradient endings, shine effects
- **Dark Background:** `#1A1A2E` - Main background, text on gold
- **Dark Secondary:** `#16213E` - Gradient backgrounds
- **Dark Tertiary:** `#0F3460` - Additional gradient color

### Status Colors
- **Success/Completed:** `#4CAF50`, `#66BB6A` - Completed items
- **Info/Discovered:** `#64B5F6` - Discovery status
- **Learning:** `#81C784` - Learning progress
- **Mastery:** `#D4A84B` - Mastered items

### Glass Colors
- **Overlay Light:** `Colors.white.withOpacity(0.12)`
- **Overlay Medium:** `Colors.white.withOpacity(0.08)`
- **Overlay Dark:** `Colors.white.withOpacity(0.04)`
- **Border:** `Colors.white.withOpacity(0.15-0.25)`

## Spacing System

```dart
import '../../../../core/theme/app_spacing.dart';

// Usage examples:
AppSpacing.xs    // 4.0
AppSpacing.sm    // 8.0
AppSpacing.md    // 16.0
AppSpacing.lg    // 24.0
AppSpacing.xl    // 32.0
AppSpacing.xxl   // 48.0

// Vertical spacing
AppSpacing.verticalSpaceSM
AppSpacing.verticalSpaceMD
AppSpacing.verticalSpaceLG

// Horizontal spacing
AppSpacing.horizontalSpaceMD

// Border radius
AppSpacing.radiusMD   // 12.0
AppSpacing.radiusLG   // 16.0
```

## Typography Scale

### Login/Explore Headers
```dart
TextStyle(
  fontSize: 32,
  fontWeight: FontWeight.bold,
  letterSpacing: 0.5,
)
```

### Card Titles
```dart
TextStyle(
  fontSize: 17,
  fontWeight: FontWeight.bold,
  letterSpacing: 0.2,
)
```

### Body Text
```dart
TextStyle(
  fontSize: 15,
  fontWeight: FontWeight.w500,
)
```

### Small Text/Stats
```dart
TextStyle(
  fontSize: 11-12,
  fontWeight: FontWeight.w600,
)
```

## Animation Guidelines

### Screen Transitions
- **Duration:** 600-800ms
- **Curve:** `Curves.easeOut` or `Curves.easeOutCubic`
- **Type:** Fade + Slide

### Interactive Elements
- **Duration:** 150-300ms
- **Curve:** `Curves.easeOut`
- **Scale:** 0.95 (pressed state)

### Staggered Animations
- **Base Duration:** 400ms
- **Stagger Delay:** 100ms per item
- **Max Items:** Limit to prevent long delays

## Component Patterns

### Glassmorphism Card
```dart
Container(
  decoration: BoxDecoration(
    gradient: LinearGradient(
      colors: [
        Colors.white.withOpacity(0.12),
        Colors.white.withOpacity(0.06),
      ],
    ),
    borderRadius: BorderRadius.circular(AppSpacing.radiusLG),
    border: Border.all(
      color: Colors.white.withOpacity(0.2),
      width: 1.5,
    ),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.2),
        blurRadius: 20,
        offset: Offset(0, 10),
      ),
    ],
  ),
)
```

### Gradient Background
```dart
Container(
  decoration: BoxDecoration(
    gradient: LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: [
        Color(0xFF1A1A2E),
        Color(0xFF16213E),
        Color(0xFF0F3460).withOpacity(0.8),
      ],
    ),
  ),
)
```

### Gold Button
```dart
ElevatedButton(
  style: ElevatedButton.styleFrom(
    backgroundColor: Color(0xFFD4A84B),
    foregroundColor: Color(0xFF1A1A2E),
    elevation: 8,
    shadowColor: Color(0xFFD4A84B).withOpacity(0.4),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(AppSpacing.radiusMD),
    ),
  ),
)
```

### Progress Indicator
```dart
CircularProgressIndicator(
  strokeWidth: 5,
  backgroundColor: Colors.white.withOpacity(0.1),
  valueColor: AlwaysStoppedAnimation(Color(0xFFD4A84B)),
)
```

## Screen-Specific Guidelines

### Login Screen
- **Logo Size:** 100x100
- **Logo Glow:** 30-50 blur radius
- **Form Field Height:** 56px (auto with padding)
- **Button Height:** 56px
- **Screen Padding:** 24px horizontal
- **Vertical Spacing:** 48px before form

### Explore Screen
- **Grid Columns:** 2 (phone), 3 (tablet), 4 (desktop)
- **Card Aspect Ratio:** 0.75 (3:4)
- **Grid Spacing:** 16px
- **Header Padding:** 24px
- **Progress Circle:** 64x64

### Urn Card
- **Border Radius:** 16px
- **Image Ratio:** 60% of card
- **Info Ratio:** 40% of card
- **Badge Padding:** 8-10px
- **Progress Bar Height:** 7px

## Accessibility Checklist

- [ ] Touch targets minimum 48x48 logical pixels
- [ ] Color contrast ratio ≥ 4.5:1 for normal text
- [ ] Color contrast ratio ≥ 3:1 for large text (18pt+)
- [ ] Semantic labels for screen readers
- [ ] Error messages are descriptive
- [ ] Loading states provide feedback
- [ ] Interactive elements have visual feedback

## Performance Tips

1. Use `const` constructors whenever possible
2. Dispose animation controllers in `dispose()`
3. Use `AnimatedSwitcher` for conditional widgets
4. Optimize image loading with `CachedNetworkImage`
5. Limit stagger animation count
6. Use `RepaintBoundary` for complex widgets
7. Avoid rebuilding entire screens

## Common Pitfalls to Avoid

1. **Don't** use arbitrary spacing values - use AppSpacing constants
2. **Don't** create animations without disposing controllers
3. **Don't** forget to handle loading/error states
4. **Don't** make touch targets too small (<48px)
5. **Don't** use pure white/black - use with opacity
6. **Don't** nest too many transparent layers (performance)
7. **Don't** animate expensive operations (layout changes)

