# 22_Checklist_MVP.md — Flutter Mobile App MVP Checklist

## Overview

This document tracks the MVP (Minimum Viable Product) features required for the initial Android release of Luuniensuki LMS.

**Target Release:** Version 1.0.0  
**Estimated Timeline:** 12 weeks

---

## MVP Scope Definition

### In Scope (Must Have)
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

### Out of Scope (Post-MVP)
- ❌ Audio narration playback
- ❌ Video lesson content
- ❌ Advanced quiz types (image_select, mesh_location)
- ❌ Quest system
- ❌ Leaderboard
- ❌ Push notifications
- ❌ AR mode
- ❌ Social features
- ❌ Dark mode
- ❌ Multi-language support

---

## Phase 1: Foundation & Auth

### Project Setup
- [ ] **P1-S1** Create Flutter project with proper package name
  - Package: `com.luuniensuki.lms`
  - Min SDK: 21 (Android 5.0)
  - Target SDK: 34

- [ ] **P1-S2** Configure pubspec.yaml with all dependencies
  - flutter_riverpod, go_router, dio, hive_flutter
  - flutter_secure_storage, cached_network_image
  - model_viewer_plus, freezed_annotation

- [ ] **P1-S3** Create folder structure following Clean Architecture
  - core/, features/, routing/, shared/

- [ ] **P1-S4** Set up code generation
  - build_runner configured
  - Freezed models generating

### Core Infrastructure
- [ ] **P1-I1** Implement API constants with all endpoints
  - Base URL: https://lms.histolab.icu
  - All /api/v1 endpoints defined

- [ ] **P1-I2** Implement error classes
  - ServerException, CacheException, NetworkException
  - Failure classes (ServerFailure, NetworkFailure, AuthFailure)

- [ ] **P1-I3** Implement secure storage wrapper
  - Token storage (access, refresh)
  - Clear tokens on logout

- [ ] **P1-I4** Implement Dio client with interceptors
  - Auth interceptor (adds Bearer token)
  - Error interceptor (maps to exceptions)
  - Logging interceptor (debug mode)

- [ ] **P1-I5** Implement theme system
  - AppColors with Vietnamese imperial palette
  - AppTheme with Material 3
  - Typography configuration

### Authentication
- [ ] **P1-A1** Create Auth DTOs with Freezed
  - LoginRequestDto, RegisterRequestDto
  - UserDto, AuthResponseDto, StatsDto

- [ ] **P1-A2** Create User entity and Rank value object
  - All user properties mapped
  - Role helper getters

- [ ] **P1-A3** Implement AuthRepository
  - login, register, getCurrentUser, logout
  - Token refresh handling
  - Cache user locally

- [ ] **P1-A4** Implement AuthNotifier provider
  - AuthState (initial, loading, authenticated, unauthenticated, error)
  - Auto-check auth on app start

- [ ] **P1-A5** Create Login screen
  - Email/password form
  - Validation
  - Error display
  - Navigate to register

- [ ] **P1-A6** Create Register screen
  - Email, password, display name form
  - Validation
  - Success navigation

---

## Phase 2: Core Screens & Navigation

### Navigation
- [ ] **P2-N1** Configure GoRouter with all routes
  - Auth routes (login, register)
  - Shell routes (home, explore, collection, achievements, profile)
  - Detail routes (urn, motif, quiz)

- [ ] **P2-N2** Implement auth redirect guard
  - Redirect to login if not authenticated
  - Redirect to home if already authenticated
  - Handle returnUrl parameter

- [ ] **P2-N3** Implement MainShell with bottom navigation
  - 5 tabs: Home, Explore, Collection, Achievements, Profile
  - Vietnamese labels
  - Active state highlighting

### Screens
- [ ] **P2-H1** Implement Home screen
  - Welcome header with user name
  - XP progress card
  - Continue learning section (horizontal scroll)
  - Quick explore urns section

- [ ] **P2-E1** Implement Explore screen (Urn grid)
  - 2-column grid of urn cards
  - Thumbnail, name, progress indicator
  - Navigate to urn viewer on tap

- [ ] **P2-C1** Implement Collection screen
  - Tab filters (All, Discovered, Learned, Mastered)
  - Grid of collected motifs
  - Empty state

- [ ] **P2-A1** Implement Achievements screen
  - Badges tab with grid
  - Earned/unearned badge display

- [ ] **P2-P1** Implement Profile screen
  - User info display
  - XP progress bar
  - Rank badge
  - Logout button

### Shared Widgets
- [ ] **P2-W1** Loading skeleton components
- [ ] **P2-W2** Error widget with retry button
- [ ] **P2-W3** Empty state widget
- [ ] **P2-W4** XpBadge component
- [ ] **P2-W5** RankBadge component
- [ ] **P2-W6** CategoryChip and RarityChip

---

## Phase 3: 3D Viewer

### 3D Model Loading
- [ ] **P3-M1** Integrate model_viewer_plus package
  - GLB model loading from server URL
  - Loading progress indicator
  - Error handling for failed loads

- [ ] **P3-M2** Implement touch controls
  - Rotate (drag)
  - Zoom (pinch)
  - Pan (two-finger drag)

- [ ] **P3-M3** Create UrnViewerScreen
  - Full-screen 3D viewer
  - Transparent app bar with back button
  - Toggle hotspots visibility

### Hotspot System
- [ ] **P3-H1** Render hotspots at motif positions
  - Circle markers on model
  - Different states (undiscovered pulse, discovered check)

- [ ] **P3-H2** Implement tap detection
  - JavaScript bridge for model-viewer hotspots
  - OR Flutter overlay positioning

- [ ] **P3-H3** Handle hotspot tap events
  - Identify tapped motif
  - Trigger discovery flow

### Discovery Flow
- [ ] **P3-D1** Implement unlock API call
  - POST /progress/unlock with motif_id
  - Handle success response

- [ ] **P3-D2** Create discovery animation
  - Celebration animation
  - XP earned display
  - Motif name reveal

- [ ] **P3-D3** Update hotspot state after discovery
  - Change from undiscovered to discovered
  - Update local cache

### Motif Sidebar
- [ ] **P3-S1** Create sliding sidebar component
  - Slide in from right on motif select
  - Motif thumbnail, name, category, rarity

- [ ] **P3-S2** Display progress stepper
  - 3 steps: Discovery, Lesson, Quiz
  - Current step highlighted
  - XP values shown

- [ ] **P3-S3** Action button based on status
  - "Start Lesson" for discovered
  - "Take Quiz" for learned

---

## Phase 4: Learning Flow

### Lesson Display
- [ ] **P4-L1** Create MotifDetailScreen
  - Hero image header
  - Tab navigation (Lesson, Info)

- [ ] **P4-L2** Implement LessonTab
  - Progress stepper
  - Lesson sections (intro, description, symbolism, historical context, fun fact)
  - Image gallery (if available)

- [ ] **P4-L3** Create lesson section components
  - LessonSection with title and icon
  - FunFactCard with special styling

- [ ] **P4-L4** Implement ImageGallery
  - Horizontal thumbnail scroll
  - Fullscreen viewer with zoom
  - Swipe between images

- [ ] **P4-L5** Implement lesson completion
  - Complete lesson button
  - API call POST /progress/complete-lesson
  - XP award animation

### Quiz System
- [ ] **P4-Q1** Create QuizScreen
  - Question progress bar
  - Page view for questions
  - Navigation (next/previous)
  - Submit button

- [ ] **P4-Q2** Implement QuestionCard
  - Question text display
  - Route to correct renderer by type

- [ ] **P4-Q3** Implement MultipleChoiceRenderer
  - Radio button options
  - Selected state styling

- [ ] **P4-Q4** Implement TrueFalseRenderer
  - Two large buttons (Đúng/Sai)
  - Selected state styling

- [ ] **P4-Q5** Implement quiz submission
  - Collect all answers
  - Calculate time spent
  - POST /motifs/{id}/quiz/submit

- [ ] **P4-Q6** Create QuizResultScreen
  - Pass/fail status
  - Score percentage
  - XP earned
  - Question breakdown
  - Retry or continue options

---

## Phase 5: Gamification (MVP Subset)

### XP & Ranks
- [ ] **P5-X1** XP badge component (various sizes)
- [ ] **P5-X2** XP progress bar with rank info
- [ ] **P5-X3** XP earn animation

### Badges
- [ ] **P5-B1** Fetch all badges from API
- [ ] **P5-B2** Fetch user's earned badges
- [ ] **P5-B3** Badge card (earned/unearned states)
- [ ] **P5-B4** Badge detail bottom sheet

---

## Phase 6: Offline & Polish (MVP Subset)

### Caching
- [ ] **P6-C1** Initialize Hive on app start
- [ ] **P6-C2** Cache urns list
- [ ] **P6-C3** Cache motif details on view
- [ ] **P6-C4** Offline-first repository pattern

### Polish
- [ ] **P6-P1** Network status indicator
- [ ] **P6-P2** Global error handler
- [ ] **P6-P3** Vietnamese error messages
- [ ] **P6-P4** App icon and splash screen

---

## Testing Requirements

### Unit Tests (Minimum)
- [ ] **T-U1** AuthRepository tests (login, register, logout)
- [ ] **T-U2** Progress calculation tests
- [ ] **T-U3** Quiz scoring tests

### Widget Tests (Minimum)
- [ ] **T-W1** Login form validation
- [ ] **T-W2** ProgressStepper states
- [ ] **T-W3** QuestionCard rendering

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
- [ ] **R-B1** Release signing key generated
- [ ] **R-B2** keystore.jks secured (not in repo)
- [ ] **R-B3** Build variants configured (debug, release)
- [ ] **R-B4** ProGuard/R8 rules if needed
- [ ] **R-B5** Version code/name set (1.0.0+1)

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
- [ ] **R-V1** No debug logs in release build
- [ ] **R-V2** API pointing to production
- [ ] **R-V3** Crash reporting enabled
- [ ] **R-V4** Analytics tracking (if any)
- [ ] **R-V5** All TODO comments addressed

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