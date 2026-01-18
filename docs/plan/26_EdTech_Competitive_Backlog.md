# EdTech Competitive Backlog (Retention-Focused)

## Goals and KPI Targets
- Activation: first lesson started < 60s, first quiz completed < 5 min
- Retention: D1, D7, D30 (track by cohort and segment)
- Engagement: WAU/MAU, streak adoption, quest completion rate
- Learning: lesson completion rate, quiz pass rate, time-on-task
- Content: weekly new content cadence, time-to-publish

## Scope
This backlog translates competitive feature needs into concrete tasks across Phase 0/1/2.

---

## Phase 0 (Weeks 1-4) - Foundation + Activation

### Epic: Activation and Onboarding
- [ ] P0-ACT-01: Add onboarding goal selection (2-3 prompts) and store user goal
- [ ] P0-ACT-02: Build "first task" flow that starts lesson within 60s
- [ ] P0-ACT-03: Create first-lesson CTA on dashboard for new users
- [ ] P0-ACT-04: Add "continue learning" targeting based on last activity

### Epic: Habit Loop (Daily/Weekly)
- [ ] P0-HAB-01: Define Daily Mission schema and progress tracking
- [ ] P0-HAB-02: Implement Weekly Quest templates + assignment flow
- [ ] P0-HAB-03: Add streak rules and daily reward for completion
- [ ] P0-HAB-04: Add basic notification schedule (streak + continue learning)

### Epic: Content Pipeline + CMS V1
- [ ] P0-CMS-01: Standardize lesson template (intro, context, symbolism, fun fact)
- [ ] P0-CMS-02: Add quiz template with difficulty and tags
- [ ] P0-CMS-03: Add content versioning metadata (version, editor, published_at)
- [ ] P0-CMS-04: Add review workflow states (draft, review, published)
- [ ] P0-CMS-05: Add content tagging for recommendation and search

### Epic: RAG/AI Admin V1
- [ ] P0-RAG-01: Expose RAG settings in admin with defaults + validation
- [ ] P0-RAG-02: Add RAG file upload, edit, activate/deactivate
- [ ] P0-RAG-03: Add "rebuild embeddings" with progress feedback
- [ ] P0-RAG-04: Add RAG health panel (coverage, last updated)

### Epic: Analytics Foundation
- [ ] P0-ANA-01: Define event taxonomy for activation, lesson, quiz, streak
- [ ] P0-ANA-02: Add server-side event logging (user_id, session_id, cohort)
- [ ] P0-ANA-03: Add basic KPI dashboard (D1, D7, D30, completion rate)
- [ ] P0-ANA-04: Add funnel: view lesson -> start -> complete -> quiz -> pass

### Epic: Mobile Performance and Reliability
- [ ] P0-MOB-01: Add caching for lesson payloads and images
- [ ] P0-MOB-02: Add retry/backoff for network calls + offline fallback UI
- [ ] P0-MOB-03: Add app-level health check and error banner

### Epic: Trust and Safety
- [ ] P0-SEC-01: Add admin audit log for content changes and AI usage
- [ ] P0-SEC-02: Add role-based access control for CMS + RAG

---

## Phase 1 (Weeks 5-12) - Retention and Growth

### Epic: Adaptive Learning
- [ ] P1-ADA-01: Build adaptive quiz engine (difficulty ramping, pools)
- [ ] P1-ADA-02: Add question performance tracking per user
- [ ] P1-ADA-03: Add remediation suggestions after incorrect answers

### Epic: Recommendations V1
- [ ] P1-REC-01: Add "next best lesson" model (rules + behavior signals)
- [ ] P1-REC-02: Add recommendation cards on dashboard and lesson end screen
- [ ] P1-REC-03: Add reason tags for recommendations

### Epic: AI Tutor (RAG + Citations)
- [ ] P1-AI-01: Add tutor endpoint that uses RAG sources with citations
- [ ] P1-AI-02: Add user-facing AI tutor screen with history
- [ ] P1-AI-03: Add AI quality guardrails (toxicity filter + safe prompt)
- [ ] P1-AI-04: Add AI usage analytics (prompt, response, status)

### Epic: Teacher Tools
- [ ] P1-TEA-01: Add assignment scheduling per class (due dates, reminders)
- [ ] P1-TEA-02: Add gradebook view (completion, quiz score)
- [ ] P1-TEA-03: Export CSV for class progress and quiz results

### Epic: Social Reinforcement
- [ ] P1-SOC-01: Add class-based leaderboard (weekly + all-time)
- [ ] P1-SOC-02: Add badge sharing and milestone highlights
- [ ] P1-SOC-03: Add peer feedback flow (controlled templates)

### Epic: Analytics and Experimentation
- [ ] P1-EXP-01: Add A/B testing framework for onboarding + notifications
- [ ] P1-EXP-02: Add cohort analysis views for retention and conversion
- [ ] P1-EXP-03: Add content performance dashboard (drop-off points)

---

## Phase 2 (Weeks 13-24) - Differentiation

### Epic: 3D Interactive Learning
- [ ] P2-3D-01: Add hotspot-based lessons on 3D models
- [ ] P2-3D-02: Add interactive tasks tied to specific motifs
- [ ] P2-3D-03: Add progress tracking per 3D interaction

### Epic: AI Authoring
- [ ] P2-AUTH-01: Add lesson/quiz auto-generation templates
- [ ] P2-AUTH-02: Add review queue for AI-generated content
- [ ] P2-AUTH-03: Add quality scoring and human approval workflow

### Epic: Community + UGC (Moderated)
- [ ] P2-UGC-01: Add user notes or annotations per lesson/motif
- [ ] P2-UGC-02: Add moderation queue and report/flag flow
- [ ] P2-UGC-03: Add community contribution badges

### Epic: Parent/Org Reporting
- [ ] P2-REP-01: Monthly report email with class progress summary
- [ ] P2-REP-02: Admin export for organization-level KPIs

### Epic: Growth Loops
- [ ] P2-GRO-01: Add referral and invite flow
- [ ] P2-GRO-02: Add campaign landing variants and tracking

---

## Dependencies and Order Notes
- RAG admin and embeddings rebuild must be stable before AI tutor and authoring.
- Analytics events are required before A/B testing and cohort analysis.
- Adaptive quiz requires question metadata (difficulty + tags).
- Teacher tools depend on reliable class and assignment data.

## Deliverables
- Each epic should ship with acceptance criteria and basic QA checklist.
- All Phase 0 tasks required before large-scale growth campaigns.
