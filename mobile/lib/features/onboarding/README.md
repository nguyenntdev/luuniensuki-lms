# Onboarding Screen - Hướng dẫn

## Tổng quan

Onboarding Screen là màn hình giới thiệu cho người dùng mới, gồm 4 slides với animations và glassmorphism design.

## Files đã tạo

```
lib/features/onboarding/
├── presentation/
│   ├── screens/
│   │   └── onboarding_screen.dart          # Main onboarding screen
│   └── widgets/
│       ├── onboarding_page.dart            # Individual page widget with animations
│       └── page_indicator.dart             # Animated page indicator
```

## Tính năng

### 4 Slides giới thiệu:

1. **Chào mừng** - Giới thiệu app Lưu Niên Sử Kí
2. **Khám phá 3D** - Giới thiệu tính năng xem mô hình 3D
3. **Gamification** - Hearts ❤️, Gems 💎, Streaks 🔥
4. **Chọn mục tiêu** - Daily goals với 3 options

### Design Features:

- ✅ AnimatedGradientBackground - animated gradient cho background
- ✅ GlassContainer cho các elements
- ✅ PageView với smooth transitions
- ✅ Animated page indicator
- ✅ Scale, rotation, slide animations cho content
- ✅ Custom gradients cho mỗi slide
- ✅ Skip button (ẩn ở slide cuối)
- ✅ Next/Bắt đầu button với gradient matching slide hiện tại

### Storage & Navigation:

- ✅ Lưu `hasSeenOnboarding` vào Hive storage
- ✅ Auto redirect new users đến onboarding
- ✅ Navigate đến `/explore` khi hoàn thành
- ✅ Router redirect logic trong `app_router.dart`

## Cách sử dụng

### 1. Generate code (nếu cần)

```bash
cd mobile
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

### 2. Test onboarding

Để test onboarding screen:

```dart
// Clear onboarding flag để test lại
final storage = ref.read(hiveStorageProvider);
await storage.setHasSeenOnboarding(false);
```

Hoặc navigate trực tiếp:

```dart
context.go('/onboarding');
```

### 3. Reset onboarding trong Settings

Có thể thêm option trong Settings screen:

```dart
GlassButton(
  text: 'Xem lại Onboarding',
  onPressed: () async {
    final storage = ref.read(hiveStorageProvider);
    await storage.setHasSeenOnboarding(false);
    context.go('/onboarding');
  },
)
```

## Customization

### Thêm slide mới

Trong `onboarding_screen.dart`:

```dart
final List<OnboardingPageData> _pages = [
  // ... existing slides ...
  OnboardingPageData(
    title: 'Tiêu đề mới',
    description: 'Mô tả tính năng',
    icon: Icons.your_icon,
    gradient: LinearGradient(
      colors: [Color(0xFF...), Color(0xFF...)],
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    ),
    color: AppColors.yourColor,
  ),
];
```

### Thay đổi animation

Trong `onboarding_page.dart`, tùy chỉnh animations:

```dart
_scaleAnimation = Tween<double>(begin: 0.5, end: 1.0).animate(
  CurvedAnimation(
    parent: _controller,
    curve: const Interval(0.0, 0.6, curve: Curves.elasticOut),
  ),
);
```

### Thay đổi màu background

Trong `onboarding_screen.dart`:

```dart
AnimatedGradientBackground(
  duration: const Duration(seconds: 8),
  colors: const [
    // Your custom colors
  ],
  child: ...
)
```

## Router Integration

File `app_router.dart` đã được cập nhật:

### 1. Thêm onboarding path

```dart
class _Paths {
  static const String onboarding = '/onboarding';
  // ...
}
```

### 2. Thêm redirect logic

```dart
// Check if user has seen onboarding
final hasSeenOnboarding = storage.hasSeenOnboarding();

// Not seen onboarding and not currently on onboarding -> redirect
if (isLoggedIn && !hasSeenOnboarding && !isOnboarding) {
  return _Paths.onboarding;
}
```

### 3. Thêm route

```dart
GoRoute(
  path: _Paths.onboarding,
  name: 'onboarding',
  builder: (context, state) => const OnboardingScreen(),
),
```

## UI Components đã sử dụng

### From design system:

- `AppColors` - color palette
- `AppSpacing` - spacing constants
- `GlassContainer` - glassmorphism containers
- `GlassButton` - glass buttons (updated to support `child` property)
- `AnimatedGradientBackground` - animated background

### Custom widgets:

- `OnboardingPage` - individual page with animations
- `PageIndicator` - animated dots indicator
- `OnboardingPageData` - data class for page content

## GlassButton Updates

File `glass_button.dart` đã được cập nhật để support cả `text` và `child`:

```dart
GlassButton(
  child: Row(...),  // Custom child widget
  gradient: gradient,
  onPressed: () {},
)

// Or traditional text-only
GlassButton(
  text: 'Button text',
  onPressed: () {},
)
```

## Flow Chart

```
App Start
    ↓
Auth Check
    ↓
Logged In?
    ├─ No → Login Screen
    └─ Yes → Has seen onboarding?
              ├─ No → Onboarding Screen → Explore Screen
              └─ Yes → Explore Screen
```

## Next Steps

### Potential enhancements:

1. **Interactive elements** - Cho phép user chọn daily goal trong onboarding
2. **Lottie animations** - Thêm Lottie animations thay vì icon tĩnh
3. **Video backgrounds** - Background video cho mỗi slide
4. **Progress save** - Lưu slide hiện tại để resume
5. **A/B testing** - Track conversion rate của onboarding

### Integration với Daily Goals:

Có thể cho phép user chọn daily goal ngay trong onboarding slide 4:

```dart
// Trong _buildGoalOption, thêm onTap callback
GestureDetector(
  onTap: () {
    setState(() {
      _selectedGoal = dailyXP;
    });
  },
  child: _buildGoalOption(...)
)

// Lưu khi complete onboarding
await ref.read(dailyGoalProvider.notifier).setDailyGoal(_selectedGoal);
```

## Troubleshooting

### Onboarding không hiện

Check storage:
```dart
final hasSeenOnboarding = storage.hasSeenOnboarding();
print('Has seen onboarding: $hasSeenOnboarding');
```

### Animation không mượt

- Check device performance
- Reduce particle count trong background
- Simplify animations

### Router không redirect

- Run code generator
- Check auth state
- Check redirect logic trong `app_router.dart`

## Credits

Design system: AppColors, AppSpacing, Glass components
Implementation: Onboarding screens với PageView và animations

