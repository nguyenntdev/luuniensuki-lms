# Explore Screen - Component Tree

## Widget Hierarchy

```
ExploreScreen (StatefulWidget)
└─ AnimatedGradientBackground
   └─ SafeArea
      └─ FadeTransition
         └─ Column
            ├─ _buildHeader()
            │  └─ Padding
            │     └─ Column
            │        ├─ Row (Top Bar)
            │        │  ├─ Text("Khám Phá")
            │        │  ├─ Spacer()
            │        │  ├─ CompactStreakWidget()
            │        │  ├─ SizedBox(width: 16)
            │        │  └─ _buildUserAvatar()
            │        │     └─ Stack
            │        │        ├─ Container (Avatar Circle)
            │        │        │  └─ ClipOval (Image.network)
            │        │        └─ Positioned (Level Badge)
            │        │           └─ Container (Gold Badge)
            │        │              └─ Text(level)
            │        │
            │        ├─ SizedBox(height: 16)
            │        │
            │        └─ _buildCompactStats()
            │           └─ Container (Glass Card)
            │              └─ Row
            │                 ├─ _buildCompactStat("👁️", "45/270")
            │                 ├─ _buildCompactDivider()
            │                 ├─ _buildCompactStat("📚", "32")
            │                 ├─ _buildCompactDivider()
            │                 └─ _buildCompactStat("⭐", "18")
            │
            └─ Expanded
               └─ _buildContent()
                  └─ RefreshIndicator
                     └─ LayoutBuilder
                        └─ GridView.builder
                           └─ UrnCard (×9)
```

## Method Reference

### Core Build Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `_buildHeader()` | Builds entire header section | Widget (Padding > Column) |
| `_buildUserAvatar()` | User avatar with level badge | Widget (Stack) |
| `_buildCompactStats()` | Stats row with 3 metrics | Widget (Container) |
| `_buildCompactStat()` | Individual stat item | Widget (Row) |
| `_buildCompactDivider()` | Vertical divider | Widget (Container) |
| `_buildContent()` | Main grid content area | Widget |
| `_buildLoadingState()` | Shimmer loading grid | Widget |
| `_buildErrorState()` | Error message UI | Widget |
| `_buildEmptyState()` | Empty state UI | Widget |

### Helper Methods

| Method | Purpose |
|--------|---------|
| `_navigateToUrn()` | Navigate to urn detail screen |
| `_checkAndLoadData()` | Initialize data loading on mount |

## State Management

```
Providers Used:
├─ exploreNotifierProvider → ExploreState (urns list)
├─ exploreProgressProvider → ExploreProgress (stats)
└─ authNotifierProvider → AuthState (user info)

State Flow:
1. Widget mounts
2. _checkAndLoadData() called
3. Listens for auth state
4. Loads urns when authenticated
5. Displays header + grid
6. User can refresh (pull-to-refresh)
```

## Data Flow

```
ExploreProgress (Provider)
├─ totalMotifs: int
├─ discoveredMotifs: int
├─ learnedMotifs: int
├─ masteredMotifs: int
└─ masteryPercent: double
   └─ Used in: _buildCompactStats()

AuthState (Provider)
├─ isAuthenticated: bool
└─ user: User?
   ├─ displayName: String
   ├─ email: String
   ├─ avatarUrl: String?
   └─ rank.level: int
      └─ Used in: _buildUserAvatar()

ExploreState (Provider)
├─ isLoading: bool
├─ hasError: bool
├─ errorMessage: String?
└─ urns: List<Urn>
   └─ Used in: _buildContent()
```

## Key Components from Other Files

### CompactStreakWidget
```dart
Source: features/streak/presentation/widgets/compact_streak_widget.dart
Display: 🔥 + day count
Responsive: Color changes based on streak length
```

### UrnCard
```dart
Source: features/explore/presentation/widgets/urn_card.dart
Display: Card with urn image, title, progress
Callback: onTap() navigation
```

### AnimatedGradientBackground
```dart
Source: shared/widgets/glass/animated_background.dart
Effect: Animated gradient background
```

## Animation Details

```
Screen Entry:
├─ FadeTransition
│  ├─ Duration: 600ms
│  ├─ Curve: easeOut
│  └─ Opacity: 0.0 → 1.0

Urn Card Stagger:
├─ TweenAnimationBuilder
│  ├─ Duration: 400ms + (index × 100ms)
│  ├─ Curve: easeOutCubic
│  ├─ Scale: 0.0 → 1.0
│  └─ Opacity: 0.0 → 1.0
```

## Performance Optimizations

```
✓ const constructors where possible
✓ Minimal rebuilds (specific providers watched)
✓ Lazy loading with GridView.builder
✓ Efficient state management
✓ Cached network images (UrnCard)
✓ Shimmer loading states
```

## Dependencies

```yaml
External Packages:
├─ flutter_riverpod (state management)
├─ go_router (navigation)
└─ Standard Flutter widgets

Internal Dependencies:
├─ core/theme/app_colors.dart
├─ core/theme/app_spacing.dart
├─ shared/widgets/glass/animated_background.dart
├─ shared/widgets/shimmer/shimmer_skeleton.dart
├─ features/auth/presentation/providers/auth_provider.dart
├─ features/streak/presentation/widgets/compact_streak_widget.dart
└─ features/explore/presentation/widgets/urn_card.dart
```

