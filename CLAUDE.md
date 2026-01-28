# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cửu Đỉnh Ký is a gamified learning platform for Vietnamese cultural heritage education, focused on the "Cửu Đỉnh" (Nine Urns) of the Nguyen Dynasty. Users explore 3D urn models, discover motifs (decorative patterns), complete lessons, and take quizzes to earn XP and badges.

**Current Version**: 1.22.0+15 (Mobile), Production domain: `cuudinh.histolab.icu`

**Development Status**: Phase 1 complete (Branding & Emoji→Icon Migration). See `TASK_PHASES.md` for roadmap.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.x, PostgreSQL 15, Alembic migrations
- **Web Frontend**: Next.js 15, React 19, Three.js/React Three Fiber, Zustand, TailwindCSS
- **Mobile App**: Flutter 3.x (SDK ^3.5.4), Riverpod 2.x, GoRouter 13.x, Hive, Freezed, model_viewer_plus for 3D
- **Infrastructure**: Docker Compose, Nginx reverse proxy

## Common Commands

### Backend
```bash
# Run tests (requires test DB: luuniensuki_test)
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_test" pytest tests/backend -v

# Run single test
pytest tests/backend/test_auth.py::test_register -v

# Seed database
python -m backend.seed --seed-path data --image-path ban-duc-noi

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### Web Frontend
```bash
cd frontend
npm run dev      # Development server on port 3000
npm run build    # Production build
npm run lint     # ESLint
npx playwright test  # E2E tests
```

### Mobile App (Flutter)
```bash
cd mobile
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs  # Generate Freezed/Riverpod code
flutter run                                                       # Run app
flutter build apk --release                                       # Build Android APK (requires key.properties)
flutter build apk --debug                                         # Build debug APK (uses shared debug keystore)

# Run single test
flutter test test/widget_test.dart

# Analyze code
flutter analyze
```

### Docker
```bash
docker compose up -d              # Start all services
docker compose exec api pytest    # Run tests in container
```

## Architecture

### Backend Structure
- `backend/main.py` - FastAPI app with all API endpoints (monolithic, 17000+ lines)
- `backend/models.py` - SQLAlchemy ORM models (User, Urn, Motif, LessonContent, UserProgress, QuizQuestion, Badge, etc.)
- `backend/schemas.py` - Pydantic request/response schemas
- `backend/errors.py` - Custom AppError exception with structured JSON responses
- `backend/seed.py` - Database seeder from JSON/Markdown files in `data/`
- `backend/security.py` - JWT token creation and password hashing (bcrypt, 12 rounds)
- `backend/rbac.py` - Role-Based Access Control (guest < learner < teacher < admin < super_admin)
- `backend/services/` - Business logic services:
  - `hearts.py` - Duolingo-style hearts/energy system
  - `spaced_repetition.py` - SM-2 algorithm for review scheduling
  - `adaptive_quiz.py` - ELO-like skill level tracking
  - `streak.py` - Daily streak tracking with freeze feature
  - `weekly_quests.py` - Weekly challenge system
  - `learning_path.py` - Personalized daily learning recommendations

### Web Frontend Structure
- `frontend/src/stores/` - Zustand stores (authStore, motifStore) with localStorage persistence
- `frontend/src/lib/api.js` - API client with automatic token refresh on 401
- `frontend/src/components/UrnViewer.js` - 3D urn viewer with Three.js, hotspot interaction
- `frontend/src/components/FloatingNavbar.jsx` - Bottom floating navigation with i18n (vi/en)
- `frontend/src/components/OnboardingModal.jsx` - First-time user onboarding wizard
- `frontend/src/components/AuthGate.jsx` - Authentication wrapper, redirects to login
- `frontend/src/app/` - Next.js App Router pages

### Mobile App Structure (Flutter)
- `mobile/lib/core/` - Core utilities (network, storage, theme, constants)
- `mobile/lib/features/` - Feature modules (auth, explore, quiz, hearts, gems, streak, etc.)
- `mobile/lib/routing/app_router.dart` - GoRouter configuration with auth guards
- `mobile/lib/shared/` - Shared widgets and services
- Uses Clean Architecture: Presentation → Domain → Data layers
- State management: Riverpod with code generation (@riverpod annotation)
- Offline-first pattern: Hive local storage with network sync

#### Mobile Feature Module Structure
Each feature in `mobile/lib/features/` follows Clean Architecture:
```
features/
  quiz/
    data/           # DTOs, repositories, datasources
    domain/         # Entities, use cases (if needed)
    presentation/   # Screens, widgets, providers
      providers/    # @riverpod annotated state management
      screens/      # Full-page widgets
      widgets/      # Reusable UI components
```

### Key Data Flow
1. User clicks hotspot sphere on 3D urn → `unlockFromClick()` in motifStore
2. POST `/progress/unlock` → creates/updates UserProgress, awards XP, checks badges
3. Response updates Zustand store → UI reflects discovered status

## Domain-Specific Logic

### XP System
- Discovery: 25 XP, Lesson: 50 XP, Mastered (quiz pass): 75 XP
- Quiz pass threshold: 80%
- XP ranks defined in `XP_RANKS` array (Vietnamese titles: Lính Mới → Sử Quan)

### Unlock Status Flow
`hidden` → `discovered` (tap hotspot) → `learned` (complete lesson) → `mastered` (pass quiz)

### Badge Awards
Badges are awarded automatically in `_award_badge()` during unlock/lesson/quiz actions:
- `first-discovery`, `first-mastered`, `streak-7`, `collector-10/50`, `explorer-all-urns`, `quiz-master`, `speed-demon`, `perfect-score`

### Hearts System (Duolingo-style)
- Max 5 hearts, lose 1 on wrong quiz answer
- Auto-refill: 1 heart every 4 hours (240 minutes)
- Unlimited hearts mode available via purchase/streak freeze
- Heart transactions logged for analytics
- Service: `backend/services/hearts.py`

### Gems System (Virtual Currency)
- Earned: lesson completion, streaks, perfect scores
- Spent: streak freeze, double XP, hints
- Mobile-only: local Hive storage with transaction history
- Initial balance: 100 gems for new users

### Spaced Repetition (SM-2 Algorithm)
- Quality rating: 0-5 (≥3 is successful review)
- Ease factor: min 1.3, default 2.5
- Initial interval: 1 day, second interval: 6 days
- Formula: `new_ease = current_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))`
- Service: `backend/services/spaced_repetition.py`

### Adaptive Quiz (ELO-like)
- Skill level: 0.0 to 1.0 (default 0.5)
- K-factor for skill updates
- Difficulty normalization: 1-5 → 0.0-1.0
- Questions selected based on recommended difficulty ± tolerance
- Service: `backend/services/adaptive_quiz.py`

### Motif Positioning
- Motifs have `pos_x/y/z` and `bounding_radius` for 3D hotspot placement
- If positions are (0,0,0), UrnViewer falls back to circular arrangement formula
- `tap_position` validation was removed - users click directly on positioned hotspot spheres

### Lesson Content Structure
- Fields: `intro_text`, `description`, `historical_context`, `symbolism`, `fun_fact`
- Recommended display order: Intro → Description → Symbolism → Historical Context → Fun Fact
- Vietnamese section headers: Giới thiệu, Mô tả chi tiết, Ý nghĩa biểu tượng, Bối cảnh lịch sử, Điều thú vị

### Seed Data
- JSON files in `data/` contain motif definitions with Vietnamese/English names, categories, lessons, quiz questions
- Images in `ban-duc-noi/` are matched to motifs via slug fuzzy matching
- `IMAGE_SLUG_ALIASES` handles known naming mismatches

### Role-Based Access Control (RBAC)
Role hierarchy: `guest < learner < teacher < admin < super_admin`
- **guest**: View public/demo content only
- **learner**: Access lessons, quizzes, progress tracking
- **teacher**: Create/edit content, manage classes, submit for review
- **admin**: Approve content, manage RAG, view analytics
- **super_admin**: Full access including audit logs, user management

## API Patterns

### Error Response Format
All errors return structured JSON:
```json
{"error": {"code": "ERROR_CODE", "message": "Human message", "details": {}}}
```

### Authentication
- JWT tokens with `type: "access"` or `type: "refresh"`
- Tokens are stored in httpOnly cookies (`luuniensuki_access`, `luuniensuki_refresh`)
- `/api/v1/auth/refresh` rotates cookies for silent renewal
- OAuth2PasswordBearer header support is retained for tests/backward compatibility
- Guest users (`role: "guest"`) can only access `is_demo: true` motifs
- Access token expires in 60 minutes, refresh token in 30 days

## Testing

### Backend Tests
- Use `conftest.py` fixtures: `db_session` (transactional), `client` (TestClient), `seeded_content`
- Tests run in transaction that rolls back after each test
- Test DB must exist: `luuniensuki_test`

### E2E Tests
- Playwright tests in `frontend/e2e/`
- Requires frontend dev server running on port 3000

## Special Logic & Edge Cases

### AuthGate & Hydration Pattern
- `AuthGate` component wraps all pages in `layout.jsx`
- Public paths: `/login`, `/register` (defined in `PUBLIC_PATH_PREFIXES`)
- Calls `useAuthStore.bootstrap()` to resolve auth status via `/api/v1/auth/me`
- Wrapped in `<Suspense>` to avoid Next.js static generation errors with `useSearchParams()`
- Unauthenticated users redirected to `/login?returnUrl=<original-path>`
- Server-side gating enforced in `frontend/middleware.ts` using access/refresh cookies

### Zustand Store Persistence
- `authStore`: no token persistence; session is cookie-based
- `motifStore`: persists `foundByMotifId`, `progressByMotifId` to localStorage key `luuniensuki-motif-progress`
- `motifStore` uses `createJSONStorage(() => localStorage)` with version tracking

### Badge Award System
- Badges are checked and awarded in `_award_badge()` function in `backend/main.py`
- Badge slugs: `first-discovery`, `first-mastered`, `streak-7`, `collector-10`, `collector-50`, `explorer-all-urns`, `quiz-master`, `speed-demon`, `perfect-score`
- Badge awards are idempotent - checks for existing UserBadge before creating
- Badge XP bonus is added to user's total_xp immediately upon award
- Badge checks happen during: unlock, complete-lesson, and quiz submission

### Streak System
- `_update_streak()` function updates user's current_streak and longest_streak
- Streak increments if last_active_at was exactly 1 day ago
- Streak resets to 1 if gap is > 1 day
- Streak freeze feature allows users to protect their streak (uses `streak_freezes` counter)
- Streak freeze sets `last_active_at` to yesterday to preserve streak continuity
- Streak is updated on any progress action (unlock, lesson, quiz)

### XP Award Logic
- XP is awarded incrementally: DISCOVERY_XP (25) → LESSON_XP (50) → MASTERED_XP (75)
- Each motif tracks `xp_earned` to prevent duplicate awards
- If user already has partial XP, only the delta is awarded
- Badge XP bonuses are added on top of base XP
- Total XP determines user rank (Vietnamese titles from "Lính Mới" to "Sử Quan")

### Race Condition Handling
- `unlock_progress()` and `complete_lesson()` have IntegrityError retry blocks
- On IntegrityError: rollback → re-fetch progress → re-apply updates → commit
- This handles concurrent requests from same user (e.g., double-click on mobile)
- Badge awards are recalculated in retry block to ensure consistency

### Motif Discovery Counting
- `_count_user_discoveries()` counts motifs with status != hidden
- Used for collector badges (10, 50 discoveries)
- Also tracks unique urns discovered for explorer-all-urns badge (requires 9 urns)
- Counts are computed during unlock to check badge thresholds

### Quiz Scoring
- Quiz pass threshold: 80% (QUIZ_PASS_PERCENT constant)
- Score calculation: exact string match between submitted answer and correct_answer (both stripped)
- Percentage rounded to nearest integer
- Quiz attempts are always recorded in QuizAttempt table, even if failed
- Best score is tracked in UserProgress.quiz_best_score
- `speed-demon` badge: complete quiz in ≤30 seconds
- `quiz-master` badge: 10 perfect (100%) quiz scores

### Guest User Restrictions
- Guest users (role="guest") can only access motifs/urns with `is_demo=true`
- Enforced in unlock_progress, complete_lesson, and quiz endpoints
- Returns 403 Forbidden if guest tries to access non-demo content

### Hotspot Positioning Logic
- Motifs have `pos_x`, `pos_y`, `pos_z`, `bounding_radius` fields
- If all positions are (0,0,0), UrnViewer uses circular arrangement fallback
- Hotspot spheres are rendered at exact motif positions
- `tap_position` validation was removed - users click directly on hotspot spheres
- Hotspot radius scales with `bounding_radius` (min 0.08, default 0.12)

### Image Resolution & Fuzzy Matching
- `scan_images()` in seed.py scans `ban-duc-noi/` directory structure
- Images matched to motifs via slugified names
- `IMAGE_SLUG_ALIASES` dict handles known mismatches (e.g., "ngu-tinh" → "moc-tinh-hoa-tinh...")
- Fuzzy matching uses `difflib.get_close_matches()` with 0.85 cutoff
- If multiple matches, requires 0.05 ratio difference to auto-select

### Enum Coercion in Seed Data
- `coerce_enum()` handles various input formats: kebab-case, snake_case, spaces
- Tries: raw value → normalized (replace - and space with _) → slugified
- Falls back to default if no match found
- Used for MotifCategory, MotifRarity, QuestionType enums

### Vietnamese Text Handling
- `slugify()` function: NFKD normalization → remove combining chars → đ→d → lowercase → replace non-alphanumeric with -
- Motif names stored in both Vietnamese (`name`) and English (`name_en`)
- UI primarily Vietnamese with i18n support in FloatingNavbar

### API Client Error Handling
- `apiRequest()` in `frontend/src/lib/api.js` extracts error messages from structured JSON responses
- Checks `data.error.message` first, then `data.detail`
- Falls back to HTTP status text if JSON parsing fails

### FloatingNavbar i18n Pattern
- Translations object with `vi` and `en` keys
- `t(key)` function returns translated string
- Language state persisted in component, not global store
- User dropdown shows avatar (or initial), display name, logout button

### Onboarding System
- `OnboardingModal` checks localStorage key `hasSeenOnboarding`
- 4-step wizard: Welcome, 3D Exploration, Learning Flow, Gamification
- First-time tooltips in UrnViewer check `hasSeenViewerTips`

### Password Security
- bcrypt with 12 rounds for hashing
- Maximum password length: 72 bytes (bcrypt limitation)
- Passwords exceeding limit rejected at hash time, return false at verify time

## Important Patterns to Preserve

### Motif Access Restriction
- Undiscovered motifs cannot be accessed directly via URL
- Client-side guard in `frontend/src/app/motif/[motifId]/page.jsx` and `quiz/page.jsx`
- Checks `progressByMotifId` from motifStore - redirects to `/explore` if status is "hidden" or undefined
- Pattern: Zustand store state + router redirect

### Fixed-Position Layout Considerations
- Fixed-positioned elements (like `UrnExperience` with `fixed inset-0`) ignore parent padding
- Must apply bottom padding (`pb-20`) directly to fixed container for FloatingNavbar clearance
- FloatingNavbar height: 80px

### Docker Volume Mounts
- Static assets served from Nginx require correct volume mounts
- Production pattern: `./ban-duc-noi:/var/www/assets/ban-duc-noi:ro`
- After changing volume mounts: `docker compose down nginx && docker compose up -d nginx`

### Translation Files Location
- `frontend/src/translations/` contains JSON files for i18n (nav.json, lesson-sidebar.json, homepage.json, onboarding.json, tooltips.json)
- Use centralized translation files rather than inline translation objects

## Mobile App Special Patterns

### Riverpod Provider Patterns
- Use `@Riverpod(keepAlive: true)` for providers that should persist across navigation (auth, router, dio, storage)
- Use `@riverpod` (default) for feature-specific providers that can be disposed
- Generated code files have `.g.dart` suffix - run `build_runner` after changes
- Use `ref.invalidate(provider)` to force refresh a provider's data

### Persistent Cookie Authentication
- Session persistence is achieved via `PersistCookieJar` stored at `{AppDocuments}/.cookies/`
- Must call `await initPersistCookieJar()` in `main()` before `runApp()`
- Authentication cookies (`luuniensuki_access`, `luuniensuki_refresh`) are httpOnly
- `hasValidSession()` checks for auth cookie presence as primary method
- On logout, call `cookieJar.deleteAll()` to clear persistent cookies

### 3D Model Viewer JavaScript Bridge
- `CustomModelViewer` widget wraps `model_viewer_plus` with custom JavaScript handlers
- JavaScript-to-Dart communication via `javascriptChannels` with channel name `ModelViewerChannel`
- Race condition fix: check both `load` event AND `.loaded` property for model load detection
- Safety timeout: 120 seconds for large GLB models (60-80MB)
- Hotspot tap detection: JavaScript sends `{type: 'hotspotTap', motifId: '...'}` message

### Quiz Heart Penalty Deduplication
- `_incorrectAnswers` map tracks questions that already deducted hearts
- Pattern: check `!_incorrectAnswers.containsKey(questionId)` before calling `loseHeart()`
- Prevents multiple heart losses on re-selecting wrong answer for same question
- State saved to provider via `markIncorrect(questionId)` for persistence

### Daily Goal Midnight Reset
- `DailyGoal.shouldReset(now)` checks if `lastUpdated` is from a previous day
- Reset logic: keep `level`, reset `currentXp` to 0, set `isCompleted` to false
- `getTimeUntilMidnight()` returns Duration for UI countdown display
- Gems awarded (20) when daily goal is completed for the first time that day

### Gems System (Mobile-Only)
- Initial balance: 100 gems for new users
- Transaction types: `earnedBonus`, `earnedStreak`, `spentRefill`, `spentHint`, `spentStreakFreeze`
- Balance and transactions persisted in Hive storage
- `addGems()` and `spendGems()` return `bool` indicating success

### Hearts Auto-Refill Timer
- Timer runs every 1 minute checking if hearts need refilling
- Refill rate: 1 heart every 240 minutes (4 hours)
- `HeartState.autoRefill()` calculates hearts gained based on elapsed time
- Timer is cancelled in `ref.onDispose()` to prevent memory leaks

### Sync Service for Offline Operations
- `SyncService` queues operations when offline for later sync
- Operations stored in Hive box with retry count (max 3 retries)
- Listens to connectivity changes via `connectivity_plus`
- Operation types: `unlockMotif`, `completeLesson`, `submitQuiz`, `updateProgress`

### GoRouter Auth Guard Pattern
- `redirect` callback checks `authNotifierProvider` state
- Returns `null` to allow navigation, or path string to redirect
- Onboarding check: `storage.hasSeenOnboarding()` gates first-time flow
- Return URL encoding: `Uri.encodeComponent(state.matchedLocation)`

## Android Build Configuration

### Debug Keystore (Team Development)
- Shared `mobile/android/debug.keystore` prevents "app not installed" errors across dev machines
- Default credentials: password `android`, alias `androiddebugkey`
- If missing, falls back to system default debug keystore

### Release Keystore Setup
1. Create keystore: `keytool -genkey -v -keystore release-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias release`
2. Copy `mobile/android/key.properties.template` to `key.properties`
3. Fill in actual passwords and keystore path
4. NEVER commit `key.properties` to version control

### ProGuard Rules
- Custom rules in `mobile/android/app/proguard-rules.pro`
- Keeps: Flutter engine, Firebase, Dio/OkHttp, Hive, model_viewer_plus
- Removes: Android logging in release builds
- Release build enables `minifyEnabled true` and `shrinkResources true`
