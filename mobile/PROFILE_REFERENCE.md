# Profile Screen - Quick Reference Guide

## 🎨 Design Features

### Color Scheme
- **Primary**: Gold gradient (AppColors.primary, primaryDark, primaryLight)
- **Stats Cards**: Color-coded by type (blue, green, purple)
- **Streak**: Orange theme when active
- **Logout**: Error red theme
- **Glass Effects**: White overlay with gradients

### Animations
1. **Fade Animation**: 0-60% of 800ms (easeOut curve)
2. **Slide Animation**: 20-100% of 800ms (easeOutCubic curve)
3. **Hero Animation**: Avatar ready for navigation transitions

## 📐 Component Dimensions

| Component | Size | Border Radius |
|-----------|------|---------------|
| Avatar | 120x120 | Circle |
| Stat Icon Container | 48x48 | 12px |
| Streak Icon Container | 64x64 | 16px |
| XP Star Container | ~36x36 | 8px |
| Progress Bar | Full width x 10px | 8px |

## 🎯 Key Widgets Used

### From Design System
- `AppColors.*` - All color definitions
- `AppSpacing.*` - All spacing/sizing constants
- `GlassContainer` - Main container widget
- `GlassCard` - Tappable card variant
- `AnimatedGradientBackground` - Screen background

### Flutter Widgets
- `Hero` - Avatar animation
- `FadeTransition` - Fade in effect
- `SlideTransition` - Slide up effect
- `CustomScrollView` - Efficient scrolling
- `SliverToBoxAdapter` - Header adapter
- `SliverPadding` - Content padding

## 🔧 Customization Points

### Easy to Modify
1. **Animation Duration**: Line 33 - Change `800ms`
2. **Avatar Size**: Line 233-234 - Change `120`
3. **Progress Bar Height**: Line 558 & 566 - Change `10`
4. **Card Padding**: Use AppSpacing constants
5. **Gradient Colors**: Use AppColors or override

### Adding New Menu Items
```dart
_buildMenuCard(
  icon: Icons.your_icon,
  title: 'Your Title',
  subtitle: 'Your description',
  color: AppColors.yourColor,
  onTap: () {
    // Your action
  },
),
```

## 📊 Stats Calculation

| Stat | Formula | Location |
|------|---------|----------|
| Total XP | `user.totalXp` | User object |
| Discovered | Collection stats | Provider |
| Lessons | `totalXp ~/ 75` | Approximate |
| Badges | Hardcoded `0` | Needs backend |

## 🎪 Interactive Elements

1. **Menu Cards**: Tap to navigate/show snackbar
2. **Logout Button**: Shows confirmation dialog
3. **Rank Badge**: Visual only (no tap)
4. **Stats Cards**: Visual only (could add tap)

## 🌈 Gradient Definitions

### XP Card
```dart
AppColors.glassWhite → primary.withOpacity(0.05)
```

### Stats Cards
Each has unique gradient based on color:
```dart
color.withOpacity(0.3) → color.withOpacity(0.1)
```

### Streak Card (Active)
```dart
streakOrange.withOpacity(0.15) → streakOrange.withOpacity(0.05)
```

### Header
```dart
primary.withOpacity(0.2) → primaryDark.withOpacity(0.1) → transparent
```

## 🚀 Performance Tips

1. **Use const**: All static widgets marked const
2. **Slivers**: Efficient scrolling with CustomScrollView
3. **Animation Controller**: Properly disposed
4. **Cached Calculations**: XP progress calculated once
5. **Gradient Reuse**: AppColors.primaryGradient

## 🐛 Common Issues & Solutions

### Avatar not showing
- Check `user.avatarUrl` is valid URL
- Fallback to initial letter placeholder

### XP Progress > 100%
- Fixed with `.clamp(0.0, 1.0)` on line 566

### Animation not playing
- Ensure `_animationController.forward()` is called
- Check widget is mounted

### Stats showing 0
- Check provider state is loaded
- Verify collection data exists

## 📱 Responsive Considerations

- Uses `Expanded` for stats grid (equal width)
- Text overflow handled with `ellipsis`
- Flexible layout with `Row`/`Column`
- Scrollable content for small screens

## 🎨 Theme Integration

All colors come from `AppColors`:
- Primary colors (gold)
- Semantic colors (success, error, info, warning)
- Gamification colors (xp, streak, badge)
- Glass effects (glassWhite, glassBorder)

## 📝 Text Styles

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Display Name | 28px | Bold | White |
| Section Title | 18px | Bold | White 90% |
| Card Title | 16px | 600 | White |
| Card Subtitle | 12px | Normal | White 60% |
| Stat Value | 22px | Bold | White |
| Stat Label | 11px | 500 | White 70% |

## 🔗 Navigation

Current navigation points:
- Login (not logged in) → `/login`
- Logout (authenticated) → `/login`
- Menu items → Snackbar (Coming soon)

Future additions could link to:
- Profile edit screen
- Settings screen
- Help/FAQ screen
- Notifications screen

