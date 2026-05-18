# Onboarding Integration Guide

## Quick Start

### 1. Chạy Code Generator

```bash
cd mobile
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

### 2. Test Onboarding

Logout và login lại, onboarding sẽ tự động hiện cho user mới.

Hoặc navigate trực tiếp:
```dart
context.go('/onboarding');
```

### 3. Reset Onboarding (for testing)

```dart
final storage = ref.read(hiveStorageProvider);
await storage.setHasSeenOnboarding(false);
```

---

## Integration với Settings Screen

### Option 1: Add OnboardingControls Widget

File: `mobile/lib/features/settings/presentation/screens/settings_screen.dart`

```dart
import '../../onboarding/presentation/widgets/onboarding_controls.dart';

// Trong settings screen body, thêm:
OnboardingControls(),
AppSpacing.verticalSpaceLG,
```

### Option 2: Add Simple Button

```dart
// Import
import '../../../core/storage/hive_storage.dart';

// Trong settings screen:
GlassButton(
  text: 'Xem lại Onboarding',
  icon: Icons.auto_awesome,
  isPrimary: false,
  onPressed: () {
    context.push('/onboarding');
  },
)

// Or with reset option:
Row(
  children: [
    Expanded(
      child: GlassButton(
        text: 'Xem Onboarding',
        onPressed: () => context.push('/onboarding'),
      ),
    ),
    AppSpacing.horizontalSpaceMD,
    GlassButton(
      text: 'Reset',
      isPrimary: false,
      onPressed: () async {
        final storage = ref.read(hiveStorageProvider);
        await storage.setHasSeenOnboarding(false);
      },
    ),
  ],
)
```

---

## Debug Testing

### Option 1: Using Test Helper (Recommended for Development)

Add to your main screen (e.g., ExploreScreen):

```dart
import 'package:flutter/foundation.dart';
import '../onboarding/presentation/widgets/onboarding_test_helper.dart';

@override
Widget build(BuildContext context) {
  return Stack(
    children: [
      // Your existing screen content
      YourScreenContent(),
      
      // Debug controls (only in debug mode)
      if (kDebugMode)
        OnboardingTestHelper.showTestControls(context, ref),
    ],
  );
}
```

### Option 2: Using Flutter DevTools Console

```dart
// Get storage instance
final storage = ProviderScope.containerOf(context).read(hiveStorageProvider);

// Check status
print(storage.hasSeenOnboarding());

// Reset
await storage.setHasSeenOnboarding(false);

// Navigate
context.go('/onboarding');
```

---

## Customization Examples

### Change Slide Content

Edit `mobile/lib/features/onboarding/presentation/screens/onboarding_screen.dart`:

```dart
final List<OnboardingPageData> _pages = [
  OnboardingPageData(
    title: 'Your Title',
    description: 'Your description',
    icon: Icons.your_icon,
    gradient: LinearGradient(
      colors: [Color(0xFF...), Color(0xFF...)],
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    ),
    color: AppColors.yourColor,
  ),
  // Add more slides...
];
```

### Change Background Animation

```dart
// In onboarding_screen.dart:
AnimatedGradientBackground(
  duration: const Duration(seconds: 10), // Slower
  colors: const [
    Color(0xFF1A1A2E),
    Color(0xFF0F3460),
    // Your colors...
  ],
  child: ...
)
```

### Change Page Transition Speed

```dart
_pageController.nextPage(
  duration: const Duration(milliseconds: 600), // Slower
  curve: Curves.easeOutCubic,
);
```

### Change Icon Animation

Edit `mobile/lib/features/onboarding/presentation/widgets/onboarding_page.dart`:

```dart
_controller = AnimationController(
  vsync: this,
  duration: const Duration(milliseconds: 1000), // Slower
);

_scaleAnimation = Tween<double>(begin: 0.3, end: 1.2).animate(...); // More dramatic
```

---

## Add Daily Goal Selection

Make slide 4 interactive to save user's selected goal:

### 1. Update OnboardingScreen state

```dart
class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  int _selectedDailyGoal = 10; // Default to "Thường xuyên"
  
  // ... existing code ...
  
  Future<void> _completeOnboarding() async {
    // Save selected daily goal
    // await ref.read(dailyGoalProvider.notifier).setDailyGoal(_selectedDailyGoal);
    
    final storage = ref.read(hiveStorageProvider);
    await storage.setHasSeenOnboarding(true);
    
    if (mounted) {
      context.go('/explore');
    }
  }
}
```

### 2. Pass selection callback to OnboardingPage

```dart
OnboardingPage(
  data: _pages[index],
  selectedDailyGoal: _selectedDailyGoal,
  onDailyGoalSelected: (goal) {
    setState(() {
      _selectedDailyGoal = goal;
    });
  },
)
```

### 3. Update OnboardingPage to handle selection

```dart
class OnboardingPage extends StatefulWidget {
  final OnboardingPageData data;
  final int? selectedDailyGoal;
  final Function(int)? onDailyGoalSelected;
  
  // Update _buildGoalOption to be interactive
  Widget _buildGoalOption(String title, String description, int goalXP) {
    final isSelected = widget.selectedDailyGoal == goalXP;
    
    return GestureDetector(
      onTap: () => widget.onDailyGoalSelected?.call(goalXP),
      child: GlassContainer(
        // ... existing code with isSelected styling
      ),
    );
  }
}
```

---

## Troubleshooting

### Onboarding doesn't show after login

**Check:**
1. Has the user seen onboarding before?
```dart
final storage = ref.read(hiveStorageProvider);
print('Has seen onboarding: ${storage.hasSeenOnboarding()}');
```

2. Is router redirect working?
```dart
// Check in app_router.dart redirect function
print('isLoggedIn: $isLoggedIn, hasSeenOnboarding: $hasSeenOnboarding');
```

3. Run code generator:
```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

### Animations are laggy

**Solutions:**
1. Reduce animation complexity in onboarding_page.dart
2. Use simpler background (GradientBackground instead of AnimatedGradientBackground)
3. Reduce particle count if using ParticleBackground

### Build errors after adding files

**Run:**
```bash
flutter clean
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

---

## Files Structure

```
mobile/lib/features/onboarding/
├── presentation/
│   ├── screens/
│   │   └── onboarding_screen.dart        # Main screen with 4 slides
│   └── widgets/
│       ├── onboarding_page.dart          # Individual slide widget
│       ├── page_indicator.dart           # Animated dots
│       ├── onboarding_controls.dart      # Settings integration
│       └── onboarding_test_helper.dart   # Debug helper
└── README.md                              # Documentation
```

Updated files:
- `mobile/lib/routing/app_router.dart` - Added onboarding route and redirect
- `mobile/lib/shared/widgets/glass/glass_button.dart` - Added child support

---

## Next Steps

1. ✅ Test onboarding flow
2. ✅ Add to Settings screen
3. ⬜ Add analytics tracking (optional)
4. ⬜ A/B test different slide content (optional)
5. ⬜ Add Lottie animations (optional)
6. ⬜ Implement daily goal selection (optional)

---

**Ready to use!** 🎉

Just run the code generator and test the flow.

