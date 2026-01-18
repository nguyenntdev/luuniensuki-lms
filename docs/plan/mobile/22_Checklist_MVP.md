# 22_Checklist_MVP.md — Flutter Mobile App MVP Checklist

## Overview

This document tracks the MVP (Minimum Viable Product) features required for the initial Android release of Luuniensuki LMS.

**Target Release:** Version 1.0.0
**Estimated Timeline:** 12 weeks
**Current Version:** 1.6.0+7 ✅ **MVP COMPLETE + Post-MVP features**
**Last Updated:** 2025-01-17

---

## MVP Scope Definition

### In Scope (Must Have) - ALL COMPLETE ✅
- ✅ User authentication (login, register, logout)
- ✅ Browse urns and motifs
- ✅ 3D urn viewer with hotspot interaction
- ✅ Motif discovery flow
- ✅ Lesson content display (text, images)
- ✅ Quiz system (multiple choice, true/false)
- ✅ Progress tracking
- ✅ XP and rank display
- ✅ Badge collection
- ✅ Basic offline caching

### Out of Scope (Post-MVP) - Many Already Implemented!
- ✅ Audio narration playback → **IMPLEMENTED** (just_audio, sound_service.dart)
- ❌ Video lesson content
- ⚠️ Advanced quiz types → **PARTIAL** (hints system implemented)
- ✅ Quest system → **IMPLEMENTED** (lib/features/quests/)
- ✅ Leaderboard → **IMPLEMENTED** (leaderboard_provider.dart)
- ✅ Push notifications → **IMPLEMENTED** (firebase_messaging)
- ❌ AR mode
- ✅ Social features → **IMPLEMENTED** (lib/features/friends/)
- ❌ Dark mode
- ❌ Multi-language support

---

## Phase 1: Foundation & Auth

### Project Setup
- [x] **P1-S1** Create Flutter project with proper package name ✅
  - Package: `com.luuniensuki.lms` (android/app/build.gradle)
  - Min SDK: 21 (Android 5.0)
  - Target SDK: 34

- [x] **P1-S2** Configure pubspec.yaml with all dependencies ✅
  - flutter_riverpod, go_router, dio, hive_flutter
  - flutter_secure_storage, cached_network_image
  - model_viewer_plus, freezed_annotation

- [x] **P1-S3** Create folder structure following Clean Architecture ✅
  - core/, features/, routing/, shared/

- [x] **P1-S4** Set up code generation ✅
  - build_runner configured
  - Freezed models generating (.freezed.dart, .g.dart files)

### Core Infrastructure
- [x] **P1-I1** Implement API constants with all endpoints ✅
  - Base URL: https://lms.histolab.icu
  - All /api/v1 endpoints defined (85 lines)

- [x] **P1-I2** Implement error classes ✅
  - 7 exception types (lib/core/errors/exceptions.dart)
  - 10 failure classes (lib/core/errors/failures.dart)

- [x] **P1-I3** Implement secure storage wrapper ✅
  - Token storage (access, refresh)
  - Clear tokens on logout

- [x] **P1-I4** Implement Dio client with interceptors ✅
  - Auth interceptor (adds Bearer token)
  - Error interceptor (maps to exceptions)
  - Logging interceptor (debug mode)
  - **Token refresh interceptor** (FIXED 2025-01-17)

- [x] **P1-I5** Implement theme system ✅
  - AppColors (360 lines, Vietnamese imperial gold)
  - AppTheme (355 lines, Material 3)
  - AppTypography (314 lines)

### Authentication
- [x] **P1-A1** Create Auth DTOs with Freezed ✅
  - LoginRequestDto, RegisterRequestDto (152 lines)
  - UserDto, AuthResponseDto, StatsDto, RankDto

- [x] **P1-A2** Create User entity and Rank value object ✅
  - All user properties mapped (246 lines)
  - Role helper getters (isGuest, isLearner, isTeacher, isAdmin)
  - 9 Vietnamese rank levels

- [x] **P1-A3** Implement AuthRepository ✅
  - login, register, getCurrentUser, logout
  - Token refresh handling
  - Cache user locally with offline fallback

- [x] **P1-A4** Implement AuthNotifier provider ✅
  - AuthState (initial, loading, authenticated, unauthenticated, error)
  - Auto-check auth on app start (158 lines)

- [x] **P1-A5** Create Login screen ✅
  - Email/password form (424 lines, with animations)
  - Validation
  - Error display
  - Navigate to register

- [x] **P1-A6** Create Register screen ✅
  - Email, password, confirm password, display name form
  - Validation
  - Success navigation

---

## Phase 2: Core Screens & Navigation

### Navigation
- [x] **P2-N1** Configure GoRouter with all routes ✅
  - Auth routes (login, register) (698 lines)
  - Shell routes (Explore, Learning Hub, AI Chat, Achievements, Profile)
  - Detail routes (urn, motif, quiz)

- [x] **P2-N2** Implement auth redirect guard ✅
  - Redirect to login if not authenticated
  - Redirect to home if already authenticated
  - redirect function in app_router.dart

- [x] **P2-N3** Implement MainShell with bottom navigation ✅
  - 5 tabs with glass morphism design
  - Vietnamese labels
  - Active state highlighting

### Screens
- [x] **P2-H1** Home/Explore screen ✅
  - Note: Home merged into Explore screen
  - explore_screen.dart (590 lines)

- [x] **P2-E1** Implement Explore screen (Urn grid) ✅
  - Grid of urn cards
  - Thumbnail, name, progress indicator
  - Navigate to urn viewer on tap

- [x] **P2-C1** Implement Collection screen ✅
  - collection_screen.dart (556 lines)
  - CollectionFilter enum (all, discovered, learned, mastered)
  - Grid of collected motifs
  - Filter chips

- [x] **P2-A1** Implement Achievements screen ✅
  - achievements_screen.dart (674 lines)
  - Tabs for badges and leaderboard
  - Earned/unearned badge display

- [x] **P2-P1** Implement Profile screen ✅
  - profile_screen.dart (1300 lines)
  - User info, XP progress, streak, gems display
  - Logout button

### Shared Widgets
- [x] **P2-W1** Loading skeleton components ✅
- [x] **P2-W2** Error widget with retry button ✅
- [x] **P2-W3** Empty state widget ✅
- [x] **P2-W4** XpBadge component ✅ (xp_celebration_overlay.dart, 441 lines)
- [x] **P2-W5** RankBadge component ✅
- [x] **P2-W6** CategoryChip and RarityChip ✅

---

## Phase 3: 3D Viewer

### 3D Model Loading
- [x] **P3-M1** Integrate model_viewer_plus package ✅
  - custom_model_viewer.dart (510 lines)
  - GLB model loading from server URL
  - Loading progress indicator
  - Error handling for failed loads
  - **Memory leak FIXED** (2025-01-17 - added dispose())

- [x] **P3-M2** Implement touch controls ✅
  - Rotate (drag)
  - Zoom (pinch)
  - cameraControls enabled in model_viewer_plus

- [x] **P3-M3** Create UrnViewerScreen ✅
  - urn_viewer_screen.dart (1524 lines)
  - Full-screen 3D viewer
  - Transparent app bar with back button
  - Toggle hotspots visibility

### Hotspot System
- [x] **P3-H1** Render hotspots at motif positions ✅
  - hotspot_overlay.dart (239 lines)
  - Circle markers on model
  - Different states (undiscovered pulse, discovered check)

- [x] **P3-H2** Implement tap detection ✅
  - JavaScript bridge for model-viewer hotspots
  - onHotspotTap callback

- [x] **P3-H3** Handle hotspot tap events ✅
  - Identify tapped motif
  - Trigger discovery flow

### Discovery Flow
- [x] **P3-D1** Implement unlock API call ✅
  - POST /progress/unlock with motif_id
  - Handle success response

- [x] **P3-D2** Create discovery animation ✅
  - discovery_animation.dart (407 lines)
  - Celebration animation with XpCelebrationService
  - XP earned display
  - Motif name reveal

- [x] **P3-D3** Update hotspot state after discovery ✅
  - Change from undiscovered to discovered
  - Update local cache via HiveStorage

### Motif Sidebar
- [x] **P3-S1** Create sliding sidebar component ✅
  - motif_sidebar.dart (622 lines)
  - Slide in from right on motif select
  - Motif thumbnail, name, category, rarity

- [x] **P3-S2** Display progress stepper ✅
  - progress_stepper.dart
  - 3 steps: Discovery, Lesson, Quiz
  - Current step highlighted
  - XP values shown (25, 50, 75)

- [x] **P3-S3** Action button based on status ✅
  - "Start Lesson" for discovered (onStartLesson)
  - "Take Quiz" for learned (onStartQuiz)

---

## Phase 4: Learning Flow

### Lesson Display
- [x] **P4-L1** Create MotifDetailScreen ✅
  - motif_detail_screen.dart (460 lines)
  - Hero image header
  - Tab navigation (Lesson, Info)

- [x] **P4-L2** Implement LessonTab ✅
  - lesson_tab.dart (754 lines)
  - Progress stepper
  - Lesson sections (introText, description, symbolism, historicalContext)
  - Image gallery support

- [x] **P4-L3** Create lesson section components ✅
  - _LessonSection widget
  - Title, icon, content display

- [x] **P4-L4** Implement ImageGallery ✅
  - CachedNetworkImage usage
  - Fullscreen viewer capability

- [x] **P4-L5** Implement lesson completion ✅
  - Complete lesson flow
  - XP award animation via XpCelebrationService
  - Gems bonus for completion

### Quiz System
- [x] **P4-Q1** Create QuizScreen ✅
  - quiz_screen.dart (939 lines)
  - Question progress bar
  - Page view for questions
  - Navigation (next/previous)
  - Submit button
  - **Navigation bug FIXED** (2025-01-17)

- [x] **P4-Q2** Implement QuestionCard ✅
  - question_card.dart (435 lines)
  - Question text display
  - Question image support
  - Answer options rendering

- [x] **P4-Q3** Implement MultipleChoiceRenderer ✅
  - Implemented in question_card.dart
  - Option buttons with selection state

- [x] **P4-Q4** Implement TrueFalseRenderer ✅
  - Implemented in question_card.dart
  - Two button options (Đúng/Sai)

- [x] **P4-Q5** Implement quiz submission ✅
  - Collect all answers
  - quiz_provider.dart
  - Quiz submission handling

- [x] **P4-Q6** Create QuizResultScreen ✅
  - quiz_result_screen.dart (846 lines)
  - Pass/fail status with confetti
  - Score percentage
  - XP earned
  - Mascot feedback
  - Gems bonus for perfect score

---

## Phase 5: Gamification (MVP Subset)

### XP & Ranks
- [x] **P5-X1** XP badge component (various sizes) ✅
- [x] **P5-X2** XP progress bar with rank info ✅
- [x] **P5-X3** XP earn animation ✅ (xp_celebration_service.dart, xp_celebration_overlay.dart)

### Badges
- [x] **P5-B1** Fetch all badges from API ✅ (badge_provider.dart)
- [x] **P5-B2** Fetch user's earned badges ✅ (badge_provider.dart)
- [x] **P5-B3** Badge card (earned/unearned states) ✅ (achievements_screen.dart)
- [x] **P5-B4** Badge detail bottom sheet ✅ (badge_detail_sheet.dart)

---

## Phase 6: Offline & Polish (MVP Subset)

### Caching
- [x] **P6-C1** Initialize Hive on app start ✅ (main.dart)
- [x] **P6-C2** Cache urns list ✅ (urn_provider.dart, hive_storage.dart)
- [x] **P6-C3** Cache motif details on view ✅ (motif_detail_provider.dart)
- [x] **P6-C4** Offline-first repository pattern ✅ (offline_first_repository.dart, sync_service.dart)

### Polish
- [x] **P6-P1** Network status indicator ✅ (network_status_indicator.dart)
- [x] **P6-P2** Global error handler ✅ (error_handler.dart)
- [x] **P6-P3** Vietnamese error messages ✅ (error_messages.dart, failures.dart vietnameseMessage getter)
- [x] **P6-P4** App icon and splash screen ✅ (Configured in AndroidManifest.xml)

---

## Testing Requirements

### Unit Tests (Minimum)
- [x] **T-U1** AuthRepository tests (login, register, logout) ✅ (auth_repository_test.dart - 12 tests)
- [x] **T-U2** Progress calculation tests ✅ (progress_calculation_test.dart - 29 tests)
- [x] **T-U3** Quiz scoring tests ✅ (quiz_scoring_test.dart - 24 tests)

### Widget Tests (Minimum)
- [x] **T-W1** Login form validation ✅ (login_form_test.dart - 17 tests)
- [x] **T-W2** ProgressStepper states ✅ (progress_stepper_test.dart - 7 tests)
- [x] **T-W3** QuestionCard rendering ✅ (question_card_test.dart - 15 tests)

### Integration Tests (Minimum)
- [ ] **T-I1** Auth flow (register → login → logout)
- [ ] **T-I2** Discovery flow (tap hotspot → unlock)
- [ ] **T-I3** Quiz flow (answer → submit → result)

### Manual Testing
- [ ] **T-M1** Test on low-end device (2GB RAM)
- [ ] **T-M2** Test on tablet
- [ ] **T-M3** Test with slow network (3G)
- [ ] **T-M4** Test offline mode
- [ ] **T-M5** Test session expiry

---

## Release Checklist

### Build Configuration
- [x] **R-B1** Release signing key generated ✅ (release-keystore.jks)
- [x] **R-B2** keystore.jks secured (not in repo) ✅ (key.properties)
- [x] **R-B3** Build variants configured (debug, release) ✅
- [x] **R-B4** ProGuard/R8 rules if needed ✅ (proguard-rules.pro - 123 lines)
- [x] **R-B5** Version code/name set (1.6.0+7) ✅

### Play Store Preparation
- [ ] **R-P1** Developer account created
- [ ] **R-P2** App icon (512x512)
- [ ] **R-P3** Feature graphic (1024x500)
- [ ] **R-P4** Screenshots (phone, tablet)
- [ ] **R-P5** App description (Vietnamese)
- [ ] **R-P6** Privacy policy URL
- [ ] **R-P7** Content rating questionnaire
- [ ] **R-P8** Target audience declaration

### Final Verification
- [x] **R-V1** No debug logs in release build ✅ (kDebugMode wrapped)
- [x] **R-V2** API pointing to production ✅ (https://lms.histolab.icu)
- [x] **R-V3** Crash reporting enabled ✅ (Firebase configured)
- [x] **R-V4** Analytics tracking (if any) ✅
- [x] **R-V5** All TODO comments addressed ✅ (non-critical future features)

---

## Metrics & Success Criteria

### Performance Targets
| Metric | Target | Measurement |
|--------|--------|-------------|
| Cold start time | < 3 seconds | Stopwatch from tap to interactive |
| 3D model load | < 5 seconds on 4G | DevTools network tab |
| Frame rate | 60 fps | DevTools performance |
| Memory usage | < 300 MB | Android Profiler |
| APK size | < 50 MB | Build output |

### Quality Targets
| Metric | Target |
|--------|--------|
| Crash-free rate | > 99% |
| ANR rate | < 0.1% |
| Unit test coverage | > 60% |
| Core flow e2e tests | 100% |

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 2 weeks | Auth flow working, API client |
| Phase 2 | 2 weeks | All main screens navigable |
| Phase 3 | 2 weeks | 3D viewer with discovery |
| Phase 4 | 2 weeks | Lessons and quizzes complete |
| Phase 5 | 1 week | XP and badges visible |
| Phase 6 | 1 week | Offline caching, polish |
| Testing | 1 week | All tests passing |
| Release | 1 week | Play Store submission |
| **Total** | **12 weeks** | |

---

## Post-MVP Roadmap

### Version 1.1
- Audio narration playback
- Video lessons
- Quest system
- Leaderboard

### Version 1.2
- Push notifications (daily reminder, streak alert)
- Advanced quiz types
- Social sharing

### Version 1.3
- AR mode for viewing urns
- Dark mode
- Multi-language (English)

### Version 2.0
- iOS release
- Classroom features
- Teacher dashboard