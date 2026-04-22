# Phase 1 Checklist - Core Loop Completion and Certificates

## Scope
- Finish lesson media support and advanced quiz interactions.
- Issue certificates for urn exam passes.
- Add public certificate verification.

## Requirements (EARS)
- WHEN lesson content has audio_narration_url THE SYSTEM SHALL render audio playback and log a play event.
- WHEN lesson content has video_url THE SYSTEM SHALL render video playback and log a play event.
- WHEN lesson content has additional_images THE SYSTEM SHALL render a responsive image gallery.
- WHEN a quiz question type is image_select THE SYSTEM SHALL display selectable images and submit the selected option.
- WHEN a quiz question type is mesh_location THE SYSTEM SHALL allow mesh selection and submit a mesh identifier.
- WHEN a learner passes an urn exam THE SYSTEM SHALL issue a certificate.
- WHEN a certificate is accessed by public code THE SYSTEM SHALL show verification details.

## Backend Checklist
- [ ] P1-B1 Add certificates model and migration.
  - Acceptance: certificates table exists with unique certificate_code and issuer_name.
- [ ] P1-B2 Issue certificate on urn exam pass (idempotent).
  - Acceptance: passing urn exam creates exactly one certificate per urn per learner.
- [ ] P1-B3 Add public certificate verification endpoint.
  - Acceptance: verify response includes status, issuer, learner display name, issue date.
- [ ] P1-B4 Add analytics events for media playback and advanced quiz actions.
  - Acceptance: analytics endpoint receives events for audio/video play and advanced quiz answers.
- [ ] P1-B5 Ensure quiz API returns required fields for new renderers.
  - Acceptance: quiz responses include question_type, options, target_mesh_name when needed.
- [ ] P1-B6 Handle missing mesh annotations in mesh_location questions.
  - Acceptance: API indicates missing data so UI can fall back to list selection.

## Frontend Checklist
- [ ] P1-F1 Render audio playback when audio_narration_url is present.
  - Acceptance: audio player renders and does not break when URL is missing.
- [ ] P1-F2 Render video playback when video_url is present.
  - Acceptance: video player renders and does not break when URL is missing.
- [ ] P1-F3 Render image gallery when additional_images exist.
  - Acceptance: gallery is responsive and handles empty array.
- [ ] P1-F4 Add image_select quiz renderer.
  - Acceptance: user can pick an image option and submit the answer.
- [ ] P1-F5 Add mesh_location quiz renderer with fallback.
  - Acceptance: mesh selection works when annotations exist; fallback list works otherwise.
- [ ] P1-F6 Add certificate verification page.
  - Acceptance: public page renders verification status and issuer name.

## Data and QA Checklist
- [ ] P1-Q1 Seed sample media content for at least one motif.
  - Acceptance: at least one lesson displays audio/video/gallery.
- [ ] P1-Q2 Add tests for certificate issuance and verification.
  - Acceptance: test covers idempotent issuance and verify payload.
- [ ] P1-Q3 Add UI smoke checks for new quiz types.
  - Acceptance: image_select and mesh_location render and submit without errors.

## Notes
- Issuer name for certificates must be exactly: Lưu Niên Sử Kí (use this exact string when setting issuer_name).
- Quest-based certificate issuance is handled in Phase 2.
