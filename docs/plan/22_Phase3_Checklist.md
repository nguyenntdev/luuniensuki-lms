# Phase 3 Checklist - Admin, Teacher, and Class Management

## Scope
- Add teacher role and RBAC.
- Add class management and quest assignments.
- Add draft/publish workflow for content.
- Exclude staff from leaderboard.

## Requirements (EARS)
- WHEN a user has the teacher role THE SYSTEM SHALL allow class management and quest assignments.
- WHEN a user has the teacher role THE SYSTEM SHALL allow creating and editing content drafts but SHALL NOT allow publishing.
- WHEN a user has the admin or super_admin role THE SYSTEM SHALL allow publishing content.
- WHEN a learner or guest accesses admin endpoints THE SYSTEM SHALL deny access.
- WHEN the leaderboard is requested THE SYSTEM SHALL exclude teacher/admin/super_admin users.

## Backend Checklist
- [ ] P3-B0 Add teacher role to UserRole enum and migrate the database enum.
  - Acceptance: teacher is a valid role in API and DB.
- [ ] P3-B1 Implement RBAC checks for all admin endpoints.
  - Acceptance: teacher can edit drafts; admin/super_admin can publish.
- [ ] P3-B2 Add content draft/publish fields and enforce publish permissions.
  - Acceptance: draft content visible to teachers; publish only by admin/super_admin.
- [ ] P3-B3 Add class, membership, and assignment models with migrations.
  - Acceptance: classes and class_members tables exist.
- [ ] P3-B4 Implement class roster endpoints.
  - Acceptance: teacher can add/remove learners from classes.
- [ ] P3-B5 Implement assignment endpoints for quest-to-class mapping.
  - Acceptance: assignments are created and tracked per class.
- [ ] P3-B6 Update leaderboard query to exclude staff roles.
  - Acceptance: only learner users appear in leaderboard results.

## Frontend Checklist
- [ ] P3-F0 Update role labels and publish gating in UI.
  - Acceptance: teachers do not see publish controls.
- [ ] P3-F1 Build admin/teacher console for content drafts.
  - Acceptance: teacher can create/edit drafts; admin can publish.
- [ ] P3-F2 Build class roster and assignment management UI.
  - Acceptance: teacher can assign quests to classes.
- [ ] P3-F3 Add class progress analytics UI.
  - Acceptance: summary shows completion rates per class.

## Data and QA Checklist
- [ ] P3-Q0 Seed demo users (teacher, admin) and a sample class.
  - Acceptance: seeded roles can access their allowed pages.
- [ ] P3-Q1 Add RBAC tests for teacher vs admin publishing.
  - Acceptance: teacher publish is blocked, admin publish is allowed.
- [ ] P3-Q2 Add leaderboard test to confirm staff exclusion.
  - Acceptance: staff users do not appear in leaderboard results.
