# Phase 2 Checklist - Curriculum and Quests

## Scope
- Add quests and cross-urn curriculum flows.
- Track quest progress and issue rewards.

## Requirements (EARS)
- WHEN a learner opens the quest map THE SYSTEM SHALL show available quests with prerequisites.
- WHEN a learner starts a quest THE SYSTEM SHALL create quest progress and initial status.
- WHEN quest objectives are met THE SYSTEM SHALL mark the quest complete and award rewards.
- WHEN a quest is locked THE SYSTEM SHALL show unlock criteria.
- WHEN the dashboard loads THE SYSTEM SHALL show active quest progress and next step.
- WHEN quest definitions change THE SYSTEM SHALL preserve existing learner progress.

## Backend Checklist
- [ ] P2-B1 Add quest models and migrations.
  - Acceptance: quests, quest_steps, quest_objectives, quest_rewards, quest_progress exist.
- [ ] P2-B2 Implement quest list and quest detail endpoints.
  - Acceptance: list/detail return metadata, prerequisites, and objective counts.
- [ ] P2-B3 Implement quest progress computation from existing progress tables.
  - Acceptance: progress derived from UserProgress, QuizAttempt, UrnExamAttempt.
- [ ] P2-B4 Implement quest completion and rewards.
  - Acceptance: completion awards XP/badges and issues certificates.
- [ ] P2-B5 Add dashboard quest summary endpoint.
  - Acceptance: returns active quest, completion percent, next objective.
- [ ] P2-B6 Preserve progress after quest definition updates.
  - Acceptance: existing progress remains valid when quest definitions change.

## Frontend Checklist
- [ ] P2-F1 Build quest map page with locked/unlocked states.
  - Acceptance: locked quests show prerequisites and are not startable.
- [ ] P2-F2 Build quest detail page with objectives and progress.
  - Acceptance: objective status is visible and updates on progress.
- [ ] P2-F3 Add dashboard quest widget.
  - Acceptance: active quest and next step are shown for logged-in learners.

## Data and QA Checklist
- [ ] P2-Q1 Seed 3 to 5 cross-urn quests from docs/curriculum.
  - Acceptance: seeded quests appear in quest map.
- [ ] P2-Q2 Add tests for quest progress and reward issuance.
  - Acceptance: tests cover completion and certificate issuance.

## Notes
- Quest completion should trigger certificate issuance (separate from urn exam pass).
