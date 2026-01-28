# Explore Header V2 - Quick Reference

## Usage

```dart
// In explore_screen.dart
ExploreHeaderV2(
  progress: progress,      // ExploreProgress from provider
  user: authState.user!,   // User entity
  onContinue: () => _navigateToUrn(context, continueUrn.slug),
  onPractice: () => context.push('/practice'),
)
```

## Component Breakdown

### 1. Greeting Section
```
┌──────────────────────────────────┐
│ Chào buổi sáng          [Avatar]│
│ User Name                    [12]│
└──────────────────────────────────┘
```
- Time-based greeting (morning/afternoon/evening)
- User display name (28px, bold)
- Animated avatar with gradient ring + level badge

### 2. Stats Dashboard
```
┌─────────────────────────────────────────────┐
│  [👁]     │    [📖]     │     [⭐]           │
│  15/45    │     8       │      3            │
│  Khám phá │  Đã học     │  Thành thạo       │
└─────────────────────────────────────────────┘
```
- Glass morphism container
- 3 stats with icons, values, labels
- Staggered entrance animations

### 3. Action Buttons
```
┌─────────────────┐  ┌──────────────────┐
│ ▶ Tiếp tục học  │  │ 🏋 Luyện tập     │
└─────────────────┘  └──────────────────┘
    (Gradient)          (Outlined)
```
- Primary: Golden gradient with glow
- Secondary: White outlined
- Slide-up animations

## Animations

| Element | Type | Duration | Curve |
|---------|------|----------|-------|
| Avatar ring | Rotation | 1500ms | Linear (repeat) |
| Level badge | Scale | 1500ms | ElasticOut |
| Stats card | Scale + Fade | 600ms | EaseOutCubic |
| Stat pods | Scale + Fade | 400ms + delay | EaseOutBack |
| Buttons | Translate + Fade | 500-600ms | EaseOutCubic |

## Key Properties

### ExploreProgress
```dart
- totalMotifs: int
- discoveredMotifs: int
- learnedMotifs: int
- masteredMotifs: int
```

### User
```dart
- displayName: String
- email: String
- avatarUrl: String?
- rank.level: int
```

## Colors Used
- `AppColors.xpGold` - Avatar ring, level badge
- `AppColors.primary` / `primaryDark` - Gradients
- `AppColors.info` - Discovered icon
- `AppColors.success` - Learned icon
- `AppColors.primary` - Mastered icon
- `Colors.white` - Text, borders

## Spacing
- Outer padding: `AppSpacing.md` (16px)
- Between sections: `AppSpacing.md` (16px)
- Stats card padding: `AppSpacing.md` (16px)
- Button gap: `AppSpacing.sm` (8px)

## File Location
```
lib/features/explore/presentation/widgets/explore_header_v2.dart
```

## Integration Points
1. Only shown for authenticated users
2. Receives progress from `exploreProgressProvider`
3. Receives user from `authNotifierProvider`
4. Callbacks for navigation (continue/practice)
5. Used in `ExploreScreen._buildHeader()`

