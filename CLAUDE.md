# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Luuniensuki LMS is a gamified learning platform for Vietnamese cultural heritage education, focused on the "Cửu Đỉnh" (Nine Urns) of the Nguyen Dynasty. Users explore 3D urn models, discover motifs (decorative patterns), complete lessons, and take quizzes to earn XP and badges.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.x, PostgreSQL 15, Alembic migrations
- **Frontend**: Next.js 15, React 19, Three.js/React Three Fiber, Zustand, TailwindCSS
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
```

### Frontend
```bash
cd frontend
npm run dev      # Development server on port 3000
npm run build    # Production build
npm run lint     # ESLint
npx playwright test  # E2E tests
```

### Docker
```bash
docker compose up -d              # Start all services
docker compose exec api pytest    # Run tests in container
```

## Architecture

### Backend Structure
- `backend/main.py` - FastAPI app with all API endpoints (monolithic, ~1500 lines)
- `backend/models.py` - SQLAlchemy ORM models (User, Urn, Motif, LessonContent, UserProgress, QuizQuestion, Badge, etc.)
- `backend/errors.py` - Custom AppError exception with structured JSON responses
- `backend/seed.py` - Database seeder from JSON/Markdown files in `data/`
- `backend/security.py` - JWT token creation and password hashing

### Frontend Structure
- `frontend/src/stores/` - Zustand stores (authStore, motifStore) with localStorage persistence
- `frontend/src/lib/api.js` - API client functions
- `frontend/src/components/UrnViewer.js` - 3D urn viewer with Three.js, hotspot interaction
- `frontend/src/components/FloatingNavbar.jsx` - Bottom floating navigation with i18n (vi/en), user dropdown, language switcher
- `frontend/src/components/OnboardingModal.jsx` - First-time user onboarding wizard
- `frontend/src/components/AuthGate.jsx` - Authentication wrapper, redirects unauthenticated users to login
- `frontend/src/app/` - Next.js App Router pages

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

## Recent Bug Fixes & Updates

### Image Loading Issue (FIXED - 2025-12-18)
- **Problem**: All thumbnails (urns/motifs) returned 404
- **Root cause**: `docker-compose.yml` had wrong volume mount: `/var/www/assets:/var/www/assets:ro` (host path empty)
- **Solution**: Changed to `./ban-duc-noi:/var/www/assets/ban-duc-noi:ro` to match production config
- **Files changed**: `docker-compose.yml` line 56
- **Note**: After changing volume mounts, must run `docker compose down nginx && docker compose up -d nginx`

### 3D Viewer Height Issue (FIXED - 2025-12-18)
- **Problem**: 3D viewer on `/urns/[urnSlug]` not full height (80px gap at bottom), FloatingNavbar overlapping 3D content
- **Root cause**: `UrnExperience` uses `fixed inset-0` positioning which ignores parent padding. FloatingNavbar (80px height) was covering bottom of 3D viewer
- **Solution**: Added `pb-20` directly to `UrnExperience` container div (line 64)
- **Files changed**:
  - `frontend/src/components/UrnExperience.js` - changed `className="fixed inset-0 w-full overflow-hidden bg-black"` to include `pb-20`
- **Pattern**: Fixed-positioned elements need their own padding/margin, cannot inherit from parent layout

### UX Improvements (2025-12-18)

#### Navigation Simplification
- **Change**: Reduced FloatingNavbar from 6 to 4 items
- **New structure**: Khám Phá (Explore), Bộ Sưu Tập (Collection), Thành Tích (Achievements), Hồ Sơ (Profile)
- **Files changed**: `frontend/src/components/FloatingNavbar.jsx`
- **Rationale**: Reduce navigation overload, combine related features

#### Achievements Page
- **Change**: Created `/achievements` page combining badges + leaderboard with tab navigation
- **Features**: Tab switching between badges and leaderboard, responsive grid layout
- **Files added**: `frontend/src/app/achievements/page.jsx`
- **Rationale**: Consolidate achievement-related features in one place

#### Dashboard → Profile Rename
- **Change**: Renamed `/dashboard` to `/profile`, added redirect from old URL
- **Files changed**:
  - Renamed `frontend/src/app/dashboard/` to `frontend/src/app/profile/`
  - Updated links in `UrnExperience.js`, `LoginPage.js`
  - Added redirect route at `frontend/src/app/dashboard/page.jsx`
- **Rationale**: "Profile" is more intuitive than "Dashboard" for user settings

#### Progress Stepper in LessonSidebar
- **Change**: Added visual progress stepper showing 3 steps (Khám Phá, Bài Học, Trắc Nghiệm) with XP values
- **Features**:
  - Visual states: completed (green checkmark), current (pulsing primary), locked (gray lock)
  - Connecting lines between steps
  - XP display for each step (25, 50, 75)
- **Files changed**: `frontend/src/components/LessonSidebar.js`
- **Rationale**: Clear visual indication of learning progress and next actions

#### Motif Access Restriction
- **Change**: Undiscovered motifs cannot be accessed via direct link or click
- **Behavior**: Redirects to `/explore` with error message if motif not discovered
- **Files changed**:
  - `frontend/src/app/motif/[motifId]/page.jsx`
  - `frontend/src/app/motif/[motifId]/quiz/page.jsx`
- **Rationale**: Enforce discovery flow, prevent spoilers via URL sharing

#### Translation Files
- **Added**: Vietnamese/English translations for new features
- **Files added**:
  - `frontend/src/translations/nav.json` - Navigation labels
  - `frontend/src/translations/lesson-sidebar.json` - Sidebar tab content
  - `frontend/src/translations/homepage.json` - Smart homepage content
  - `frontend/src/translations/onboarding.json` - Updated onboarding steps
  - `frontend/src/translations/tooltips.json` - Feature tooltips
- **Rationale**: Centralize i18n content for easier maintenance

## UX Improvements (2025-12-18)

### Progress Stepper Component (Task 1.4)
- **Added**: Visual progress stepper in LessonSidebar header showing 3 steps with XP values
- **Steps**: Khám Phá (25 XP), Bài Học (50 XP), Trắc Nghiệm (75 XP)
- **Visual states**:
  - Completed: green checkmark, filled circle
  - Current: primary color with pulsing animation
  - Locked: gray with lock icon
- **Features**: Connecting lines between steps, XP display, accessibility support
- **Files changed**: `frontend/src/components/LessonSidebar.js`
- **Removed**: Old 3-column status grid (redundant with new stepper)

### Navigation Simplification (Task 1.1)
- **Reduced**: FloatingNavbar from 6 to 4 items
- **New items**: Khám Phá, Bộ Sưu Tập, Thành Tích, Hồ Sơ
- **Files changed**: `frontend/src/components/FloatingNavbar.jsx`

### Achievements Page (Task 1.2)
- **Created**: `/achievements` page combining badges + leaderboard with tab navigation
- **Features**: Tab switching, Vietnamese UI, responsive grid layout
- **Files**: `frontend/src/app/achievements/page.jsx`

### Dashboard → Profile Rename (Task 3.1)
- **Renamed**: `/dashboard` → `/profile`
- **Added**: Redirect from `/dashboard` to `/profile`
- **Files changed**:
  - `frontend/src/app/profile/` (renamed from dashboard)
  - `frontend/src/components/UrnExperience.js`
  - `frontend/src/components/LoginPage.js`

### Motif Access Restriction (NEW - 2025-12-18)
- **Implemented**: Undiscovered motifs cannot be accessed directly via URL or link
- **Behavior**:
  - Check `progressByMotifId` from motifStore
  - If status is "hidden" or undefined, show error and redirect to `/explore`
  - Users must discover motifs on 3D viewer before accessing lesson/quiz pages
- **Files changed**:
  - `frontend/src/app/motif/[motifId]/page.jsx` - added discovery check
  - `frontend/src/app/motif/[motifId]/quiz/page.jsx` - added discovery check
- **Pattern**: Client-side guard using Zustand store state + router redirect

### Translation Files (Task 1.3)
- **Created**: `frontend/src/translations/nav.json` with Vietnamese/English translations
- **Content**: Navigation labels, tab labels, empty states, loading states

## Additional AI Tools

When working on this project, use specialized AI tools for different tasks:

- **Codex CLI (`codex`)**: Use for main tasks requiring code generation, designing, and refactoring
- **Gemini CLI (`gemini`)**: Use with model `gemini-3-pro-preview` (must be this exact model) for:
  - Finding documentation
  - Writing informational content
  - Generating long text
  - i18n translations
  - UX specifications

Example usage:
```bash
# Codex for code tasks
codex "Refactor component X to use hooks"

# Gemini for content/docs
gemini -m gemini-3.0-pro "Write Vietnamese translations for navigation items"
```

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **luuniensuki-lms** (23843 symbols, 33193 relationships, 274 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/luuniensuki-lms/context` | Codebase overview, check index freshness |
| `gitnexus://repo/luuniensuki-lms/clusters` | All functional areas |
| `gitnexus://repo/luuniensuki-lms/processes` | All execution flows |
| `gitnexus://repo/luuniensuki-lms/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
