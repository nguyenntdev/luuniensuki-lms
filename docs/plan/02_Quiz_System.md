# 02_Quiz_System.md

## Goal

Implement the **quiz loop** that upgrades a motif from `discovered → learned → mastered` and awards XP/badges.

This is the “core LMS” gameplay loop; without quizzes the product is only a “viewer”.

## Current State

- DB models exist:
  - `QuizQuestion`
  - `QuizAttempt`
  - `UserProgress` already has `quiz_attempts`, `quiz_best_score`, `learned_at`, `mastered_at`
- Seed script currently imports some quiz questions (multiple-choice only).
- **No quiz APIs** exist yet.
- Frontend has no quiz pages/components.

## UX Flow (Target)

1. User unlocks motif in 3D → status `discovered`.
2. User reads lesson → status `learned` (new endpoint).
3. User takes quiz:
   - pass threshold → status `mastered`
   - fail → stay `learned` (or `discovered` if you allow quiz without lesson)
4. XP/rank updates; optional badge awards.

## Backend API Design

### 1) Fetch quiz questions

- **BE-QUIZ-01**: `GET /api/v1/motifs/{motif_id}/quiz`
  - Auth required (recommended). If guest support is desired, allow for demo motifs only.
  - Response:
    - motif metadata
    - list of active questions
    - for each question: **do not include `correct_answer`**
  - Options should be shuffled server-side (deterministic shuffle can be added later).

### 2) Submit quiz attempt

- **BE-QUIZ-02**: `POST /api/v1/quizzes/submit`
  - Auth required.
  - Request includes:
    - `motif_id`
    - `answers`: `[{question_id, answer}]`
    - `time_taken_seconds`
  - Server responsibilities:
    - load questions (active only)
    - validate answers reference the given motif questions
    - compute score + pass/fail
    - insert `QuizAttempt`
    - update `UserProgress`:
      - increment `quiz_attempts`
      - update `quiz_best_score` if improved
      - set `mastered_at` + `status=mastered` if passed (and not already mastered)
    - award XP:
      - choose a policy (see next section)
    - return per-question result breakdown (safe to include correct answer *after* submit).

### 3) Lesson completion (dependency)

Quiz depends on a “learned” state if we want an LMS-like flow.

- **BE-LESSON-01** (from backend backlog): `POST /api/v1/motifs/{motif_id}/complete-lesson`

## XP & Progression Policy (Proposed)

Keep it simple and consistent; tweak later based on retention metrics.

### Discovery XP (already implemented)

- On first unlock: `DISCOVERY_XP = 25`

### Lesson XP (new)

- On first lesson completion: `LESSON_XP = 25`
- Only awarded once per motif (idempotent).

### Quiz XP (new)

Two safe options:

**Option A — One-time mastery bonus**
- If user passes threshold for the first time:
  - award `MASTERY_XP = 50` (or 75)
- If user re-takes quiz: no more XP (but `QuizAttempt` recorded).

**Option B — Best-score bonus (bounded)**
- XP earned = `floor(MAX_QUIZ_XP * score_percent)` but only for **improvements** above prior best.
- This encourages retries without allowing farming.

Recommended to start with **Option A** for simplicity.

### Pass Threshold

- Start: `PASS_PERCENT = 70`
- Can later be dynamic by difficulty.

## Data Requirements (QuizQuestion)

For `multiple_choice`:
- `question_text` (required)
- `options` (list[str], required)
- `correct_answer` (string, must be one of options)
- `explanation` (optional)

For `true_false`:
- `options = ["True", "False"]`
- `correct_answer = "True" | "False"`

Future question types (later phase):
- `mesh_location`: answer is a mesh name or region label; requires `target_mesh_name`
- `image_select`: answer is an asset id/url

## Task Breakdown (Ticket-Sized)

### Backend

- [ ] **BE-QUIZ-00**: Create `backend/routers/quiz.py` + `backend/schemas/quiz.py` (or equivalent module split)
- [ ] **BE-QUIZ-01**: Implement `GET /api/v1/motifs/{motif_id}/quiz`
- [ ] **BE-QUIZ-02**: Implement `POST /api/v1/quizzes/submit`
- [ ] **BE-QUIZ-03**: Implement XP awarding policy + status transition rules
- [ ] **BE-QUIZ-04**: Add rate limits (per user) for submits (optional, but recommended)

### Frontend

- [ ] **FE-QUIZ-00**: Add API client functions: `getQuiz(motifId)`, `submitQuiz(...)`
- [ ] **FE-QUIZ-01**: Page `frontend/src/app/motif/[motifId]/quiz/page.jsx`
- [ ] **FE-QUIZ-02**: Components:
  - `QuizContainer`
  - `MultipleChoiceQuestion`
  - `QuizResults`
- [ ] **FE-QUIZ-03**: Integrate with `UserProfile`/collection refresh after mastery

### Testing

- [ ] **TEST-QUIZ-01**: backend unit tests:
  - fetch quiz questions hides correct answers
  - submit computes correct score
  - status transitions correct
  - XP idempotent rules enforced
- [ ] **TEST-QUIZ-02**: minimal e2e manual script (curl) for register → unlock → complete-lesson → submit quiz

## Definition of Done (Quiz MVP)

- A logged-in user can complete a quiz and see results + updated XP.
- Motif progress transitions to `mastered` when passing.
- Tests cover at least:
  - unauthorized access
  - invalid question IDs
  - duplicate submissions do not double-award mastery XP

