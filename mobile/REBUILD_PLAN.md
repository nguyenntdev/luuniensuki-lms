# Mobile App Rebuild Plan - Bug Analysis & Glassmorphism Redesign

## Table of Contents
1. [Bug Deep Dive Analysis](#bug-deep-dive-analysis)
2. [Glassmorphism Design System](#glassmorphism-design-system)
3. [Implementation Plan](#implementation-plan)
4. [File Structure](#file-structure)
5. [Timeline](#timeline)

---

## Bug Deep Dive Analysis

### Problem Statement
TextField/TextFormField widgets are not responding to touch events - users cannot tap to focus and input text.

### Symptoms Observed
1. ✅ Layout renders correctly (no infinite scroll)
2. ✅ TextFields are visible with correct styling
3. ❌ Tapping on TextFields does nothing
4. ❌ Keyboard never appears
5. ❌ Issue persists across multiple fix attempts

### Root Cause Analysis

#### Primary Cause: GoRouter Continuous Rebuild

The core issue is in `app_router.dart`:

```dart
@riverpod
GoRouter appRouter(AppRouterRef ref) {
  final authState = ref.watch(authNotifierProvider);  // ← PROBLEM
  
  return GoRouter(
    initialLocation: _Paths.explore,
    refreshListenable: GoRouterRefreshStream(ref),  // ← ALSO PROBLEM
    redirect: (context, state) {
      // Uses authState for redirect logic
    },
    routes: [...],
  );
}
```

**What happens:**
1. App starts → AuthNotifier.build() is called
2. `_checkAuthStatus()` runs asynchronously
3. Auth state changes: `initial` → `loading` → `unauthenticated`
4. Each state change triggers `ref.watch(authNotifierProvider)`
5. This causes `appRouter` provider to rebuild
6. New GoRouter instance is created
7. Current screen (LoginScreen) is rebuilt
8. TextField loses focus immediately after gaining it
9. User experiences "cannot tap" behavior

#### Secondary Cause: Auth Provider Async Init

```dart
@riverpod
class AuthNotifier extends _$AuthNotifier {
  @override
  AuthState build() {
    _checkAuthStatus();  // ← Async call in sync method
    return const AuthState.initial();
  }
}
```

This pattern causes multiple state transitions on app startup:
- `initial` (immediate)
- `loading` (when checking)
- `unauthenticated` or `authenticated` (after check)

Each transition ripples through the app, causing rebuilds.

#### Tertiary Cause: ConsumerStatefulWidget Issues

Using `ConsumerStatefulWidget` for login/register screens means:
- Any provider change can trigger rebuild
- Local state (TextEditingController) conflicts with provider-driven rebuilds
- Focus state is lost on rebuild

### Why Previous Fixes Failed

| Fix Attempt | Why It Failed |
|-------------|---------------|
| Remove IntrinsicHeight/Spacer | Fixed layout but didn't address rebuild issue |
| Wrap TextField in Material | Material was already provided by Scaffold |
| Add GestureDetector for unfocus | Actually made it worse - could absorb taps |
| Simplify InputDecoration | Styling wasn't the issue |
| Use TextField instead of TextFormField | Same underlying issue |

### Correct Solution

1. **Don't recreate GoRouter on auth state changes**
   - Create GoRouter once
   - Use `redirect` callback to check auth state dynamically
   - Don't use `ref.watch` for auth state at router level

2. **Use StatefulWidget instead of ConsumerStatefulWidget for auth screens**
   - Only access providers in action handlers (onPressed, onSubmitted)
   - Keep all UI state local

3. **Proper auth initialization**
   - Check auth status before showing UI
   - Or show loading screen while checking

---

## Glassmorphism Design System

### What is Glassmorphism?
A design trend featuring:
- **Frosted glass effect** - Blur behind semi-transparent surfaces
- **Subtle borders** - Light borders that catch light
- **Vibrant backgrounds** - Colorful gradients behind glass
- **Depth through layering** - Multiple glass layers create depth

### Color Palette

```dart
// Background Gradient
static const backgroundGradient = LinearGradient(
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
  colors: [
    Color(0xFF1A1A2E),  // Deep navy
    Color(0xFF16213E),  // Dark blue
    Color(0xFF0F3460),  // Royal blue
    Color(0xFF1A1A2E),  // Deep navy
  ],
);

// Glass Effect Colors
static const glassWhite = Color(0x1AFFFFFF);      // 10% white
static const glassBorder = Color(0x33FFFFFF);     // 20% white
static const glassHighlight = Color(0x4DFFFFFF);  // 30% white

// Accent Colors (Vietnamese Imperial)
static const accentGold = Color(0xFFD4A84B);
static const accentGoldLight = Color(0xFFE8C87E);
static const accentRed = Color(0xFFDC2626);

// Text Colors
static const textPrimary = Color(0xFFF5F0E6);
static const textSecondary = Color(0xAAF5F0E6);
static const textMuted = Color(0x77F5F0E6);
```

### Glass Container Widget

```dart
class GlassContainer extends StatelessWidget {
  final Widget child;
  final double blur;
  final double opacity;
  final BorderRadius? borderRadius;
  final EdgeInsets? padding;

  const GlassContainer({
    super.key,
    required this.child,
    this.blur = 10,
    this.opacity = 0.1,
    this.borderRadius,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: borderRadius ?? BorderRadius.circular(16),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
        child: Container(
          padding: padding ?? const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(opacity),
            borderRadius: borderRadius ?? BorderRadius.circular(16),
            border: Border.all(
              color: Colors.white.withOpacity(0.2),
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: child,
        ),
      ),
    );
  }
}
```

### Glass TextField

```dart
class GlassTextField extends StatelessWidget {
  final TextEditingController controller;
  final String hintText;
  final bool obscureText;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final Widget? suffixIcon;
  final ValueChanged<String>? onSubmitted;

  const GlassTextField({
    super.key,
    required this.controller,
    required this.hintText,
    this.obscureText = false,
    this.keyboardType,
    this.textInputAction,
    this.suffixIcon,
    this.onSubmitted,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
        child: TextField(
          controller: controller,
          obscureText: obscureText,
          keyboardType: keyboardType,
          textInputAction: textInputAction,
          onSubmitted: onSubmitted,
          style: const TextStyle(
            color: Color(0xFFF5F0E6),
            fontSize: 16,
          ),
          cursorColor: const Color(0xFFD4A84B),
          decoration: InputDecoration(
            hintText: hintText,
            hintStyle: TextStyle(
              color: const Color(0xFFF5F0E6).withOpacity(0.4),
            ),
            filled: true,
            fillColor: Colors.white.withOpacity(0.08),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 20,
              vertical: 18,
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: Colors.white.withOpacity(0.1),
              ),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: Colors.white.withOpacity(0.15),
              ),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(
                color: Color(0xFFD4A84B),
                width: 2,
              ),
            ),
            suffixIcon: suffixIcon,
          ),
        ),
      ),
    );
  }
}
```

### Glass Button

```dart
class GlassButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isPrimary;

  const GlassButton({
    super.key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.isPrimary = true,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: isLoading ? null : onPressed,
            borderRadius: BorderRadius.circular(12),
            child: Container(
              height: 56,
              decoration: BoxDecoration(
                gradient: isPrimary
                    ? const LinearGradient(
                        colors: [
                          Color(0xFFD4A84B),
                          Color(0xFFE8C87E),
                        ],
                      )
                    : null,
                color: isPrimary ? null : Colors.white.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: isPrimary
                    ? null
                    : Border.all(
                        color: Colors.white.withOpacity(0.2),
                      ),
              ),
              child: Center(
                child: isLoading
                    ? SizedBox(
                        height: 24,
                        width: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          color: isPrimary
                              ? const Color(0xFF1A1A2E)
                              : Colors.white,
                        ),
                      )
                    : Text(
                        text,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: isPrimary
                              ? const Color(0xFF1A1A2E)
                              : Colors.white,
                        ),
                      ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
```

### Animated Background

```dart
class AnimatedGradientBackground extends StatefulWidget {
  final Widget child;

  const AnimatedGradientBackground({
    super.key,
    required this.child,
  });

  @override
  State<AnimatedGradientBackground> createState() =>
      _AnimatedGradientBackgroundState();
}

class _AnimatedGradientBackgroundState
    extends State<AnimatedGradientBackground>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 10),
      vsync: this,
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color.lerp(
                  const Color(0xFF1A1A2E),
                  const Color(0xFF0F3460),
                  _controller.value,
                )!,
                Color.lerp(
                  const Color(0xFF16213E),
                  const Color(0xFF1A1A2E),
                  _controller.value,
                )!,
                Color.lerp(
                  const Color(0xFF0F3460),
                  const Color(0xFF16213E),
                  _controller.value,
                )!,
              ],
            ),
          ),
          child: widget.child,
        );
      },
    );
  }
}
```

---

## Implementation Plan

### Phase 1: Fix Core Architecture (Critical)

#### Task 1.1: Fix GoRouter Provider
**File:** `lib/routing/app_router.dart`

Changes:
- Remove `ref.watch(authNotifierProvider)` from provider function
- Create GoRouter once with redirect callback
- Use `ref.read` inside redirect callback (not `ref.watch`)

```dart
@riverpod
GoRouter appRouter(AppRouterRef ref) {
  // DON'T watch auth state here - it causes rebuilds
  
  return GoRouter(
    initialLocation: '/login',  // Start at login, redirect if authenticated
    debugLogDiagnostics: true,
    
    redirect: (context, state) {
      // Use ref.read inside redirect - this is called on navigation
      final authState = ref.read(authNotifierProvider);
      
      final isLoggedIn = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation == '/login' ||
          state.matchedLocation == '/register';
      
      // Still loading auth status
      if (authState.isInitial || authState.isLoading) {
        return null;  // Stay on current route
      }
      
      // Not logged in and not on auth route
      if (!isLoggedIn && !isAuthRoute) {
        return '/login';
      }
      
      // Logged in and on auth route
      if (isLoggedIn && isAuthRoute) {
        return '/explore';
      }
      
      return null;
    },
    
    routes: [...],
  );
}
```

#### Task 1.2: Fix Auth Provider Initialization
**File:** `lib/features/auth/presentation/providers/auth_provider.dart`

Changes:
- Don't call async function in build()
- Provide a separate method to initialize auth

```dart
@riverpod
class AuthNotifier extends _$AuthNotifier {
  @override
  AuthState build() {
    // Start as unauthenticated - don't do async work here
    return const AuthState.unauthenticated();
  }
  
  /// Call this once from app initialization
  Future<void> initialize() async {
    if (state != const AuthState.unauthenticated()) return;
    
    state = const AuthState.loading();
    
    final isLoggedIn = await _repository.isLoggedIn();
    if (!isLoggedIn) {
      state = const AuthState.unauthenticated();
      return;
    }
    
    final result = await _repository.getCurrentUser();
    result.fold(
      (failure) => state = const AuthState.unauthenticated(),
      (user) => state = AuthState.authenticated(user: user),
    );
  }
}
```

#### Task 1.3: Initialize Auth in main.dart
**File:** `lib/main.dart`

```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // ... other init code ...
  
  runApp(
    ProviderScope(
      child: Consumer(
        builder: (context, ref, child) {
          // Initialize auth once
          ref.read(authNotifierProvider.notifier).initialize();
          return const LuuniensukiApp();
        },
      ),
    ),
  );
}
```

### Phase 2: Rebuild Auth Screens with Glassmorphism

#### Task 2.1: Create Glass UI Components
**Directory:** `lib/shared/widgets/glass/`

Files to create:
- `glass_container.dart`
- `glass_text_field.dart`
- `glass_button.dart`
- `animated_background.dart`
- `glass_card.dart`

#### Task 2.2: Rebuild Login Screen
**File:** `lib/features/auth/presentation/screens/login_screen.dart`

Key changes:
- Use plain `StatefulWidget` (not ConsumerStatefulWidget)
- Only access providers in button handlers
- Use glassmorphism UI components
- Animated gradient background
- Glass card for form
- Glass text fields
- Glass buttons

#### Task 2.3: Rebuild Register Screen
**File:** `lib/features/auth/presentation/screens/register_screen.dart`

Same approach as login screen.

### Phase 3: Update Theme & Colors

#### Task 3.1: Update App Colors
**File:** `lib/core/theme/app_colors.dart`

Add glassmorphism color palette.

#### Task 3.2: Update App Theme
**File:** `lib/core/theme/app_theme.dart`

- Remove complex InputDecorationTheme (let glass widgets handle it)
- Update button themes for glass effect
- Add glass-compatible text styles

### Phase 4: Implement Remaining Screens

#### Task 4.1: Explore Screen (Urn Grid)
- Glass cards for urn tiles
- Animated selection effects

#### Task 4.2: Collection Screen
- Glass filter chips
- Glass grid items

#### Task 4.3: Profile Screen
- Glass stat cards
- Glass avatar container

#### Task 4.4: Achievements Screen
- Glass tabs
- Glass badge cards

---

## File Structure

```
lib/
├── main.dart                          # App entry point
├── app.dart                           # MaterialApp configuration
│
├── core/
│   ├── theme/
│   │   ├── app_colors.dart            # Updated with glass colors
│   │   ├── app_theme.dart             # Simplified theme
│   │   └── app_typography.dart        # Text styles
│   ├── network/                       # (unchanged)
│   ├── storage/                       # (unchanged)
│   └── errors/                        # (unchanged)
│
├── routing/
│   ├── app_router.dart                # Fixed router (no rebuild)
│   ├── app_router.g.dart
│   └── route_names.dart
│
├── shared/
│   └── widgets/
│       └── glass/
│           ├── glass_container.dart   # NEW
│           ├── glass_text_field.dart  # NEW
│           ├── glass_button.dart      # NEW
│           ├── glass_card.dart        # NEW
│           ├── animated_background.dart # NEW
│           └── index.dart             # Barrel export
│
├── features/
│   ├── auth/
│   │   ├── data/                      # (unchanged)
│   │   ├── domain/                    # (unchanged)
│   │   └── presentation/
│   │       ├── providers/
│   │       │   ├── auth_provider.dart # Fixed initialization
│   │       │   └── auth_state.dart
│   │       └── screens/
│   │           ├── login_screen.dart  # REBUILT with glass
│   │           └── register_screen.dart # REBUILT with glass
│   │
│   ├── explore/                       # NEW
│   │   └── presentation/
│   │       └── screens/
│   │           └── explore_screen.dart
│   │
│   ├── collection/                    # NEW
│   │   └── presentation/
│   │       └── screens/
│   │           └── collection_screen.dart
│   │
│   ├── profile/                       # NEW
│   │   └── presentation/
│   │       └── screens/
│   │           └── profile_screen.dart
│   │
│   ├── achievements/                  # NEW
│   │   └── presentation/
│   │       └── screens/
│   │           └── achievements_screen.dart
│   │
│   ├── urn_viewer/                    # (unchanged)
│   ├── lesson/                        # (unchanged)
│   └── quiz/                          # (unchanged)
```

---

## Timeline

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| **Phase 1** | Fix core architecture | 2-3 hours |
| Task 1.1 | Fix GoRouter provider | 30 min |
| Task 1.2 | Fix Auth provider | 30 min |
| Task 1.3 | Fix main.dart | 15 min |
| Test & verify | | 1-2 hours |
| **Phase 2** | Glassmorphism auth screens | 4-6 hours |
| Task 2.1 | Create glass components | 2-3 hours |
| Task 2.2 | Rebuild login screen | 1-2 hours |
| Task 2.3 | Rebuild register screen | 1 hour |
| **Phase 3** | Theme updates | 1-2 hours |
| **Phase 4** | Remaining screens | 6-8 hours |
| Task 4.1 | Explore screen | 2 hours |
| Task 4.2 | Collection screen | 2 hours |
| Task 4.3 | Profile screen | 2 hours |
| Task 4.4 | Achievements screen | 2 hours |

**Total: 13-19 hours**

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Can tap on TextField and keyboard appears
- [ ] Can type in TextField
- [ ] Form submission works
- [ ] Login/Register navigation works
- [ ] No screen rebuilds when typing

### Phase 2 Complete When:
- [ ] Login screen has glassmorphism design
- [ ] Register screen has glassmorphism design
- [ ] Animated gradient background works
- [ ] Glass blur effect is visible
- [ ] All inputs are functional

### Phase 3 Complete When:
- [ ] Theme colors updated
- [ ] Consistent styling across app
- [ ] No theme conflicts

### Phase 4 Complete When:
- [ ] All placeholder screens replaced
- [ ] Navigation works between all screens
- [ ] Data loads from API
- [ ] Glass design consistent

---

## Next Steps

1. **Immediate:** Start Phase 1 - Fix the core architecture bug
2. **After Phase 1 verified:** Proceed with Phase 2 glass components
3. **Build and test APK after each phase**