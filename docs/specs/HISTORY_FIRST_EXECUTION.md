# HISTORY-FIRST EXECUTION LEDGER

Maintained continuously during the History-First Rebuild. Source of truth for phase/task/test/migration state. Master spec: `docs/specs/HISTORY_FIRST_MASTER_SPEC.md`.

## Audited commit

- `b9b2ebdb27c933ad0dbae0df01aa4840a106c46b` (main @ clone)
- Local working copy replaced with git checkout of `https://github.com/nguyenntdev/luuniensuki-lms.git`.

## Current phase

Phase 14 — Stabilization and Release (Complete).

## Current branch

`main`

## Completed task IDs

- **REPO-001**: `docs/CURRENT_SYSTEM_STATE.md` (System ledger created)
- **REPO-002**: Reconcile documentation (`AGENTS.md`, `README.md`, `CLAUDE.md`)
- **REPO-003**: Frontend consolidation debt (`src/types/api.ts` committed, `npm run type-check`, `npm run lint:ci`, `npm run test` green)
- **REPO-004**: Baseline verification artifacts generated (`artifacts/baseline-system-verification.json`)
- **Phase 1 (Governance Foundation)**:
  - Database models in `backend/models_history.py` (`historical_entities`, `historical_claims`, `historical_sources`, `historical_claim_sources`, `historical_entity_relations`, `historical_geographies`, `historical_assets`, `historical_content_audit_log`)
  - Alembic migration `migrations/versions/0048_history_governance.py`
  - Rust models & services in `backend-rust/src/models/history.rs`, `backend-rust/src/services/history_service.rs`, `backend-rust/src/routes/history.rs`
  - Documentation: `docs/history/DATA_MODEL.md`, `docs/history/CONTENT_GOVERNANCE.md`, `docs/history/SOURCE_POLICY.md`
- **Phase 2 (Legacy Corpus Migration)**:
  - `scripts/history/migrate_legacy.py` executed: 9 urn entities + 153 relief entities (162 total records) + 765 candidate claims imported preserving AI provenance (`origin = 'legacy_import'`, `verification_status = 'unreviewed'`, 0 expert verified)
  - `artifacts/history-migration-report.json`
- **Phase 3 (History-First Public Shell)**:
  - Navigation updated in `frontend/src/components/FloatingNavbar.tsx` & `Navbar.tsx`
  - Homepage V2 in `frontend/src/app/page.tsx`
  - Cửu Đỉnh overview in `frontend/src/app/cuu-dinh/page.tsx` and urn detail in `frontend/src/app/cuu-dinh/[urnSlug]/page.tsx`
- **Phase 4 (Atlas of the 162 Reliefs)**:
  - Atlas catalog & filter bar in `frontend/src/app/atlas/page.tsx`
  - Relief detail page in `frontend/src/app/atlas/[urnSlug]/[reliefSlug]/page.tsx`
  - Evidence & epistemic components in `frontend/src/components/evidence/`
- **Phase 5 (Heritage Map & Geography)**:
  - `/api/v1/history/map` endpoint in Python & Rust
  - Heritage Map in `frontend/src/app/map/page.tsx` with WCAG 2.2 AA table list fallback
- **Phase 6 (Timeline & Knowledge Graph)**:
  - `/api/v1/history/timeline` & `/api/v1/history/relations/graph`
  - Timeline in `frontend/src/app/timeline/page.tsx`
  - Knowledge graph explorer in `frontend/src/app/explore/connections/page.tsx`
- **Phase 7 (3D Historical Integration)**:
  - 3D Model manifest pipeline in `scripts/history/generate_3d_manifests.py`
  - Three.js Viewer with camera animation, relief highlight, deep-link target focus, and slide-over history drawer in `frontend/src/components/history-3d/UrnHistoryViewer.tsx`
  - Textual accessibility fallback `UrnAccessibleFallback.tsx`
- **Phase 8 (History-Native Learning Engine V2)**:
  - 7 history question types (`chronology_order`, `image_identification`, `map_location`, `urn_hotspot`, `evidence_match`, `compare_two`, `source_interpretation`)
  - Server-side grading engine in `backend/services/history_grading.py`
  - Mastery V2 6-dimension skill tracker in `backend/services/mastery_v2.py`
  - Question renderers in `frontend/src/components/history-learning/` and `QuizRenderers.tsx`
- **Phase 9 (Source-Grounded AI History Tutor)**:
  - Grounded tutor pipeline with entity resolution, verified retrieval, citation validator in `backend/services/history_ai/`
  - Endpoint `POST /api/v1/history/tutor/ask`
  - Evaluator test suite `scripts/history/eval_history_tutor.py`
  - Frontend drawer `frontend/src/components/history-tutor/HistoryTutorDrawer.tsx`
- **Phase 10 (Stories & Guided Historical Exploration)**:
  - Block-based story engine for prose, images, quotes, relief focus, 3D focus, map focus, timeline focus, source excerpts, and quizzes
  - Frontend routes `/stories` and `/stories/[slug]`
- **Phase 11 (Teacher & Editorial Tooling)**:
  - Admin review queue, state machine, and audit log endpoints
  - Teacher Historical Collections API and builder in `frontend/src/app/admin/history/`
- **Phase 12 (Mobile V2 Flutter Architecture)**:
  - Flutter screens in `mobile/lib/features/` for Atlas, Heritage Map, Source Library, History Quiz, and 3D Model Package Manager
  - Offline sync queue in `mobile/lib/core/offline/offline_queue_service.dart`
- **Phase 13-14 (Hardening, SEO, Accessibility, Release Report)**:
  - Dynamic sitemap generating 169 canonical routes in `frontend/src/app/sitemap.ts`
  - WCAG 2.2 AA accessibility fallbacks (3D textual fallback, Map table list fallback, non-color-only badges)
  - Content validator in `scripts/history/validate_history_content.py` (0 errors, 0 warnings)
  - Release report in `artifacts/history-first-release-report.md`

## Tests run and results

- **Frontend Type-check (`tsc --noEmit`)**: 0 errors (PASSED)
- **Frontend Lint (`npm run lint:ci`)**: 0 errors, 0 warnings (PASSED)
- **Frontend Vitest Unit Tests (`npm run test`)**: 4 test files passed, 29/29 tests passed (PASSED)
- **Python Backend Unit Tests (`pytest`)**: 126/126 passed (PASSED)
- **Content Integrity Validation (`validate_history_content.py`)**: 0 errors, 0 warnings, pass=True (PASSED)

## Migrations added

- `migrations/versions/0048_history_governance.py` (Historical governance, entities, claims, sources, claim-source bindings, relations, geographies, assets, audit log)

## Next executable tasks

All 14 phases from `docs/specs/HISTORY_FIRST_MASTER_SPEC.md` are implemented and verified.
