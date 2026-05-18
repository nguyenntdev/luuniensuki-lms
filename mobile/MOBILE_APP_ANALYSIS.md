# Mobile App Analysis & Implementation Plan

## Table of Contents
1. [Infinite Scroll Bug Deep Dive](#infinite-scroll-bug-deep-dive)
2. [Missing Features from Web Edition](#missing-features-from-web-edition)
3. [Implementation Plan](#implementation-plan)

---

## Infinite Scroll Bug Deep Dive

### Problem Description
Login and Register screens exhibit "infinite scroll" behavior where:
- The page scrolls continuously without stopping
- Input fields (TextFormField) are not tappable/focusable
- The gray input box appears to expand infinitely

### Screenshot Analysis
From the provided screenshot:
- Logo and title render correctly at top
- Form card starts rendering with "Email" label
- Below the label, a massive gray area fills the screen
- This gray area is the TextFormField's fill color expanding uncontrollably

### Root Cause Analysis

#### 1. Flutter Version & InputDecoration Issue
- Flutter 3.24.5 has known issues with `InputDecoration` when:
  - `filled: true` is set
  - No explicit `constraints` are provided
  - The parent widget doesn't constrain height properly

#### 2. SingleChildScrollView + Column + TextFormField Interaction
The problematic widget tree:
```
Scaffold
└── SafeArea
    └── SingleChildScrollView
        └── Column (crossAxisAlignment: stretch)
            └── Container (Form Card)
                └── Form
                    └── Column (mainAxisSize: min)
                        └── TextFormField ← PROBLEM HERE
```

When `crossAxisAlignment: CrossAxisAlignment.stretch` is used with `SingleChildScrollView`, and the `TextFormField` doesn't have explicit height constraints, Flutter's layout algorithm can enter an infinite loop trying to calculate the intrinsic height.

#### 3. InputDecoration Border Configuration
The current code uses:
```dart
border: OutlineInputBorder(
  borderRadius: BorderRadius.circular(12),
  borderSide: BorderSide.none,  // ← This can cause issues
),
```

Setting `borderSide: BorderSide.none` on `border` while having different `enabledBorder` and `focusedBorder` configurations can confuse the layout calculation.

#### 4. Form Key Inside StatefulWidget
The `GlobalKey<FormState>` being recreated or the Form widget being rebuilt during hot reload can cause layout issues.

### Verified Solutions

#### Solution 1: Use SizedBox Constraints on TextFormField
Wrap each TextFormField in a SizedBox with explicit height:
```dart
SizedBox(
  height: 52, // Explicit height
  child: TextFormField(...),
)
```

#### Solution 2: Use ConstrainedBox for Form Card
```dart
ConstrainedBox(
  constraints: BoxConstraints(
    maxHeight: MediaQuery.of(context).size.height * 0.7,
  ),
  child: Container(
    // Form card content
  ),
)
```

#### Solution 3: Simplify InputDecoration
Use consistent border configuration:
```dart
decoration: InputDecoration(
  filled: true,
  fillColor: _inputBg,
  isDense: true, // Add this
  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
  border: OutlineInputBorder(
    borderRadius: BorderRadius.circular(12),
    borderSide: BorderSide(color: _border),
  ),
  // Remove separate enabledBorder, focusedBorder, etc.
  // Let Flutter derive them from border
),
```

#### Solution 4: Use ListView instead of Column
```dart
SingleChildScrollView(
  child: Padding(
    padding: EdgeInsets.symmetric(horizontal: 24),
    child: Column(
      mainAxisSize: MainAxisSize.min, // Important!
      children: [
        // widgets
      ],
    ),
  ),
)
```

#### Solution 5: Intrinsic Height (Last Resort)
Wrap the entire scrollable content:
```dart
SingleChildScrollView(
  child: IntrinsicHeight(
    child: Column(...),
  ),
)
```
Note: This is expensive and should be avoided if possible.

### Recommended Fix
Combine Solutions 1, 3, and 4:
1. Add `isDense: true` to all InputDecoration
2. Ensure `mainAxisSize: MainAxisSize.min` on all Columns
3. Wrap TextFormField in SizedBox with explicit height
4. Use consistent border configuration

---

## Missing Features from Web Edition

### Feature Comparison Matrix

| Feature | Web | Mobile | Priority |
|---------|-----|--------|----------|
| **Authentication** |
| Login | ✅ | ✅ (buggy) | P0 |
| Register | ✅ | ✅ (buggy) | P0 |
| OAuth (Google/Facebook) | ❌ | ❌ | P2 |
| Password Reset | ❌ | ❌ | P2 |
| **Navigation** |
| Bottom Navigation | ✅ | ✅ | - |
| Floating Navbar | ✅ | ❌ | P1 |
| **Explore/Home** |
| Urn Grid | ✅ | ❌ (placeholder) | P0 |
| Smart Homepage | ✅ | ❌ | P1 |
| **3D Viewer** |
| Urn 3D Model | ✅ (Three.js) | ✅ (WebView) | - |
| Hotspot Spheres | ✅ | ✅ | - |
| Motif Discovery | ✅ | ✅ | - |
| **Collection** |
| Collection Grid | ✅ | ❌ (placeholder) | P0 |
| Filter by Status | ✅ | ❌ | P1 |
| Filter by Urn | ✅ | ❌ | P1 |
| **Motif Detail** |
| Lesson Content | ✅ | ✅ | - |
| Progress Stepper | ✅ | ❌ | P1 |
| **Quiz** |
| Quiz Questions | ✅ | ✅ | - |
| Timer | ✅ | ❌ | P1 |
| Results Screen | ✅ | ❌ | P1 |
| **Profile** |
| User Stats | ✅ | ❌ (placeholder) | P0 |
| XP Progress | ✅ | ❌ | P0 |
| Rank Display | ✅ | ❌ | P0 |
| Streak Display | ✅ | ❌ | P1 |
| Settings | ✅ | ❌ | P1 |
| **Achievements** |
| Badge Grid | ✅ | ❌ (placeholder) | P0 |
| Leaderboard | ✅ | ❌ (placeholder) | P0 |
| Tab Navigation | ✅ | ❌ | P1 |
| **Gamification** |
| XP Animation | ✅ | ❌ | P2 |
| Confetti | ✅ | ❌ | P2 |
| Level Up Modal | ✅ | ❌ | P2 |
| **Onboarding** |
| Onboarding Wizard | ✅ | ❌ | P1 |
| First-time Tooltips | ✅ | ❌ | P2 |
| **i18n** |
| Vietnamese | ✅ | ✅ | - |
| English | ✅ | ❌ | P2 |
| Language Switcher | ✅ | ❌ | P2 |
| **Offline** |
| Offline Mode | ❌ | ❌ | P2 |
| Data Caching | Partial | Partial | P2 |

### Priority Legend
- **P0**: Critical - Must fix/implement before release
- **P1**: High - Should implement for good UX
- **P2**: Medium - Nice to have

---

## Implementation Plan

### Phase 1: Fix Critical Bugs (P0)

#### Task 1.1: Fix Login Screen Infinite Scroll
**File**: `lib/features/auth/presentation/screens/login_screen.dart`

Changes:
1. Add `isDense: true` to all InputDecoration
2. Wrap TextFormField in SizedBox with height: 52
3. Use consistent border configuration
4. Add `mainAxisSize: MainAxisSize.min` to all Columns

#### Task 1.2: Fix Register Screen Infinite Scroll
**File**: `lib/features/auth/presentation/screens/register_screen.dart`

Same changes as 1.1

#### Task 1.3: Verify Fix
- Build APK
- Test on physical device
- Verify inputs are tappable
- Verify form submission works

### Phase 2: Implement Core Screens (P0)

#### Task 2.1: Explore Screen (Urn Grid)
**File**: `lib/features/explore/presentation/screens/explore_screen.dart`

Features:
- Grid of 9 urns
- Urn thumbnail images
- Urn names
- Navigation to 3D viewer

API: `GET /api/v1/urns`

#### Task 2.2: Collection Screen
**File**: `lib/features/collection/presentation/screens/collection_screen.dart`

Features:
- Grid of discovered motifs
- Status indicators (discovered/learned/mastered)
- Navigation to motif detail

API: `GET /api/v1/progress/motifs`

#### Task 2.3: Profile Screen
**File**: `lib/features/profile/presentation/screens/profile_screen.dart`

Features:
- User avatar and name
- Total XP with progress bar
- Current rank
- Stats (discoveries, lessons, quizzes)

API: `GET /api/v1/auth/me`

#### Task 2.4: Achievements Screen (Badges Tab)
**File**: `lib/features/achievements/presentation/screens/achievements_screen.dart`

Features:
- Tab bar (Badges / Leaderboard)
- Badge grid with locked/unlocked states
- Badge descriptions

API: `GET /api/v1/badges`, `GET /api/v1/badges/earned`

#### Task 2.5: Achievements Screen (Leaderboard Tab)
Features:
- Top 10 users list
- User rank, name, XP
- Current user highlight

API: `GET /api/v1/leaderboard`

### Phase 3: Enhance UX (P1)

#### Task 3.1: Progress Stepper in Motif Detail
**File**: `lib/features/lesson/presentation/widgets/progress_stepper.dart`

Visual stepper showing:
- Khám Phá (25 XP) - Discovery
- Bài Học (50 XP) - Lesson
- Trắc Nghiệm (75 XP) - Quiz

#### Task 3.2: Quiz Results Screen
**File**: `lib/features/quiz/presentation/screens/quiz_result_screen.dart`

Features:
- Score display
- Pass/fail indication
- XP earned animation
- Return to motif button

#### Task 3.3: Onboarding Wizard
**File**: `lib/features/onboarding/presentation/screens/onboarding_screen.dart`

4 steps:
1. Welcome
2. 3D Exploration intro
3. Learning flow intro
4. Gamification intro

#### Task 3.4: Streak Display
Add streak counter to Profile screen

#### Task 3.5: Collection Filters
Add filter chips for:
- Status (All, Discovered, Learned, Mastered)
- Urn (All 9 urns)

### Phase 4: Polish (P2)

#### Task 4.1: XP Animation System
Global XP award animation when XP is earned

#### Task 4.2: Confetti Animation
Use `confetti` package for celebrations

#### Task 4.3: English Language Support
Add English translations

#### Task 4.4: Settings Screen
- Language switcher
- Notification preferences
- Account management

---

## File Structure for New Features

```
lib/features/
├── explore/
│   ├── data/
│   │   ├── datasources/
│   │   │   └── explore_remote_datasource.dart
│   │   ├── models/
│   │   │   └── urn_dto.dart
│   │   └── repositories/
│   │       └── explore_repository_impl.dart
│   ├── domain/
│   │   ├── entities/
│   │   │   └── urn.dart
│   │   └── repositories/
│   │       └── explore_repository.dart
│   └── presentation/
│       ├── providers/
│       │   └── explore_provider.dart
│       ├── screens/
│       │   └── explore_screen.dart
│       └── widgets/
│           └── urn_card.dart
├── collection/
│   └── (same structure)
├── profile/
│   └── (same structure)
├── achievements/
│   └── (same structure)
└── onboarding/
    └── (same structure)
```

---

## Testing Checklist

### After Phase 1 (Bug Fixes)
- [ ] Login screen renders correctly
- [ ] Email field is tappable
- [ ] Password field is tappable
- [ ] Form submits successfully
- [ ] Register screen renders correctly
- [ ] All register fields are tappable
- [ ] Registration works end-to-end

### After Phase 2 (Core Screens)
- [ ] Explore screen shows 9 urns
- [ ] Tapping urn navigates to 3D viewer
- [ ] Collection screen shows user's motifs
- [ ] Profile screen shows user stats
- [ ] Achievements tabs work
- [ ] Badge grid displays correctly
- [ ] Leaderboard shows rankings

### After Phase 3 (UX Enhancements)
- [ ] Progress stepper shows correct states
- [ ] Quiz results display properly
- [ ] Onboarding runs for new users
- [ ] Streak displays on profile

---

## Estimated Timeline

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1 | Bug fixes | 1-2 hours |
| Phase 2 | Core screens | 8-12 hours |
| Phase 3 | UX enhancements | 4-6 hours |
| Phase 4 | Polish | 4-6 hours |

**Total**: 17-26 hours

---

## Next Steps

1. **Immediate**: Fix login/register infinite scroll bug
2. **Today**: Build and test APK
3. **This week**: Implement Phase 2 core screens
4. **Next week**: Phase 3 UX enhancements