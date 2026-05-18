# Phase 4 Checklist - AI Recommendations (Deepseek)

## Scope
- Add AI-assisted recommendations and provenance tracking.
- Use Deepseek LLM API with opt-out and disclosure.

## Requirements (EARS)
- WHEN a learner completes activities THE SYSTEM SHALL recommend next motifs or quests.
- WHEN quiz performance is weak THE SYSTEM SHALL suggest remediation items.
- WHEN AI-assisted content is used THE SYSTEM SHALL store provenance and disclosure metadata.
- WHEN AI jobs fail THE SYSTEM SHALL provide status and retry capability.
- WHEN a learner opts out of personalization THE SYSTEM SHALL stop AI-driven recommendations.
- WHEN AI output is flagged THE SYSTEM SHALL support manual review.

## Backend Checklist
- [ ] P4-B1 Implement rules-based recommendation engine (non-LLM).
  - Acceptance: recommendation endpoint returns deterministic results.
- [ ] P4-B2 Add recommendations table and migration.
  - Acceptance: recommendations persist for auditing.
- [ ] P4-B3 Add ai_jobs table for AI job tracking.
  - Acceptance: AI jobs have status and retry_count.
- [ ] P4-B4 Integrate Deepseek LLM API for recommendations.
  - Acceptance: LLM output stored with provenance metadata.
- [ ] P4-B5 Add content_provenance fields on AI-assisted content.
  - Acceptance: provenance includes provider, model, and timestamp.
- [ ] P4-B6 Add content flagging and review endpoints.
  - Acceptance: flags stored and retrievable for review.
- [ ] P4-B7 Add personalization opt-out flag in user profile.
  - Acceptance: opt-out disables LLM recommendations for the user.

## Frontend Checklist
- [ ] P4-F1 Add dashboard recommendation panel.
  - Acceptance: shows next best step and can be dismissed.
- [ ] P4-F2 Add remediation cards for weak topics.
  - Acceptance: ties to quiz performance and links to lessons.
- [ ] P4-F3 Add AI disclosure badges and provenance view.
  - Acceptance: AI-assisted content is clearly labeled.

## Data and QA Checklist
- [ ] P4-Q1 Add tests for rules-based recommendations.
  - Acceptance: deterministic outputs for known inputs.
- [ ] P4-Q2 Add tests for provenance and flagging flows.
  - Acceptance: provenance stored and flags recorded.
- [ ] P4-Q3 Perform Deepseek API security and compliance review.
  - Acceptance: review completed and documented before production use.

## Notes
- Deepseek API usage requires external security review and provider policy check.
