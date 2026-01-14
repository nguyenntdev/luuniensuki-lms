# Profile Screen - Code Structure

## File Organization

```
profile_screen.dart (1,143 lines)
│
├── Imports (12 lines)
│   ├── Flutter core
│   ├── Riverpod
│   ├── Navigation (go_router)
│   ├── Theme (AppColors, AppSpacing)
│   ├── Widgets (GlassContainer, AnimatedGradientBackground)
│   └── Domain/Providers (User, Auth, Collection)
│
├── ProfileScreen (StatefulWidget)
│   └── _ProfileScreenState (with SingleTickerProviderStateMixin)
│
├── State Management (Lines 24-60)
│   ├── AnimationController (800ms)
│   ├── FadeAnimation (0-60%, easeOut)
│   ├── SlideAnimation (20-100%, easeOutCubic)
│   ├── initState() - Setup & start animations
│   └── dispose() - Cleanup animation controller
│
├── Main Build Method (Lines 62-74)
│   ├── Watch auth state
│   ├── AnimatedGradientBackground
│   └── Conditional: Not logged in OR Profile
│
├── Not Logged In State (Lines 76-148)
│   ├── FadeTransition wrapper
│   ├── Gradient icon container (120x120)
│   ├── Title & subtitle text
│   └── Login button with shadow
│
├── Profile Build (Lines 150-203)
│   ├── FadeTransition
│   ├── SlideTransition
│   └── CustomScrollView with Slivers
│       ├── SliverToBoxAdapter (Header)
│       └── SliverPadding (Content list)
│           ├── XP Card
│           ├── Stats Grid
│           ├── Streak Card
│           ├── Section Header
│           ├── Settings Cards
│           └── Bottom Padding
│
└── Widget Builders (Lines 205-1143)
    ├── _buildProfileHeader()
    ├── _buildAvatarPlaceholder()
    ├── _buildXpCard()
    ├── _buildStatsGrid()
    ├── _buildStatCard()
    ├── _buildStreakCard()
    ├── _buildSettingsCards()
    ├── _buildMenuCard()
    ├── _buildLogoutButton()
    └── _showLogoutDialog()
```

---

## Widget Tree Structure

```
ProfileScreen (StatefulWidget)
└── AnimatedGradientBackground
    └── SafeArea
        └── [Conditional]
            │
            ├── If NOT logged in:
            │   └── FadeTransition
            │       └── Center
            │           └── Column
            │               ├── Icon Container (gradient)
            │               ├── Title Text
            │               ├── Subtitle Text
            │               └── Login Button
            │
            └── If logged in:
                └── FadeTransition
                    └── SlideTransition
                        └── CustomScrollView
                            ├── SliverToBoxAdapter
                            │   └── Container (gradient header)
                            │       └── Column
                            │           ├── Hero (Avatar)
                            │           ├── Display Name
                            │           ├── Email Row
                            │           └── Rank Badge
                            │
                            └── SliverPadding
                                └── SliverList
                                    ├── XP Card (GlassContainer)
                                    ├── Stats Row (3x GlassContainer)
                                    ├── Streak Card (GlassContainer)
                                    ├── Section Header (Text)
                                    ├── Settings Column
                                    │   ├── 4x Menu Cards (GlassCard)
                                    │   └── Logout Button
                                    └── Bottom Spacing
```

---

## Key Methods Breakdown

### 1. _buildProfileHeader() - Lines 205-363
```dart
Returns: SliverToBoxAdapter
Contains:
  - Gradient background container
  - Hero widget with avatar (120x120)
  - Display name (28px bold)
  - Email with icon (14px)
  - Rank badge with icon
Features:
  - Dual shadow layers
  - Gradient borders
  - Text shadows
  - Responsive padding
```

### 2. _buildXpCard() - Lines 381-585
```dart
Input: User user
Returns: GlassContainer
Calculates:
  - totalXp, xpToNext, xpProgress, progress
Contains:
  - Icon container with gradient
  - XP display with formatting
  - Current/next rank badges
  - Progress bar with glow
Features:
  - Gradient glass background
  - Percentage badge
  - Conditional next rank display
  - Clamped progress (0.0-1.0)
```

### 3. _buildStatsGrid() - Lines 587-635
```dart
Input: WidgetRef ref, User user
Returns: Row of 3 Expanded widgets
Stats:
  1. Discovered (blue) - from collection
  2. Lessons (green) - from totalXp / 75
  3. Badges (purple) - hardcoded 0
Features:
  - Equal width columns
  - Color-coded themes
  - Gradient backgrounds
```

### 4. _buildStatCard() - Lines 636-687
```dart
Input: icon, label, value, color, gradientColors
Returns: GlassContainer
Contains:
  - Icon container (48x48)
  - Value text (22px bold)
  - Label text (11px)
Features:
  - Themed gradient background
  - Color-coded icon container
  - Text overflow handling
```

### 5. _buildStreakCard() - Lines 689-866
```dart
Input: User user
Returns: GlassContainer
Calculates:
  - currentStreak, longestStreak, streakFreezes
  - hasStreak boolean
Contains:
  - Fire icon (64x64)
  - Streak number (32px)
  - Record badge
  - Freeze badge
Features:
  - Conditional theming
  - Orange glow when active
  - Dual stat badges
```

### 6. _buildSettingsCards() - Lines 868-935
```dart
Input: BuildContext context, WidgetRef ref
Returns: Column of menu cards + logout
Cards:
  1. Personal Info (blue)
  2. Notifications (amber)
  3. Settings (gray)
  4. Help & Support (green)
  5. Logout button (red)
Features:
  - Color-coded themes
  - Descriptive subtitles
  - Tap handlers
```

### 7. _buildMenuCard() - Lines 937-1007
```dart
Input: icon, title, subtitle, color, onTap
Returns: GlassCard (tappable)
Contains:
  - Icon container (48x48)
  - Title (16px bold)
  - Subtitle (12px)
  - Chevron indicator
Features:
  - Gradient icon background
  - Tap feedback
  - Themed colors
```

### 8. _buildLogoutButton() - Lines 1010-1052
```dart
Input: BuildContext context, WidgetRef ref
Returns: GestureDetector
Contains:
  - Logout icon
  - "Đăng xuất" text
  - Centered layout
Features:
  - Red gradient background
  - Error theme
  - Shows dialog on tap
```

### 9. _showLogoutDialog() - Lines 1054-1142
```dart
Input: BuildContext context, WidgetRef ref
Action: Shows AlertDialog
Contains:
  - Icon in title
  - Confirmation message
  - Cancel button
  - Logout button (red)
Features:
  - Glass-themed dialog
  - Proper spacing
  - Logout action
```

---

## Animation Details

### Animation Controller Setup
```dart
_animationController = AnimationController(
  vsync: this,
  duration: const Duration(milliseconds: 800),
);
```

### Fade Animation (0-60%)
```dart
_fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
  CurvedAnimation(
    parent: _animationController,
    curve: const Interval(0.0, 0.6, curve: Curves.easeOut),
  ),
);
```

### Slide Animation (20-100%)
```dart
_slideAnimation = Tween<Offset>(
  begin: const Offset(0, 0.3),
  end: Offset.zero,
).animate(
  CurvedAnimation(
    parent: _animationController,
    curve: const Interval(0.2, 1.0, curve: Curves.easeOutCubic),
  ),
);
```

### Usage
```dart
FadeTransition(
  opacity: _fadeAnimation,
  child: SlideTransition(
    position: _slideAnimation,
    child: CustomScrollView(...),
  ),
)
```

---

## Provider Integration

### Auth Provider
```dart
final authState = ref.watch(authNotifierProvider);
final user = authState.user;

// Logout
ref.read(authNotifierProvider.notifier).logout();
```

### Collection Provider
```dart
final collectionState = ref.watch(collectionNotifierProvider);
final discoveredCount = collectionState.collection?.stats.discovered ?? 0;
```

---

## Constants Used

### AppColors
- primary, primaryDark, primaryLight
- info, success, error, warning
- badgePurple, streakOrange
- xpGold, xpGoldDark
- glassWhite, glassBorder
- textPrimary, textSecondary
- onPrimary, onSurface
- primaryGradient, xpGradient

### AppSpacing
- xs, sm, md, lg, xl, xxl (4, 8, 16, 24, 32, 48)
- radiusXS, SM, MD, LG, XL (4, 8, 12, 16, 24)
- verticalSpace[Size], horizontalSpace[Size]

---

## Performance Considerations

1. **Const constructors** where possible
2. **Animation disposal** in dispose()
3. **Slivers** for efficient scrolling
4. **Calculated once** per build
5. **Conditional rendering** for null safety
6. **Provider watching** only necessary data

---

## Testing Points

✅ Not logged in state
✅ Logged in with full user data
✅ XP progress calculation
✅ Stats display from collection
✅ Streak active/inactive states
✅ Menu card taps (snackbars)
✅ Logout confirmation flow
✅ Animation playback
✅ Avatar image loading
✅ Avatar fallback (initials)
✅ Next rank display (when available)
✅ Max level display (no next rank)

---

## Future Extension Points

1. **Add real badge count** - Line 632
2. **Profile edit navigation** - Line 880
3. **Settings navigation** - Line 904
4. **Notifications navigation** - Line 892
5. **Help navigation** - Line 916
6. **Achievement details** - Add tap to stat cards
7. **XP breakdown** - Add tap to XP card
8. **Streak calendar** - Add tap to streak card

---

This code structure provides a clear overview of the implementation!

