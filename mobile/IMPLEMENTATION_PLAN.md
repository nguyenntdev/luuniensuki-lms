# Mobile App Implementation Plan - Lưu Niên Sử Kí

**Date:** January 11, 2025
**Version:** 2.0
**Status:** In Progress

---

## Executive Summary

This plan outlines the complete implementation roadmap to bring the mobile app to feature parity with the web application, with modern glassmorphism UI/UX design.

---

## Current State Analysis

### Web Features (Frontend)
| Feature | Path | Status in Mobile |
|---------|------|------------------|
| Login/Register | `/login`, `/register` | ✅ Implemented |
| Explore (Urn Grid) | `/explore` | ❌ Placeholder |
| Collection | `/collection` | ❌ Placeholder |
| Achievements (Badges + Leaderboard) | `/achievements` | ❌ Placeholder |
| Profile | `/profile` | ❌ Placeholder |
| Urn 3D Viewer | `/urns/[urnSlug]` | ⚠️ Partial (screen exists) |
| Motif Detail | `/motif/[motifId]` | ⚠️ Partial (screen exists) |
| Quiz | `/motif/[motifId]/quiz` | ⚠️ Partial (screen exists) |
| Quests | `/quests` | ❌ Not implemented |
| Certificates | `/certificates` | ❌ Not implemented |

### Mobile-Specific Components Needed
| Component | Status |
|-----------|--------|
| Glass UI Components | ⚠️ Partial (need enhancement) |
| Bottom Navigation | ✅ Implemented |
| Pull-to-refresh | ❌ Not implemented |
| Offline caching | ⚠️ Partial (Hive setup done) |
| Loading states/Shimmer | ❌ Not implemented |

---

## Implementation Tasks

### Phase 1: Core Screens (Priority: HIGH)

#### Task 1.1: Explore Screen - Urn Grid
**Description:** Display all 9 urns in a grid with progress indicators
**Files to create/modify:**
- `lib/features/explore/presentation/screens/explore_screen.dart`
- `lib/features/explore/presentation/widgets/urn_card.dart`
- `lib/features/explore/data/repositories/urn_repository.dart`
- `lib/features/explore/domain/entities/urn.dart`

**UI Requirements:**
- Glassmorphism cards for each urn
- Progress ring showing discovery percentage
- Urn thumbnail image
- Vietnamese name + English name
- Tap to navigate to 3D viewer

#### Task 1.2: Collection Screen
**Description:** Show user's discovered motifs organized by urn
**Files to create/modify:**
- `lib/features/collection/presentation/screens/collection_screen.dart`
- `lib/features/collection/presentation/widgets/motif_card.dart`
- `lib/features/collection/presentation/widgets/filter_chips.dart`

**UI Requirements:**
- Filter by: All, Discovered, Learned, Mastered
- Glassmorphism motif cards
- Progress badge (status icon)
- Grouped by urn with collapsible sections

#### Task 1.3: Achievements Screen
**Description:** Combined badges and leaderboard with tabs
**Files to create/modify:**
- `lib/features/achievements/presentation/screens/achievements_screen.dart`
- `lib/features/achievements/presentation/widgets/badge_card.dart`
- `lib/features/achievements/presentation/widgets/leaderboard_item.dart`

**UI Requirements:**
- Tab bar: Huy Hiệu | Bảng Xếp Hạng
- Glassmorphism badge cards (earned vs locked)
- Leaderboard with rank, avatar, name, XP
- Current user highlighted

#### Task 1.4: Profile Screen
**Description:** User profile with stats and settings
**Files to create/modify:**
- `lib/features/profile/presentation/screens/profile_screen.dart`
- `lib/features/profile/presentation/widgets/stat_card.dart`
- `lib/features/profile/presentation/widgets/xp_progress_bar.dart`

**UI Requirements:**
- Avatar with edit button
- Display name, username, email
- XP progress to next rank
- Stats grid: Motifs discovered, learned, mastered
- Streak counter
- Settings button
- Logout button

---

### Phase 2: Enhanced Screens (Priority: MEDIUM)

#### Task 2.1: Enhance 3D Urn Viewer
**Description:** Improve the 3D viewer with hotspots and interactions
**Files to modify:**
- `lib/features/urn_viewer/presentation/screens/urn_viewer_screen.dart`
- `lib/features/urn_viewer/presentation/widgets/hotspot_overlay.dart`

**Features:**
- Hotspot markers on 3D model
- Tap hotspot to discover motif
- Progress indicator overlay
- Back button + share button

#### Task 2.2: Enhance Motif Detail Screen
**Description:** Full lesson content with progress stepper
**Files to modify:**
- `lib/features/lesson/presentation/screens/motif_detail_screen.dart`
- `lib/features/lesson/presentation/widgets/lesson_content.dart`
- `lib/features/lesson/presentation/widgets/progress_stepper.dart`

**Features:**
- 3-step stepper: Khám Phá → Bài Học → Trắc Nghiệm
- Lesson sections: Intro, Description, Symbolism, History, Fun Fact
- "Hoàn thành bài học" button
- Navigate to quiz

#### Task 2.3: Enhance Quiz Screen
**Description:** Interactive quiz with results
**Files to modify:**
- `lib/features/quiz/presentation/screens/quiz_screen.dart`
- `lib/features/quiz/presentation/widgets/question_card.dart`
- `lib/features/quiz/presentation/widgets/quiz_result.dart`

**Features:**
- Question counter (1/5)
- Multiple choice options (glassmorphism)
- Timer display
- Results screen with score, badges earned, XP gained

---

### Phase 3: Glassmorphism UI Components (Priority: HIGH)

#### Task 3.1: Create/Enhance Glass Components
**Files to create/modify:**
- `lib/shared/widgets/glass/glass_card.dart`
- `lib/shared/widgets/glass/glass_app_bar.dart`
- `lib/shared/widgets/glass/glass_bottom_nav.dart`
- `lib/shared/widgets/glass/glass_chip.dart`
- `lib/shared/widgets/glass/glass_progress_bar.dart`
- `lib/shared/widgets/glass/animated_background.dart`

**Design Specs:**
```dart
// Colors
const backgroundGradient = [Color(0xFF1A1A2E), Color(0xFF16213E), Color(0xFF0F3460)];
const glassWhite = Color(0x1AFFFFFF); // 10% white
const glassBorder = Color(0x33FFFFFF); // 20% white
const accentGold = Color(0xFFD4A84B);
const accentGoldLight = Color(0xFFE8C87E);

// Glass effect
BorderRadius: 16-20px
Border: 1px solid glassBorder
Background: glassWhite
Shadow: subtle drop shadow
```

#### Task 3.2: Loading States
**Files to create:**
- `lib/shared/widgets/loading/shimmer_card.dart`
- `lib/shared/widgets/loading/shimmer_list.dart`
- `lib/shared/widgets/loading/loading_overlay.dart`

---

### Phase 4: Data Layer (Priority: HIGH)

#### Task 4.1: API Integration
**Files to create/modify:**
- `lib/features/explore/data/datasources/urn_remote_datasource.dart`
- `lib/features/collection/data/datasources/progress_remote_datasource.dart`
- `lib/features/achievements/data/datasources/badges_remote_datasource.dart`
- `lib/features/achievements/data/datasources/leaderboard_remote_datasource.dart`

**Endpoints to integrate:**
- `GET /api/v1/urns` - List all urns
- `GET /api/v1/urns/:slug` - Urn detail with motifs
- `GET /api/v1/users/me/progress` - User progress
- `GET /api/v1/badges` - All badges
- `GET /api/v1/users/me/badges` - User's badges
- `GET /api/v1/leaderboard` - Leaderboard

#### Task 4.2: Offline Caching with Hive
**Files to modify:**
- `lib/core/storage/hive_storage.dart`

**Cache Strategy:**
- Cache urns list on first load
- Cache user progress
- Cache badges (refresh on pull)
- Show cached data immediately, refresh in background

---

### Phase 5: Polish & UX (Priority: MEDIUM)

#### Task 5.1: Animations
- Page transitions (slide, fade)
- XP gain animation (confetti)
- Badge unlock animation
- Progress bar animations

#### Task 5.2: Error Handling
- Network error screens
- Retry buttons
- Offline mode indicators

#### Task 5.3: Pull-to-Refresh
- All list screens
- Refresh indicators

---

## Implementation Order

1. **Task 3.1** - Glass UI Components (foundation for all screens)
2. **Task 1.1** - Explore Screen (main entry point after login)
3. **Task 4.1** - API Integration for Explore
4. **Task 1.4** - Profile Screen (user context)
5. **Task 1.2** - Collection Screen
6. **Task 1.3** - Achievements Screen
7. **Task 2.1-2.3** - Enhance existing screens
8. **Task 5.1-5.3** - Polish

---

## Success Criteria

- [ ] All placeholder screens replaced with functional screens
- [ ] API integration complete for all endpoints
- [ ] Glassmorphism design consistent across app
- [ ] Login/logout flow works correctly
- [ ] Progress tracking works (discover → learn → master)
- [ ] Offline mode shows cached data
- [ ] No crashes on Android 10+
- [ ] APK size < 25MB

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1 | 4-6 hours | 🔄 In Progress |
| Phase 2 | 3-4 hours | ⏳ Pending |
| Phase 3 | 2-3 hours | ⏳ Pending |
| Phase 4 | 3-4 hours | ⏳ Pending |
| Phase 5 | 2-3 hours | ⏳ Pending |

**Total Estimated Time:** 14-20 hours

---

## Notes

- All screens should use dark theme with glassmorphism
- Vietnamese is primary language, English secondary
- Reuse web API - no backend changes needed
- Focus on mobile-first UX (touch targets, gestures)