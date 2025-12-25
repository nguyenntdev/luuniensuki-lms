# TASK_PHASES - Full 4-Phase Execution Task List

This file consolidates all tasks across Phases 1-4.
Detailed acceptance criteria live in:
- docs/plan/20_Phase1_Checklist.md
- docs/plan/21_Phase2_Checklist.md
- docs/plan/22_Phase3_Checklist.md
- docs/plan/23_Phase4_Checklist.md

## Phase 1 - Core Loop Completion and Certificates
### Backend
- [ ] P1-B1 Add certificates model and migration.
- [ ] P1-B2 Issue certificate on urn exam pass (idempotent).
- [ ] P1-B3 Public certificate verification endpoint.
- [ ] P1-B4 Analytics for media playback and advanced quiz actions.
- [ ] P1-B5 Quiz API returns required fields for new renderers.
- [ ] P1-B6 Handle missing mesh annotations for mesh_location.

### Frontend
- [ ] P1-F1 Render audio playback.
- [ ] P1-F2 Render video playback.
- [ ] P1-F3 Render additional images gallery.
- [ ] P1-F4 image_select quiz renderer.
- [ ] P1-F5 mesh_location quiz renderer with fallback.
- [ ] P1-F6 Certificate verification page.

### Data and QA
- [ ] P1-Q1 Seed sample media content.
- [ ] P1-Q2 Tests for certificate issuance and verification.
- [ ] P1-Q3 UI smoke checks for new quiz types.

## Phase 2 - Curriculum and Quests
### Backend
- [ ] P2-B1 Quest models and migrations.
- [ ] P2-B2 Quest list/detail endpoints.
- [ ] P2-B3 Quest progress computation.
- [ ] P2-B4 Quest completion and rewards (certificate issuance included).
- [ ] P2-B5 Dashboard quest summary endpoint.
- [ ] P2-B6 Preserve progress after quest definition updates.

### Frontend
- [ ] P2-F1 Quest map page.
- [ ] P2-F2 Quest detail page.
- [ ] P2-F3 Dashboard quest widget.

### Data and QA
- [ ] P2-Q1 Seed initial quests.
- [ ] P2-Q2 Tests for quest progress and rewards.

## Phase 3 - Admin, Teacher, and Class Management
### Backend
- [ ] P3-B0 Add teacher role to enum and migrate DB.
- [ ] P3-B1 RBAC checks for admin and teacher routes.
- [ ] P3-B2 Draft/publish fields and publish enforcement.
- [ ] P3-B3 Class and membership models.
- [ ] P3-B4 Class roster endpoints.
- [ ] P3-B5 Assignment endpoints.
- [ ] P3-B6 Leaderboard excludes staff roles.

### Frontend
- [ ] P3-F0 Role labels and publish gating.
- [ ] P3-F1 Admin/teacher console for drafts.
- [ ] P3-F2 Class roster and assignments UI.
- [ ] P3-F3 Class progress analytics UI.

### Data and QA
- [ ] P3-Q0 Seed demo users and classes.
- [ ] P3-Q1 RBAC tests for teacher vs admin publish.
- [ ] P3-Q2 Leaderboard staff exclusion test.

## Phase 4 - AI Recommendations (Deepseek)
### Backend
- [ ] P4-B1 Rules-based recommendation engine.
- [ ] P4-B2 Recommendations table and migration.
- [ ] P4-B3 AI jobs table.
- [ ] P4-B4 Deepseek LLM integration for recommendations.
- [ ] P4-B5 Content provenance fields.
- [ ] P4-B6 Content flagging and review endpoints.
- [ ] P4-B7 Personalization opt-out flag.

### Frontend
- [ ] P4-F1 Dashboard recommendation panel.
- [ ] P4-F2 Remediation cards.
- [ ] P4-F3 AI disclosure badges.

### Data and QA
- [ ] P4-Q1 Recommendation tests.
- [ ] P4-Q2 Provenance and flagging tests.
- [ ] P4-Q3 Deepseek API security/compliance review.

## Dependencies
- Phase 1 must complete before Phase 2.
- Phase 2 must complete before Phase 3.
- Phase 4 can start after Phase 2 and should align with Phase 3 governance.
