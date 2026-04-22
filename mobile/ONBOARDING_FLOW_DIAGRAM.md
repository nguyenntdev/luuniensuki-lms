# Onboarding Flow Visualization

## User Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        APP LAUNCH                               │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │  Auth Check   │
              │ (AuthProvider)│
              └───────┬───────┘
                      │
              ┌───────┴───────┐
              │               │
              ▼               ▼
      ┌──────────────┐   ┌──────────────┐
      │ Not Logged In│   │  Logged In   │
      └──────┬───────┘   └──────┬───────┘
             │                  │
             ▼                  ▼
      ┌──────────────┐   ┌──────────────┐
      │ Login Screen │   │ Check        │
      │              │   │ hasSeenOnb?  │
      └──────┬───────┘   └──────┬───────┘
             │                  │
             │           ┌──────┴──────┐
             │           │             │
             │           ▼             ▼
             │      ┌─────────┐   ┌─────────┐
             │      │   No    │   │   Yes   │
             │      │(Show Onb)   │ (Skip)  │
             │      └────┬────┘   └────┬────┘
             │           │             │
             │           ▼             │
             │      ┌──────────────┐   │
             │      │  ONBOARDING  │   │
             │      │   SCREEN     │   │
             │      └──────┬───────┘   │
             │             │           │
             │      ┌──────┴──────┐    │
             │      │             │    │
             │      ▼             ▼    │
             │   ┌──────┐    ┌──────┐ │
             │   │ Skip │    │Finish│ │
             │   └──┬───┘    └──┬───┘ │
             │      │           │     │
             │      ▼           ▼     │
             │   ┌─────────────────┐  │
             │   │ Save hasSeenOnb │  │
             │   │    = true       │  │
             │   └────────┬────────┘  │
             │            │           │
             └────────────┼───────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │    EXPLORE   │
                  │    SCREEN    │
                  └──────────────┘
```

## Onboarding Screen Internal Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ONBOARDING SCREEN                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  AnimatedGradientBackground               │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │              Top Bar (Skip Button)                 │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │                                                     │  │  │
│  │  │              PageView (Slides 1-4)                │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌──────────────────────────────────────────────┐ │  │  │
│  │  │  │  Slide 1: Chào mừng                          │ │  │  │
│  │  │  │  - Icon: auto_awesome                        │ │  │  │
│  │  │  │  - Title: "Chào mừng..."                     │ │  │  │
│  │  │  │  - Description in GlassContainer             │ │  │  │
│  │  │  └──────────────────────────────────────────────┘ │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌──────────────────────────────────────────────┐ │  │  │
│  │  │  │  Slide 2: Khám phá 3D                        │ │  │  │
│  │  │  │  - Icon: view_in_ar_rounded                  │ │  │  │
│  │  │  │  - Description                               │ │  │  │
│  │  │  └──────────────────────────────────────────────┘ │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌──────────────────────────────────────────────┐ │  │  │
│  │  │  │  Slide 3: Gamification                       │ │  │  │
│  │  │  │  - Icon: emoji_events_rounded                │ │  │  │
│  │  │  │  - Hearts ❤️  Gems 💎  Streaks 🔥            │ │  │  │
│  │  │  └──────────────────────────────────────────────┘ │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌──────────────────────────────────────────────┐ │  │  │
│  │  │  │  Slide 4: Daily Goals                        │ │  │  │
│  │  │  │  - Icon: track_changes_rounded               │ │  │  │
│  │  │  │  - ○ Thư giãn (5 XP/ngày)                    │ │  │  │
│  │  │  │  - ● Thường xuyên (10 XP/ngày)               │ │  │  │
│  │  │  │  - ○ Nghiêm túc (20 XP/ngày)                 │ │  │  │
│  │  │  └──────────────────────────────────────────────┘ │  │  │
│  │  │                                                     │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │          Page Indicator (Animated Dots)           │  │  │
│  │  │              ──── ○ ○ ○                           │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │   Navigation Button (Next / Bắt đầu)              │  │  │
│  │  │   [────────── Tiếp theo →  ──────────]            │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Animation Timeline (per slide)

```
Time: 0ms ───────────────────────────────────────────────────── 800ms

Icon:
  Scale:    [0.5 ──────────────▶ 1.0]
  Rotation: [-0.2 ─────────────▶ 0.0]
  ████████████████████████████░░░░░░░░  (0-600ms, elastic)

Content:
  Slide:    [down ────────────▶ up]
  Fade:     [0.0 ─────────────▶ 1.0]
  ░░░░░░░░░░░░██████████████████████  (300-800ms, ease out)

Page Indicator:
  Width:    [8px ───────────▶ 32px]
  ████████████████████████  (300ms, ease in out)
```

## State Management

```
┌─────────────────────────────────────────────────────┐
│               OnboardingScreen State                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Variables:                                         │
│  - _currentPage: int                                │
│  - _pageController: PageController                  │
│  - _animationController: AnimationController        │
│  - _fadeAnimation: Animation<double>                │
│                                                     │
│  Methods:                                           │
│  - _onPageChanged(int page)                         │
│  - _nextPage()                                      │
│  - _skipOnboarding()                                │
│  - _completeOnboarding()                            │
│                                                     │
│  Dependencies:                                      │
│  - ref.read(hiveStorageProvider)                    │
│  - context.go('/explore')                           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Component Hierarchy

```
OnboardingScreen (ConsumerStatefulWidget)
│
├── Scaffold
│   └── AnimatedGradientBackground
│       └── SafeArea
│           └── Column
│               ├── _buildTopBar()
│               │   └── TextButton (Skip)
│               │
│               ├── PageView.builder
│               │   └── FadeTransition
│               │       └── OnboardingPage
│               │           ├── GlassContainer (Icon)
│               │           ├── Text (Title)
│               │           ├── GlassContainer (Description)
│               │           └── _buildFeatureHighlight()
│               │               ├── _buildGamificationIcons()
│               │               │   └── 3x GlassContainer (Hearts, Gems, Streaks)
│               │               └── _buildGoalOptions()
│               │                   └── 3x GlassContainer (Goals)
│               │
│               ├── PageIndicator
│               │   └── Row (4x AnimatedContainer dots)
│               │
│               └── _buildNavigationButton()
│                   └── GlassButton (Next/Bắt đầu)
```

## Data Flow

```
User Action                    State Change                Navigation
───────────────────────────────────────────────────────────────────────

Swipe/Tap Next        ──▶  _currentPage++          ──▶  PageView animates
                           _animationController          to next slide
                           .reset() + .forward()
                                                         Page indicator
                                                         updates

Tap Skip              ──▶  setHasSeenOnboarding    ──▶  context.go(
                           (true)                        '/explore')

Complete Last Slide   ──▶  setHasSeenOnboarding    ──▶  context.go(
                           (true)                        '/explore')

App Launch            ──▶  router checks           ──▶  if !hasSeenOnboarding
                           hasSeenOnboarding()           redirect to
                                                         '/onboarding'
```

## Router Decision Tree

```
                    Router Redirect Check
                            │
                    ┌───────┴────────┐
                    │                │
                  Auth?          Onboarding?
                    │                │
        ┌───────────┼────────┐       │
        │                    │       │
     Not Auth             Auth       │
        │                    │       │
        ▼                    ▼       ▼
   ┌─────────┐      ┌──────────────────┐
   │ /login  │      │ hasSeenOnboarding?│
   └─────────┘      └─────────┬─────────┘
                              │
                     ┌────────┴────────┐
                     │                 │
                    No                Yes
                     │                 │
                     ▼                 ▼
              ┌────────────┐    ┌──────────┐
              │/onboarding │    │ /explore │
              └────────────┘    └──────────┘
```

---

This visualization helps understand the complete flow and structure of the onboarding implementation.

