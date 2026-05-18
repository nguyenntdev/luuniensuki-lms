# PHASE 1: REQUIREMENTS ANALYSIS DOCUMENT

> **Project:** Lưu Niên Sử Kí LMS  
> **Version:** 1.0  
> **Date:** 2024-12-14  
> **Status:** APPROVED

> **Repo layout note:** backend code lives in `backend/` and the working implementation guides are in `docs/implementation/`.

---

## 1. EXECUTIVE SUMMARY

### 1.1 Current State Analysis

| Component | Completion | Implemented | Missing |
|-----------|------------|-------------|---------|
| **Backend APIs** | 12% | 6 endpoints | 44+ endpoints |
| **Database Models** | 85% | All models | Migrations |
| **Frontend Pages** | 25% | 3 pages | 10+ pages |
| **Quiz System** | 5% | Models only | Full API + UI |
| **Gamification** | 10% | XP logic | Badges, Leaderboard |
| **3D Integration** | 20% | Fallback spheres | GLB loading |
| **Testing** | 0% | None | Full coverage |
| **CI/CD** | 0% | None | GitHub Actions |

### 1.2 Existing Technical Patterns

```
Backend (FastAPI):
├── Dependency Injection: Depends(get_db), Depends(get_current_user)
├── Pydantic Models: BaseModel with ConfigDict(from_attributes=True)
├── Error Handling: HTTPException with status codes
├── Auth: JWT (access + refresh tokens)
└── Database: SQLAlchemy 2.0 with Mapped[] type hints

Frontend (Next.js 15):
├── State: Zustand with persist middleware
├── API: fetch wrapper with token injection
├── Routing: App Router (/app directory)
├── Styling: Tailwind CSS
└── 3D: React Three Fiber + Drei
```

---

## 2. DETAILED REQUIREMENTS (EARS Notation)

### 2.1 DOMAIN A: QUIZ SYSTEM

#### A.1 Quiz Question Retrieval
```
REQ-QUIZ-001: GET /api/v1/motifs/{motif_id}/quiz
├── WHEN a user requests quiz for a motif
├── AND the user has discovered this motif (status >= discovered)
├── THE SYSTEM SHALL return quiz questions with:
│   ├── question_id: UUID
│   ├── question_type: enum (multiple_choice|true_false|image_select|mesh_location)
│   ├── question_text: string
│   ├── options: array (shuffled, 4 items for multiple_choice)
│   ├── difficulty: int (1-5)
│   └── target_mesh_name: string (for mesh_location type only)
├── AND shuffle options order randomly
└── IF user has not discovered motif THEN return 403 Forbidden
```

#### A.2 Quiz Submission
```
REQ-QUIZ-002: POST /api/v1/quiz/submit
├── WHEN a user submits quiz answers
├── WITH payload:
│   ├── motif_id: UUID
│   ├── answers: array of { question_id: UUID, answer: string }
│   └── time_taken_seconds: int
├── THE SYSTEM SHALL:
│   ├── Validate each answer against correct_answer
│   ├── Calculate score percentage
│   ├── Create QuizAttempt record
│   ├── Award XP based on score:
│   │   ├── score >= 70%: +100 XP, status → learned
│   │   ├── score = 100%: +50 XP bonus, status → mastered
│   │   └── score < 70%: +10 XP (participation)
│   └── Return detailed results with explanations
└── RESPONSE:
    ├── attempt_id: UUID
    ├── score: float (0.0-1.0)
    ├── xp_earned: int
    ├── new_status: enum
    ├── results: array of { question_id, correct, user_answer, correct_answer, explanation }
    └── badges_earned: array (if any)
```

#### A.3 Lesson Completion
```
REQ-QUIZ-003: POST /api/v1/motifs/{motif_id}/complete-lesson
├── WHEN a user completes reading lesson content
├── THE SYSTEM SHALL:
│   ├── Update UserProgress.lesson_viewed_at = now()
│   ├── Return quiz_unlocked: true
│   └── Award +10 XP for lesson completion
└── IF lesson already viewed THEN skip XP award
```

#### A.4 Quiz History
```
REQ-QUIZ-004: GET /api/v1/users/me/quiz-history
├── WHEN a user requests their quiz history
├── THE SYSTEM SHALL return paginated list of attempts:
│   ├── attempt_id, motif_id, motif_name
│   ├── score, xp_earned, passed (bool)
│   ├── time_taken_seconds
│   └── created_at
└── SUPPORT query params: ?motif_id=&limit=20&offset=0
```

---

### 2.2 DOMAIN B: GAMIFICATION (Badges & Achievements)

#### B.1 Badge Definitions (Seed Data)
```
REQ-BADGE-001: Badge Categories
├── discovery: First discoveries, exploration milestones
├── collection: Collection completion (per urn, per category)
├── mastery: Quiz performance, perfect scores
├── streak: Daily activity consistency
└── special: Hidden achievements, events
```

#### B.2 Badge Criteria Table
```
| Badge Slug              | Category   | Criteria                           | XP Bonus |
|-------------------------|------------|---------------------------------------|----------|
| first_discovery         | discovery  | Discover 1 motif                      | 50       |
| explorer_10             | discovery  | Discover 10 motifs                    | 100      |
| explorer_50             | discovery  | Discover 50 motifs                    | 250      |
| explorer_100            | discovery  | Discover 100 motifs                   | 500      |
| cao_complete            | collection | All motifs in Cao Đỉnh                | 200      |
| nhan_complete           | collection | All motifs in Nhân Đỉnh               | 200      |
| ... (all 9 urns)        | collection | ...                                   | 200      |
| linh_thu_master         | collection | All Linh Thú category                 | 300      |
| thao_moc_master         | collection | All Thảo Mộc category                 | 300      |
| ... (all 9 categories)  | collection | ...                                   | 300      |
| quiz_perfect_1          | mastery    | 1 perfect quiz score                  | 75       |
| quiz_perfect_10         | mastery    | 10 perfect quiz scores                | 200      |
| streak_7                | streak     | 7-day streak                          | 100      |
| streak_30               | streak     | 30-day streak                         | 500      |
| streak_100              | streak     | 100-day streak                        | 1000     |
| night_owl               | special    | Learn after midnight                  | 50       |
| speed_learner           | special    | Complete quiz in <30 seconds          | 75       |
| collector_complete      | special    | 100% collection (162 motifs)          | 2000     |
```

#### B.3 Badge API Endpoints
```
REQ-BADGE-002: GET /api/v1/users/me/badges
├── WHEN a user requests their badges
├── THE SYSTEM SHALL return:
│   ├── earned: array of { badge, earned_at }
│   ├── available: array of { badge, progress, criteria }
│   └── total_badge_xp: int
└── Group by category for display

REQ-BADGE-003: GET /api/v1/badges
├── WHEN anyone requests badge catalog
├── THE SYSTEM SHALL return all badges with:
│   ├── slug, name, name_en, description
│   ├── icon_url, category
│   └── is_hidden (for secret badges)
└── Hidden badges show "???" until earned

REQ-BADGE-004: POST /api/v1/badges/check (Internal)
├── WHEN any XP-awarding action completes
├── THE SYSTEM SHALL:
│   ├── Query all unearned badges for user
│   ├── Check each badge's criteria
│   ├── Award badge if criteria met
│   └── Return newly earned badges for notification
└── Run as background task (async)
```

---

### 2.3 DOMAIN C: LEADERBOARD SYSTEM

#### C.1 Leaderboard Retrieval
```
REQ-LEAD-001: GET /api/v1/leaderboard
├── WHEN a user requests leaderboard
├── WITH query params:
│   ├── period: all_time | weekly | monthly (default: all_time)
│   ├── limit: int (default: 50, max: 100)
│   └── offset: int (default: 0)
├── THE SYSTEM SHALL return:
│   ├── entries: array of { rank, user_id, display_name, avatar_url, total_xp, level }
│   ├── current_user: { rank, total_xp } (even if not in top)
│   └── total_users: int
└── Order by total_xp DESC, created_at ASC (tiebreaker)
```

#### C.2 Weekly/Monthly Reset Logic
```
REQ-LEAD-002: Periodic Leaderboard Calculation
├── WHEN period=weekly requested
├── THE SYSTEM SHALL:
│   ├── Sum XP earned from QuizAttempts where created_at >= week_start
│   ├── Add XP from UserProgress updates in same period
│   └── Cache result for 5 minutes
└── Weekly resets: Monday 00:00 UTC+7
```

---

### 2.4 DOMAIN D: STREAK SYSTEM

#### D.1 Streak Calculation
```
REQ-STREAK-001: Streak Update Logic
├── WHEN a user performs any learning activity:
│   ├── Discovers a motif
│   ├── Completes a lesson
│   ├── Submits a quiz
│   └── Views lesson content
├── THE SYSTEM SHALL:
│   ├── Check if user has activity today (UTC+7)
│   ├── IF first activity today:
│   │   ├── IF yesterday had activity: current_streak += 1
│   │   ├── ELSE IF missed 1 day AND has freeze: use freeze, keep streak
│   │   └── ELSE: current_streak = 1
│   ├── Update longest_streak if current > longest
│   └── Update last_active_at = now()
└── Store last_streak_date in user record
```

#### D.2 Streak API
```
REQ-STREAK-002: GET /api/v1/users/me/streak
├── THE SYSTEM SHALL return:
│   ├── current_streak: int
│   ├── longest_streak: int
│   ├── last_active_date: date
│   ├── streak_freezes_available: int (max 2)
│   ├── streak_at_risk: bool (true if no activity today and streak > 0)
│   └── days_until_next_badge: int
└── Include streak badge progress

REQ-STREAK-003: POST /api/v1/users/me/streak/freeze
├── WHEN user activates streak freeze
├── THE SYSTEM SHALL:
│   ├── Decrement streak_freezes_available
│   ├── Set streak_frozen_until = tomorrow
│   └── Return updated streak info
└── IF no freezes available THEN return 400
```

---

### 2.5 DOMAIN E: URN & MOTIF APIS

#### E.1 Urns Listing
```
REQ-URN-001: GET /api/v1/urns
├── THE SYSTEM SHALL return all 9 urns with:
│   ├── id, slug, name, name_han
│   ├── represents, description
│   ├── thumbnail_url, model_url
│   ├── display_order
│   ├── motif_count: int (total)
│   └── user_progress: { discovered, learned, mastered } (if authenticated)
└── Order by display_order ASC
```

#### E.2 Single Urn Detail
```
REQ-URN-002: GET /api/v1/urns/{slug}
├── THE SYSTEM SHALL return urn detail with:
│   ├── All fields from URN-001
│   ├── motifs: array (with progress status if authenticated)
│   └── completion_percentage: float
└── IF not found THEN return 404
```

#### E.3 Motif Detail
```
REQ-MOTIF-001: GET /api/v1/motifs/{motif_id}
├── THE SYSTEM SHALL return:
│   ├── id, urn_id, mesh_name, name, name_en
│   ├── category, rarity
│   ├── pos_x, pos_y, pos_z, bounding_radius
│   ├── cam_pos_x, cam_pos_y, cam_pos_z
│   ├── cam_look_at_x, cam_look_at_y, cam_look_at_z
│   ├── thumbnail_url, silhouette_url
│   ├── lesson: { intro_text, description, historical_context, symbolism, fun_fact }
│   ├── quiz_question_count: int
│   └── user_progress: { status, discovered_at, learned_at, mastered_at, xp_earned }
└── Return silhouette_url only if not discovered
```

#### E.4 Motif Search
```
REQ-MOTIF-002: GET /api/v1/motifs/search
├── WITH query params:
│   ├── q: string (search name, name_en, description)
│   ├── category: enum (optional)
│   ├── rarity: enum (optional)
│   ├── urn_id: UUID (optional)
│   └── limit, offset
├── THE SYSTEM SHALL return matching motifs
└── Use PostgreSQL full-text search (ts_vector)
```

---

### 2.6 DOMAIN F: COLLECTION (Pokédex)

#### F.1 Full Collection View
```
REQ-COLL-001: GET /api/v1/users/me/collection
├── ALREADY IMPLEMENTED (partial)
├── ENHANCE to include:
│   ├── Filter by: urn_slug, category, rarity, status
│   ├── Sort by: discovered_at, name, rarity
│   └── Pagination: limit, offset
└── Return silhouette for undiscovered
```

#### F.2 Collection Statistics
```
REQ-COLL-002: GET /api/v1/users/me/collection/stats
├── THE SYSTEM SHALL return:
│   ├── total_motifs: 162
│   ├── discovered: int, learned: int, mastered: int
│   ├── by_urn: array of { urn_slug, total, discovered, learned, mastered }
│   ├── by_category: array of { category, total, discovered, learned, mastered }
│   ├── by_rarity: array of { rarity, total, discovered }
│   └── completion_percentage: float
└── Cache result for 1 minute
```

---

### 2.7 DOMAIN G: USER PROFILE

#### G.1 Profile Detail
```
REQ-PROF-001: GET /api/v1/users/me/profile
├── THE SYSTEM SHALL return:
│   ├── user: { id, email, display_name, avatar_url, role, created_at }
│   ├── stats: { total_xp, rank, xp_to_next_rank }
│   ├── streak: { current, longest, last_active }
│   ├── collection: { discovered, learned, mastered, total }
│   ├── badges: { earned_count, recent_badges }
│   ├── quiz: { attempts, avg_score, perfect_count }
│   └── activity: { days_active, favorite_urn, favorite_category }
└── Aggregate from multiple tables
```

#### G.2 Profile Update
```
REQ-PROF-002: PATCH /api/v1/users/me/profile
├── WITH payload:
│   ├── display_name: string (optional)
│   └── avatar_url: string (optional)
├── THE SYSTEM SHALL validate and update
└── Return updated profile
```

#### G.3 Public Profile (Optional)
```
REQ-PROF-003: GET /api/v1/users/{user_id}/public
├── THE SYSTEM SHALL return (if user allows):
│   ├── display_name, avatar_url
│   ├── rank, total_xp
│   ├── badges (public only)
│   └── collection_count
└── Hide if user.is_public = false
```

---

### 2.8 DOMAIN H: ADMIN PANEL

#### H.1 Access Control
```
REQ-ADMIN-001: Admin Role Check
├── WHEN any /api/v1/admin/* endpoint is called
├── THE SYSTEM SHALL:
│   ├── Verify Authorization header
│   ├── Check user.role in (admin, super_admin)
│   └── IF not authorized THEN return 403
└── Log all admin actions
```

#### H.2 Motif Management
```
REQ-ADMIN-002: CRUD /api/v1/admin/motifs
├── GET /: List all motifs with pagination
├── GET /{id}: Get motif detail (including inactive)
├── POST /: Create new motif
│   ├── Required: urn_id, mesh_name, name, category
│   └── Optional: all other fields
├── PUT /{id}: Update motif
├── DELETE /{id}: Soft delete (is_active = false)
└── POST /{id}/restore: Restore deleted motif
```

#### H.3 Quiz Question Management
```
REQ-ADMIN-003: CRUD /api/v1/admin/quiz-questions
├── GET /: List questions with filters
├── POST /: Create question
│   ├── Required: motif_id, question_type, question_text, correct_answer
│   └── For multiple_choice: options array (4 items)
├── PUT /{id}: Update question
└── DELETE /{id}: Soft delete
```

#### H.4 User Management
```
REQ-ADMIN-004: /api/v1/admin/users (super_admin only)
├── GET /: List users with filters (role, search)
├── GET /{id}: User detail with full stats
├── PATCH /{id}/role: Change user role
├── POST /{id}/ban: Ban user (role → banned)
└── POST /{id}/reset-password: Send password reset
```

#### H.5 Analytics Dashboard
```
REQ-ADMIN-005: GET /api/v1/admin/analytics
├── THE SYSTEM SHALL return:
│   ├── user_stats: { total, active_today, active_week, new_this_month }
│   ├── learning_stats: { discoveries_today, quizzes_today, avg_score }
│   ├── content_stats: { motifs_total, motifs_with_lesson, questions_total }
│   ├── engagement: { avg_session_time, retention_7d, top_motifs }
│   └── period_comparison: { xp_this_week vs last_week }
└── Cache for 5 minutes
```

---

### 2.9 DOMAIN I: INFRASTRUCTURE & TESTING

#### I.1 Database Migrations
```
REQ-INFRA-001: Alembic Setup
├── THE SYSTEM SHALL use Alembic for migrations
├── WITH:
│   ├── alembic.ini configured for PostgreSQL
│   ├── migrations/ folder with version scripts
│   └── alembic upgrade head in deploy script
└── NO more Base.metadata.create_all() in production
```

#### I.2 Testing Framework
```
REQ-TEST-001: Backend Testing
├── THE SYSTEM SHALL include:
│   ├── pytest as test runner
│   ├── pytest-asyncio for async tests
│   ├── httpx for API testing
│   ├── factory_boy for test data
│   └── pytest-cov for coverage
├── Coverage targets:
│   ├── Overall: >= 60%
│   ├── API routes: >= 80%
│   └── Models: >= 70%
└── Test database: SQLite in-memory or Docker PostgreSQL
```

#### I.3 CI/CD Pipeline
```
REQ-INFRA-002: GitHub Actions
├── .github/workflows/ci.yml:
│   ├── Trigger: push/PR to main
│   ├── Jobs: lint, typecheck, test, build
│   └── Matrix: Python 3.11, Node 20
├── .github/workflows/deploy-staging.yml:
│   └── Deploy to staging on main push
└── .github/workflows/deploy-production.yml:
    └── Deploy to prod on release tag
```

---

## 3. NON-FUNCTIONAL REQUIREMENTS

### 3.1 Performance
```
NFR-PERF-001: API response time < 200ms (p95) for list endpoints
NFR-PERF-002: API response time < 100ms (p95) for single resource
NFR-PERF-003: 3D model initial load < 3 seconds on 4G connection
NFR-PERF-004: Leaderboard query < 50ms with caching
```

### 3.2 Security
```
NFR-SEC-001: All passwords hashed with bcrypt (rounds=12)
NFR-SEC-002: JWT tokens expire (access: 60min, refresh: 30days)
NFR-SEC-003: Rate limiting: 100 requests/minute per IP
NFR-SEC-004: Input validation on all endpoints
NFR-SEC-005: SQL injection prevention via ORM
```

### 3.3 Reliability
```
NFR-REL-001: 99.9% uptime target
NFR-REL-002: Graceful degradation when 3D models fail to load
NFR-REL-003: Retry logic for API calls (3 attempts)
```

---

## 4. ACCEPTANCE CRITERIA SUMMARY

| Domain | Criteria | Measurement |
|--------|----------|-------------|
| Quiz | User can complete quiz and see results | Manual test |
| Badges | Badges auto-awarded when criteria met | Unit test |
| Leaderboard | Top 50 users displayed with current user rank | Manual test |
| Streak | Streak increments daily on activity | Integration test |
| Collection | Filter/sort works, silhouettes for hidden | Manual test |
| Admin | CRUD operations work for admin users | Integration test |
| Tests | Coverage >= 60% | CI pipeline |

---

**END OF PHASE 1 DOCUMENT**
