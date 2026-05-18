# 00_Mobile_Index.md — Flutter Mobile App Implementation Plan

This folder contains the detailed implementation plan for converting Luuniensuki LMS into a native Android app using Flutter, while reusing the existing web API.

## Project Overview

**Goal:** Create a native Android app that provides a superior mobile experience for learning about Vietnamese cultural heritage (Cửu Đỉnh), leveraging the existing backend API at `https://lms.histolab.icu`.

**Technology Stack:**
- Framework: Flutter 3.x (Dart)
- State Management: Riverpod 2.x
- 3D Rendering: flutter_3d_controller / model_viewer_plus
- HTTP Client: Dio with interceptors
- Local Storage: Hive / SharedPreferences
- Authentication: Cookie-based (matching web) + Secure Storage

## Plan Documents

### Core Planning
1. **00_Mobile_Index.md** (this file) — Overview and navigation
2. **01_Architecture_Overview.md** — App architecture, folder structure, state management (Clean Architecture + Riverpod)
3. **02_API_Integration.md** — Dio client, interceptors, DTOs, error handling

### Feature Implementation (Phases)
4. **10_Phase1_Setup_Auth.md** — Project setup, dependencies, authentication flow (2 weeks)
5. **11_Phase2_Core_Screens.md** — Home, Explore, Collection, Achievements, Profile, Navigation (2 weeks)
6. **12_Phase3_3D_Viewer.md** — 3D urn viewer with model_viewer_plus, hotspot interaction, motif discovery (2 weeks)
7. **13_Phase4_Learning_Flow.md** — Lesson display, media players, quiz system with all question types (2 weeks)
8. **14_Phase5_Gamification.md** — XP/Ranks, badges, streaks, leaderboard, quests (2 weeks)
9. **15_Phase6_Offline_Polish.md** — Hive caching, offline-first pattern, performance optimization (2 weeks)

### Quality & Release
10. **22_Checklist_MVP.md** — Complete MVP feature checklist with acceptance criteria and timeline

## Phased Delivery

### Phase 1: Foundation (Week 1-2)
- Project setup with Flutter 3.x
- Folder structure and architecture
- API client with Dio
- Authentication (login, register, session management)
- Basic navigation shell

### Phase 2: Core Screens (Week 3-4)
- Home/Dashboard screen
- Explore screen (urn grid)
- Profile screen
- Collection screen
- Bottom navigation

### Phase 3: 3D Viewer (Week 5-6)
- GLB model loading
- Touch interaction (rotate, zoom, pan)
- Hotspot rendering and tap detection
- Motif discovery flow

### Phase 4: Learning Flow (Week 7-8)
- Lesson content display
- Media playback (audio, video, images)
- Quiz system (all question types)
- Progress stepper

### Phase 5: Gamification (Week 9-10)
- XP and rank display
- Badge collection
- Streak tracking
- Leaderboard
- Quest system

### Phase 6: Polish & Release (Week 11-12)
- Offline caching
- Performance optimization
- Error handling improvements
- Play Store submission

## Key Differences from Web

| Aspect | Web (Next.js) | Mobile (Flutter) |
|--------|---------------|------------------|
| 3D Rendering | Three.js / React Three Fiber | flutter_3d_controller / model_viewer_plus |
| State | Zustand + localStorage | Riverpod + Hive |
| Navigation | Next.js App Router | GoRouter |
| Auth Storage | httpOnly cookies | flutter_secure_storage |
| Offline | Limited (PWA) | Full offline with Hive |
| Push Notifications | Not implemented | Firebase Cloud Messaging |

## API Compatibility

The Flutter app will use the same API endpoints as the web app:

| Category | Endpoints |
|----------|-----------|
| Auth | `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/me`, `/api/v1/auth/refresh` |
| Urns | `/api/v1/urns`, `/api/v1/urns/{slug}` |
| Motifs | `/api/v1/motifs/{id}`, `/api/v1/motifs/{id}/lesson` |
| Progress | `/api/v1/progress/unlock`, `/api/v1/progress/complete-lesson` |
| Quiz | `/api/v1/motifs/{id}/quiz`, `/api/v1/motifs/{id}/quiz/submit` |
| Gamification | `/api/v1/badges`, `/api/v1/leaderboard`, `/api/v1/quests` |
| User | `/api/v1/users/me/dashboard`, `/api/v1/users/me/stats` |

## Success Metrics

- **Performance:** App cold start < 3s, 3D model load < 5s
- **Reliability:** Crash-free rate > 99%
- **Engagement:** Same feature parity as web for core learning loop
- **Offline:** Cached content accessible without network

## Prerequisites

Before starting mobile development:
- [ ] Ensure all API endpoints are stable and documented
- [ ] Verify CORS allows requests from mobile (or use different auth)
- [ ] Prepare 3D model assets in GLB format
- [ ] Set up Firebase project for FCM (optional)

## Getting Started

1. Read **01_Architecture_Overview.md** for app structure and key decisions
2. Read **02_API_Integration.md** for API client setup and DTOs
3. Follow **10_Phase1_Setup_Auth.md** for initial project setup
4. Implement phases sequentially (10 → 11 → 12 → 13 → 14 → 15)
5. Track progress with **22_Checklist_MVP.md**

## Quick Reference

### Key Dependencies
```yaml
flutter_riverpod: ^2.4.9    # State management
go_router: ^13.0.0          # Navigation
dio: ^5.4.0                 # HTTP client
hive_flutter: ^1.1.0        # Local cache
model_viewer_plus: ^1.6.0   # 3D rendering
freezed: ^2.4.6             # Immutable models
```

### API Base URL
```
Production: https://lms.histolab.icu/api/v1
```

### Key Commands
```bash
# Generate code (Freezed, Riverpod)
dart run build_runner build --delete-conflicting-outputs

# Watch mode during development
dart run build_runner watch --delete-conflicting-outputs

# Build release APK
flutter build apk --release

# Build app bundle for Play Store
flutter build appbundle --release
```