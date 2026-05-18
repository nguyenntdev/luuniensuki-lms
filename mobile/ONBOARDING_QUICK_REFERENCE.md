# Onboarding - Quick Reference

## 🚀 Quick Start (3 steps)

```bash
# 1. Generate code
cd mobile && flutter pub run build_runner build --delete-conflicting-outputs

# 2. Test (reset onboarding first)
# In Dart DevTools Console or add to code:
ref.read(hiveStorageProvider).setHasSeenOnboarding(false);

# 3. Run app
flutter run
```

## 📁 Files Created

```
mobile/lib/features/onboarding/
├── presentation/
│   ├── screens/
│   │   └── onboarding_screen.dart          # Main screen
│   └── widgets/
│       ├── onboarding_page.dart            # Slide widget
│       ├── page_indicator.dart             # Dots indicator
│       ├── onboarding_controls.dart        # Settings widget
│       └── onboarding_test_helper.dart     # Debug helper
└── *.md                                     # Documentation

Updated:
- mobile/lib/routing/app_router.dart
- mobile/lib/shared/widgets/glass/glass_button.dart
```

## 🎨 Features

- ✅ 4 slides với animated transitions
- ✅ AnimatedGradientBackground
- ✅ GlassContainer design
- ✅ Skip button
- ✅ Page indicator
- ✅ Auto-redirect cho new users
- ✅ Saved to Hive storage

## 💡 Common Tasks

### Check if user has seen onboarding
```dart
final storage = ref.read(hiveStorageProvider);
final hasSeenOnboarding = storage.hasSeenOnboarding();
```

### Reset onboarding (for testing)
```dart
await ref.read(hiveStorageProvider).setHasSeenOnboarding(false);
```

### Navigate to onboarding
```dart
context.go('/onboarding');
// or
context.push('/onboarding');
```

### Add to Settings screen
```dart
import '../../onboarding/presentation/widgets/onboarding_controls.dart';

// In Settings screen body:
OnboardingControls(),
```

### Show debug controls (development)
```dart
import 'package:flutter/foundation.dart';
import '../onboarding/presentation/widgets/onboarding_test_helper.dart';

@override
Widget build(BuildContext context) {
  return Stack(
    children: [
      YourScreenContent(),
      if (kDebugMode)
        OnboardingTestHelper.showTestControls(context, ref),
    ],
  );
}
```

## 🎯 The 4 Slides

1. **Chào mừng** - Welcome + app intro
2. **Khám phá 3D** - 3D viewer feature
3. **Gamification** - Hearts, Gems, Streaks
4. **Mục tiêu** - Daily goals

## 🔧 Customization

### Change slide content
Edit `onboarding_screen.dart` → `_pages` list

### Change animations
Edit `onboarding_page.dart` → animation parameters

### Change colors
Use different `AppColors` constants or custom gradients

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Onboarding doesn't show | Check `hasSeenOnboarding()`, run code generator |
| Build errors | Run `flutter clean && flutter pub get` |
| Animations laggy | Reduce animation complexity or use simpler background |
| Router not redirecting | Verify redirect logic in `app_router.dart` |

## 📊 Key Components

```dart
// Main Screen
OnboardingScreen()

// Individual Slide
OnboardingPage(data: OnboardingPageData(...))

// Indicator
PageIndicator(currentPage: 0, pageCount: 4)

// Storage
HiveStorage.hasSeenOnboarding()
HiveStorage.setHasSeenOnboarding(bool)
```

## 🔄 Flow

```
Login → hasSeenOnboarding? 
        ├─ No  → Onboarding → Explore
        └─ Yes → Explore
```

## 📚 Documentation

- `README.md` - Feature documentation
- `ONBOARDING_IMPLEMENTATION.md` - Implementation details
- `ONBOARDING_INTEGRATION_GUIDE.md` - How to integrate
- `ONBOARDING_CHECKLIST.md` - Task checklist
- `ONBOARDING_FLOW_DIAGRAM.md` - Visual flow

## ⚡ Commands

```bash
# Clean build
flutter clean

# Get dependencies
flutter pub get

# Generate code
flutter pub run build_runner build --delete-conflicting-outputs

# Run app
flutter run

# Analyze code
flutter analyze

# Format code
flutter format .
```

## 🎁 Extras

### Test Helper
```dart
OnboardingTestHelper.resetAndShow(context, ref);
OnboardingTestHelper.checkStatus(ref);
```

### Settings Widget
```dart
OnboardingControls() // Shows status + buttons
```

---

**Status**: ✅ Ready to use
**Version**: 1.0.0

Need help? Check the full documentation in README.md

